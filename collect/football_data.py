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

    def __init__(self, manifest: Manifest) -> None:
        self.manifest = manifest

    async def run(self, selection: Selection) -> None:
        pairs = selection.pairs()
        log(self.name, f"{len(pairs)} files")
        # The site answered 429 when hit quickly: one request every 2 s.
        limiter = RateLimiter(rate=0.5, concurrency=1)
        async with httpx.AsyncClient(follow_redirects=True, timeout=30, headers={"User-Agent": USER_AGENT}) as client:
            fetcher = FileFetcher(self.name, client, limiter, self.manifest)
            for league, season in pairs:
                url = URL.format(season_code=fd_season_code(season), div=league.fd_div)
                await fetcher.fetch(url, raw_path(league, season), check_csv, dry_run=selection.dry_run)
        log(self.name, f"done: {fetcher.stats}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_selection_args(parser)
    asyncio.run(FootballDataCollector(Manifest()).run(Selection.from_args(parser.parse_args())))


if __name__ == "__main__":
    main()
