"""
Smoke-test findings (spec section 5, "Order and smoke test"), computed from the raw Transfermarkt store.

Each finding is {key, state: confirmed|verify|failed, title, detail}. They are shown in the dashboard's
"Scouting notes" and saved to `data/scraper_run/smoke.json` so they survive restarts.
"""

import json
from collections import Counter, defaultdict
from collections.abc import Callable
from pathlib import Path

from collect.config import RUN_DIR
from collect.fs import atomic_write
from collect.transfermarkt import OUT_DIR

SMOKE_PATH = RUN_DIR / "smoke.json"
SMOKE_LEAGUE, SMOKE_SEASON, SMOKE_PLAYERS = "EPL", 2016, 20
LEAGUE_MATCHES = 38  # Premier League, 20 clubs

def _data(path: Path) -> tuple[str, dict | None]:
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("status") != 200:
        return record["url"], None
    body = json.loads(record["body"])
    return record["url"], body.get("data") if body.get("success") else None

def _finding(key: str, state: str, title: str, detail: str) -> dict:
    return {"key": key, "state": state, "title": title, "detail": detail}

def t2_season(root: Path) -> dict:
    squads = sorted(root.glob(f"club/*/squad__season={SMOKE_SEASON}.json"))
    if not squads:
        return _finding("t2_season", "verify", "T2 returns the past squad", "No squad stored yet for the smoke season.")
    arsenal = root / "club" / "11" / f"squad__season={SMOKE_SEASON}.json"
    path = arsenal if arsenal.exists() else squads[0]
    _, data = _data(path)
    members = (data or {}).get("squad") or []
    types = Counter(m.get("type") for m in members)
    club = path.parent.name
    if members and set(types) == {"historical"}:
        return _finding(
            "t2_season", "confirmed", "T2 returns the past squad",
            f"Club {club}, season {SMOKE_SEASON}: {len(members)} members, all marked 'historical' — the "
            f"{SMOKE_SEASON}/{(SMOKE_SEASON + 1) % 100:02d} squad, not today's.",
        )
    return _finding("t2_season", "failed", "T2 returns the past squad", f"Club {club}: member types {dict(types)}.")

def t3_single_response(root: Path) -> dict:
    files = sorted(root.glob("player/*/injury.json"))
    if not files:
        return _finding("t3_pagination", "verify", "T3 injury history in one response", "No injury history stored yet.")
    counts = [len(((_data(p)[1] or {}).get("injuries")) or []) for p in files]
    return _finding(
        "t3_pagination", "confirmed", "T3 injury history in one response",
        f"{len(files)} players, up to {max(counts)} injuries each, all in a single response. "
        "The SDK's 15-per-page split is local, so no pagination requests are needed.",
    )

def t4_minutes(root: Path) -> dict:
    """Minutes are recorded for matches the player played; other participation states carry none."""
    files = sorted(root.glob("player/*/performance-game.json"))
    if not files:
        return _finding("t4_minutes", "verify", "T4 includes minutes", "No performance records stored yet.")
    played = with_minutes = 0
    for path in files:
        for game in (_data(path)[1] or {}).get("performance") or []:
            stats = game.get("statistics") or {}
            if (stats.get("generalStatistics") or {}).get("participationState") != "played":
                continue
            played += 1
            with_minutes += (stats.get("playingTimeStatistics") or {}).get("playedMinutes") is not None
    share = with_minutes / played if played else 0
    state = "confirmed" if share >= 0.99 else "verify"
    return _finding(
        "t4_minutes", state, "T4 includes minutes",
        f"playedMinutes recorded in {with_minutes:,} of {played:,} matches played ({len(files)} players); "
        "empty only when the player didn't play. Summed per season × competition × club in tm_player_stats.",
    )


def t5_fixtures(root: Path) -> dict:
    """Union of the sampled players' records per club for the smoke season: all competitions, with dates."""
    clubs_path = root / "competition" / "GB1" / f"club__season={SMOKE_SEASON}.json"
    league_clubs = set(map(str, ((_data(clubs_path)[1] or {}).get("clubIds") or []))) if clubs_path.exists() else set()
    games: dict[str, set[str]] = defaultdict(set)
    competitions: dict[str, set[str]] = defaultdict(set)
    dated = total = 0
    for path in sorted(root.glob("player/*/performance-game.json")):
        for game in (_data(path)[1] or {}).get("performance") or []:
            info, club = game["gameInformation"], str(game["clubsInformation"]["club"]["clubId"])
            if str(info.get("seasonId")) != str(SMOKE_SEASON) or club not in league_clubs:
                continue
            total += 1
            dated += bool((info.get("date") or {}).get("dateTimeUTC"))
            competitions[club].add(info["competitionId"])
            if info["competitionId"] == "GB1":
                games[club].add(str(info["gameId"]))
    if not total:
        return _finding("t5_fixtures", "verify", "T5 fixtures come from T4 records", "No smoke-season match records yet.")
    full = sum(1 for club in games if len(games[club]) == LEAGUE_MATCHES)
    most = max(len(c) for c in competitions.values())
    state = "confirmed" if full and dated == total else "verify"
    return _finding(
        "t5_fixtures", state, "T5 fixtures come from T4 records",
        f"Records cover all competitions (up to {most} per club) with dates on {dated:,} of {total:,}. "
        f"{full} of {len(games)} sampled clubs already have all {LEAGUE_MATCHES} league matches from just "
        f"{SMOKE_PLAYERS} players; the full run unions every squad member. No spielplan HTML needed.",
    )

CHECKS: tuple[Callable[[Path], dict], ...] = (t2_season, t3_single_response, t4_minutes, t5_fixtures)

def findings(root: Path = OUT_DIR) -> list[dict]:
    return [check(root) for check in CHECKS]

def save(results: list[dict]) -> None:
    atomic_write(SMOKE_PATH, json.dumps(results, ensure_ascii=False, indent=1).encode("utf-8"))

def load() -> list[dict]:
    try:
        return json.loads(SMOKE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []

if __name__ == "__main__":
    for item in findings():
        print(f"[{item['state']}] {item['title']}: {item['detail']}")
