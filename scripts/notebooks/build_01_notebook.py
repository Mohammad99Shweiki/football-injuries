"""Writes notebooks/01_entities.ipynb: Phase 1 as a sequence of steps, each with notes, code and a check."""

import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
cells = []


def md(text: str) -> None:
    cells.append({"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)})


def code(text: str) -> None:
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
                  "source": text.strip("\n").splitlines(keepends=True)})


md('''
# Phase 1: Entity resolution (data integration)

**Goal:** one identity per club across Transfermarkt (TM), Football-Data (FD) and Understat (US), so team-season
features (Phase 3) and injuries (Phase 2, TM) can be joined. Plus one season key across sources.

**Steps**
1. List each source's team-seasons
2. Normalise names (for comparison only)
3. Score a pair of names
4. Match teams within each league-season (exact → normalised → fuzzy, one-to-one)
5. Collapse to one row per club: the proposed team map
6. Load the reviewed map (`mappings/team_map.csv`)
7. Build the team-season table and check it is complete
8. Put each source's league matches in one format
9. Verify the map on fixtures (independent of names)
10. Check season labels against match dates
11. Write the report

**Inputs:** `data/tables/` (`tm_clubs`, `fd_matches`, `us_team_matches`, `us_matches`, `tm_fixtures`).
**Outputs:** `mappings/team_map.csv` (reviewed, in git), `data/01_entities/`, `reports/01_entities.md`.
Each step is logged in `docs/PREPROCESSING_LOG.md`; choices in `docs/DECISIONS.md`.
''')

code('''
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, str(Path.cwd().parent))  # project root, for the analysis package
from analysis.config import LEAGUES, MAPPINGS_DIR, REPORTS_DIR, phase_dir
from analysis.load import league_from_tm, league_from_understat, read_table, season_from_date, season_key
from analysis.report import md_table, pct

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 200)

PHASE = "01_entities"
OUT_DIR = phase_dir(PHASE)
TEAM_MAP = MAPPINGS_DIR / "team_map.csv"
''')

# ---- step 1
md('''
## Step 1. Team-seasons per source

One row per team per league-season from each source. TM is the master list: its club id is the key and its name
becomes the one club name, `club`. Football-Data has no club table, so its names come from the home and away columns;
its season code `"1415"` becomes start year 2014 (TM and Understat already use start years).
''')
code('''
def tm_team_seasons() -> pd.DataFrame:
    cl = read_table("tm_clubs")
    return pd.DataFrame({
        "league": cl.league,
        "season": cl.season_param.astype(int),
        "tm_club_id": cl.club_id,
        "club": cl.club_name,  # the one club name used everywhere (Transfermarkt's)
    }).drop_duplicates()


def fd_team_seasons() -> pd.DataFrame:
    fd = read_table("fd_matches")
    names = pd.concat([fd[["league", "season_code", "HomeTeam"]].set_axis(["league", "season_code", "fd_name"], axis=1),
                       fd[["league", "season_code", "AwayTeam"]].set_axis(["league", "season_code", "fd_name"], axis=1)])
    names["season"] = 2000 + names.season_code.str[:2].astype(int)
    return names[["league", "season", "fd_name"]].drop_duplicates().reset_index(drop=True)


def us_team_seasons() -> pd.DataFrame:
    us = read_table("us_team_matches")
    out = pd.DataFrame({
        "league": us.league.map(league_from_understat),
        "season": us.season.astype(int),
        "us_team_id": us.team_id,
        "us_name": us.team_title,
    })
    return out.drop_duplicates().reset_index(drop=True)


tm, fd, us = tm_team_seasons(), fd_team_seasons(), us_team_seasons()
''')
code('''
# Check: the same number of team-seasons in every source and in every league-season.
sizes = pd.DataFrame({
    "TM": tm.groupby(["league", "season"]).size(),
    "FD": fd.groupby(["league", "season"]).size(),
    "US": us.groupby(["league", "season"]).size(),
})
assert (sizes.nunique(axis=1) == 1).all(), sizes[sizes.nunique(axis=1) > 1]
pd.DataFrame({"team-seasons": [len(tm), len(fd), len(us)],
              "distinct clubs": [tm.tm_club_id.nunique(), fd.fd_name.nunique(), us.us_team_id.nunique()]},
             index=["Transfermarkt", "Football-Data", "Understat"])
''')

