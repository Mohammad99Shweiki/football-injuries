"""Writes notebooks/03_features.ipynb: Phase 3 as a sequence of steps, each with notes, code and a check."""

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
# Phase 3: Team-season features (transformation + reduction)

**Goal:** one row per team-season (1,170) describing **playing style**, plus the team's **workload** and team
strength measures kept alongside. Every feature is a per-match rate, a share or a season total, so leagues of 18 and
20 clubs and the shortened Ligue 1 2019-20 are comparable.

Each feature has a **role**:
- **style**: clustered in Phase 4 (how a team plays);
- **outcome**: npxG and npxGA, kept to check how far clusters follow team strength, not clustered (open decision 5);
- **exposure**: workload and rotation, not clustered; used in Phase 5 as the load players are exposed to.

| Group | Features | Role | Source |
|---|---|---|---|
| Pressing | PPDA (Σ passes allowed / Σ defensive actions), opponent PPDA | style | Understat league data |
| Ball progression | deep completions for and against (per match) | style | Understat league data |
| Attack type and shape | fast-attack share, slow-attack share, conceded fast-attack share, set-piece share, outside-box shot share, back-three minutes share | style | Understat team statistics |
| Physical intensity | fouls committed and suffered, cards (yellow + 2 × red), corners for and against (per match) | style | Football-Data |
| Chance quality | npxG and npxGA per match | outcome | Understat league data |
| Workload | matches in all competitions, European matches, mean rest days, share of matches on < 4 days' rest, rest-day SD (gaps > 21 days left out) | exposure | TM fixtures |
| Rotation | share of the club's minutes played by its top 14 players | exposure | TM minutes (Phase 2) |

Shooting (shots on target) is computed for the record but **not used**: it reflects team strength more than style,
and Football-Data's Serie A values are inflated in 2018-19 to 2020-21 (see `DECISIONS.md`).

**Steps**
1. Team-season keys
2. Understat league data: pressing, ball progression, chance quality
3. Understat team statistics: attack type and shape
4. Football-Data: physical intensity (and shots on target, not used)
5. TM fixtures: workload
6. TM minutes: rotation
7. One table, checked complete
8. How features differ by season and league
9. Correlations and redundant features
10. Standardise and save, with roles
11. Style dimensions: one equal-weight score per way of playing
12. Report

**Inputs:** `data/tables/` (`us_team_matches`, `us_team_stats`, `fd_matches`, `tm_fixtures`),
`data/01_entities/team_seasons.csv`, `data/02_injuries/player_club_seasons.parquet`.
**Outputs:** `data/03_features/`, `reports/03_features.md`.
''')

code('''
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd().parent))  # project root, for the analysis package
from analysis.config import DATA_DIR, REPORTS_DIR, phase_dir
from analysis.load import league_from_understat, read_table, season_key
from analysis.report import md_table

pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 220)

PHASE = "03_features"
OUT_DIR = phase_dir(PHASE)
REDUNDANT_R = 0.9  # |r| above this marks a pair of features as redundant
TOP_N = 14  # rotation: share of minutes played by the club's top 14 players
SHORT_REST = 4  # a match on fewer than 4 days' rest counts as short rest
BREAK_DAYS = 21  # gaps longer than this are breaks (winter, COVID, World Cup 2022), not rest

LOG = []  # one row per preprocessing operation, for docs/PREPROCESSING_LOG.md


def log(step: str, operation: str, rows_in: int, rows_out: int) -> None:
    LOG.append({"step": step, "operation": operation, "rows in": rows_in, "rows out": rows_out})
    print(f"[{step}] {operation}: {rows_in:,} → {rows_out:,}")
''')

# ---- step 1
md('''
## Step 1. Team-season keys

The 1,170 team-seasons from Phase 1, with each source's identity. Every feature table is joined to these keys.
''')
code('''
keys = pd.read_csv(DATA_DIR / "01_entities" / "team_seasons.csv", dtype={"tm_club_id": str, "us_team_id": str})
assert len(keys) == 1170 and not keys.duplicated(["league", "season", "tm_club_id"]).any()
keys.head(3)
''')

# ---- step 2
md('''
## Step 2. Understat league data: pressing, ball progression, chance quality

