"""Understat payloads -> `us_team_matches`, `us_player_seasons`, `us_matches` (league data), `us_team_stats` (team data)."""

import json
from collections.abc import Iterator
from pathlib import Path

from collect.understat import OUT_DIR, TEAM_DIR
from parse.common import Row, TableBuilder, flatten, source_file


class _UnderstatTable(TableBuilder):
    def __init__(self, raw_dir: Path = OUT_DIR) -> None:
        self.raw_dir = raw_dir

    def payloads(self) -> Iterator[tuple[Path, dict, Row]]:
        """(path, payload, key columns) per league-season file."""
        for path in sorted(self.raw_dir.glob("*/*.json")):
            yield path, json.loads(path.read_bytes()), {"league": path.parent.name, "season": path.stem}


class UsTeamMatches(_UnderstatTable):
    """One row per team per match from `teams[*].history`; `ppda` and `ppda_allowed` keep `att`/`def` as given."""

    name = "us_team_matches"

    def rows(self) -> Iterator[Row]:
        for path, payload, keys in self.payloads():
            for team in payload["teams"].values():
                for match in team["history"]:
                    yield keys | {"team_id": team["id"], "team_title": team["title"]} | flatten(match) | {
                        "source_file": source_file(path)
                    }


class UsPlayerSeasons(_UnderstatTable):
    name = "us_player_seasons"

    def rows(self) -> Iterator[Row]:
        for path, payload, keys in self.payloads():
            for player in payload["players"]:
                yield keys | flatten(player) | {"source_file": source_file(path)}


class UsMatches(_UnderstatTable):
    name = "us_matches"

    def rows(self) -> Iterator[Row]:
        for path, payload, keys in self.payloads():
            for match in payload["dates"]:
                yield keys | flatten(match) | {"source_file": source_file(path)}


class UsTeamStats(TableBuilder):
    """One row per team-season, statistics block and category, e.g. `attackSpeed` / `Fast` with shots, goals, xG
    and the same for the opponents (`against.*`); formations also carry minutes played (`time`)."""

    name = "us_team_stats"

    def __init__(self, raw_dir: Path = TEAM_DIR) -> None:
        self.raw_dir = raw_dir

    def rows(self) -> Iterator[Row]:
        for path in sorted(self.raw_dir.glob("*/*/*.json")):
            keys = {"league": path.parent.parent.name, "season": path.parent.name, "team_id": path.stem}
            for block, categories in json.loads(path.read_bytes())["statistics"].items():
                for category, values in categories.items():
                    yield keys | {"block": block, "category": category} | flatten(values) | {"source_file": source_file(path)}