# ---- step 2
md('''
## Step 2. Normalise names

Reduces a name to the words that identify the club, **for comparison only** (original names are kept):
accents removed, lower case, punctuation removed, Football-Data abbreviations expanded, legal forms and
sport-club prefixes (FC, SC, Calcio, …) and founding years dropped.
''')
code('''
# Words that say nothing about which club it is: legal forms, sport-club prefixes, articles.
STOPWORDS = {
    "fc", "cf", "afc", "ac", "as", "ss", "ssc", "sc", "us", "rc", "rcd", "ud", "cd", "sd", "ca", "sv", "vfb", "vfl",
    "tsg", "fsv", "ogc", "losc", "acf", "bc", "club", "calcio", "de", "del", "la", "le", "1", "and", "hove", "albion",
    "balompie", "futbol", "football", "olympique", "stade", "en",
}
# Football-Data abbreviations, expanded before comparing.
ABBREVIATIONS = {
    "ath": "athletic", "man": "manchester", "nott'm": "nottingham", "utd": "united", "sp": "sporting",
    "ein": "eintracht", "m'gladbach": "monchengladbach", "m.gladbach": "monchengladbach", "wolves": "wolverhampton",
    "spurs": "tottenham", "qpr": "queens park rangers", "sg": "saint germain", "st": "saint",
}


def normalise(name: str) -> str:
    """Lower case, no accents or punctuation, abbreviations expanded, stopwords and founding years dropped."""
    # NFKD splits "ö" into "o" + a combining mark; encoding to ASCII drops the mark.
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    tokens = []
    for token in re.split(r"[\\s\\-/]+", text):
        token = ABBREVIATIONS.get(token, token)
        for part in re.sub(r"[^a-z0-9 ]", " ", token).split():
            if part not in STOPWORDS and not part.isdigit():
                tokens.append(part)
    return " ".join(tokens)
''')
code('''
# Check: examples from each source.
examples = ["1.FC Köln", "FC Koln", "FC Cologne", "Nott'm Forest", "Nottingham Forest", "Ath Madrid",
            "Atlético de Madrid", "Paris Saint-Germain", "Paris SG", "Paris FC", "Borussia Mönchengladbach", "M'gladbach"]
pd.DataFrame({"name": examples, "normalised": [normalise(n) for n in examples]})
''')

# ---- step 3
md('''
## Step 3. Score a pair of names

Returns a similarity from 0 to 100 and how it was reached: `exact` (same name, ignoring case), `normalised`
(equal after step 2) or `fuzzy`. The fuzzy score is the mean of rapidfuzz's token-set and token-sort ratios:
token-set alone gives 100 when one name is contained in another ("paris" in "paris saint germain"), which once
mapped PSG to Paris FC.
''')
code('''
METHOD_RANK = {"exact": 0, "normalised": 1, "fuzzy": 2}


def name_score(a: str, b: str) -> tuple[float, str]:
    """Similarity 0–100 and how it was reached: exact, normalised (equal after normalise) or fuzzy."""
    if a.casefold() == b.casefold():
        return 100.0, "exact"
    na, nb = normalise(a), normalise(b)
    if na == nb:
        return 100.0, "normalised"
    # Mean of set and sort ratios: a name contained in a longer one is not a full match.
    return (fuzz.token_set_ratio(na, nb) + fuzz.token_sort_ratio(na, nb)) / 2, "fuzzy"
''')
code('''
# Check: the PSG / Paris FC case and a few typical pairs.
pairs = [("Paris Saint-Germain", "Paris SG"), ("Paris Saint-Germain", "Paris FC"), ("Paris FC", "Paris FC"),
         ("1.FC Köln", "FC Koln"), ("1.FC Köln", "FC Cologne"), ("Leicester City", "Leicester")]
pd.DataFrame([(a, b, *name_score(a, b)) for a, b in pairs], columns=["TM name", "source name", "score", "method"]).round(1)
''')

