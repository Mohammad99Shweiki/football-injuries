"""
Transfermarkt via its JSON API (tmapi.transfermarkt.technology), through the transfermarkt-api SDK.

Every upstream response is recorded to disk by `RecordReplayTransport` and replayed on later runs, so the stored
JSON is the dataset and re-runs cost nothing. SDK calls are only used to navigate (club and player IDs).

We call the SDK's low-level client (`Transfermarkt._client`, a `TfmktClient`) instead of the high-level methods:
- T2 `club_players()` also fetches every squad member's transfer history (~40 extra requests per club);
  `club_squad()` is a single request.
- T3 upstream returns a player's full injury history in one response; the SDK's 15-per-page split is local.
- T4/T5 `player_stats()` and `player_matches()` are both computed from `/player/{id}/performance-game`, which
  lists every match of the player's club in all competitions (including matches he missed). One request per
  player therefore serves both the season stats and the club fixtures; T5 needs no requests of its own.
"""

import argparse
import asyncio
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import httpx
from transfermarkt_api import Transfermarkt
from transfermarkt_api.exceptions import TransfermarktError
from transfermarkt_api.tfmkt import TfmktClient

from collect.common import (
    AdaptiveThrottle,
    Collector,
    Counter,
    FetchStatus,
    Manifest,
    RateLimiter,
    RetryPolicy,
    RunContext,
    Selection,
    add_selection_args,
    atomic_write,
    log,
    run_bounded,
    utc_now_iso,
)
from collect.config import RAW_DIR, League
from collect.status import StatusReporter

OUT_DIR = RAW_DIR / "transfermarkt"
SOURCE = "transfermarkt"
KEY = "tm"
BATCH_SIZE = 100  # same chunk size the SDK uses for batch routes
WORKERS = 32  # coroutines in flight; the transport's limiter decides how many requests actually run
PROGRESS_EVERY = 500
# Hop-by-hop or encoding headers that would be wrong for a response rebuilt from a decoded body.
DROP_ON_REPLAY = {"content-encoding", "content-length", "transfer-encoding", "connection"}


class DryRunMiss(Exception):
    """Raised by the transport in dry-run mode when a response is not on disk."""


# --------------------------------------------------------------------------- raw response store


class ResponseStore:
    """Maps a request (method + full URL) to a JSON record on disk and back."""

    _READABLE_QUERY = re.compile(r"[\w.=&-]{1,40}")

    def __init__(self, root: Path = OUT_DIR) -> None:
        self.root = root

    def path_for(self, request: httpx.Request) -> Path:
        segments = [s for s in request.url.path.split("/") if s] or ["index"]
        name = segments[-1]
        if query := unquote(request.url.query.decode()):
            suffix = query if self._READABLE_QUERY.fullmatch(query) else hashlib.sha1(query.encode()).hexdigest()[:16]
            name += "__" + suffix.replace("&", "__")
        if request.method != "GET":
            name = f"{request.method}__{name}"
        return self.root.joinpath(*segments[:-1], f"{name}.json")

    def load(self, request: httpx.Request) -> dict | None:
        path = self.path_for(request)
        if not path.exists():
            return None
        record = json.loads(path.read_text(encoding="utf-8"))
        same_request = record.get("method") == request.method and record.get("url") == str(request.url)
        return record if same_request else None

    def save(self, request: httpx.Request, response: httpx.Response) -> Path:
        path = self.path_for(request)
        record = {
            "method": request.method,
            "url": str(request.url),
            "status": response.status_code,
            "headers": {k: v for k, v in response.headers.items() if k.lower() != "set-cookie"},
            "fetched_at": utc_now_iso(),
            "body": response.text,
        }
        atomic_write(path, json.dumps(record, ensure_ascii=False).encode("utf-8"))
        return path

    @staticmethod
    def to_response(record: dict, request: httpx.Request) -> httpx.Response:
        fetched_at = datetime.strptime(record["fetched_at"], "%Y-%m-%dT%H:%M:%SZ")
        return httpx.Response(
            record["status"],
            headers={k: v for k, v in record["headers"].items() if k.lower() not in DROP_ON_REPLAY},
            content=record["body"].encode("utf-8"),
            request=request,
            # The SDK reads this to report data age; naive UTC, as it expects.
            extensions={"transfermarkt_fetched_at": fetched_at},
        )


