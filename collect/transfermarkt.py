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
    Selection,
    add_selection_args,
    atomic_write,
    log,
    run_bounded,
    utc_now_iso,
)
from collect.config import RAW_DIR, League

OUT_DIR = RAW_DIR / "transfermarkt"
SOURCE = "transfermarkt"
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
        manifest: Manifest,
        *,
        retry: RetryPolicy = RetryPolicy(),
        dry_run: bool = False,
        inner: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.store, self.throttle, self.manifest, self.retry, self.dry_run = store, throttle, manifest, retry, dry_run
        self.inner = inner or httpx.AsyncHTTPTransport()
        self.stats = Counter()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if (record := self.store.load(request)) is not None:
            self.stats.add("cached")
            return self.store.to_response(record, request)
        if self.dry_run:
            self.stats.add("would_fetch")
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
                await asyncio.sleep(self.retry.delay(attempt))
                continue

            last = response
            if reason := self._block_reason(response):
                error = reason
                self.throttle.on_block(reason)  # the limiter's pause delays the next attempt
                continue
            if response.status_code == 200 and response.content:
                return self._record(request, response, FetchStatus.OK)
            if response.status_code == 404:
                return self._record(request, response, FetchStatus.NOT_FOUND)
            error = f"HTTP {response.status_code}" + ("" if response.content else " (empty body)")
            if response.status_code != 200 and not self.retry.is_retryable(response.status_code):
                break
            await asyncio.sleep(self.retry.delay(attempt))

        self.stats.add("failed")
        self.manifest.log(SOURCE, url, None, FetchStatus.FAILED, last.status_code if last else None, error=error)
        log(SOURCE, f"FAILED {url}: {error}")
        if last is None:
            raise httpx.ConnectError(error, request=request)
        return self._rebuild(last, request)

    def _record(self, request: httpx.Request, response: httpx.Response, status: FetchStatus) -> httpx.Response:
        path = self.store.save(request, response)
        self.manifest.log(SOURCE, str(request.url), path, status, response.status_code, len(response.content))
        self.throttle.on_success()
        self.stats.add("fetched")
        return self.store.to_response(json.loads(path.read_text(encoding="utf-8")), request)

    @staticmethod
    def _rebuild(response: httpx.Response, request: httpx.Request) -> httpx.Response:
        headers = {k: v for k, v in response.headers.items() if k.lower() not in DROP_ON_REPLAY}
        return httpx.Response(response.status_code, headers=headers, content=response.content, request=request)

    @staticmethod
    def _block_reason(response: httpx.Response) -> str | None:
        if waf := response.headers.get("x-amzn-waf-action"):
            return f"WAF action '{waf}' (HTTP {response.status_code})"
        if response.status_code == 202 and not response.content:
            return "WAF challenge (empty 202)"
        if response.status_code in (403, 429):
            return f"HTTP {response.status_code}"
        return None

    async def aclose(self) -> None:
        await self.inner.aclose()


# --------------------------------------------------------------------------- collection steps


@dataclass(frozen=True)
class ClubSeason:
    league: League
    season: int
    club_id: str