# ---- step 4
md('''
## Step 4. Match teams within each league-season

A club is only compared with the ~20 clubs in the same league-season. Within each:
1. Fix **exact** pairs, then **normalised** pairs, each only when it is the single such candidate on both sides.
2. Match the rest with the **Hungarian algorithm** (`linear_sum_assignment`): the one-to-one pairing with the
   highest total score, so two TM clubs can never take the same name.
''')
code('''
def assign(tm: pd.DataFrame, other: pd.DataFrame, key: str, name: str) -> pd.DataFrame:
    """One-to-one TM club for each `other` team within every league-season, maximising the summed name score."""
    rows = []
    for (league, season), left in tm.groupby(["league", "season"]):
        right = other[(other.league == league) & (other.season == season)]
        scores = [[name_score(t, o) for o in right[name]] for t in left.club]
        pairs = []
        free_i, free_j = set(range(len(left))), set(range(len(right)))
        # Exact, then normalised: fix a pair only when it is the single such candidate on both sides.
        for method in ("exact", "normalised"):
            hits = [(i, j) for i in free_i for j in free_j if scores[i][j][1] == method]
            for i, j in hits:
                if sum(a == i for a, _ in hits) == 1 and sum(b == j for _, b in hits) == 1:
                    pairs.append((i, j))
            free_i -= {i for i, _ in pairs}
            free_j -= {j for _, j in pairs}
        fi, fj = sorted(free_i), sorted(free_j)
        cost = [[-scores[i][j][0] for j in fj] for i in fi]
        pairs += [(fi[a], fj[b]) for a, b in zip(*linear_sum_assignment(cost))] if fi and fj else []
        for i, j in pairs:
            score, method = scores[i][j]
            rows.append({
                "league": league, "season": season, "tm_club_id": left.tm_club_id.iloc[i],
                key: right[key].iloc[j], f"{key}_score": score, f"{key}_method": method,
            })
    return pd.DataFrame(rows)


fd_match = assign(tm, fd, "fd_name", "fd_name")
us_match = assign(tm, us, "us_team_id", "us_name")
''')
code('''
# Check: every team-season matched, and how (team-season level).
assert len(fd_match) == len(fd) and len(us_match) == len(us)
pd.DataFrame({"Football-Data": fd_match.fd_name_method.value_counts(),
              "Understat": us_match.us_team_id_method.value_counts()}).reindex(list(METHOD_RANK))
''')
code('''
# Check: the weakest fuzzy matches (lowest scores first).
weakest = fd_match.merge(tm, on=["league", "season", "tm_club_id"]).nsmallest(8, "fd_name_score")
weakest[["league", "season", "club", "fd_name", "fd_name_score"]].round(1)
''')