Season PPDA is **Σ passes allowed / Σ defensive actions** over the team's league matches, not the mean of match
PPDAs (a low-pass match would otherwise weigh as much as a busy one). Lower PPDA = more intense pressing. *Opponent
PPDA* is the same for the opponents: low means the team is pressed hard, typical of teams that keep the ball.
''')
code('''
um = read_table("us_team_matches")
num = ["ppda.att", "ppda.def", "ppda_allowed.att", "ppda_allowed.def", "deep", "deep_allowed", "npxG", "npxGA"]
um[num] = um[num].astype(float)
um["league"] = um.league.map(league_from_understat)
um["season"] = um.season.astype(int)
g = um.groupby(["league", "season", "team_id"])
understat = pd.DataFrame({
    "us_matches": g.size(),
    "ppda": g["ppda.att"].sum() / g["ppda.def"].sum(),
    "opp_ppda": g["ppda_allowed.att"].sum() / g["ppda_allowed.def"].sum(),
    "deep_pm": g.deep.mean(),
    "deep_against_pm": g.deep_allowed.mean(),
    "npxg_pm": g.npxG.mean(),
    "npxga_pm": g.npxGA.mean(),
}).reset_index().rename(columns={"team_id": "us_team_id"})
log("3.2", "Understat team-matches aggregated to team-seasons", len(um), len(understat))
''')
code('''
# Check: one row per Understat team-season, plausible ranges.
understat.describe().round(2).T
''')

# ---- step 3 (Understat team statistics)
md('''
## Step 3. Understat team statistics: attack type and shape

From `us_team_stats` (Understat team pages, league matches, collected 2026-10-21). Shares, so they don't depend on
how many shots a team takes:
- **fast-attack share**: shots from fast attacks / all shots (counter-attacking);
- **slow-attack share**: shots from slow, patient attacks / all shots (possession build-up);
- **conceded fast-attack share**: the same for shots conceded (a high line exposed to counters);
- **set-piece share**: shots from corners, set pieces and direct free kicks / all shots (penalties excluded);
- **outside-box shot share**: shots from outside the box / all shots;
- **back-three share**: minutes in formations starting with a back three / all minutes.
''')
code('''
ts = read_table("us_team_stats")
for c in ["shots", "against.shots", "time"]:
    ts[c] = pd.to_numeric(ts[c], errors="coerce")
ts["league"] = ts.league.map(league_from_understat)
ts["season"] = ts.season.astype(int)
TS_KEY = ["league", "season", "team_id"]


def share(block: str, categories: list[str], column: str = "shots") -> pd.Series:
    rows = ts[ts.block == block]
    total = rows.groupby(TS_KEY)[column].sum()
    part = rows[rows.category.isin(categories)].groupby(TS_KEY)[column].sum()
    return part.reindex(total.index, fill_value=0) / total


back_three = [c for c in ts[ts.block == "formation"].category.unique() if c.startswith("3")]
team_stats = pd.DataFrame({
    "fast_attack_share": share("attackSpeed", ["Fast"]),
    "slow_attack_share": share("attackSpeed", ["Slow"]),
    "conceded_fast_share": share("attackSpeed", ["Fast"], "against.shots"),
    "set_piece_share": share("situation", ["FromCorner", "SetPiece", "DirectFreekick"]),
    "outside_box_share": share("shotZone", ["shotOboxTotal"]),
    "back_three_share": share("formation", back_three, "time"),
}).reset_index().rename(columns={"team_id": "us_team_id"})
log("3.3", "Understat team statistics to style shares per team-season", len(ts), len(team_stats))
print("back-three formations:", ", ".join(sorted(back_three)))
''')
code('''
# Check: ranges, and the team-seasons at the top of each share (should read like football).
display(team_stats.describe().round(3).T)
named = team_stats.merge(keys[["league", "season", "us_team_id", "club", "season_key"]], on=["league", "season", "us_team_id"])
pd.DataFrame({c: named.nlargest(4, c).apply(lambda r: f"{r.club} {r.season_key}", axis=1).to_list()
              for c in team_stats.columns if c.endswith("share")})
