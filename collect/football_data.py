"""Football-Data.co.uk: one CSV per league-season, saved byte-for-byte."""

import argparse
import asyncio
from pathlib import Path

import httpx

from collect.common import (
    Collector,
    FileFetcher,
    Manifest,
    RateLimiter,
    RunContext,
    Selection,
    add_selection_args,
    log,
)
from collect.config import RAW_DIR, USER_AGENT, League, fd_season_code

URL = "https://www.football-data.co.uk/mmz4281/{season_code}/{div}.csv"
OUT_DIR = RAW_DIR / "football_data"
MIN_BYTES = 2_000


def raw_path(league: League, season: int) -> Path:
    return OUT_DIR / fd_season_code(season) / f"{league.fd_div}.csv"


def check_csv(body: bytes) -> str | None:
    """Reject HTML error pages and stubs; the bytes themselves are never altered."""
    if len(body) < MIN_BYTES:
        return f"body too small ({len(body)} bytes)"
    if body.lstrip()[:1] == b"<":
        return "HTML instead of CSV"
    return None


class FootballDataCollector(Collector):
    name = "football_data"
    key = "fd"

    async def run(self, selection: Selection) -> None:
        pairs = selection.pairs()
        log(self.name, f"{len(pairs)} files")
        reporter = self.ctx.reporter
        reporter.source_started(self.key, total=len(pairs), estimate=False, rate="1 / 2 s")
        # The site answered 429 when hit quickly: one request every 2 s.
        limiter = RateLimiter(rate=0.5, concurrency=1, gate=self.ctx.gate)
        async with httpx.AsyncClient(follow_redirects=True, timeout=30, headers={"User-Agent": USER_AGENT}) as client:
            fetcher = FileFetcher(self, client, limiter)
            for league, season in pairs:
                url = URL.format(season_code=fd_season_code(season), div=league.fd_div)
                reporter.coverage(self.key, league, season, "running")
                saved = await fetcher.fetch(url, raw_path(league, season), check_csv, dry_run=selection.dry_run)
                self._report(league, season, saved, selection.dry_run)
        reporter.source_finished(self.key, note="Bytes saved as received. Documented quirk: Serie A shots include blocked shots from 2018/19.")
        log(self.name, f"done: {fetcher.stats}")

    def _report(self, league: League, season: int, saved: Path | None, dry_run: bool) -> None:
        failed = saved is None and not dry_run
        self.ctx.reporter.source_progress(self.key, failed=failed)
        state = "done" if saved else "queued" if dry_run else "failed"
        self.ctx.reporter.coverage(self.key, league, season, state)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_selection_args(parser)
    asyncio.run(FootballDataCollector(RunContext(Manifest())).run(Selection.from_args(parser.parse_args())))


if __name__ == "__main__":
    main()
