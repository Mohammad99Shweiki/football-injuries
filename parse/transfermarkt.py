"""
Transfermarkt raw records -> `tm_clubs`, `tm_squads`, `tm_injuries`, `tm_player_stats`, `tm_fixtures`.

Each raw file is a recorded HTTP exchange: {method, url, status, headers, fetched_at, body}; `body` holds the
upstream JSON text, whose `data` member is the payload.
"""

import json
from collections import Counter, defaultdict
from collections.abc import Iterator
from functools import cached_property
from pathlib import Path

import httpx

from collect.config import LEAGUES
from collect.transfermarkt import OUT_DIR
from parse.common import Row, TableBuilder, flatten, source_file, text

LEAGUE_BY_TM_ID = {league.tm_id: league for league in LEAGUES}
# Counted per (player, season, competition, club) like the SDK's player_stats; national-team matches are kept,
# so they can be filtered later by `competition_type_id` (11, 17, 19, 20 per the SDK).
STAT_FIELDS = {
    "goals": ("goalStatistics", "goalsScoredTotal"),
    "assists": ("goalStatistics", "assists"),
    "minutes_played": ("playingTimeStatistics", "playedMinutes"),
}


def load_record(path: Path) -> tuple[str, dict | None]:
    """(request URL, `data` payload); payload is None for 404s and unsuccessful bodies."""
    record = json.loads(path.read_text(encoding="utf-8"))
    if record["status"] != 200:
        return record["url"], None
    body = json.loads(record["body"])
    return record["url"], body.get("data") if body.get("success") else None


def season_param(url: str) -> str:
    return httpx.URL(url).params.get("season", "")


class TransfermarktRaw:
    """Index over the raw store, shared by the table builders so lookups are built once."""

    def __init__(self, root: Path = OUT_DIR) -> None:
        self.root = root

    def batch_records(self, route: str) -> dict[str, dict]:
        records: dict[str, dict] = {}
        for path in self.root.glob(f"{route}__*.json"):
            _, data = load_record(path)
            records |= {str(entity["id"]): entity for entity in data or []}
        return records

    @cached_property
    def club_names(self) -> dict[str, str]:
        return {club_id: club.get("name") for club_id, club in self.batch_records("clubs").items()}

    @cached_property
    def players(self) -> dict[str, dict]:
        return self.batch_records("players")

    @cached_property
    def club_league(self) -> dict[tuple[str, str], str]:
        """(club_id, season) -> Transfermarkt competition ID, from T1."""
        mapping = {}
        for path in sorted(self.root.glob("competition/*/club__season=*.json")):
            url, data = load_record(path)
            for club_id in (data or {}).get("clubIds", []):
                mapping[(str(club_id), season_param(url))] = path.parent.name
        return mapping

    def files(self, pattern: str) -> list[Path]:
        return sorted(self.root.glob(pattern))


class _TmTable(TableBuilder):
    def __init__(self, raw: TransfermarktRaw) -> None:
        self.raw = raw


class TmClubs(_TmTable):
    name = "tm_clubs"

    def rows(self) -> Iterator[Row]:
        for path in self.raw.files("competition/*/club__season=*.json"):
            url, data = load_record(path)
            if not data:
                continue
            competition_id = path.parent.name
            for club_id in data["clubIds"]:
                yield {
                    "league": LEAGUE_BY_TM_ID[competition_id].name,
                    "competition_id": competition_id,
                    "season_param": season_param(url),
                    "seasonId": text(data.get("seasonId")),
                    "season_display": text((data.get("season") or {}).get("display")),
                    "club_id": text(club_id),
                    "club_name": text(self.raw.club_names.get(str(club_id))),
                    "source_file": source_file(path),
                }


class TmSquads(_TmTable):
    """Squad membership from T2, with player attributes from today's player records (batch `/players`)."""

    name = "tm_squads"

    def rows(self) -> Iterator[Row]:
        for path in self.raw.files("club/*/squad__season=*.json"):
            url, data = load_record(path)
            if not data:
                continue
            season = season_param(url)
            club_id = path.parent.name
            for member in data.get("squad") or []:
                player = self.raw.players.get(str(member["playerId"]), {})
                attributes = player.get("attributes") or {}
                yield {
                    "competition_id": self.raw.club_league.get((club_id, season), ""),
                    "season_param": season,
                    "club_id": club_id,
                    **{k: text(v) for k, v in member.items()},
                    "player_name": text(player.get("name")),
                    "date_of_birth": text((player.get("lifeDates") or {}).get("dateOfBirth")),
                    "height": text(attributes.get("height")),
                    "preferred_foot": text((attributes.get("preferredFoot") or {}).get("name")),
                    "position": text((attributes.get("position") or {}).get("name")),
                    "position_group": text(attributes.get("positionGroup")),
                    "source_file": source_file(path),
                }