# --------------------------------------------------------------------------- record/replay transport


class RecordReplayTransport(httpx.AsyncBaseTransport):
    """
    Replays stored responses; otherwise fetches (throttled, with retries), records 200/404 responses, and returns.

    Blocks (403, 429, any `x-amzn-waf-action` header, or an empty 202 challenge) trigger the throttle's
    pause-and-halve; 5xx and network errors back off exponentially. Failures are logged and the last response is
    returned so the SDK raises its usual error.
    """

    def __init__(
        self,
        store: ResponseStore,
        throttle: AdaptiveThrottle,
        ctx: RunContext,
        *,
        retry: RetryPolicy = RetryPolicy(),
        dry_run: bool = False,
        inner: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.store, self.throttle, self.retry, self.dry_run = store, throttle, retry, dry_run
        self.manifest, self.reporter = ctx.manifest, ctx.reporter
        self.inner = inner or httpx.AsyncHTTPTransport()
        self.stats = Counter()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if (record := self.store.load(request)) is not None:
            self.stats.add("cached")
            self.reporter.request(KEY, str(request.url), status=record["status"], nbytes=len(record["body"]), result="Replayed from disk")
            return self.store.to_response(record, request)
        if self.dry_run:
            self.stats.add("would_fetch")
            self.reporter.request(KEY, str(request.url), status=None, nbytes=0, result="Planned")
            raise DryRunMiss(str(request.url))
        return await self._fetch(request)

    async def _fetch(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        last: httpx.Response | None = None
        error = ""
        for attempt in range(1, self.retry.max_attempts + 1):
            try:
                async with self.throttle.limiter:
                    response = await self.inner.handle_async_request(request)
                    try:
                        await response.aread()  # decodes gzip/br per content-encoding
                    finally:
                        await response.aclose()
            except httpx.TransportError as exc:
                error = f"{type(exc).__name__}: {exc}"
                self._retrying(url, None, error, attempt)
                await asyncio.sleep(self.retry.delay(attempt))
                continue

            last = response
            if block := self._block(response):
                reason, waf_action = block
                error = reason
                self.throttle.on_block(reason, status=response.status_code, waf_action=waf_action)
                self._retrying(url, response.status_code, reason, attempt)
                continue  # the limiter's pause delays the next attempt
            if response.status_code == 200 and response.content:
                return self._record(request, response, FetchStatus.OK)
            if response.status_code == 404:
                return self._record(request, response, FetchStatus.NOT_FOUND)
            error = f"HTTP {response.status_code}" + ("" if response.content else " (empty body)")
            if response.status_code != 200 and not self.retry.is_retryable(response.status_code):
                break
            self._retrying(url, response.status_code, error, attempt)
            await asyncio.sleep(self.retry.delay(attempt))

        self.stats.add("failed")
        status = last.status_code if last else None
        self.manifest.log(SOURCE, url, None, FetchStatus.FAILED, status, error=error)
        self.reporter.request(KEY, url, status=status, nbytes=0, result="Failed")
        log(SOURCE, f"FAILED {url}: {error}")
        if last is None:
            raise httpx.ConnectError(error, request=request)
        return self._rebuild(last, request)

    def _retrying(self, url: str, status: int | None, error: str, attempt: int) -> None:
        if attempt < self.retry.max_attempts:
            self.reporter.request(KEY, url, status=status, nbytes=0, result=f"{error} — retry {attempt}/{self.retry.max_attempts}")

    def _record(self, request: httpx.Request, response: httpx.Response, status: FetchStatus) -> httpx.Response:
        path = self.store.save(request, response)
        self.manifest.log(SOURCE, str(request.url), path, status, response.status_code, len(response.content))
        self.reporter.request(KEY, str(request.url), status=response.status_code, nbytes=len(response.content), result="Fetched")
        self.throttle.on_success()
        self.stats.add("fetched")
        return self.store.to_response(json.loads(path.read_text(encoding="utf-8")), request)

    @staticmethod
    def _rebuild(response: httpx.Response, request: httpx.Request) -> httpx.Response:
        headers = {k: v for k, v in response.headers.items() if k.lower() not in DROP_ON_REPLAY}
        return httpx.Response(response.status_code, headers=headers, content=response.content, request=request)

    @staticmethod
    def _block(response: httpx.Response) -> tuple[str, str] | None:
        """(reason, WAF action) when upstream challenged or refused the request."""
        if waf := response.headers.get("x-amzn-waf-action"):
            return f"WAF action '{waf}' (HTTP {response.status_code})", waf
        if response.status_code == 202 and not response.content:
            return "WAF challenge (empty 202)", "challenge"
        if response.status_code in (403, 429):
            return f"HTTP {response.status_code}", ""
        return None

    async def aclose(self) -> None:
        await self.inner.aclose()


# --------------------------------------------------------------------------- collection steps


@dataclass(frozen=True)
class ClubSeason:
    league: League
    season: int
    club_id: str


# Rough sizes used for totals until T1/T2 tell us the real ones (squads list ~37 players; ~13 unique per club-season
# once players are deduplicated across seasons).
EST_CLUBS_PER_LEAGUE_SEASON = 20
EST_UNIQUE_PLAYERS_PER_CLUB_SEASON = 13


class TmProgress:
    """Turns step results into dashboard progress: step bars, source totals and the league-season coverage board."""

    def __init__(self, reporter: StatusReporter, pairs: list[tuple[League, int]]) -> None:
        self.reporter, self.pairs = reporter, pairs
        self.done = Counter()
        self.clubs = len(pairs) * EST_CLUBS_PER_LEAGUE_SEASON
        self.players = 0
        self.players_known = False
        self._remaining: dict[tuple[League, int], int] = {}
        self._failed: set[tuple[League, int]] = set()
        self._total_of: dict[tuple[League, int], int] = {}
        self._player_pairs: dict[str, list[tuple[League, int]]] = {}
        self._jobs_left: dict[str, int] = {}
        self._job_failed: set[str] = set()

    def total(self) -> int:
        players = self.players if self.players_known else self.clubs * EST_UNIQUE_PLAYERS_PER_CLUB_SEASON
        return len(self.pairs) + self.clubs + 2 * players

    def start(self) -> None:
        self.reporter.source_started(KEY, total=self.total(), estimate=True, rate="4 conc · ~4/s")
        self.reporter.step("T1", done=0, total=len(self.pairs), sub="running")

    def t1_done(self, pair: tuple[League, int], failed: bool) -> None:
        self.done.add("T1")
        self.reporter.source_progress(KEY, failed=failed)
        self.reporter.coverage(KEY, *pair, "failed" if failed else "running", "clubs listed" if not failed else "T1 failed")
        self.reporter.step("T1", done=self.done["T1"], total=len(self.pairs), sub="running")

    def t1_finished(self, club_seasons: int) -> None:
        self.clubs = club_seasons
        self.reporter.step("T1", done=self.done["T1"], total=len(self.pairs), sub="done", state="done")
        self.reporter.step("T2", done=0, total=club_seasons, sub="running")
        self.reporter.source_total(KEY, total=self.total(), estimate=True)

    def t2_done(self, failed: bool) -> None:
        self.done.add("T2")
        self.reporter.source_progress(KEY, failed=failed)
        self.reporter.step("T2", done=self.done["T2"], total=self.clubs, sub="running")

    def t2_finished(self, squads: dict[ClubSeason, list[str]], selected: list[str]) -> None:
        """Map league-seasons to their (selected) players so each board cell knows when its player work is done."""
        self.reporter.step("T2", done=self.done["T2"], total=self.clubs, sub="done", state="done")
        chosen = set(selected)
        per_pair: dict[tuple[League, int], set[str]] = {}
        for cs, players in squads.items():
            per_pair.setdefault((cs.league, cs.season), set()).update(p for p in players if p in chosen)
        for pair, players in per_pair.items():
            self._remaining[pair] = self._total_of[pair] = len(players)
            for pid in players:
                self._player_pairs.setdefault(pid, []).append(pair)
            self._update_cell(pair)
        self._jobs_left = {pid: 2 for pid in selected}
        self.players, self.players_known = len(selected), True
        self.reporter.unique_players(len({p for players in squads.values() for p in players}))
        self.reporter.source_total(KEY, total=self.total(), estimate=False)
        for step in ("T3", "T4"):
            self.reporter.step(step, done=0, total=self.players, sub="running")
        self.reporter.step("T5", done=0, total=self.players, sub="built from T4 — no requests")

    def player_job_done(self, step: str, pid: str, failed: bool) -> None:
        self.done.add(step)
        self.reporter.source_progress(KEY, failed=failed)
        if failed:
            self._job_failed.add(pid)
        sub = "full history, 1 request each" if step == "T3" else "running"
        state = "done" if self.done[step] == self.players else "running"
        self.reporter.step(step, done=self.done[step], total=self.players, sub=sub if state == "running" else "done", state=state)
        if step == "T4":
            self.reporter.step("T5", done=self.done["T4"], total=self.players, sub="built from T4 — no requests", state=state)
        self._jobs_left[pid] -= 1
        if self._jobs_left[pid] == 0:
            for pair in self._player_pairs.get(pid, []):
                self._remaining[pair] -= 1
                if pid in self._job_failed:
                    self._failed.add(pair)
                self._update_cell(pair)

    def _update_cell(self, pair: tuple[League, int]) -> None:
        total, left = self._total_of[pair], self._remaining[pair]
        state = ("failed" if pair in self._failed else "done") if left == 0 else "running"
        self.reporter.coverage(KEY, *pair, state, f"{total - left:,} / {total:,} players")

    def finished(self) -> None:
        self.reporter.source_finished(KEY, note="Record + replay transport. SDK cache=None; responses keyed by method + full URL.")


class TransfermarktSteps:
    """T1-T4 on top of the SDK's low-level client. Errors are counted and logged; collection carries on."""

    def __init__(self, api: TfmktClient, transport: RecordReplayTransport, throttle: AdaptiveThrottle, progress: TmProgress) -> None:
        self.api, self.transport, self.throttle, self.progress = api, transport, throttle, progress
        self.errors = Counter()

    async def _call[R](self, step: str, what: str, call: Any) -> tuple[bool, R | None]:
        """(ok, result). Dry-run misses count as ok: nothing failed, nothing was fetched."""
        try:
            return True, await call
        except DryRunMiss:
            return True, None
        except (TransfermarktError, httpx.HTTPError, KeyError, TypeError) as exc:
            self.errors.add(step)
            log(SOURCE, f"{step} {what}: {type(exc).__name__}: {exc}")
            return False, None

    async def clubs(self, pairs: list[tuple[League, int]]) -> list[ClubSeason]:
        """T1: club IDs per league-season, plus club and competition records (names) in batches."""

        async def one(pair: tuple[League, int]) -> list[ClubSeason]:
            league, season = pair
            ok, data = await self._call("T1", f"{league.tm_id} {season}", self.api.competition_clubs(league.tm_id, str(season)))
            self.progress.t1_done(pair, failed=not ok)
            return [ClubSeason(league, season, str(club_id)) for club_id in (data or {}).get("clubIds", [])]

        club_seasons = [cs for batch in await run_bounded(pairs, one, WORKERS) for cs in batch]
        await self._batches("T1", self.api.competitions, sorted({league.tm_id for league, _ in pairs}))
        await self._batches("T1", self.api.clubs, sorted({cs.club_id for cs in club_seasons}))
        self.progress.t1_finished(len(club_seasons))
        log(SOURCE, f"T1 done: {len(club_seasons)} club-seasons from {len(pairs)} league-seasons")
        return club_seasons

    async def squads(self, club_seasons: list[ClubSeason]) -> dict[ClubSeason, list[str]]:
        """T2: squad per club-season (player IDs), plus player records (names) in batches."""

        async def one(cs: ClubSeason) -> list[str]:
            ok, data = await self._call("T2", f"club {cs.club_id} {cs.season}", self.api.club_squad(cs.club_id, str(cs.season)))
            self.progress.t2_done(failed=not ok)
            return [str(member["playerId"]) for member in (data or {}).get("squad") or []]

        squads = dict(zip(club_seasons, await run_bounded(club_seasons, one, WORKERS)))
        player_ids = sorted({pid for squad in squads.values() for pid in squad}, key=int)
        await self._batches("T2", self.api.players, player_ids)
        log(SOURCE, f"T2 done: {len(player_ids)} unique players from {len(club_seasons)} squads")
        return squads

    async def player_histories(self, player_ids: list[str]) -> None:
        """T3 + T4 (and T5): injury history and per-match performance for every player."""
        jobs = [(step, pid) for pid in player_ids for step in ("T3", "T4")]
        done = 0

        async def one(job: tuple[str, str]) -> None:
            nonlocal done
            step, pid = job
            call = self.api.player_injuries(pid) if step == "T3" else self.api.player_performance_games(pid)
            ok, _ = await self._call(step, f"player {pid}", call)
            self.progress.player_job_done(step, pid, failed=not ok)
            done += 1
            if done % PROGRESS_EVERY == 0 or done == len(jobs):
                log(SOURCE, f"T3/T4 {done}/{len(jobs)} | {self.transport.stats} | {self.throttle.describe()}")

        await run_bounded(jobs, one, WORKERS)

    async def _batches(self, step: str, route: Any, ids: list[str]) -> None:
        """Call a batch route in fixed chunks so one failing chunk doesn't lose the rest."""
        chunks = [ids[i : i + BATCH_SIZE] for i in range(0, len(ids), BATCH_SIZE)]
        await run_bounded(chunks, lambda chunk: self._call(step, f"batch of {len(chunk)}", route(chunk)), WORKERS)


class TransfermarktCollector(Collector):
    name = SOURCE
    key = KEY

    def __init__(self, ctx: RunContext, *, max_players: int | None = None) -> None:
        super().__init__(ctx)
        self.max_players = max_players

    async def run(self, selection: Selection) -> None:
        pairs = selection.pairs()
        progress = TmProgress(self.ctx.reporter, pairs)
        progress.start()
        # Start at 4 concurrent / 4 req/s; after 500 clean responses ramp to 8 concurrent / 7 req/s.
        limiter = RateLimiter(rate=4, concurrency=4, gate=self.ctx.gate)
        throttle = AdaptiveThrottle(limiter, max_rate=7, max_concurrency=8, reporter=self.ctx.reporter)
        transport = RecordReplayTransport(ResponseStore(), throttle, self.ctx, dry_run=selection.dry_run)
        # cache=None: the disk store replaces the SDK's in-memory cache. The SDK's own semaphore is set above
        # WORKERS so that the transport's limiter is the only effective cap.
        async with Transfermarkt(transport=transport, cache=None, max_concurrency=WORKERS * 2, timeout=30) as tm:
            steps = TransfermarktSteps(tm._client, transport, throttle, progress)
            club_seasons = await steps.clubs(pairs)
            squads = await steps.squads(club_seasons)
            player_ids = sorted({pid for squad in squads.values() for pid in squad}, key=int)
            if self.max_players:
                player_ids = player_ids[: self.max_players]
            progress.t2_finished(squads, player_ids)
            log(SOURCE, f"T3/T4: {len(player_ids)} players ({len(player_ids) * 2} requests at most)")
            await steps.player_histories(player_ids)
        progress.finished()
        log(SOURCE, f"done: {transport.stats}; errors by step: {steps.errors}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_selection_args(parser)
    parser.add_argument("--players", type=int, help="T3/T4 for at most N players (smoke test)")
    args = parser.parse_args()
    collector = TransfermarktCollector(RunContext(Manifest()), max_players=args.players)
    asyncio.run(collector.run(Selection.from_args(args)))


if __name__ == "__main__":
    main()