# ---- step 5
md('''
## Step 5. One row per club: the proposed team map

The 1,170 team-season matches collapse to one row per club, keeping the worst method and score over its seasons.
A club gets two rows only if a source uses two names or ids for it. Rows are flagged for review when the name
score is below `REVIEW_BELOW` or the club has two rows.
''')
code('''
REVIEW_BELOW = 75  # name score under which a match is listed for manual review (short forms like "Leicester" score 80-90)


def propose_team_map(tm: pd.DataFrame, us: pd.DataFrame, fd_match: pd.DataFrame, us_match: pd.DataFrame) -> pd.DataFrame:
    """Club-level proposal: one row per TM club and source names (more rows only if a source uses two)."""
    ts = tm.merge(fd_match, on=["league", "season", "tm_club_id"], how="left").merge(
        us_match, on=["league", "season", "tm_club_id"], how="left"
    ).merge(us[["league", "season", "us_team_id", "us_name"]], on=["league", "season", "us_team_id"], how="left")

    def worst(methods: pd.Series) -> str:
        return max(methods, key=METHOD_RANK.get)

    grouped = ts.groupby(["tm_club_id", "fd_name", "us_team_id", "us_name"], sort=False)
    proposal = grouped.agg(
        club=("club", "first"),
        leagues=("league", lambda s: ", ".join(sorted(set(s)))),
        n_seasons=("season", "nunique"),
        first_season=("season", "min"),
        last_season=("season", "max"),
        fd_method=("fd_name_method", worst),
        fd_score=("fd_name_score", "min"),
        us_method=("us_team_id_method", worst),
        us_score=("us_team_id_score", "min"),
    ).reset_index()
    proposal[["fd_score", "us_score"]] = proposal[["fd_score", "us_score"]].round(1)
    proposal["first_season"] = proposal.first_season.map(season_key)
    proposal["last_season"] = proposal.last_season.map(season_key)
    proposal["review"] = (proposal[["fd_score", "us_score"]].min(axis=1) < REVIEW_BELOW) | proposal.tm_club_id.duplicated(keep=False)
    cols = ["tm_club_id", "club", "fd_name", "us_team_id", "us_name", "leagues", "n_seasons", "first_season",
            "last_season", "fd_method", "fd_score", "us_method", "us_score", "review"]
    return proposal[cols].sort_values(["leagues", "club"]).reset_index(drop=True)


proposal = propose_team_map(tm, us, fd_match, us_match)
proposal.to_csv(OUT_DIR / "team_map_proposed.csv", index=False)
''')
code('''
# Check: club rows by method, and the rows flagged for review.
methods = pd.DataFrame({"Football-Data": proposal.fd_method.value_counts(),
                        "Understat": proposal.us_method.value_counts()}).reindex(list(METHOD_RANK)).fillna(0).astype(int)
methods = methods.rename_axis("method (worst over seasons)")
review = proposal[proposal.review][["tm_club_id", "club", "fd_name", "fd_score", "us_name", "us_score", "leagues", "n_seasons"]]
print(len(proposal), "club rows for", proposal.tm_club_id.nunique(), "clubs")
display(methods, review)
''')

# ---- step 6
md('''
## Step 6. Load the reviewed map

`mappings/team_map.csv` is the reviewed mapping, tracked in git. The first run creates it from the proposal; after
that it is never overwritten, so manual edits stick. Any difference between the reviewed map and a fresh proposal
is shown here and in the report.
''')
code('''
def load_reviewed_map(proposal: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, bool]:
    """The reviewed map (created from the proposal on the first run) and rows where it differs from the proposal."""
    created = not TEAM_MAP.exists()
    if created:
        MAPPINGS_DIR.mkdir(exist_ok=True)
        proposal.to_csv(TEAM_MAP, index=False)
    reviewed = pd.read_csv(TEAM_MAP, dtype=str, keep_default_na=False)
    key = ["tm_club_id", "fd_name", "us_team_id"]
    diff = proposal[key].astype(str).merge(reviewed[key], how="outer", indicator=True)
    diff = diff[diff._merge != "both"].replace({"_merge": {"left_only": "proposal only", "right_only": "reviewed only"}})
    return reviewed, diff.rename(columns={"_merge": "in"}), created


team_map, diff, created = load_reviewed_map(proposal)
print("created from proposal" if created else "reviewed file used as is", "|", len(diff), "differences from the proposal")
diff
''')

