"""
Validation report over the raw store, the manifest and the parsed tables.

Printed to the terminal after each run (`run_checks`) and served to the dashboard as JSON (`build_report`); both
use the same Check classes.

Usage: python validate.py [--fix]   (--fix deletes suspicious raw files so the next collection run re-fetches them)
"""

import argparse
import hashlib
import json
import re
from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from collect import football_data, transfermarkt, understat
from collect.common import FetchStatus, Manifest
from collect.config import LEAGUES, ROOT, SEASONS, TABLES_DIR, League, expected_clubs, expected_league_matches
from parse.common import read_table

FD_SEASON = {f"{s % 100:02d}{(s + 1) % 100:02d}": s for s in range(2000, 2030)}
BY_NAME = {league.name: league for league in LEAGUES}
BY_UNDERSTAT = {league.understat: league for league in LEAGUES}
BY_TM = {league.tm_id: league for league in LEAGUES}
SOURCE_KEY = {"football_data": "fd", "understat": "us", "transfermarkt": "tm"}
TABLES = (
    "fd_matches", "us_team_matches", "us_player_seasons", "us_matches",
    "tm_clubs", "tm_squads", "tm_injuries", "tm_player_stats", "tm_fixtures",
)
KNOWN_EXCEPTIONS = {(LEAGUES[4], 2019): "COVID, stopped early"}
QUIRKS = ["Serie A shot counts (Football-Data) appear to include blocked shots from 2018/19 onwards."]
README_TODO = "_fill in after the full run_"


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


@dataclass(frozen=True)
class FixtureCount:
    league: League
    season: int
    club: str
    found: int
    expected: int

    @property
    def ok(self) -> bool:
        if (self.league, self.season) in KNOWN_EXCEPTIONS:
            return self.found >= 27  # COVID: 27-28 matches per club
        return self.found == self.expected


class TmLeagueFixtureCounts(Check):
    """Each club plays 2 x (clubs - 1) league matches; fewer means the squad records didn't cover every match."""

    def items(self) -> list[FixtureCount]:
        clubs = read_table("tm_clubs")
        league_of = {(r["club_id"], r["season_param"]): r["competition_id"] for r in clubs}
        names = {r["club_id"]: r["club_name"] for r in clubs}
        counts = Counter(
            (r["club_id"], r["game.seasonId"])
            for r in read_table("tm_fixtures")
            if league_of.get((r["club_id"], r["game.seasonId"])) == r["game.competitionId"]
        )
        out = []
        for (club_id, season), competition_id in sorted(league_of.items()):
            league = BY_TM[competition_id]
            want = 2 * (expected_clubs(league, int(season)) - 1)
            out.append(FixtureCount(league, int(season), names.get(club_id) or club_id, counts.get((club_id, season), 0), want))
        return out

    def run(self) -> CheckResult:
        result = CheckResult("Transfermarkt: league fixtures per club-season (T5)")
        items = self.items()
        for item in items:
            if not item.ok:
                result.fail(f"{item.club} ({item.league.tm_id} {item.season}): {item.found} (expected {item.expected})")
        result.lines.insert(0, f"{len(items)} club-seasons checked; Ligue 1 2019/20 short seasons accepted")
        return result


# --------------------------------------------------------------------------- raw/manifest checks


@dataclass(frozen=True)
class Problem:
    """A failed request or a suspicious stored response; `id` is what the dashboard sends back to re-queue it."""

    id: str
    source: str
    url: str
    code: int | None
    why: str
    attempts: int
    path: Path | None = None

    def as_dict(self) -> dict:
        return {"id": self.id, "source": self.source, "url": self.url, "code": self.code, "why": self.why, "attempts": self.attempts}


class ManifestFailures(Check):
    def __init__(self, manifest: Manifest) -> None:
        self.manifest = manifest

    def items(self) -> list[Problem]:
        return [
            Problem(
                id="m:" + hashlib.sha1(url.encode()).hexdigest()[:12],
                source=SOURCE_KEY.get(row["source"], row["source"]),
                url=url,
                code=int(row["http_status"]) if row["http_status"] else None,
                why=row["error"],
                attempts=5,
            )
            for url, row in self.manifest.latest().items()
            if row["status"] == FetchStatus.FAILED
        ]

    def run(self) -> CheckResult:
        result = CheckResult("Manifest: requests whose latest attempt failed")
        for item in self.items():
            result.fail(f"{item.source}: {item.url} -> {item.why}")
        result.lines.insert(0, f"{len(self.manifest.latest())} distinct URLs in manifest")
        return result


