"""
Live run status for the dashboard.

Collectors report through the `StatusReporter` protocol; `NullReporter` is used on the command line, `RunStatus`
when the dashboard is running. `RunStatus` is thread-safe: collectors run in a worker thread, the HTTP server reads
snapshots from its own threads, and a flusher writes `data/scraper_run/status.json` (atomically) at most once per second.
"""

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field, fields
from datetime import UTC, datetime
from typing import Any, Protocol

from collect.fs import atomic_write
from collect.config import LEAGUES, RUN_DIR, SEASONS, League

STATUS_PATH = RUN_DIR / "status.json"
SOURCES = ("fd", "us", "tm")
TAIL_SIZE = 50
HISTORY_MINUTES = 30
TARGET_S = (5400, 7200)


class StatusReporter(Protocol):
    """What collectors may tell the dashboard. Every method must be cheap and never raise."""

    def source_started(self, source: str, *, total: int, estimate: bool, rate: str, note: str = "") -> None: ...
    def source_total(self, source: str, *, total: int, estimate: bool) -> None: ...
    def source_progress(self, source: str, *, failed: bool = False) -> None: ...
    def source_finished(self, source: str, *, note: str = "") -> None: ...
    def request(self, source: str, url: str, *, status: int | None, nbytes: int, result: str) -> None: ...
    def coverage(self, source: str, league: League, season: int, state: str, detail: str = "") -> None: ...
    def step(self, step_id: str, *, done: int, total: int, estimate: bool = False, sub: str = "", state: str = "running") -> None: ...
    def unique_players(self, count: int) -> None: ...
    def limiter(self, *, concurrency: int, rate: float, phase: int, clean_streak: int) -> None: ...
    def backoff(self, *, status: int | None, waf_action: str, paused_s: float, concurrency_from: int, concurrency_to: int) -> None: ...


class NullReporter:
    """Reporter for command-line runs: does nothing."""

    def __getattr__(self, name: str) -> Any:
        return lambda *args, **kwargs: None


# --------------------------------------------------------------------------- dashboard implementation


@dataclass
class SourceState:
    state: str = "queued"
    done: int = 0
    total: int = 0
    total_is_estimate: bool = True
    rate: str = ""
    cache_hits: int = 0
    failed: int = 0
    note: str = ""


@dataclass
class StepState:
    id: str
    label: str
    call: str
    done: int = 0
    total: int = 0
    total_is_estimate: bool = True
    sub: str = "queued"
    state: str = "queued"


def initial_us_steps() -> list[StepState]:
    return [
        StepState("U1", "League data", "getLeagueData(league, season)"),
        StepState("U2", "Team statistics", "getTeamData(team, season)"),
    ]


def initial_steps() -> list[StepState]:
    return [
        StepState("T1", "Clubs per league-season", "competition_clubs(comp_id, season_id)"),
        StepState("T2", "Squads per club-season", "club_squad(club_id, season_id)"),
        StepState("T3", "Injury history", "player_injuries(player_id)"),
        StepState("T4", "Player stats", "player_performance_games(player_id)"),
        StepState("T5", "Fixtures, all competitions", "built from T4 records"),
    ]


@dataclass
class LimiterState:
    concurrency: int = 4
    phase: int = 1
    rate: float = 4.0
    clean_streak: int = 0
    backoff_until: float | None = None
    last_backoff: dict | None = None