# ---- step 7
md('''
## Step 7. Team-season table

One row per TM team-season with its Football-Data name and Understat id, built from the **reviewed** map. This is
the join key for Phase 3. The checks below must all be zero.
''')
code('''
def build_team_seasons(team_map: pd.DataFrame, tm: pd.DataFrame, fd: pd.DataFrame, us: pd.DataFrame) -> pd.DataFrame:
    """One row per TM team-season with its Football-Data and Understat identity, from the reviewed map."""
    fd_ids = team_map[["fd_name", "tm_club_id"]].drop_duplicates()
    us_ids = team_map[["us_team_id", "tm_club_id"]].drop_duplicates()
    fd = fd.merge(fd_ids, on="fd_name", how="left")
    us = us.merge(us_ids, on="us_team_id", how="left")
    ts = tm.merge(fd, on=["league", "season", "tm_club_id"], how="left").merge(
        us, on=["league", "season", "tm_club_id"], how="left"
    )
    ts.insert(1, "season_key", ts.season.map(season_key))
    return ts.sort_values(["league", "season", "club"]).reset_index(drop=True)


ts = build_team_seasons(team_map, tm, fd, us)
ts.to_csv(OUT_DIR / "team_seasons.csv", index=False)
''')
code('''
# Check: completeness and uniqueness (all must be 0).
checks = {
    "FD names tied to 2+ clubs": team_map.groupby("fd_name").tm_club_id.nunique().gt(1).sum(),
    "Understat ids tied to 2+ clubs": team_map.groupby("us_team_id").tm_club_id.nunique().gt(1).sum(),
    "team-seasons without FD name": ts.fd_name.isna().sum(),
    "team-seasons without Understat id": ts.us_team_id.isna().sum(),
    "FD team-seasons not mapped": len(fd) - ts.fd_name.notna().sum(),
    "Understat team-seasons not mapped": len(us) - ts.us_team_id.notna().sum(),
    "duplicate team-seasons": ts.duplicated(["league", "season", "tm_club_id"]).sum(),
}
assert not any(checks.values()), checks
print(len(ts), "team-seasons")
pd.Series(checks, name="count").to_frame()
''')

# ---- step 8
md('''
## Step 8. League matches in one format

Each source's league matches as `league, season, date, home, away, hg, ag`:
- **TM:** Big Five league games only. Every game appears once per club, so duplicates on `game_id` are removed and
  the home side is put first.
- **FD:** two date formats (`dd/mm/yyyy` and `dd/mm/yy`).
- **Understat:** unplayed fixtures (`isResult = false`, the cancelled Ligue 1 2019-20 games) dropped.
''')
code('''
def tm_league_matches() -> pd.DataFrame:
    """TM league matches (Big Five competitions only), one row per game, home side first."""
    fx = read_table("tm_fixtures")
    fx = fx[fx["game.competitionId"].isin([lg.tm_id for lg in LEAGUES]) & (fx["club.goalsTotal"] != "")]
    home = fx["club.venue"] == "home"
    out = pd.DataFrame({
        "game_id": fx.game_id,
        "league": fx["game.competitionId"].map(league_from_tm),
        "season": fx["game.seasonId"].astype(int),
        "date": pd.to_datetime(fx["game.date.dateTimeUTC"].str[:10]),
        "home": fx["club.clubId"].where(home, fx["opponent.clubId"]),
        "away": fx["opponent.clubId"].where(home, fx["club.clubId"]),
        "hg": fx["club.goalsTotal"].where(home, fx["opponent.goalsTotal"]).astype(int),
        "ag": fx["opponent.goalsTotal"].where(home, fx["club.goalsTotal"]).astype(int),
    })
    return out.drop_duplicates("game_id").reset_index(drop=True)


def fd_league_matches() -> pd.DataFrame:
    fd = read_table("fd_matches")
    long_year = fd.Date.str.len() == 10
    dates = pd.to_datetime(fd.Date.where(long_year), format="%d/%m/%Y").fillna(
        pd.to_datetime(fd.Date.where(~long_year), format="%d/%m/%y")
    )
    return pd.DataFrame({
        "league": fd.league,
        "season": 2000 + fd.season_code.str[:2].astype(int),
        "date": dates,
        "home": fd.HomeTeam,
        "away": fd.AwayTeam,
        "hg": fd.FTHG.astype(int),
        "ag": fd.FTAG.astype(int),
    })


def us_league_matches() -> pd.DataFrame:
    um = read_table("us_matches")
    um = um[um.isResult == "true"]
    return pd.DataFrame({
        "league": um.league.map(league_from_understat),
        "season": um.season.astype(int),
        "date": pd.to_datetime(um.datetime.str[:10]),
        "home": um["h.id"],
        "away": um["a.id"],
        "hg": um["goals.h"].astype(int),
        "ag": um["goals.a"].astype(int),
    })


tm_m, fd_m, us_m = tm_league_matches(), fd_league_matches(), us_league_matches()
''')
code('''
# Check: the same number of league matches in every source, and no missing dates.
assert len(tm_m) == len(fd_m) == len(us_m)
assert not (tm_m.date.isna().any() or fd_m.date.isna().any() or us_m.date.isna().any())
pd.DataFrame({"matches": [len(tm_m), len(fd_m), len(us_m)]}, index=["Transfermarkt", "Football-Data", "Understat"])
''')

