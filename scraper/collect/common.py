"""Shared collection infrastructure: selection/CLI, manifest, rate limiting, retries, disk cache and file fetching."""

import argparse
import asyncio
import csv
import random
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Self

import httpx

from collect.config import LEAGUES, MANIFEST_PATH, ROOT, SEASONS, League, league_by_key
from collect.fs import atomic_write, is_cached
from collect.status import NullReporter, StatusReporter


# --------------------------------------------------------------------------- selection / CLI


@dataclass(frozen=True)
class Selection:
    """Which league-seasons to collect, and how (dry run, request limit)."""

    leagues: tuple[League, ...] = LEAGUES
    seasons: tuple[int, ...] = SEASONS
    limit: int | None = None
    dry_run: bool = False

    def pairs(self) -> list[tuple[League, int]]:
        """League-season pairs in a stable order, truncated to `limit`."""
        pairs = [(league, season) for season in self.seasons for league in self.leagues]
        return pairs[: self.limit] if self.limit else pairs

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> Self:
        leagues = tuple(league_by_key(k) for k in args.leagues) if args.leagues else LEAGUES
        seasons = tuple(sorted({s for spec in args.seasons for s in _season_range(spec)})) if args.seasons else SEASONS
        return cls(leagues=leagues, seasons=seasons, limit=args.limit, dry_run=args.dry_run)


def _season_range(spec: str) -> range:
    """'2016' -> 2016; '2016-2018' -> 2016..2018 (start years)."""
    start, _, end = spec.partition("-")
    return range(int(start), int(end or start) + 1)


def add_selection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true", help="use the disk cache only; report what would be fetched")
    parser.add_argument("--limit", type=int, help="process at most N league-seasons")
    parser.add_argument("--leagues", nargs="+", metavar="KEY", help="league ids in any source's scheme, e.g. EPL GB1 D1")
    parser.add_argument("--seasons", nargs="+", metavar="YEAR", help="season start years, e.g. 2016 or 2014-2016")


class PauseGate:
    """Pause switch shared by every rate limiter of a run; safe to flip from another thread."""

    def __init__(self) -> None:
        self._open = threading.Event()
        self._open.set()

    def pause(self) -> None:
        self._open.clear()

    def resume(self) -> None:
        self._open.set()

    @property
    def is_paused(self) -> bool:
        return not self._open.is_set()

    async def wait(self) -> None:
        while not self._open.is_set():
            await asyncio.sleep(0.2)


@dataclass
class RunContext:
    """What every collector needs besides its own source details: where to log, whom to tell, when to wait."""

    manifest: "Manifest"
    reporter: StatusReporter = field(default_factory=NullReporter)
    gate: PauseGate = field(default_factory=PauseGate)


class Collector(ABC):
    """One data source. Collectors are independent so they can run concurrently against their own hosts."""

    name: str
    key: str  # short source id used by the dashboard: fd, us, tm

    def __init__(self, ctx: RunContext) -> None:
        self.ctx = ctx

    @abstractmethod
    async def run(self, selection: Selection) -> None: ...


# --------------------------------------------------------------------------- manifest


class FetchStatus(StrEnum):
    OK = "ok"
    NOT_FOUND = "not_found"
    FAILED = "failed"
    DRY_RUN = "dry_run"


class Manifest:
    """Append-only log of every network request (cache hits are not requests and are not logged)."""

    FIELDS = ("source", "url", "local_path", "status", "http_status", "bytes", "fetched_at", "error")

    def __init__(self, path: Path = MANIFEST_PATH) -> None:
        self.path = path

    def log(
        self,
        source: str,
        url: str,
        local_path: Path | None,
        status: FetchStatus,
        http_status: int | None = None,
        nbytes: int = 0,
        error: str = "",
    ) -> None:
        if status is FetchStatus.DRY_RUN:
            return
        is_new = not self.path.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # One synchronous write per row: safe between asyncio tasks, and append-atomic between processes.
        with self.path.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            if is_new:
                writer.writerow(self.FIELDS)
            writer.writerow([
                source,
                url,
                str(local_path.relative_to(ROOT)) if local_path else "",
                status.value,
                http_status or "",
                nbytes,
                utc_now_iso(),
                error[:500],
            ])

    def latest(self) -> dict[str, dict[str, str]]:
        """Most recent row per URL."""
        if not self.path.exists():
            return {}
        with self.path.open(newline="", encoding="utf-8") as fh:
            return {row["url"]: row for row in csv.DictReader(fh)}


def utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- rate limiting / retries


class RateLimiter:
    """
    Caps both concurrency and request rate for one host, and supports a global pause.

    Use as `async with limiter:` around each network request.
    """

    def __init__(self, rate: float, concurrency: int, gate: PauseGate | None = None) -> None:
        self.rate = rate
        self.concurrency = concurrency
        self.gate = gate or PauseGate()
        self._in_flight = 0
        self._capacity = asyncio.Condition()
        self._slot_lock = asyncio.Lock()
        self._next_slot = 0.0
        self._paused_until = 0.0

    def set_limits(self, rate: float, concurrency: int) -> None:
        self.rate, self.concurrency = rate, max(1, concurrency)

    def pause(self, seconds: float) -> None:
        self._paused_until = max(self._paused_until, time.monotonic() + seconds)

    @property
    def is_paused(self) -> bool:
        return time.monotonic() < self._paused_until

    async def __aenter__(self) -> Self:
        await self.gate.wait()
        async with self._capacity:
            await self._capacity.wait_for(lambda: self._in_flight < self.concurrency)
            self._in_flight += 1
        async with self._slot_lock:
            while (wait := max(self._next_slot, self._paused_until) - time.monotonic()) > 0:
                await asyncio.sleep(wait)
            self._next_slot = time.monotonic() + 1 / self.rate
        return self

    async def __aexit__(self, *exc: object) -> None:
        async with self._capacity:
            self._in_flight -= 1
            self._capacity.notify_all()


