"""
Validation report over the raw store, the manifest and the parsed tables.

Usage: python validate.py [--fix]   (--fix deletes suspicious raw files so the next collection run re-fetches them)
"""

import argparse
import json
from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from collect import football_data, transfermarkt, understat
from collect.common import FetchStatus, Manifest
from collect.config import LEAGUES, ROOT, League, expected_clubs, expected_league_matches
from parse.common import read_table

FD_SEASON = {f"{s % 100:02d}{(s + 1) % 100:02d}": s for s in range(2000, 2030)}
BY_NAME = {league.name: league for league in LEAGUES}
BY_UNDERSTAT = {league.understat: league for league in LEAGUES}
BY_TM = {league.tm_id: league for league in LEAGUES}


@dataclass
class CheckResult:
    name: str
    ok: bool = True
    lines: list[str] = field(default_factory=list)

    def fail(self, line: str) -> None:
        self.ok = False
        self.lines.append(line)


class Check(ABC):
    @abstractmethod
    def run(self) -> CheckResult: ...


# --------------------------------------------------------------------------- count checks


class _CountCheck(Check):
    """Compares observed counts per league-season with the expected count; only collected pairs are checked."""

    title: str
    expected: Callable[[League, int], int]

    @abstractmethod
    def observed(self) -> Counter[tuple[League, int]]: ...

    def run(self) -> CheckResult:
        result = CheckResult(self.title)
        counts = self.observed()
        if not counts:
            result.fail("no data")
        for (league, season), count in sorted(counts.items(), key=lambda kv: (kv[0][1], kv[0][0].name)):
            if count != (want := self.expected(league, season)):
                result.fail(f"{league.name} {season}/{(season + 1) % 100:02d}: {count} (expected {want})")
        result.lines.insert(0, f"{len(counts)} league-seasons checked")
        return result


class FdMatchCounts(_CountCheck):
    title = "Football-Data: league matches per season"
    expected = staticmethod(expected_league_matches)

    def observed(self) -> Counter:
        return Counter((BY_NAME[r["league"]], FD_SEASON[r["season_code"]]) for r in read_table("fd_matches"))


class UsMatchCounts(_CountCheck):
    title = "Understat: played matches per season"
    expected = staticmethod(expected_league_matches)

    def observed(self) -> Counter:
        return Counter(
            (BY_UNDERSTAT[r["league"]], int(r["season"])) for r in read_table("us_matches") if r["isResult"] == "true"
        )


class TmClubCounts(_CountCheck):
    title = "Transfermarkt: clubs per league-season"
    expected = staticmethod(expected_clubs)

    def observed(self) -> Counter:
        return Counter((BY_TM[r["competition_id"]], int(r["season_param"])) for r in read_table("tm_clubs"))


class TmLeagueFixtureCounts(Check):
    """Each club plays 2 x (clubs - 1) league matches; fewer means the squad records didn't cover every match."""

    def run(self) -> CheckResult:
        result = CheckResult("Transfermarkt: league fixtures per club-season (T5)")
        clubs = read_table("tm_clubs")
        league_of = {(r["club_id"], r["season_param"]): r["competition_id"] for r in clubs}
        counts = Counter(
            (r["club_id"], r["game.seasonId"])
            for r in read_table("tm_fixtures")
            if league_of.get((r["club_id"], r["game.seasonId"])) == r["game.competitionId"]
        )
        names = {r["club_id"]: r["club_name"] for r in clubs}
        exempt = 0
        for (club_id, season), competition_id in sorted(league_of.items()):
            league = BY_TM[competition_id]
            want = 2 * (expected_clubs(league, int(season)) - 1)
            got = counts.get((club_id, season), 0)
            if league.fd_div == "F1" and int(season) == 2019 and got >= 27:
                exempt += 1  # COVID: 27-28 matches per club
            elif got != want:
                result.fail(f"{names.get(club_id) or club_id} ({competition_id} {season}): {got} (expected {want})")
        result.lines.insert(0, f"{len(league_of)} club-seasons checked; {exempt} Ligue 1 2019/20 short seasons accepted")
        return result


