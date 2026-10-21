"""
Understat: one JSON payload per league-season (U1) and one per team-season (U2), from the site's XHR endpoints,
saved byte-for-byte.

U1  `getLeagueData/{league}/{season}`: `teams` (with match history incl. ppda), `players` and `dates`.
U2  `getTeamData/{team}/{season}`: season `statistics` per team (attack speed, shot situations, formations, shot
    zones, game states, timing, shot results), plus its `dates` and `players`. The team list comes from U1; the
    path segment is the Understat team title with spaces as underscores (the team page URL).
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
from collect.config import RAW_DIR, USER_AGENT, League, expected_clubs

URL = "https://understat.com/getLeagueData/{league}/{season}"
PAGE_URL = "https://understat.com/league/{league}/{season}"
TEAM_URL = "https://understat.com/getTeamData/{team}/{season}"
TEAM_PAGE_URL = "https://understat.com/team/{team}/{season}"
OUT_DIR = RAW_DIR / "understat"
TEAM_DIR = OUT_DIR / "team"
REQUIRED_KEYS = ("teams", "players", "dates")
TEAM_BLOCKS = ("situation", "formation", "attackSpeed", "shotZone", "result")


def raw_path(league: League, season: int) -> Path:
    return OUT_DIR / league.understat / f"{season}.json"


def team_path(league: League, season: int, team_id: str) -> Path:
    return TEAM_DIR / league.understat / str(season) / f"{team_id}.json"


def team_slug(title: str) -> str:
    return title.replace(" ", "_")


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


def check_team_payload(body: bytes) -> str | None:
    try:
        payload = json.loads(body)
    except ValueError:
        return "not JSON"
    stats = payload.get("statistics") if isinstance(payload, dict) else None
    if not isinstance(stats, dict):
        return "no statistics"
    if missing := [k for k in TEAM_BLOCKS if not stats.get(k)]:
        return f"missing or empty statistics: {missing}"
    return None


def teams_of(league_file: Path) -> list[tuple[str, str]]:
    """(team id, title) for every team in a saved league-season payload."""
    teams = json.loads(league_file.read_bytes())["teams"].values()
    return sorted((t["id"], t["title"]) for t in teams)


class UnderstatCollector(Collector):
    name = "understat"
    key = "us"

    async def run(self, selection: Selection) -> None:
        pairs = selection.pairs()
        team_total = sum(expected_clubs(league, season) for league, season in pairs)
        log(self.name, f"{len(pairs)} league-seasons, about {team_total} team-seasons")
        reporter = self.ctx.reporter
        reporter.source_started(self.key, total=len(pairs) + team_total, estimate=False, rate="1 / s")
        limiter = RateLimiter(rate=1.0, concurrency=1, gate=self.ctx.gate)
        headers = {"User-Agent": USER_AGENT, "X-Requested-With": "XMLHttpRequest"}
        leagues_done = teams_done = 0
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            fetcher = FileFetcher(self, client, limiter)
            for league, season in pairs:
                reporter.coverage(self.key, league, season, "running")
                client.headers["Referer"] = PAGE_URL.format(league=league.understat, season=season)
                url = URL.format(league=league.understat, season=season)
                saved = await fetcher.fetch(url, raw_path(league, season), check_payload, dry_run=selection.dry_run)
                leagues_done += 1
                reporter.source_progress(self.key, failed=saved is None and not selection.dry_run)
                reporter.step("U1", done=leagues_done, total=len(pairs), state="done" if leagues_done == len(pairs) else "running")
                if saved is None:
                    self._report(league, season, ok=False, dry_run=selection.dry_run, detail="league data missing")
                    continue

                teams = teams_of(saved)
                ok = 0
                for team_id, title in teams:
                    slug = team_slug(title)
                    client.headers["Referer"] = TEAM_PAGE_URL.format(team=slug, season=season)
                    url = TEAM_URL.format(team=slug, season=season)
                    got = await fetcher.fetch(url, team_path(league, season, team_id), check_team_payload, dry_run=selection.dry_run)
                    ok += got is not None
                    teams_done += 1
                    reporter.source_progress(self.key, failed=got is None and not selection.dry_run)
                    reporter.step("U2", done=teams_done, total=team_total, sub=f"{league.understat} {season}: {title}")
                self._report(league, season, ok=ok == len(teams), dry_run=selection.dry_run, detail=f"{ok} / {len(teams)} teams")
        reporter.step("U2", done=teams_done, total=teams_done, state="done", sub="done")
        reporter.source_finished(self.key, note="XHR endpoints: getLeagueData per league-season, getTeamData per team-season.")
        log(self.name, f"done: {fetcher.stats}")

    def _report(self, league: League, season: int, *, ok: bool, dry_run: bool, detail: str) -> None:
        state = "done" if ok else "queued" if dry_run else "failed"
        self.ctx.reporter.coverage(self.key, league, season, state, detail)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_selection_args(parser)
    asyncio.run(UnderstatCollector(RunContext(Manifest())).run(Selection.from_args(parser.parse_args())))


if __name__ == "__main__":
    main()