class SuspiciousRawFiles(Check):
    """Empty/too-small bodies, HTML error pages, WAF challenges; with `fix`, delete them so they get re-queued."""

    def __init__(self, fix: bool = False) -> None:
        self.fix = fix

    def items(self) -> list[Problem]:
        return [problem for problem in self._scan() if problem]

    def run(self) -> CheckResult:
        result = CheckResult("Raw store: suspicious files" + (" (deleted for re-fetch)" if self.fix else ""))
        checked = 0
        for problem in self._scan(count=True):
            checked += 1
            if problem:
                result.fail(f"{problem.path.relative_to(ROOT)}: {problem.why}")
                if self.fix:
                    problem.path.unlink()
        result.lines.insert(0, f"{checked} raw files checked")
        return result

    def _scan(self, count: bool = False) -> Iterator[Problem | None]:
        sources = (
            ("fd", football_data.OUT_DIR.glob("*/*.csv"), lambda p: (football_data.check_csv(p.read_bytes()), None, "")),
            ("us", understat.OUT_DIR.glob("*/*.json"), lambda p: (understat.check_payload(p.read_bytes()), None, "")),
            ("tm", transfermarkt.OUT_DIR.rglob("*.json"), self._tm_problem),
        )
        for source, paths, check in sources:
            for path in paths:
                why, code, url = check(path)
                if why:
                    yield Problem("f:" + str(path.relative_to(ROOT)), source, url or str(path.relative_to(ROOT)), code or 200, why, 1, path)
                elif count:
                    yield None

    @staticmethod
    def _tm_problem(path: Path) -> tuple[str | None, int | None, str]:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            return "unreadable record", None, ""
        url, status = record.get("url", ""), record.get("status")
        if any(k.lower() == "x-amzn-waf-action" for k in record.get("headers", {})):
            return "WAF challenge stored", status, url
        if status == 404:
            return None, status, url
        if status != 200 or not record.get("body"):
            return f"Body {len(record.get('body') or '')} bytes — likely empty", status, url
        try:
            body = json.loads(record["body"])
        except ValueError:
            return "Challenge HTML instead of JSON", status, url
        return (None if body.get("success") and "data" in body else "Unsuccessful payload"), status, url


# --------------------------------------------------------------------------- injury summary


class InjurySummary(Check):
    """Informational: injuries per season, and how many collected players have no injuries at all (normal)."""

    def per_season(self) -> Counter:
        return Counter(r["seasonId"] for r in read_table("tm_injuries"))

    def players(self) -> tuple[int, int]:
        """(players collected, players with zero injuries)."""
        files = list(transfermarkt.OUT_DIR.glob("player/*/injury.json"))
        injured = {r["playerId"] for r in read_table("tm_injuries")}
        return len(files), len(files) - len(injured)

    def run(self) -> CheckResult:
        result = CheckResult("Transfermarkt: injuries")
        per_season = self.per_season()
        for season in SEASONS:
            result.lines.append(f"season {season}: {per_season.get(str(season), 0)} injuries")
        players, zero = self.players()
        result.lines.append(f"{sum(per_season.values())} injury events (all seasons); {players} players collected, {zero} with zero injuries")
        return result


def all_checks(fix: bool = False) -> list[Check]:
    return [
        FdMatchCounts(),
        UsMatchCounts(),
        TmClubCounts(),
        TmLeagueFixtureCounts(),
        ManifestFailures(Manifest()),
        SuspiciousRawFiles(fix),
        InjurySummary(),
    ]


def run_checks(fix: bool = False) -> bool:
    print("\n=================== VALIDATION REPORT ===================")
    all_ok = True
    for check in all_checks(fix):
        result = check.run()
        all_ok &= result.ok
        print(f"\n[{'PASS' if result.ok else 'FAIL'}] {result.name}")
        for line in result.lines[:40]:
            print(f"   {line}")
        if len(result.lines) > 40:
            print(f"   ... {len(result.lines) - 40} more")
    print(f"\nOverall: {'PASS' if all_ok else 'FAIL (see above; known exceptions are documented in README)'}")
    return all_ok


# --------------------------------------------------------------------------- dashboard JSON


def _grid(counts: Counter) -> list[list[int | None]]:
    return [[counts.get((league, season)) for season in SEASONS] for league in LEAGUES]


def _tile(label: str, value: str, sub: str, ok: bool) -> dict:
    return {"label": label, "value": value, "sub": sub, "state": "pass" if ok else "attention"}


def _dod(title: str, done: bool, status: str) -> dict:
    return {"title": title, "state": "done" if done else "open", "status": "Done" if done else status}