# ---- step 9
md('''
## Step 9. Verify the map on fixtures

Independent of names: each FD and Understat match is translated to TM club ids through the map and looked up in
TM by league, season, home and away club. A wrong mapping would leave matches unfound. Scores and dates are compared
too; a one-day gap is TM's UTC kick-off time.
''')
code('''
def verify_fixtures(matches: pd.DataFrame, ids: pd.DataFrame, key: str, tm: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Translate a source's matches to TM club ids and look each one up in TM (same league-season, home and away)."""
    to_tm = ids.set_index(key).tm_club_id
    m = matches.assign(home=matches.home.map(to_tm), away=matches.away.map(to_tm))
    joined = m.merge(tm, on=["league", "season", "home", "away"], how="left", suffixes=("", "_tm"))
    found = joined.game_id.notna()
    same_score = found & (joined.hg == joined.hg_tm) & (joined.ag == joined.ag_tm)
    days = (joined.date - joined.date_tm).dt.days.abs()
    summary = {
        "matches": len(m),
        "unmapped_team": int((m.home.isna() | m.away.isna()).sum()),
        "found_in_tm": int(found.sum()),
        "same_score": int(same_score.sum()),
        "same_date": int((found & (days == 0)).sum()),
        "date_off_1_day": int((found & (days == 1)).sum()),
        "date_off_more": int((found & (days > 1)).sum()),
    }
    problems = joined[~same_score | (days > 1)]
    return summary, problems


fd_sum, fd_bad = verify_fixtures(fd_m, team_map[["fd_name", "tm_club_id"]].drop_duplicates(), "fd_name", tm_m)
us_sum, us_bad = verify_fixtures(us_m, team_map[["us_team_id", "tm_club_id"]].drop_duplicates(), "us_team_id", tm_m)
bad = pd.concat([fd_bad.assign(source="Football-Data"), us_bad.assign(source="Understat")])
bad.to_csv(OUT_DIR / "fixture_mismatches.csv", index=False)
fixtures = pd.DataFrame({"Football-Data": fd_sum, "Understat": us_sum}).T.rename_axis("source")
fixtures
''')
code('''
# Check: matches whose score differs (all are awarded results: one source has the score on the pitch).
clubs = tm.drop_duplicates("tm_club_id").set_index("tm_club_id").club
diff_score = bad[(bad.hg != bad.hg_tm) | (bad.ag != bad.ag_tm)]
score_diff = pd.DataFrame({
    "league": diff_score.league, "season": diff_score.season.map(season_key),
    "date": diff_score.date.dt.date, "home": diff_score.home.map(clubs), "away": diff_score.away.map(clubs),
    "source": diff_score.source, "source score": diff_score.hg.astype(str) + "-" + diff_score.ag.astype(str),
    "TM score": diff_score.hg_tm.astype(int).astype(str) + "-" + diff_score.ag_tm.astype(int).astype(str),
}).sort_values(["date", "source"])
score_diff
''')