class TransfermarktSteps:
    """T1-T4 on top of the SDK's low-level client. Errors are counted and logged; collection carries on."""

    def __init__(self, api: TfmktClient, transport: RecordReplayTransport, throttle: AdaptiveThrottle) -> None:
        self.api, self.transport, self.throttle = api, transport, throttle
        self.errors = Counter()

    async def _safe[R](self, step: str, what: str, call: Any) -> R | None:
        try:
            return await call
        except DryRunMiss:
            return None
        except (TransfermarktError, httpx.HTTPError, KeyError, TypeError) as exc:
            self.errors.add(step)
            log(SOURCE, f"{step} {what}: {type(exc).__name__}: {exc}")
            return None

    async def clubs(self, pairs: list[tuple[League, int]]) -> list[ClubSeason]:
        """T1: club IDs per league-season, plus club and competition records (names) in batches."""

        async def one(pair: tuple[League, int]) -> list[ClubSeason]:
            league, season = pair
            data = await self._safe("T1", f"{league.tm_id} {season}", self.api.competition_clubs(league.tm_id, str(season)))
            return [ClubSeason(league, season, str(club_id)) for club_id in (data or {}).get("clubIds", [])]

        club_seasons = [cs for batch in await run_bounded(pairs, one, WORKERS) for cs in batch]
        await self._batches("T1", self.api.competitions, sorted({league.tm_id for league, _ in pairs}))
        await self._batches("T1", self.api.clubs, sorted({cs.club_id for cs in club_seasons}))
        log(SOURCE, f"T1 done: {len(club_seasons)} club-seasons from {len(pairs)} league-seasons")
        return club_seasons

    async def squads(self, club_seasons: list[ClubSeason]) -> list[str]:
        """T2: squad per club-season; returns the unique player IDs, plus player records (names) in batches."""

        async def one(cs: ClubSeason) -> list[str]:
            data = await self._safe("T2", f"club {cs.club_id} {cs.season}", self.api.club_squad(cs.club_id, str(cs.season)))
            return [str(member["playerId"]) for member in (data or {}).get("squad") or []]

        player_ids = sorted({pid for squad in await run_bounded(club_seasons, one, WORKERS) for pid in squad}, key=int)
        await self._batches("T2", self.api.players, player_ids)
        log(SOURCE, f"T2 done: {len(player_ids)} unique players from {len(club_seasons)} squads")
        return player_ids

    async def player_histories(self, player_ids: list[str]) -> None:
        """T3 + T4 (and T5): injury history and per-match performance for every player."""
        jobs = [(kind, pid) for pid in player_ids for kind in ("injury", "performance")]
        done = 0

        async def one(job: tuple[str, str]) -> None:
            nonlocal done
            kind, pid = job
            if kind == "injury":
                await self._safe("T3", f"player {pid}", self.api.player_injuries(pid))
            else:
                await self._safe("T4", f"player {pid}", self.api.player_performance_games(pid))
            done += 1
            if done % PROGRESS_EVERY == 0 or done == len(jobs):
                log(SOURCE, f"T3/T4 {done}/{len(jobs)} | {self.transport.stats} | {self.throttle.describe()}")

        await run_bounded(jobs, one, WORKERS)

    async def _batches(self, step: str, route: Any, ids: list[str]) -> None:
        """Call a batch route in fixed chunks so one failing chunk doesn't lose the rest."""
        chunks = [ids[i : i + BATCH_SIZE] for i in range(0, len(ids), BATCH_SIZE)]
        await run_bounded(chunks, lambda chunk: self._safe(step, f"batch of {len(chunk)}", route(chunk)), WORKERS)


class TransfermarktCollector(Collector):
    name = SOURCE

    def __init__(self, manifest: Manifest, *, max_players: int | None = None) -> None:
        self.manifest = manifest
        self.max_players = max_players

    async def run(self, selection: Selection) -> None:
        # Start at 4 concurrent / 4 req/s; after 500 clean responses ramp to 8 concurrent / 7 req/s.
        throttle = AdaptiveThrottle(RateLimiter(rate=4, concurrency=4), max_rate=7, max_concurrency=8)
        transport = RecordReplayTransport(ResponseStore(), throttle, self.manifest, dry_run=selection.dry_run)
        # cache=None: the disk store replaces the SDK's in-memory cache. The SDK's own semaphore is set above
        # WORKERS so that the transport's limiter is the only effective cap.
        async with Transfermarkt(transport=transport, cache=None, max_concurrency=WORKERS * 2, timeout=30) as tm:
            steps = TransfermarktSteps(tm._client, transport, throttle)
            club_seasons = await steps.clubs(selection.pairs())
            player_ids = await steps.squads(club_seasons)
            if self.max_players:
                player_ids = player_ids[: self.max_players]
            log(SOURCE, f"T3/T4: {len(player_ids)} players ({len(player_ids) * 2} requests at most)")
            await steps.player_histories(player_ids)
        log(SOURCE, f"done: {transport.stats}; errors by step: {steps.errors}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_selection_args(parser)
    parser.add_argument("--players", type=int, help="T3/T4 for at most N players (smoke test)")
    args = parser.parse_args()
    asyncio.run(TransfermarktCollector(Manifest(), max_players=args.players).run(Selection.from_args(args)))


if __name__ == "__main__":
    main()