def build_report(run: dict | None = None) -> dict:
    """The `/api/validation` payload (see ui-handoff/HANDOFF.md section 2)."""
    run = run or {}
    total_pairs = len(LEAGUES) * len(SEASONS)
    fd, us, tm_clubs = FdMatchCounts().observed(), UsMatchCounts().observed(), TmClubCounts().observed()
    fixtures = TmLeagueFixtureCounts().items()
    failures = ManifestFailures(Manifest()).items()
    suspicious = SuspiciousRawFiles().items()
    injuries = InjurySummary()
    per_season = injuries.per_season()
    players, zero = injuries.players()

    fd_files = sum(1 for _ in football_data.OUT_DIR.glob("*/*.csv"))
    us_files = sum(1 for _ in understat.OUT_DIR.glob("*/*.json"))
    tm_files = sum(1 for _ in transfermarkt.OUT_DIR.rglob("*.json"))
    tables = sum(1 for name in TABLES if (TABLES_DIR / f"{name}.csv").exists())
    tm_failed = [f for f in failures if f.source == "tm"]
    tm_suspicious = [s for s in suspicious if s.source == "tm"]

    expected = [[expected_league_matches(league, season) for season in SEASONS] for league in LEAGUES]
    match_ok = all(
        count == expected_league_matches(league, season)
        for counts in (fd, us)
        for (league, season), count in counts.items()
    )
    clubs = []
    for li, league in enumerate(LEAGUES):
        seasons_found = {s for (lg, s) in tm_clubs if lg == league}
        ok = sum(1 for s in seasons_found if tm_clubs[(league, s)] == expected_clubs(league, s))
        league_fixtures = [f for f in fixtures if f.league == league]
        clubs.append({
            "league": li,
            "expected": "20, then 18 from 2023/24" if league.fd_div == "F1" else f"{expected_clubs(league, 2014)} every season",
            "found_ok": ok,
            "of": len(SEASONS),
            "fixtures_ok": sum(1 for f in league_fixtures if f.ok),
            "fixtures_of": len(league_fixtures),
        })
    clubs_ok = all(c["found_ok"] == c["of"] for c in clubs)
    fixtures_ok = all(f.ok for f in fixtures) and bool(fixtures)
    problems = failures + suspicious
    readme_done = README_TODO not in (ROOT / "README.md").read_text(encoding="utf-8")

    checks_ok = [match_ok and bool(fd) and bool(us), clubs_ok, fixtures_ok, not problems]
    return {
        "finished_at": run.get("finished_at"),
        "run_time_s": run.get("run_time_s"),
        "attention": checks_ok.count(False),
        "summary": [
            _tile("Football-Data CSVs", f"{fd_files} / {total_pairs}", "Union of columns at parse time", fd_files == total_pairs),
            _tile("Understat league-seasons", f"{us_files} / {total_pairs}", "XHR getLeagueData payloads", us_files == total_pairs),
            _tile(
                "Transfermarkt requests", f"{tm_files:,}",
                f"{len(tm_failed)} failed · {len(tm_suspicious)} suspicious bodies", not tm_failed and not tm_suspicious,
            ),
            _tile("Parsed tables", f"{tables} / {len(TABLES)}", "Original values + source_file", tables == len(TABLES)),
        ],
        "matches": {
            "found": {"fd": _grid(fd), "us": _grid(us)},
            "expected": expected,
            "known_exceptions": [
                {"league": LEAGUES.index(league), "season": SEASONS.index(season), "note": note}
                for (league, season), note in KNOWN_EXCEPTIONS.items()
            ],
        },
        "failures": [p.as_dict() for p in problems],
        "clubs": clubs,
        "injuries_per_season": [per_season.get(str(season), 0) for season in SEASONS],
        "zero_injury_players": zero,
        "players_total": players,
        "dod": [
            _dod("60 Football-Data CSVs and 60 Understat league-seasons saved raw",
                 fd_files == total_pairs and us_files == total_pairs, f"{fd_files} + {us_files} of {total_pairs} each"),
            _dod("Transfermarkt T1–T5 complete, manifest clean", clubs_ok and fixtures_ok and not problems,
                 f"{len(problems)} entries to re-queue" if problems else "T1–T5 not complete yet"),
            _dod(f"{len(TABLES)} tables parsed with original values", tables == len(TABLES), f"{tables} of {len(TABLES)} tables"),
            _dod("Validation report passes, exceptions documented", all(checks_ok),
                 f"{checks_ok.count(False)} checks need attention"),
            _dod("README: endpoint behaviour, concurrency, run time", readme_done, "Run time and final settings still to fill in"),
        ],
        "documented_quirks": QUIRKS,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fix", action="store_true", help="delete suspicious raw files so they are re-fetched")
    parser.add_argument("--json", action="store_true", help="print the dashboard JSON instead of the text report")
    args = parser.parse_args()
    if args.json:
        print(json.dumps(build_report(), indent=1))
        return
    raise SystemExit(0 if run_checks(args.fix) else 1)


if __name__ == "__main__":
    main()
