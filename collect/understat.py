"""
Understat: one JSON payload per league-season from the site's XHR endpoint, saved byte-for-byte.

The league page no longer embeds `JSON.parse('...')` data; `js/league.min.js` loads everything from
`getLeagueData/{league}/{season}`, which returns `teams` (with match history incl. ppda), `players` and `dates`.
"""

import argparse
import asyncio
import json
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
from collect.config import RAW_DIR, USER_AGENT, League

URL = "https://understat.com/getLeagueData/{league}/{season}"
PAGE_URL = "https://understat.com/league/{league}/{season}"
OUT_DIR = RAW_DIR / "understat"
REQUIRED_KEYS = ("teams", "players", "dates")


def raw_path(league: League, season: int) -> Path:
    return OUT_DIR / league.understat / f"{season}.json"


def check_payload(body: bytes) -> str | None:
    try:
        payload = json.loads(body)
    except ValueError:
        return "not JSON"
    if not isinstance(payload, dict):
        return "unexpected JSON shape"
    if missing := [k for k in REQUIRED_KEYS if not payload.get(k)]:
        return f"missing or empty keys: {missing}"
    return None


class UnderstatCollector(Collector):
    name = "understat"

    def __init__(self, manifest: Manifest) -> None:
        self.manifest = manifest

    async def run(self, selection: Selection) -> None:
        pairs = selection.pairs()
        log(self.name, f"{len(pairs)} league-seasons")
        limiter = RateLimiter(rate=1.0, concurrency=1)
        headers = {"User-Agent": USER_AGENT, "X-Requested-With": "XMLHttpRequest"}
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            fetcher = FileFetcher(self.name, client, limiter, self.manifest)
            for league, season in pairs:
                url = URL.format(league=league.understat, season=season)
                client.headers["Referer"] = PAGE_URL.format(league=league.understat, season=season)
                await fetcher.fetch(url, raw_path(league, season), check_payload, dry_run=selection.dry_run)
        log(self.name, f"done: {fetcher.stats}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_selection_args(parser)
    asyncio.run(UnderstatCollector(Manifest()).run(Selection.from_args(parser.parse_args())))


if __name__ == "__main__":
    main()