''')

# ---- step 3
md('''
## Step 4. Football-Data: physical intensity (and shots on target, not used)

Each match gives one row for the home team and one for the away team. *Fouls suffered* is the opponent's fouls
committed. Cards weigh a red as two yellows. Rates are means over the matches that have the statistic (3 matches
have none, Phase 0).
''')
code('''
fd = read_table("fd_matches")
stats = ["HST", "AST", "HF", "AF", "HC", "AC", "HY", "AY", "HR", "AR"]
fd[stats] = fd[stats].apply(pd.to_numeric, errors="coerce")
fd["season"] = 2000 + fd.season_code.str[:2].astype(int)


def side(team: str, us: str, them: str) -> pd.DataFrame:
    return pd.DataFrame({
        "league": fd.league, "season": fd.season, "fd_name": fd[team],
        "sot_for": fd[f"{us}ST"], "sot_against": fd[f"{them}ST"],
        "fouls": fd[f"{us}F"], "fouled": fd[f"{them}F"],
        "corners_for": fd[f"{us}C"], "corners_against": fd[f"{them}C"],
        "cards": fd[f"{us}Y"] + 2 * fd[f"{us}R"],
    })


fd_long = pd.concat([side("HomeTeam", "H", "A"), side("AwayTeam", "A", "H")], ignore_index=True)
g = fd_long.groupby(["league", "season", "fd_name"])
football_data = g.agg(
    fd_matches=("sot_for", "size"),
    sot_for_pm=("sot_for", "mean"), sot_against_pm=("sot_against", "mean"),
    fouls_pm=("fouls", "mean"), fouled_pm=("fouled", "mean"), cards_pm=("cards", "mean"),
    corners_for_pm=("corners_for", "mean"), corners_against_pm=("corners_against", "mean"),
).reset_index()
log("3.3", "Football-Data matches to team-matches (home + away) to team-seasons", len(fd), len(football_data))
''')
code('''
# Check: plausible ranges; Serie A shots on target by season (the total-shots definition changed in 2018-19).
display(football_data.describe().round(2).T)
football_data[football_data.league == "Serie A"].groupby("season").sot_for_pm.mean().round(2).to_frame().T
''')

# ---- step 4
md('''
## Step 5. TM fixtures: workload

All official matches of each club-season (league, domestic cups, super cups, European and other international club
competitions, relegation playoffs), from TM fixtures. **Rest days** = days since the club's previous match in the
same season; the first match of a season has none. Gaps of more than 21 days are breaks (winter break, COVID
suspension, World Cup 2022 stop; 0.7% of gaps) and are left out of the rest features; international breaks stay in. *European matches* are UEFA and FIFA club competitions
(competition types 10 and 13, qualifiers included).
''')
code('''
fx = read_table("tm_fixtures")
fx = pd.DataFrame({
    "tm_club_id": fx.club_id, "game_id": fx.game_id, "season": fx["game.seasonId"].astype(int),
    "type": fx["game.competitionTypeId"].astype(int), "date": pd.to_datetime(fx["game.date.dateTimeUTC"].str[:10]),
}).drop_duplicates(["tm_club_id", "game_id"]).sort_values(["tm_club_id", "season", "date"])
fx["rest_days"] = fx.groupby(["tm_club_id", "season"]).date.diff().dt.days
breaks = fx.rest_days > BREAK_DAYS
print(f"{breaks.sum():,} gaps of more than {BREAK_DAYS} days left out of the rest features ({breaks.mean():.1%} of gaps)")
fx.loc[breaks, "rest_days"] = np.nan
g = fx.groupby(["tm_club_id", "season"])
workload = pd.DataFrame({
    "matches_all": g.size(),
    "matches_europe": g.type.apply(lambda t: t.isin([10, 13]).sum()),
    "rest_mean": g.rest_days.mean(),
    "short_rest_share": g.rest_days.apply(lambda r: (r.dropna() < SHORT_REST).mean()),
    "rest_sd": g.rest_days.std(),
}).reset_index()
log("3.4", "TM club fixtures to club-season workload", len(fx), len(workload))
''')
code('''
# Check: ranges, and no two matches of a club on one day.
assert (fx.rest_days.dropna() > 0).all()
workload.describe().round(2).T
''')

# ---- step 5
md('''
## Step 6. TM minutes: rotation