@dataclass
class AdaptiveThrottle:
    """
    Ramps a RateLimiter up after a run of clean responses and backs off when the host blocks us.

    Every `ramp_after` clean responses, rate and concurrency double (capped at the maxima). A block pauses
    all requests for `block_pause` seconds and halves both; concurrent blocks during a pause count once.
    """

    limiter: RateLimiter
    max_rate: float
    max_concurrency: int
    ramp_after: int = 500
    block_pause: float = 60.0
    reporter: StatusReporter = field(default_factory=NullReporter)
    clean_streak: int = field(default=0, init=False)
    phase: int = field(default=1, init=False)
    start_concurrency: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.start_concurrency = self.limiter.concurrency
        self._report()

    def on_success(self) -> None:
        self.clean_streak += 1
        if self.clean_streak % self.ramp_after == 0 and self.limiter.concurrency < self.max_concurrency:
            self.limiter.set_limits(
                min(self.max_rate, self.limiter.rate * 2), min(self.max_concurrency, self.limiter.concurrency * 2)
            )
            self.phase += 1
            log("throttle", f"ramp up -> {self.describe()}")
        self._report()

    def on_block(self, reason: str, *, status: int | None = None, waf_action: str = "") -> None:
        self.clean_streak = 0
        if self.limiter.is_paused:
            self._report()
            return
        before = self.limiter.concurrency
        self.limiter.pause(self.block_pause)
        self.limiter.set_limits(max(0.5, self.limiter.rate / 2), self.limiter.concurrency // 2)
        log("throttle", f"blocked ({reason}); pausing {self.block_pause:.0f}s -> {self.describe()}")
        self.reporter.backoff(
            status=status,
            waf_action=waf_action,
            paused_s=self.block_pause,
            concurrency_from=before,
            concurrency_to=self.limiter.concurrency,
        )
        self._report()

    def _report(self) -> None:
        self.reporter.limiter(
            concurrency=self.limiter.concurrency, rate=self.limiter.rate, phase=self.phase, clean_streak=self.clean_streak
        )

    def describe(self) -> str:
        return f"{self.limiter.concurrency} concurrent, {self.limiter.rate:g} req/s"


@dataclass(frozen=True)
class RetryPolicy:
    """Exponential backoff on 403, 429 and 5xx, up to `max_attempts` attempts."""

    max_attempts: int = 5
    base_delay: float = 2.0

    @staticmethod
    def is_retryable(status: int) -> bool:
        return status in (403, 429) or status >= 500

    def delay(self, attempt: int) -> float:
        return self.base_delay * 2 ** (attempt - 1) + random.uniform(0, 1)


# --------------------------------------------------------------------------- disk + fetching


BodyCheck = Callable[[bytes], str | None]
"""Returns an error message when a 200 body is unusable (empty, HTML error page, ...), else None."""


class FileFetcher:
    """Downloads URLs to files, byte-for-byte, with disk cache, retries, throttling, manifest and status reporting."""

    def __init__(
        self,
        collector: Collector,
        client: httpx.AsyncClient,
        limiter: RateLimiter,
        retry: RetryPolicy = RetryPolicy(),
    ) -> None:
        self.source, self.key = collector.name, collector.key
        self.manifest, self.reporter = collector.ctx.manifest, collector.ctx.reporter
        self.client, self.limiter, self.retry = client, limiter, retry
        self.stats = Counter()

    async def fetch(self, url: str, path: Path, check: BodyCheck, *, dry_run: bool = False) -> Path | None:
        if is_cached(path):
            self.stats.add("cached")
            self.reporter.request(self.key, url, status=200, nbytes=path.stat().st_size, result="Replayed from disk")
            return path
        if dry_run:
            self.stats.add("would_fetch")
            self.reporter.request(self.key, url, status=None, nbytes=0, result="Planned")
            log(self.source, f"would fetch {url}")
            return None

        error, status = "", None
        for attempt in range(1, self.retry.max_attempts + 1):
            try:
                async with self.limiter:
                    response = await self.client.get(url)
            except httpx.HTTPError as exc:
                error, status = f"{type(exc).__name__}: {exc}", None
            else:
                status = response.status_code
                if status == 200:
                    if (error := check(response.content) or "") == "":
                        atomic_write(path, response.content)
                        self.manifest.log(self.source, url, path, FetchStatus.OK, status, len(response.content))
                        self.reporter.request(self.key, url, status=status, nbytes=len(response.content), result="Fetched")
                        self.stats.add("fetched")
                        return path
                elif status == 404:
                    self.manifest.log(self.source, url, None, FetchStatus.NOT_FOUND, status)
                    self.reporter.request(self.key, url, status=status, nbytes=0, result="Not found")
                    self.stats.add("not_found")
                    return None
                elif not self.retry.is_retryable(status):
                    error = f"HTTP {status}"
                    break
                else:
                    error = f"HTTP {status}"
            if attempt < self.retry.max_attempts:
                self.reporter.request(self.key, url, status=status, nbytes=0, result=f"{error} — retry {attempt}/{self.retry.max_attempts}")
                await asyncio.sleep(self.retry.delay(attempt))

        self.manifest.log(self.source, url, None, FetchStatus.FAILED, status, error=error)
        self.reporter.request(self.key, url, status=status, nbytes=0, result="Failed")
        self.stats.add("failed")
        log(self.source, f"FAILED {url}: {error}")
        return None


# --------------------------------------------------------------------------- small utilities


class Counter:
    """Named counters for progress reporting."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def add(self, key: str, n: int = 1) -> None:
        self._counts[key] = self._counts.get(key, 0) + n

    def __getitem__(self, key: str) -> int:
        return self._counts.get(key, 0)

    def __str__(self) -> str:
        return ", ".join(f"{k}={v}" for k, v in sorted(self._counts.items())) or "nothing"


def log(source: str, message: str) -> None:
    print(f"{datetime.now():%H:%M:%S} [{source}] {message}", flush=True)


async def run_bounded[T, R](items: Sequence[T], worker: Callable[[T], Awaitable[R]], workers: int) -> list[R]:
    """Run `worker` over `items` with at most `workers` in flight; results keep the input order."""
    results: list[R] = [None] * len(items)  # type: ignore[list-item]
    queue: Iterable[tuple[int, T]] = iter(enumerate(items))

    async def drain() -> None:
        for index, item in queue:
            results[index] = await worker(item)

    await asyncio.gather(*(drain() for _ in range(max(1, min(workers, len(items))))))
    return results