# ---- step 10
md('''
## Step 10. Season labels vs match dates

The date rule (1 July – 30 June) is what Phase 2 would use for injuries. Here it is compared with each source's
own season label for league matches.
''')
code('''
def season_label_check(matches: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Per source: league matches whose 1 July – 30 June date season differs from the source's season label."""
    rows = []
    for source, m in matches.items():
        off = m[season_from_date(m.date) != m.season]
        rows.append({"source": source, "matches": len(m), "date season ≠ label": len(off),
                     "share": pct(len(off), len(m)),
                     "where": ", ".join(f"{lg} {season_key(s)}: {n}" for (lg, s), n in off.groupby(["league", "season"]).size().items()) or "–"})
    return pd.DataFrame(rows).set_index("source")


seasons = season_label_check({"Transfermarkt": tm_m, "Football-Data": fd_m, "Understat": us_m})
seasons
''')

# ---- step 11
md('''
## Step 11. Report

Writes `reports/01_entities.md` from the results above.
''')
code('''
renamed = proposal[proposal.tm_club_id.duplicated(keep=False)]
fixture_ok = fd_sum["found_in_tm"] == fd_sum["matches"] and us_sum["found_in_tm"] == us_sum["matches"]
n_awarded = score_diff[["date", "home"]].drop_duplicates().shape[0]

out = [
    "# Phase 1: Entity resolution",
    "",
    f"Generated {date.today().isoformat()} by `notebooks/01_entities.ipynb`, where each step is shown with its checks.",
    "",
    "## Key findings",
    "",
    f"- **Every team-season maps.** {len(ts):,} TM team-seasons, each with one Football-Data name and one Understat team "
    f"({team_map.tm_club_id.nunique()} clubs). No source name points to two clubs, and no team-season is duplicated.",
    f"- **Fixtures confirm the map{'' if fixture_ok else ' only partly'}.** Of {fd_sum['matches']:,} Football-Data and {us_sum['matches']:,} Understat league matches, "
    f"{fd_sum['found_in_tm']:,} and {us_sum['found_in_tm']:,} are found in TM with the same home and away club. "
    f"Scores differ only for {n_awarded} awarded results.",
    f"- **Names:** {proposal.review.sum()} club rows score below {REVIEW_BELOW} on names alone or have two rows, and are listed below for review; "
    "the fixture check is the stronger evidence for them.",
    "- **Seasons:** canonical key `\\"2014-15\\"`. League matches played after 30 June are labelled with the earlier season by every source "
    "(the 2019-20 COVID restart ran into July and August 2020), so the date rule (1 July – 30 June) and the season label disagree there. "
    "Phase 2 must attribute injuries to club-seasons by squad membership, not by the date rule alone.",
    "",
    "## 1. Method",
    "",
    "1. **Team-seasons per source:** TM `tm_clubs`; Football-Data home and away names per league-season; Understat `team_id` and title.",
    "2. **Names, within each league-season:** exact match, then equal after normalising (accents, legal forms such as FC/SC/AC, "
    "founding years and Football-Data abbreviations removed), each fixed only when unambiguous. The rest are fuzzy: the mean of `rapidfuzz` "
    "token-set and token-sort ratios, assigned one-to-one (Hungarian algorithm), so a club can't take two names in one league-season.",
    f"3. **Club level:** the league-season matches are collapsed to one row per club in `mappings/team_map.csv`. A row is flagged for review "
    f"if its worst name score is below {REVIEW_BELOW} or a club has more than one row (a source uses two names or ids for it).",
    "4. **Fixture check (independent of names):** each Football-Data and Understat league match is translated to TM club ids "
    "and looked up in TM's fixtures by league, season, home and away club; score and date are compared.",
    "",
    "## 2. Results",
    "",
    "### Clubs and team-seasons",
    "",
    md_table(pd.DataFrame({
        "clubs": [tm.tm_club_id.nunique(), fd.fd_name.nunique(), us.us_team_id.nunique()],
        "team-seasons": [len(tm), len(fd), len(us)],
        "team-seasons mapped": [len(ts), ts.fd_name.notna().sum(), ts.us_team_id.notna().sum()],
    }, index=pd.Index(["Transfermarkt", "Football-Data", "Understat"], name="source"))),
    "",
    "### How names matched (club rows)",
    "",
    md_table(methods),
    "",
    f"### For review: name score below {REVIEW_BELOW}",
    "",
    "Each club is called by its Transfermarkt name (`club`); the other two columns are the names the sources use, kept as join keys.",
    "",
    md_table(review, index=False) if len(review) else "None.",
    "",
    "### Clubs with more than one row (a source uses two names or ids)",
    "",
    md_table(renamed[["tm_club_id", "club", "fd_name", "us_team_id", "us_name", "first_season", "last_season"]], index=False) if len(renamed) else "None.",
    "",
    "Parma went bankrupt in 2015 and was refounded; Understat gives the new club a new id, while TM keeps one club. "
    "Both rows are kept, so each Understat team-season still maps to TM club 130.",
    "",
    "### Fixture check",
    "",
    md_table(fixtures),
    "",
    "- `found_in_tm`: same league-season, home and away club in TM. `same_score`: also the same final score.",
    "- Dates: TM stores kick-off in UTC; a one-day difference is a time-zone shift, not a different match. Understat's few larger gaps "
    "are postponed matches listed under another date.",
    f"- Matches failing a check are in `data/{PHASE}/fixture_mismatches.csv` ({len(bad)} rows).",
    "",
    "Score differences. All are awarded results, where a source keeps either the score on the pitch or the awarded score; "
    "the teams agree in every case:",
    "",
    md_table(score_diff, index=False) if len(score_diff) else "None.",
    "",
    "## 3. Seasons",
    "",
    "One key across sources, `season = \\"2014-15\\"` … `\\"2025-26\\"` (`analysis.load.season_key`): Football-Data `season_code` 1415, "
    "Understat and TM start year 2014. TM's injury `seasonId` agrees with the date season for 98.3% of in-window injuries (Phase 0).",
    "",
    "League matches whose date season (1 July – 30 June) differs from the source's own label:",
    "",
    md_table(seasons),
    "",
    "## 4. Outputs",
    "",
    f"- `mappings/team_map.csv`: the reviewed club map (tracked in git). {'Created from the proposal on this run.' if created else 'Used as is.'}",
    f"- `data/{PHASE}/team_map_proposed.csv`: the automatic proposal. Differences from the reviewed map: {len(diff)}.",
    f"- `data/{PHASE}/team_seasons.csv`: one row per team-season (`league, season_key, season, tm_club_id, club, fd_name, us_team_id, us_name`), "
    "the join key for Phase 3.",
    "",
]
if len(diff):
    out += ["### Reviewed map vs proposal", "", md_table(diff, index=False), ""]
(REPORTS_DIR / "01_entities.md").write_text("\\n".join(out), encoding="utf-8")
print("wrote", REPORTS_DIR / "01_entities.md")
''')

for i, cell in enumerate(cells):
    cell["id"] = f"entities-{i:02d}"
old = json.loads((ROOT / "notebooks/01_entities.ipynb").read_text())
nb = {"cells": cells, "metadata": old["metadata"], "nbformat": 4, "nbformat_minor": 5}
(ROOT / "notebooks/01_entities.ipynb").write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
print(len(cells), "cells")