@dataclass
class RunStatus:
    """Mutable status of the current (or last) run. All public methods take the lock."""

    phase: str = "idle"
    flags: dict = field(default_factory=lambda: {"dry_run": False, "limit": None})
    mode: str = "full"
    sources: dict[str, SourceState] = field(default_factory=lambda: {s: SourceState() for s in SOURCES})
    steps: list[StepState] = field(default_factory=initial_steps)
    us_steps: list[StepState] = field(default_factory=initial_us_steps)
    players: int = 0
    lim: LimiterState = field(default_factory=LimiterState)
    cov: dict[str, list[list[str]]] = field(default_factory=dict)
    cov_detail: dict[str, list[list[str]]] = field(default_factory=dict)
    tail: deque = field(default_factory=lambda: deque(maxlen=TAIL_SIZE))
    smoke: list[dict] = field(default_factory=list)
    started_at: float | None = None
    finished_at: float | None = None
    paused_total: float = 0.0
    paused_since: float | None = None
    _tm_times: deque = field(default_factory=lambda: deque(maxlen=20_000))
    _progress: deque = field(default_factory=lambda: deque(maxlen=600))
    _minutes: dict[int, int] = field(default_factory=dict)
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def __post_init__(self) -> None:
        self._reset_grid()

    def _reset_grid(self) -> None:
        self.cov = {s: [["queued"] * len(SEASONS) for _ in LEAGUES] for s in SOURCES}
        self.cov_detail = {s: [[""] * len(SEASONS) for _ in LEAGUES] for s in SOURCES}

    # ----------------------------------------------------------------- run lifecycle (called by the controller)

    def begin(self, *, mode: str, dry_run: bool, limit: int | None) -> None:
        with self._lock:
            # Fresh state on the same object (the server holds a reference); keep the lock and smoke findings.
            fresh = RunStatus()
            for f in fields(self):
                if f.name not in ("_lock", "smoke"):
                    setattr(self, f.name, getattr(fresh, f.name))
            self.phase, self.mode = "running", mode
            self.flags = {"dry_run": dry_run, "limit": limit}
            self.started_at = time.time()

    def set_phase(self, phase: str) -> None:
        with self._lock:
            now = time.time()
            if phase == "paused" and self.paused_since is None:
                self.paused_since = now
            if phase != "paused" and self.paused_since is not None:
                self.paused_total += now - self.paused_since
                self.paused_since = None
            for s in self.sources.values():
                if s.state in ("running", "paused"):
                    s.state = "paused" if phase == "paused" else "running"
            self.phase = phase
            if phase == "finished":
                self.finished_at = now

    def set_smoke(self, findings: list[dict]) -> None:
        with self._lock:
            self.smoke = findings

    # ----------------------------------------------------------------- StatusReporter

    def source_started(self, source: str, *, total: int, estimate: bool, rate: str, note: str = "") -> None:
        with self._lock:
            s = self.sources[source]
            s.state = "paused" if self.phase == "paused" else "running"
            s.total, s.total_is_estimate, s.rate = total, estimate, rate
            s.note = note or s.note

    def source_total(self, source: str, *, total: int, estimate: bool) -> None:
        with self._lock:
            s = self.sources[source]
            s.total, s.total_is_estimate = max(total, s.done), estimate

    def source_progress(self, source: str, *, failed: bool = False) -> None:
        with self._lock:
            s = self.sources[source]
            s.done += 1
            s.failed += int(failed)
            self._progress.append((time.time(), self._overall_done()))

    def source_finished(self, source: str, *, note: str = "") -> None:
        with self._lock:
            s = self.sources[source]
            s.state = "failed" if s.failed else "done"
            s.total, s.total_is_estimate = s.done, False
            s.note = note or s.note

    def request(self, source: str, url: str, *, status: int | None, nbytes: int, result: str) -> None:
        with self._lock:
            now = time.time()
            if result == "Replayed from disk":
                self.sources[source].cache_hits += 1
            elif source == "tm" and result != "Planned":
                self._tm_times.append(now)
                minute = int(now // 60)
                self._minutes[minute] = self._minutes.get(minute, 0) + 1
            self.tail.appendleft({
                "fetched_at_elapsed_s": self._elapsed(now),
                "source": source,
                "url": url,
                "status": status,
                "bytes": nbytes,
                "result": result,
            })

    def coverage(self, source: str, league: League, season: int, state: str, detail: str = "") -> None:
        with self._lock:
            li, si = LEAGUES.index(league), SEASONS.index(season)
            self.cov[source][li][si] = state
            if detail:
                self.cov_detail[source][li][si] = detail

    def step(self, step_id: str, *, done: int, total: int, estimate: bool = False, sub: str = "", state: str = "running") -> None:
        with self._lock:
            step = next(s for s in self.steps + self.us_steps if s.id == step_id)
            step.done, step.total, step.total_is_estimate, step.state = done, total, estimate, state
            step.sub = sub or state

    def unique_players(self, count: int) -> None:
        with self._lock:
            self.players = count

    def limiter(self, *, concurrency: int, rate: float, phase: int, clean_streak: int) -> None:
        with self._lock:
            self.lim.concurrency, self.lim.rate, self.lim.phase, self.lim.clean_streak = concurrency, rate, phase, clean_streak

    def backoff(self, *, status: int | None, waf_action: str, paused_s: float, concurrency_from: int, concurrency_to: int) -> None:
        with self._lock:
            now = time.time()
            self.lim.backoff_until = now + paused_s
            self.lim.last_backoff = {
                "at_elapsed_s": self._elapsed(now),
                "status": status,
                "waf_action": waf_action,
                "paused_s": paused_s,
                "concurrency_from": concurrency_from,
                "concurrency_to": concurrency_to,
            }

    # ----------------------------------------------------------------- snapshot

    def _elapsed(self, now: float | None = None) -> int:
        if self.started_at is None:
            return 0
        end = self.finished_at or now or time.time()
        paused = self.paused_total + ((end - self.paused_since) if self.paused_since else 0)
        return max(0, int(end - self.started_at - paused))

    def _overall_done(self) -> int:
        return sum(s.done for s in self.sources.values())

    def _eta(self) -> int | None:
        """Seconds left, from the progress rate over the last ~5 minutes; None until it can be estimated."""
        if self.phase != "running" or len(self._progress) < 20:
            return None
        now = time.time()
        recent = [(t, d) for t, d in self._progress if now - t <= 300] or list(self._progress)
        (t0, d0), (t1, d1) = recent[0], recent[-1]
        if t1 - t0 < 15 or d1 <= d0:
            return None
        remaining = sum(s.total for s in self.sources.values()) - self._overall_done()
        return max(0, int(remaining / ((d1 - d0) / (t1 - t0))))

    def _rps(self, now: float) -> float:
        recent = sum(1 for t in self._tm_times if now - t <= 10)
        return round(recent / 10, 1)

    def snapshot(self) -> dict:
        with self._lock:
            now = time.time()
            current = int(now // 60)
            first = int(self.started_at // 60) if self.started_at else current + 1
            # None for minutes before the run started, so the chart can tell "no run yet" from "paused".
            history = [
                round(self._minutes.get(m, 0) / 60, 1) if m >= first else None
                for m in range(current - HISTORY_MINUTES + 1, current + 1)
            ]
            backoff_until = self.lim.backoff_until if self.lim.backoff_until and self.lim.backoff_until > now else None
            return {
                "phase": self.phase,
                "mode": self.mode,
                "started_at": iso(self.started_at),
                "finished_at": iso(self.finished_at),
                "elapsed_s": self._elapsed(now),
                "eta_s": self._eta(),
                "target_s": list(TARGET_S),
                "flags": dict(self.flags),
                "sources": {k: vars(v).copy() for k, v in self.sources.items()},
                "tm_steps": [vars(s).copy() for s in self.steps],
                "us_steps": [vars(s).copy() for s in self.us_steps],
                "tm_unique_players": self.players,
                "limiter": {
                    "concurrency": self.lim.concurrency,
                    "phase": self.lim.phase,
                    "req_per_s": self._rps(now),
                    "target": "6–8 req/s" if self.lim.phase > 1 else "~4 req/s",
                    "clean_streak": self.lim.clean_streak,
                    "rampup_needs": 500,
                    "history_rps": history,
                    "backoff_until": iso(backoff_until),
                    "last_backoff": self.lim.last_backoff,
                },
                "coverage": {k: [row[:] for row in v] for k, v in self.cov.items()},
                "coverage_detail": {k: [row[:] for row in v] for k, v in self.cov_detail.items()},
                "manifest_tail": list(self.tail),
                "smoke_test": list(self.smoke),
            }


def iso(ts: float | None) -> str | None:
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None


class StatusFlusher(threading.Thread):
    """Writes `data/scraper_run/status.json` at most once per second while the process runs."""

    def __init__(self, status: RunStatus, interval: float = 1.0) -> None:
        super().__init__(daemon=True, name="status-flusher")
        self.status, self.interval = status, interval
        self._stop = threading.Event()

    def run(self) -> None:
        while not self._stop.wait(self.interval):
            atomic_write(STATUS_PATH, json.dumps(self.status.snapshot()).encode("utf-8"))

    def stop(self) -> None:
        self._stop.set()