# --------------------------------------------------------------------------- raw/manifest checks


class ManifestFailures(Check):
    def __init__(self, manifest: Manifest) -> None:
        self.manifest = manifest

    def run(self) -> CheckResult:
        result = CheckResult("Manifest: requests whose latest attempt failed")
        rows = self.manifest.latest()
        for url, row in rows.items():
            if row["status"] == FetchStatus.FAILED:
                result.fail(f"{row['source']}: {url} -> {row['error']}")
        result.lines.insert(0, f"{len(rows)} distinct URLs in manifest")
        return result


class SuspiciousRawFiles(Check):
    """Empty/too-small bodies, HTML error pages, WAF challenges; with `fix`, delete them so they get re-queued."""

    def __init__(self, fix: bool) -> None:
        self.fix = fix

    def run(self) -> CheckResult:
        result = CheckResult("Raw store: suspicious files" + (" (deleted for re-fetch)" if self.fix else ""))
        checked = 0
        for path, problem in self._problems():
            checked += 1
            if problem:
                result.fail(f"{path.relative_to(ROOT)}: {problem}")
                if self.fix:
                    path.unlink()
        result.lines.insert(0, f"{checked} raw files checked")
        return result

    def _problems(self):
        for path in football_data.OUT_DIR.glob("*/*.csv"):
            yield path, football_data.check_csv(path.read_bytes())
        for path in understat.OUT_DIR.glob("*/*.json"):
            yield path, understat.check_payload(path.read_bytes())
        for path in transfermarkt.OUT_DIR.rglob("*.json"):
            yield path, self._tm_problem(path)

    @staticmethod
    def _tm_problem(path: Path) -> str | None:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            return "unreadable record"
        if any(k.lower() == "x-amzn-waf-action" for k in record.get("headers", {})):
            return "WAF challenge stored"
        if record.get("status") == 404:
            return None
        if record.get("status") != 200 or not record.get("body"):
            return f"status {record.get('status')} / empty body"
        try:
            body = json.loads(record["body"])
        except ValueError:
            return "body is not JSON"
        return None if body.get("success") and "data" in body else "unsuccessful payload"


# --------------------------------------------------------------------------- injury summary


class InjurySummary(Check):
    """Informational: injuries per season, and how many collected players have no injuries at all (normal)."""

    def run(self) -> CheckResult:
        result = CheckResult("Transfermarkt: injuries")
        injuries = read_table("tm_injuries")
        per_season = Counter(r["seasonId"] for r in injuries)
        for season in sorted(per_season, key=lambda s: int(s or 0)):
            if season and int(season) >= 2014:
                result.lines.append(f"season {season}: {per_season[season]} injuries")
        files = list(transfermarkt.OUT_DIR.glob("player/*/injury.json"))
        injured = {r["playerId"] for r in injuries}
        result.lines.append(
            f"{len(injuries)} injury events (all seasons); {len(files)} players collected, "
            f"{len(files) - len(injured)} with zero injuries"
        )
        return result


def run_checks(fix: bool = False) -> bool:
    checks: list[Check] = [
        FdMatchCounts(),
        UsMatchCounts(),
        TmClubCounts(),
        TmLeagueFixtureCounts(),
        ManifestFailures(Manifest()),
        SuspiciousRawFiles(fix),
        InjurySummary(),
    ]
    print("\n=================== VALIDATION REPORT ===================")
    all_ok = True
    for check in checks:
        result = check.run()
        all_ok &= result.ok
        print(f"\n[{'PASS' if result.ok else 'FAIL'}] {result.name}")
        for line in result.lines[:40]:
            print(f"   {line}")
        if len(result.lines) > 40:
            print(f"   ... {len(result.lines) - 40} more")
    print(f"\nOverall: {'PASS' if all_ok else 'FAIL (see above; known exceptions are documented in README)'}")
    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fix", action="store_true", help="delete suspicious raw files so they are re-fetched")
    raise SystemExit(0 if run_checks(parser.parse_args().fix) else 1)


if __name__ == "__main__":
    main()