From Phase 2's membership table (minutes in all competitions for each player at each club-season): the share of the
club's minutes played by its **top 14 players**. High = a fixed core plays most minutes; low = heavy rotation.
The Herfindahl index (sum of squared minute shares) is computed as a check on the choice.
''')
code('''
members = pd.read_parquet(DATA_DIR / "02_injuries" / "player_club_seasons.parquet")


def concentration(minutes: pd.Series) -> pd.Series:
    m = minutes.sort_values(ascending=False)
    share = m / m.sum()
    return pd.Series({"top14_share": share.head(TOP_N).sum(), "minutes_hhi": (share ** 2).sum(), "players_used": int((m > 0).sum())})


rotation = members.groupby(["club_id", "season"]).minutes.apply(concentration).unstack().reset_index()
rotation = rotation.rename(columns={"club_id": "tm_club_id"})
log("3.5", "player-club-season minutes to club-season rotation", len(members), len(rotation))
print(f"top-14 share vs HHI: r = {rotation.top14_share.corr(rotation.minutes_hhi):.2f}")
rotation.describe().round(3).T
''')

# ---- step 6
md('''
## Step 7. One table

All feature groups joined to the 1,170 keys. Every team-season must have every feature, and each source's match
count must agree with the expected league schedule.
''')
code('''
features = (keys
            .merge(understat, on=["league", "season", "us_team_id"], how="left")
            .merge(team_stats, on=["league", "season", "us_team_id"], how="left")
            .merge(football_data, on=["league", "season", "fd_name"], how="left")
            .merge(workload, on=["tm_club_id", "season"], how="left")
            .merge(rotation, on=["tm_club_id", "season"], how="left"))
FEATURES = {
    "pressing": ["ppda", "opp_ppda"],
    "ball progression": ["deep_pm", "deep_against_pm"],
    "attack type and shape": ["fast_attack_share", "slow_attack_share", "conceded_fast_share", "set_piece_share",
                              "outside_box_share", "back_three_share"],
    "physical intensity": ["fouls_pm", "fouled_pm", "cards_pm", "corners_for_pm", "corners_against_pm"],
    "chance quality": ["npxg_pm", "npxga_pm"],
    "workload": ["matches_all", "matches_europe", "rest_mean", "short_rest_share", "rest_sd"],
    "rotation": ["top14_share"],
}
ROLE = {"chance quality": "outcome", "workload": "exposure", "rotation": "exposure"}  # every other group: style
ALL = [f for group in FEATURES.values() for f in group]
assert len(features) == 1170
missing = features[ALL].isna().sum()
assert not missing.any(), missing[missing > 0]
assert (features.us_matches == features.fd_matches).all()
log("3.6", "feature groups joined to team-seasons", len(keys), len(features))
print(len(ALL), "features, none missing;", "league matches agree between Understat and Football-Data")
''')

# ---- step 7
md('''
## Step 8. How features differ by season and league

Season means show how football changed over the period; league means show how leagues differ. Both are part of
what clustering should see, which is why the features are standardised over all team-seasons together (step 9).
''')
code('''
by_season = features.groupby("season_key")[ALL].mean()
by_league = features.groupby("league")[ALL].mean()
display(by_season.round(2))
display(by_league.round(2))
''')

# ---- step 8
md('''
## Step 9. Correlations and redundant features

Pairs with |r| > 0.9 carry nearly the same information and would count twice in the distance K-means uses. For
each such pair one feature is dropped; the choice is written next to `DROP` in step 9.
''')
code('''
corr = features[ALL].corr()
pairs = (corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1)).stack().rename("r").reset_index()
         .rename(columns={"level_0": "feature_a", "level_1": "feature_b"}))
