"""Loading the parsed tables and shared keys. Tables are read as text, exactly as the parsers wrote them."""

from pathlib import Path

import pandas as pd

from analysis.config import LEAGUES, SEASONS, TABLES_DIR, League

TABLES = (
    "fd_matches",
    "us_matches",
    "us_team_matches",
    "us_player_seasons",
    "tm_clubs",
    "tm_squads",
    "tm_injuries",
    "tm_player_stats",
    "tm_fixtures",
)

FIRST_SEASON, LAST_SEASON = SEASONS[0], SEASONS[-1]


def table_path(name: str) -> Path:
    return TABLES_DIR / f"{name}.csv"


def read_table(name: str) -> pd.DataFrame:
    """One parsed table, every column as text; empty cells stay empty strings (never NaN)."""
    return pd.read_csv(table_path(name), dtype=str, keep_default_na=False, encoding="utf-8")


def season_key(start_year: int) -> str:
    """Canonical season key used across all sources: 2014 -> '2014-15'."""
    return f"{start_year}-{(start_year + 1) % 100:02d}"


def season_from_date(dates: pd.Series) -> pd.Series:
    """Start year of the 1 July – 30 June season each date falls in (nullable int)."""
    d = pd.to_datetime(dates, errors="coerce")
    return (d.dt.year - (d.dt.month < 7)).astype("Int64")


def league_by_name(name: str) -> League:
    """League from its display name (as written by the Football-Data and TM club parsers)."""
    return next(league for league in LEAGUES if league.name == name)


def league_from_understat(key: str) -> str:
    return next(league.name for league in LEAGUES if league.understat == key)


def league_from_tm(competition_id: str) -> str:
    return next(league.name for league in LEAGUES if league.tm_id == competition_id)
