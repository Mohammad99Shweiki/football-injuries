"""One run end to end: collectors in parallel -> retry pass -> parse -> validate. Used by run_all.py and serve.py."""

import asyncio
import json
import time
from dataclasses import dataclass

from collect.common import Collector, RunContext, Selection, log
from collect.config import LEAGUES, ROOT, League
from collect.football_data import FootballDataCollector
from collect.fs import atomic_write
from collect.status import RunStatus, iso
from collect.transfermarkt import TransfermarktCollector
from collect.understat import UnderstatCollector
from parse.__main__ import parse_all
from validate import ManifestFailures, SuspiciousRawFiles, run_checks

LAST_RUN_PATH = ROOT / "data" / "last_run.json"


@dataclass(frozen=True)
class RunPlan:
    """What to run: the league-season selection plus the Transfermarkt player cap (smoke test)."""

    selection: Selection
    max_players: int | None = None
    mode: str = "full"

    @classmethod
    def smoke(cls, *, dry_run: bool = False) -> "RunPlan":
        """Spec section 5: one league-season (Premier League 2016/17), T3/T4 for 20 of its players."""
        from collect.smoke import SMOKE_PLAYERS, SMOKE_SEASON

        league: League = LEAGUES[0]
        return cls(Selection(leagues=(league,), seasons=(SMOKE_SEASON,), dry_run=dry_run), SMOKE_PLAYERS, "smoke")


def collectors(ctx: RunContext, plan: RunPlan) -> list[Collector]:
    return [
        FootballDataCollector(ctx),
        UnderstatCollector(ctx),
        TransfermarktCollector(ctx, max_players=plan.max_players),
    ]


async def collect(ctx: RunContext, plan: RunPlan) -> None:
    await asyncio.gather(*(c.run(plan.selection) for c in collectors(ctx, plan)))


def needs_retry(ctx: RunContext) -> bool:
    """Delete suspicious raw files and report whether anything must be fetched again."""
    suspicious = SuspiciousRawFiles(fix=True).run()
    failures = ManifestFailures(ctx.manifest).run()
    for result in (suspicious, failures):
        if not result.ok:
            log("run", f"{result.name}: {len(result.lines) - 1} to retry")
    return not (suspicious.ok and failures.ok)


def run(ctx: RunContext, plan: RunPlan, *, parse: bool = True) -> dict:
    """Run synchronously (call from a worker thread when serving). Returns the last-run record."""
    started = time.time()
    asyncio.run(collect(ctx, plan))
    if not plan.selection.dry_run and needs_retry(ctx):
        log("run", "retry pass (stored responses are replayed from disk, only missing ones are fetched)")
        asyncio.run(collect(ctx, plan))
    log("run", f"collection finished in {(time.time() - started) / 60:.1f} min")
    if parse and not plan.selection.dry_run:
        parse_all()
        run_checks()
    record = {
        "mode": plan.mode,
        "dry_run": plan.selection.dry_run,
        "started_at": iso(started),
        "finished_at": iso(time.time()),
        "run_time_s": int(time.time() - started - (ctx.reporter.paused_total if isinstance(ctx.reporter, RunStatus) else 0)),
    }
    atomic_write(LAST_RUN_PATH, json.dumps(record).encode("utf-8"))
    log("run", f"total run time {record['run_time_s'] / 60:.1f} min")
    return record


def last_run() -> dict:
    try:
        return json.loads(LAST_RUN_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