class TmInjuries(_TmTable):
    """One row per injury event from `/player/{id}/injury` (full career; season filtering happens later)."""

    name = "tm_injuries"

    def rows(self) -> Iterator[Row]:
        for path in self.raw.files("player/*/injury.json"):
            _, data = load_record(path)
            for injury in (data or {}).get("injuries") or []:
                yield flatten(injury) | {"source_file": source_file(path)}


class _PerformanceTable(_TmTable):
    def games(self) -> Iterator[tuple[Path, str, dict]]:
        for path in self.raw.files("player/*/performance-game.json"):
            _, data = load_record(path)
            for game in (data or {}).get("performance") or []:
                yield path, path.parent.name, game


class TmPlayerStats(_PerformanceTable):
    """
    Player x season x competition x club totals of the per-match records (no upstream table exists).

    `appearances` counts participationState == 'played' (as the SDK and website do); `state_*` columns count every
    participation state, e.g. `state_injured` = club matches missed through injury.
    """

    name = "tm_player_stats"

    def rows(self) -> Iterator[Row]:
        totals: dict[tuple[str, str, str, str], Counter] = defaultdict(Counter)
        meta: dict[tuple[str, str, str, str], Row] = {}
        for path, player_id, game in self.games():
            info, stats = game["gameInformation"], game["statistics"]
            key = (player_id, text(info["seasonId"]), text(info["competitionId"]), text(game["clubsInformation"]["club"]["clubId"]))
            meta.setdefault(key, {"competition_type_id": text(info.get("competitionTypeId")), "source_file": source_file(path)})
            total = totals[key]
            state = stats["generalStatistics"].get("participationState") or "unknown"
            total["matches_listed"] += 1
            total[f"state_{state.replace(' ', '_')}"] += 1
            if state != "played":
                continue
            total["appearances"] += 1
            for column, (group, field) in STAT_FIELDS.items():
                total[column] += (stats.get(group) or {}).get(field) or 0
            cards = stats.get("cardStatistics") or {}
            total["yellow_cards"] += 1 if cards.get("yellowCard") else 0
            total["second_yellow_cards"] += 1 if cards.get("yellowRedCard") else 0
            total["red_cards"] += 1 if cards.get("redCard") else 0

        count_columns = ["matches_listed", "appearances", *STAT_FIELDS, "yellow_cards", "second_yellow_cards", "red_cards"]
        count_columns += sorted({c for total in totals.values() for c in total} - set(count_columns))
        for key, total in totals.items():
            player_id, season_id, competition_id, club_id = key
            yield {
                "player_id": player_id,
                "season_id": season_id,
                "competition_id": competition_id,
                "competition_type_id": meta[key]["competition_type_id"],
                "club_id": club_id,
                **{column: str(total[column]) for column in count_columns},
                "source_file": meta[key]["source_file"],
            }


class TmFixtures(_PerformanceTable):
    """
    Club x match for every club-season collected in T2, in all competitions, from the squad players'
    `performance-game` records (union over the squad, deduplicated on club + game).
    """

    name = "tm_fixtures"

    def rows(self) -> Iterator[Row]:
        wanted = set(self.raw.club_league)
        seen: set[tuple[str, str]] = set()
        for path, _, game in self.games():
            info, clubs = game["gameInformation"], game["clubsInformation"]
            club_id, game_id = text(clubs["club"]["clubId"]), text(info["gameId"])
            if (club_id, text(info["seasonId"])) not in wanted or (club_id, game_id) in seen:
                continue
            seen.add((club_id, game_id))
            yield (
                {"club_id": club_id, "game_id": game_id}
                | flatten(info, "game.")
                | flatten(clubs["club"], "club.")
                | flatten(clubs["opponent"], "opponent.")
                | {"source_file": source_file(path)}
            )


def builders(root: Path = OUT_DIR) -> list[TableBuilder]:
    raw = TransfermarktRaw(root)
    return [TmClubs(raw), TmSquads(raw), TmInjuries(raw), TmPlayerStats(raw), TmFixtures(raw)]