pairs["abs_r"] = pairs.r.abs()
strong = pairs.sort_values("abs_r", ascending=False)
redundant = strong[strong.abs_r > REDUNDANT_R]
print(f"{len(redundant)} pairs with |r| > {REDUNDANT_R}")
display(redundant.round(3))
strong.head(12).round(3)
''')

# ---- step 9
md('''
## Step 10. Standardise and save

Z-scores over **all** team-seasons together (open decision 4), so that changes over time and differences between
leagues stay visible to the clustering. Raw values and z-scores are both saved.
''')
code('''
# For each redundant pair, the feature to drop (see DECISIONS.md).
# rest_mean vs short_rest_share (r = -0.90): matches on < 4 days' rest are the congestion measure linked to injury
# risk (Dupont et al. 2010), and rest_mean is also close to matches_all (r = -0.89).
DROP = ["rest_mean"]
unresolved = redundant[~(redundant.feature_a.isin(DROP) | redundant.feature_b.isin(DROP))]
assert unresolved.empty, f"redundant pairs without a decision: {unresolved[['feature_a', 'feature_b']].values.tolist()}"
KEEP = [f for f in ALL if f not in DROP]
z = (features[KEEP] - features[KEEP].mean()) / features[KEEP].std(ddof=0)
out = features[["league", "season", "season_key", "tm_club_id", "club"] + ALL].join(z.add_prefix("z_"))
out.to_parquet(OUT_DIR / "team_season_features.parquet", index=False)
roles = pd.DataFrame([(f, g, ROLE.get(g, "style"), "dropped (redundant)" if f in DROP else "kept")
                      for g, fs in FEATURES.items() for f in fs], columns=["feature", "group", "role", "status"])
roles.to_csv(OUT_DIR / "feature_roles.csv", index=False)
STYLE = roles[(roles.role == "style") & (roles.status == "kept")].feature.tolist()
log("3.9", f"standardised {len(KEEP)} features over all team-seasons (dropped: {', '.join(DROP) or 'none'})", len(features), len(out))
assert np.allclose(z.mean(), 0) and np.allclose(z.std(ddof=0), 1)
roles.groupby(["role", "status"]).feature.apply(", ".join).to_frame()
''')

# ---- step 11 (style dimensions)
md('''
## Step 11. Style dimensions

Several style features measure the same thing: opponent PPDA, deep completions for and against, corners for and
against and the slow-attack share all describe **dominance** of the ball. In the distance K-means uses, that one
dimension would count six times, and the clusters would mostly sort teams by strength. So each **way of playing**
becomes one score, the mean of the signed z-scores of its features, re-standardised; every style feature is used
exactly once (see `DECISIONS.md`).

