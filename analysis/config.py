"""Analysis configuration: paths, leagues, seasons and expected counts. Independent of the scraper code."""

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"  # scraper downloads, read only
TABLES_DIR = DATA_DIR / "tables"  # parsed tables, read only
MAPPINGS_DIR = ROOT / "mappings"  # hand-reviewed inputs, tracked in git
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# One output folder per phase: data/<phase>/. A phase writes only to its own folder and reads earlier ones.
PHASES = ("01_entities", "02_injuries", "03_features", "04_clusters", "05_injury_analysis", "06_report")


def phase_dir(phase: str) -> Path:
    """Output folder of a phase, e.g. phase_dir("02_injuries") -> data/02_injuries/ (created if missing)."""
    if phase not in PHASES:
        raise ValueError(f"Unknown phase: {phase}. Known: {', '.join(PHASES)}")
    path = DATA_DIR / phase
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass(frozen=True)
class League:
    """One league and its identifier in every source."""

    name: str
    fd_div: str
    understat: str
    tm_id: str


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
