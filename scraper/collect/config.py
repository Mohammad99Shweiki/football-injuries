"""Static project configuration: paths, leagues, seasons and the expected counts used by validation."""

import os
from dataclasses import dataclass
from pathlib import Path

# Repository root: data/ and README.md live there, the scraper code in scraper/.
SCRAPER_DIR = Path(__file__).resolve().parent.parent
ROOT = SCRAPER_DIR.parent
RAW_DIR = ROOT / "data" / "raw"
TABLES_DIR = ROOT / "data" / "tables"
# Run state (manifest, live status, last run, smoke test) lives together, on the data volume in Docker too.
RUN_DIR = ROOT / "data" / "scraper_run"
MANIFEST_PATH = Path(os.environ.get("MANIFEST_PATH", RUN_DIR / "manifest.csv"))

USER_AGENT = "football-injuries-research/0.1 (academic coursework)"


@dataclass(frozen=True)
class League:
    """One league and its identifier in every source."""

    name: str
    fd_div: str
    understat: str
    tm_id: str

    def matches(self, key: str) -> bool:
        """True when `key` is any of this league's identifiers (case-insensitive)."""
        return key.lower() in {self.fd_div.lower(), self.understat.lower(), self.tm_id.lower()}


LEAGUES: tuple[League, ...] = (
    League("Premier League", "E0", "EPL", "GB1"),
    League("La Liga", "SP1", "La_liga", "ES1"),
    League("Serie A", "I1", "Serie_A", "IT1"),
    League("Bundesliga", "D1", "Bundesliga", "L1"),
    League("Ligue 1", "F1", "Ligue_1", "FR1"),
)

# Seasons are identified by their start year: 2014 means 2014/15.
SEASONS: tuple[int, ...] = tuple(range(2014, 2026))


def fd_season_code(season: int) -> str:
    """Football-Data season code, e.g. 2014 -> '1415'."""
    return f"{season % 100:02d}{(season + 1) % 100:02d}"


def season_label(season: int) -> str:
    """Human-readable season, e.g. 2014 -> '2014/15'."""
    return f"{season}/{(season + 1) % 100:02d}"


def league_by_key(key: str) -> League:
    for league in LEAGUES:
        if league.matches(key):
            return league
    raise ValueError(f"Unknown league: {key}")


def expected_clubs(league: League, season: int) -> int:
    if league.fd_div == "D1" or (league.fd_div == "F1" and season >= 2023):
        return 18
    return 20


def expected_league_matches(league: League, season: int) -> int:
    """Matches per league-season; Ligue 1 2019/20 stopped early because of COVID."""
    if league.fd_div == "F1" and season == 2019:
        return 279
    clubs = expected_clubs(league, season)
    return clubs * (clubs - 1)