| Dimension | Features (sign) |
|---|---|
| dominance | opponent PPDA (+), deep completions (+), deep completions against (−), corners for (+), corners against (−), slow-attack share (+) |
| pressing | PPDA (−): fewer passes allowed per defensive action = more pressing |
| counter | fast-attack share (+) |
| high line | conceded fast-attack share (+) |
| physical | fouls committed (+), fouls suffered (+), cards (+) |
| set pieces | set-piece share (+) |
| long shots | outside-box shot share (+) |
| back three | back-three minutes share (+) |
''')
code('''
DIMENSIONS = {
    "dominance": {"opp_ppda": 1, "deep_pm": 1, "deep_against_pm": -1, "corners_for_pm": 1, "corners_against_pm": -1,
                  "slow_attack_share": 1},
    "pressing": {"ppda": -1},
    "counter": {"fast_attack_share": 1},
    "high_line": {"conceded_fast_share": 1},
    "physical": {"fouls_pm": 1, "fouled_pm": 1, "cards_pm": 1},
    "set_pieces": {"set_piece_share": 1},
    "long_shots": {"outside_box_share": 1},
    "back_three": {"back_three_share": 1},
}
used = [f for parts in DIMENSIONS.values() for f in parts]
assert sorted(used) == sorted(STYLE) and len(used) == len(set(used)), "every style feature exactly once"
dims = pd.DataFrame({name: sum(sign * z[f] for f, sign in parts.items()) / len(parts) for name, parts in DIMENSIONS.items()})
dims = (dims - dims.mean()) / dims.std(ddof=0)
style_dims = features[["league", "season", "season_key", "tm_club_id", "club"]].join(dims)
style_dims.to_parquet(OUT_DIR / "style_dimensions.parquet", index=False)
log("3.11", f"{len(STYLE)} style features combined into {len(DIMENSIONS)} equal-weight style dimensions", len(features), len(style_dims))
dim_corr = dims.corr().round(2)
dim_corr
''')

# ---- step 10
md('''
## Step 12. Report
''')
code('''
log_table = pd.DataFrame(LOG)
log_table.to_csv(OUT_DIR / "preprocessing_counts.csv", index=False)
groups = roles[["group", "feature", "role", "status"]]
ranges = features[ALL].describe().T[["mean", "std", "min", "max"]].round(2)
text = [
    "# Phase 3: Team-season features",
    "",
    f"Generated {date.today().isoformat()} by `notebooks/03_features.ipynb`, where each step is shown with its checks.",
    "",
    "## Key findings",
    "",
    f"- **{len(out):,} team-seasons, {len(ALL)} features, none missing.** League match counts agree between Understat and Football-Data.",
    f"- **Redundant pairs (|r| > {REDUNDANT_R}):** {len(redundant)}" + (f"; dropped {', '.join(DROP)}." if DROP else "."),
    f"- **{len(STYLE)} style features** form **{len(DIMENSIONS)} equal-weight style dimensions**, which are clustered; "
    f"{len(KEEP)} features in all are standardised over all team-seasons (outcome and exposure features are kept for "
    "Phases 4–5, not clustered).",
    "",
    "## 1. Features",
    "",
    md_table(groups, index=False),
    "",
    "## 2. Ranges (raw units)",
    "",
    md_table(ranges.rename_axis("feature")),
    "",
    "## 3. Style dimensions (clustered in Phase 4)",
    "",
    md_table(pd.DataFrame({"features (sign)": {d: ", ".join(f"{f} ({'+' if v > 0 else '−'})" for f, v in parts.items())
                                                for d, parts in DIMENSIONS.items()}}).rename_axis("dimension")),
    "",
    "Correlations between the dimensions:",
    "",
    md_table(dim_corr.rename_axis("dimension")),
    "",
    "## 3b. Strongest correlations between features",
    "",
    md_table(strong.head(12)[["feature_a", "feature_b", "r"]].round(3), index=False),
    "",
    "## 4. Season means",
    "",
    md_table(by_season.round(2).T.rename_axis("feature")),
    "",
    "## 5. League means",
    "",
    md_table(by_league.round(2).T.rename_axis("feature")),
    "",
    "## 6. Steps and row counts",
    "",
    md_table(log_table, index=False),
    "",
    "## 7. Outputs",
    "",
    f"- `data/{PHASE}/team_season_features.parquet`: raw features and z-scores (`z_*`, the {len(KEEP)} kept features).",
    f"- `data/{PHASE}/feature_roles.csv`: group, role (style / outcome / exposure) and status of every feature.",
    f"- `data/{PHASE}/style_dimensions.parquet`: the {len(DIMENSIONS)} style dimension scores per team-season (Phase 4 input).",
    "",
]
(REPORTS_DIR / "03_features.md").write_text("\\n".join(text), encoding="utf-8")
print("wrote", REPORTS_DIR / "03_features.md")
''')

for i, cell in enumerate(cells):
    cell["id"] = f"features-{i:02d}"
meta = json.loads((ROOT / "notebooks/01_entities.ipynb").read_text())["metadata"]
nb = {"cells": cells, "metadata": meta, "nbformat": 4, "nbformat_minor": 5}
(ROOT / "notebooks/03_features.ipynb").write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
print(len(cells), "cells")
