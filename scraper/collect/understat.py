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
    RunContext,
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
    key = "us"

    async def run(self, selection: Selection) -> None:
        pairs = selection.pairs()
        log(self.name, f"{len(pairs)} league-seasons")
        reporter = self.ctx.reporter
        reporter.source_started(self.key, total=len(pairs), estimate=False, rate="1 / s")
        limiter = RateLimiter(rate=1.0, concurrency=1, gate=self.ctx.gate)
        headers = {"User-Agent": USER_AGENT, "X-Requested-With": "XMLHttpRequest"}
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            fetcher = FileFetcher(self, client, limiter)
            for league, season in pairs:
                url = URL.format(league=league.understat, season=season)
                client.headers["Referer"] = PAGE_URL.format(league=league.understat, season=season)
                reporter.coverage(self.key, league, season, "running")
                saved = await fetcher.fetch(url, raw_path(league, season), check_payload, dry_run=selection.dry_run)
                self._report(league, season, saved, selection.dry_run)
        reporter.source_finished(self.key, note="Live layout: XHR endpoint getLeagueData, one request per league-season.")
        log(self.name, f"done: {fetcher.stats}")

    def _report(self, league: League, season: int, saved: Path | None, dry_run: bool) -> None:
        failed = saved is None and not dry_run
        self.ctx.reporter.source_progress(self.key, failed=failed)
        state = "done" if saved else "queued" if dry_run else "failed"
        self.ctx.reporter.coverage(self.key, league, season, state)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_selection_args(parser)
    asyncio.run(UnderstatCollector(RunContext(Manifest())).run(Selection.from_args(parser.parse_args())))


if __name__ == "__main__":
    main()
