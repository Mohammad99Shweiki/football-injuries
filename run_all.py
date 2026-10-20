"""
Run the three collectors concurrently (each with its own host rate limit), retry what failed, parse and validate.

Usage: python run_all.py [--dry-run] [--limit N] [--leagues ...] [--seasons ...] [--players N]
"""

import argparse
import asyncio
import time

from collect.common import Collector, Manifest, Selection, add_selection_args, log
from collect.football_data import FootballDataCollector
from collect.transfermarkt import TransfermarktCollector
from collect.understat import UnderstatCollector
from parse.__main__ import parse_all
from validate import ManifestFailures, SuspiciousRawFiles, run_checks


async def collect(collectors: list[Collector], selection: Selection) -> None:
    await asyncio.gather(*(collector.run(selection) for collector in collectors))


def needs_retry(manifest: Manifest) -> bool:
    """Delete suspicious raw files and report whether anything must be fetched again."""
    suspicious = SuspiciousRawFiles(fix=True).run()
    failures = ManifestFailures(manifest).run()
    for result in (suspicious, failures):
        if not result.ok:
            log("run_all", f"{result.name}: {len(result.lines) - 1} to retry")
    return not (suspicious.ok and failures.ok)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_selection_args(parser)
    parser.add_argument("--players", type=int, help="Transfermarkt T3/T4 for at most N players")
    parser.add_argument("--skip-parse", action="store_true")
    args = parser.parse_args()

    selection = Selection.from_args(args)
    manifest = Manifest()
    collectors: list[Collector] = [
        FootballDataCollector(manifest),
        UnderstatCollector(manifest),
        TransfermarktCollector(manifest, max_players=args.players),
    ]

    started = time.monotonic()
    asyncio.run(collect(collectors, selection))
    if not selection.dry_run and needs_retry(manifest):
        log("run_all", "retry pass (stored responses are replayed from disk, only missing ones are fetched)")
        asyncio.run(collect(collectors, selection))
    log("run_all", f"collection finished in {(time.monotonic() - started) / 60:.1f} min")

    if not args.skip_parse:
        parse_all()
        run_checks()
    log("run_all", f"total run time {(time.monotonic() - started) / 60:.1f} min")


if __name__ == "__main__":
    main()
