"""Phase 05: Injury analysis. Cells in the percent format; run with `python -m analysis.run 05`, notebook built by `scripts/notebooks/build_notebook.py`."""

# %% [markdown]
# # Phase 5: Injury analysis (pattern evaluation)
#
# **Question:** how did playing styles evolve between 2014/15 and 2025/26, and how did injuries (frequency, days lost,
# body area) change with them, across seasons and leagues?
#
# **Unit:** the **player-club-season** (Phase 2 membership), carrying its team's **attacking style**, **defensive
# style**, their combination (Phase 4) and its **formation** (back three: ≥ 50% of minutes). Injuries last > 7 days.
#
# **Methods** (descriptive, as the course allows):
# - **Rates:** injuries per player-season, per 1,000 minutes, days lost per player-season, share severe (> 28 days).
# - **Rate ratio (RR):** observed injuries ÷ expected (indirect standardisation), because Transfermarkt records injuries
#   at very different rates per league and season. Expected values are **nested**: league × season (main), then
#   + team strength (thirds of points per match), then + age band × position. Two **exposures** side by side: per
#   player-season, and per team match (expected = the league-season's injuries per player-season-match × the team's
#   matches in all competitions), since stronger teams play more matches.
# - **95% CIs:** bootstrap over **clubs** (a club's seasons and players are not independent), 1,000 resamples, each
#   seeded from the table it belongs to (seed 42), so adding a table does not shift the others.
# - **Tests:** chi-square (observed vs expected; body-area mix with Cramér's V). Body-area patterns: a **permutation
#   test** (style labels shuffled among team-seasons within each league-season, 10,000 times) with Benjamini–Hochberg
#   over 72 tests; the Mantel–Haenszel odds ratio (strata league × era) as effect size.
# - **Days lost** count each day once (overlapping absences merged in Phase 2).
# - **Evolution:** eras 2014–18, 2018–22, 2022–26; trend shapes; style transitions; Kitagawa decomposition of injury
#   trends into the style mix and within-style change.
#
# **Steps**
# 1. Player-season table
# 2. Rate and bootstrap helpers; league baselines
# 3. Injuries by attacking style, defensive style, combination and formation
# 4. Body areas by style (within leagues)
# 5. Seasons: injury trend and style shares over time
# 6. Leagues: style effects within each league
# 7. Adjusting step by step: season, team strength, age and position, matches played
# 8. Team strength and workload; same club with and without the style
# 9. Fitness absences (secondary outcome)
# 10. Sensitivity checks
# 11. Style cards: what each style looks like on the pitch
# 12. How the ways of attacking and defending changed, and in what shape
# 13. How teams move between styles
# 14. Style mix and injuries per era
# 15. How much of the injury trend comes from styles changing (decomposition)
# 16. Style dimensions vs injury outcomes across league-seasons
# 17. One story per league
# 18. Making results clearer without overfitting: shrinkage, rolling trends, FDR, breakdowns
# 19. Report
#
# **Inputs:** `data/02_injuries/`, `data/03_features/`, `data/04_clusters/`, `tm_squads`, `us_team_matches`.
# **Outputs:** `data/05_injury_analysis/`, `reports/05_injury_analysis.md`, `reports/figures/05_*.png`.

# %%
import sys
import zlib
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import Image, Markdown, display
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import chi2, chi2_contingency

sys.path.insert(0, str(Path.cwd().parent))  # project root, for the analysis package
from analysis.config import DATA_DIR, FIGURES_DIR, REPORTS_DIR, phase_dir
from analysis.load import league_from_understat, read_table
from analysis.report import md_table

pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 220)
pd.set_option("display.max_colwidth", 160)

PHASE = "05_injury_analysis"
OUT_DIR = phase_dir(PHASE)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
SEED = 42
N_BOOT = 1000
AGE_BANDS = [0, 21, 25, 29, 99]  # ≤ 21, 22–25, 26–29, 30+ (age on 1 January of the season)
AGE_LABELS = ["≤21", "22–25", "26–29", "30+"]
COVID_SEASONS = ["2019-20", "2020-21"]
LEAGUES = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
ATTACK = ["Positional possession", "Build-up into the box", "Counter-attack", "Direct play"]
DEFENCE = ["High press, high line", "Compact mid-block", "Aggressive duel press", "Low block"]
FORMATION = ["back three", "back four"]
ERAS = {range(2014, 2018): "2014–18", range(2018, 2022): "2018–22", range(2022, 2026): "2022–26"}
ERA_ORDER = list(ERAS.values())
RARE = "rare combination"

# Chart palette: validated reference palette (dataviz skill), categorical slots in fixed order.
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
DIVERGING = LinearSegmentedColormap.from_list("blue_gray_red", ["#2a78d6", "#f0efec", "#e34948"])
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
    "axes.titlesize": 11, "axes.titleweight": "bold", "lines.linewidth": 2,
})


def save(fig, name: str) -> str:
    path = FIGURES_DIR / name
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    display(Image(filename=str(path)))
    return name


def era_of(season: int) -> str:
    return next(label for years, label in ERAS.items() if season in years)

# %% [markdown]
# ## Step 1. Player-season table
#
# One row per player-club-season with league, season, club, the team's attacking and defensive style and their
# combination, formation, strength (points per match), workload (Phase 3 exposure features), the player's age band and
# position, minutes in all competitions, and his injuries there that season (count, days lost, severe, surgery, by body
# area), plus mild injuries (4–7 days) and fitness absences.

# %%
members = pd.read_parquet(DATA_DIR / "02_injuries" / "player_club_seasons.parquet")
injuries = pd.read_parquet(DATA_DIR / "02_injuries" / "injuries_clean.parquet")
mild = pd.read_parquet(DATA_DIR / "02_injuries" / "injuries_mild.parquet")
non_inj = pd.read_parquet(DATA_DIR / "02_injuries" / "non_injuries.parquet")
clusters = pd.read_parquet(DATA_DIR / "04_clusters" / "team_season_clusters.parquet").rename(columns={"tm_club_id": "club_id"})
features = pd.read_parquet(DATA_DIR / "03_features" / "team_season_features.parquet").rename(columns={"tm_club_id": "club_id"})
style_dims = pd.read_parquet(DATA_DIR / "03_features" / "style_dimensions.parquet").rename(columns={"tm_club_id": "club_id"})
roles = pd.read_csv(DATA_DIR / "03_features" / "feature_roles.csv")
EXPOSURE = roles[(roles.role == "exposure") & (roles.status == "kept")].feature.tolist()
DIMS = {ph: [c for c in style_dims.columns if c.startswith(f"{ph}_")] for ph in ["attack", "defence"]}

clusters["formation"] = np.where(clusters.back_three, "back three", "back four")
clusters["style_group"] = np.where(clusters.rare_style, RARE, clusters["style"])
clusters["era"] = clusters.season.map(era_of)
COMBOS = (clusters[~clusters.rare_style].drop_duplicates("style")
          .assign(a=lambda d: d.attack_style.map(ATTACK.index), d=lambda d: d.defence_style.map(DEFENCE.index))
          .sort_values(["a", "d"])["style"].tolist())

um = read_table("us_team_matches")
points = (um.assign(league=um.league.map(league_from_understat), season=um.season.astype(int), pts=um.pts.astype(float))
          .groupby(["league", "season", "team_id"]).pts.mean().rename("points_pm").reset_index().rename(columns={"team_id": "us_team_id"}))
keys = pd.read_csv(DATA_DIR / "01_entities" / "team_seasons.csv", dtype={"tm_club_id": str, "us_team_id": str}).rename(columns={"tm_club_id": "club_id"})
team = (clusters.merge(keys[["league", "season", "club_id", "us_team_id"]], on=["league", "season", "club_id"])
        .merge(points, on=["league", "season", "us_team_id"])
        .merge(features[["league", "season", "club_id"] + EXPOSURE], on=["league", "season", "club_id"])
        .merge(style_dims[["season", "club_id"] + DIMS["attack"] + DIMS["defence"]], on=["season", "club_id"]))
team["strength"] = pd.qcut(team.points_pm, 3, labels=["weaker third", "middle third", "stronger third"])
assert len(team) == 1170

sq = read_table("tm_squads")
player = sq[["playerId", "position_group", "date_of_birth"]].replace("", np.nan).groupby("playerId").first()
TEAM_COLS = ["league", "season", "club_id", "attack_style", "defence_style", "style", "style_group", "rare_style", "formation",
             "back_three_share", "era", "points_pm", "strength", "attack_k3_style", "defence_k3_style",
             "attack_rel_style", "defence_rel_style"] + EXPOSURE
ps = members.merge(team[TEAM_COLS], on=["league", "season", "club_id"], how="left").join(player, on="playerId")
dob = pd.to_datetime(ps.date_of_birth, errors="coerce")
ps["age"] = ((pd.to_datetime((ps.season + 1).astype(str) + "-01-01") - dob).dt.days / 365.25).round(1)
ps["age_band"] = pd.cut(ps.age, AGE_BANDS, labels=AGE_LABELS)
ps["position"] = ps.position_group.str.title()

KEY = ["playerId", "club_id", "season"]
DAYS_CAP = 365  # sensitivity: no single injury counts for more than a season
inj = injuries.assign(severe=injuries.severity.str.startswith("severe"), surgery=injuries.surgery.astype(bool),
                      days_capped=injuries.days_merged.clip(upper=DAYS_CAP))
agg = inj.groupby(KEY).agg(injuries=("days", "size"), days_lost=("days_merged", "sum"), days_raw=("days", "sum"),
                           days_capped=("days_capped", "sum"), severe=("severe", "sum"), surgeries=("surgery", "sum"))
areas = pd.crosstab([inj.playerId, inj.club_id, inj.season], inj.body_area).add_prefix("area: ")
mild_n = mild.groupby(KEY).size().rename("mild_injuries")
fit_n = non_inj[non_inj.non_injury_reason == "fitness"].groupby(KEY).size().rename("fitness_absences")
ps = ps.join(agg, on=KEY).join(areas, on=KEY).join(mild_n, on=KEY).join(fit_n, on=KEY)
count_cols = ["injuries", "days_lost", "days_raw", "days_capped", "severe", "surgeries", "mild_injuries", "fitness_absences"] + list(areas.columns)
ps[count_cols] = ps[count_cols].fillna(0).astype(int)
ps["team_season"] = ps.league + " " + ps.season_key + " " + ps.club_id

assert ps.attack_style.notna().all() and ps.defence_style.notna().all()
assert ps.injuries.sum() == len(injuries), (ps.injuries.sum(), len(injuries))
assert ps.days_lost.sum() == injuries.days_merged.sum() and ps.matches_all.notna().all()
pd.Series({
    "player-club-seasons": len(ps), "players": ps.playerId.nunique(), "team-seasons": ps.team_season.nunique(),
    "injuries > 7 days": int(ps.injuries.sum()), "days lost (overlaps merged)": int(ps.days_lost.sum()),
    "days lost (raw, overlaps double)": int(ps.days_raw.sum()), "only marked injured (0 appearances)": int((ps.appearances == 0).sum()),
    "mild injuries (4–7 days)": int(ps.mild_injuries.sum()), "fitness absences": int(ps.fitness_absences.sum()),
    "in rare combinations": int(ps.rare_style.sum()), "missing age": int(ps.age.isna().sum()),
}, name="count").to_frame()

# %% [markdown]
# ## Step 2. Rate and bootstrap helpers; league baselines
#
# `summarise(df, by, adjust)` gives per group: player-seasons, injuries, the rates and the rate ratios (frequency and
# days lost) against one of the expected values, with bootstrap 95% CIs over clubs. Expected values:
#
# | suffix | expected from | exposure |
# |---|---|---|
# | (none, main) | league × season | player-season |
# | `_str` | league × season × strength third | player-season |
# | `_full` | league × season × strength × age band × position | player-season |
# | `_match` | league × season | team matches (all competitions) |
# | `_match_str` | league × season × strength | team matches |
#
# `GROUPINGS` lists the four ways of grouping teams.

# %%
def add_expected(df: pd.DataFrame, strata: list[str], suffix: str = "") -> pd.DataFrame:
    """Expected injuries and days lost per player-season from the mean of its stratum."""
    means = df.groupby(strata, observed=True)[["injuries", "days_lost"]].transform("mean")
    return df.assign(**{f"exp_inj{suffix}": means.injuries, f"exp_days{suffix}": means.days_lost})


def add_expected_per_match(df: pd.DataFrame, strata: list[str], suffix: str) -> pd.DataFrame:
    """Expected injuries and days lost from the stratum's rate per player-season-match times the team's matches."""
    g = df.groupby(strata, observed=True)
    per_match = df.matches_all / g.matches_all.transform("sum")
    return df.assign(**{f"exp_inj{suffix}": g.injuries.transform("sum") * per_match,
                        f"exp_days{suffix}": g.days_lost.transform("sum") * per_match})


ps = add_expected(ps, ["league", "season"])
ps = add_expected(ps, ["league", "season", "strength"], "_str")
full = add_expected(ps.dropna(subset=["age_band", "position"]).copy(), ["league", "season", "strength", "age_band", "position"], "_full")
ps = ps.join(full[["exp_inj_full", "exp_days_full"]])
ps = add_expected_per_match(ps, ["league", "season"], "_match")
ps = add_expected_per_match(ps, ["league", "season", "strength"], "_match_str")
for suffix in ["", "_str", "_match", "_match_str"]:
    assert np.isclose(ps[f"exp_inj{suffix}"].sum(), ps.injuries.sum()), suffix


def boot_ratio(units: pd.DataFrame, num: str, den: str, seed_key: str) -> tuple[float, float]:
    """95% CI of sum(num) / sum(den), resampling clubs; the generator is seeded from the table and group."""
    rng = np.random.default_rng([SEED, zlib.crc32(seed_key.encode())])
    n, v_num, v_den = len(units), units[num].to_numpy(), units[den].to_numpy()
    idx = rng.integers(0, n, (N_BOOT, n))
    return tuple(np.percentile(v_num[idx].sum(axis=1) / v_den[idx].sum(axis=1), [2.5, 97.5]))


def summarise(df: pd.DataFrame, by: str | list[str], adjust: str = "") -> pd.DataFrame:
    by = [by] if isinstance(by, str) else by
    cols = ["injuries", "days_lost", "severe", "minutes", f"exp_inj{adjust}", f"exp_days{adjust}"]
    clubs = df.assign(ps=1).groupby(by + ["club_id"], observed=True)[cols + ["ps"]].sum().reset_index()
    n_teams = df.groupby(by, observed=True).team_season.nunique()
    rows = []
    for key, t in clubs.groupby(by, observed=True):
        key = key if isinstance(key, tuple) else (key,)
        seed_key = f"{by}|{key}|{adjust}"
        rr_lo, rr_hi = boot_ratio(t, "injuries", f"exp_inj{adjust}", seed_key + "|inj")
        dr_lo, dr_hi = boot_ratio(t, "days_lost", f"exp_days{adjust}", seed_key + "|days")
        tot = t[cols + ["ps"]].sum()
        rows.append(dict(zip(by, key)) | {
            "player-seasons": int(tot.ps), "team-seasons": int(n_teams.loc[key[0] if len(key) == 1 else key]),
            "clubs": len(t), "injuries": int(tot.injuries),
            "injuries / player-season": tot.injuries / tot.ps, "per 1,000 min": 1000 * tot.injuries / tot.minutes,
            "days lost / player-season": tot.days_lost / tot.ps,
            "severe share": tot.severe / tot.injuries if tot.injuries else np.nan,
            "excess / 100 player-seasons": 100 * (tot.injuries - tot[f"exp_inj{adjust}"]) / tot.ps,
            "excess days / player-season": (tot.days_lost - tot[f"exp_days{adjust}"]) / tot.ps,
            "RR": tot.injuries / tot[f"exp_inj{adjust}"], "RR low": rr_lo, "RR high": rr_hi,
            "days RR": tot.days_lost / tot[f"exp_days{adjust}"], "days RR low": dr_lo, "days RR high": dr_hi,
        })
    return pd.DataFrame(rows).set_index(by)


def fmt(table: pd.DataFrame) -> pd.DataFrame:
    t = table.copy()
    t["RR (95% CI)"] = t.apply(lambda r: f"{r['RR']:.2f} ({r['RR low']:.2f}–{r['RR high']:.2f})", axis=1)
    t["days RR (95% CI)"] = t.apply(lambda r: f"{r['days RR']:.2f} ({r['days RR low']:.2f}–{r['days RR high']:.2f})", axis=1)
    t = t.drop(columns=["RR", "RR low", "RR high", "days RR", "days RR low", "days RR high"])
    return t.round({"injuries / player-season": 3, "per 1,000 min": 3, "days lost / player-season": 1, "severe share": 3,
                    "excess / 100 player-seasons": 1, "excess days / player-season": 1})


def gof_test(df: pd.DataFrame, by: str) -> tuple[float, int, float]:
    """Chi-square of observed vs expected injuries across groups (Poisson assumption; overdispersed data, so the
    bootstrap CIs are the main evidence)."""
    g = df.groupby(by, observed=True)[["injuries", "exp_inj"]].sum()
    stat = (((g.injuries - g.exp_inj) ** 2) / g.exp_inj).sum()
    return stat, len(g) - 1, chi2.sf(stat, len(g) - 1)


GROUPINGS = {"attacking style": ("attack_style", ATTACK), "defensive style": ("defence_style", DEFENCE),
             "combined style": ("style", COMBOS), "formation": ("formation", FORMATION)}
COLS = ["player-seasons", "team-seasons", "injuries", "injuries / player-season", "per 1,000 min",
        "days lost / player-season", "severe share", "excess / 100 player-seasons", "excess days / player-season",
        "RR (95% CI)", "days RR (95% CI)"]
baseline = ps.groupby("league")[["injuries", "days_lost", "matches_all"]].mean().round(3)
baseline

# %% [markdown]
# ## Step 3. Injuries by attacking style, defensive style, combination and formation
#
# Rate ratios against league × season (main) with 95% CIs for each grouping; Step 7 adds the stricter adjustments. The attack × defence grid then shows whether a difference belongs
# to the attacking or the defensive phase: reading **along a row** changes only the defensive style, **down a column**
# only the attacking style.

# %%
results = {name: summarise(ps[~ps.rare_style] if col == "style" else ps, col).loc[order] for name, (col, order) in GROUPINGS.items()}
tests = {name: gof_test(ps[~ps.rare_style] if col == "style" else ps, col) for name, (col, order) in GROUPINGS.items()}
for name, t in results.items():
    print(f"\n{name}: observed vs expected chi² = {tests[name][0]:.1f}, df = {tests[name][1]}, p = {tests[name][2]:.2g}")
    display(fmt(t)[COLS])
grid = summarise(ps, ["attack_style", "defence_style"])
grid_rr = grid["RR"].unstack().loc[ATTACK, DEFENCE]
grid_n = grid["team-seasons"].unstack().loc[ATTACK, DEFENCE]
grid_days = grid["days RR"].unstack().loc[ATTACK, DEFENCE]
display(grid_rr.round(2))
grid_days.round(2)

# %%
def ci_plot(ax, table: pd.DataFrame, rr: str, lo: str, hi: str, title: str, colors=SERIES) -> None:
    y = np.arange(len(table))[::-1]
    for yi, (name, r), color in zip(y, table.iterrows(), colors):
        ax.plot([r[lo], r[hi]], [yi, yi], color=color, linewidth=2.5, solid_capstyle="round")
        ax.scatter(r[rr], yi, s=60, color=color, edgecolors=SURFACE, linewidths=1.5, zorder=3)
        ax.text(r[hi] + 0.01, yi, f"{r[rr]:.2f}", va="center", fontsize=9, color=INK)
    ax.axvline(1, color=MUTED, linewidth=1, linestyle="--")
    ax.set_yticks(y, table.index)
    ax.set_title(title, loc="left")
    ax.grid(axis="y", visible=False)


fig, axes = plt.subplots(3, 2, figsize=(13, 9.5), gridspec_kw={"height_ratios": [4, 4, 2]})
for row, name in enumerate(["attacking style", "defensive style", "formation"]):
    t = results[name]
    ci_plot(axes[row, 0], t, "RR", "RR low", "RR high", f"{name.capitalize()}: injuries (RR, 95% CI)")
    ci_plot(axes[row, 1], t, "days RR", "days RR low", "days RR high", f"{name.capitalize()}: days lost (RR, 95% CI)")
for ax in axes[-1]:
    ax.set_xlabel("rate ratio (1 = league average)")
fig.tight_layout()
style_fig = save(fig, "05_rates_by_style.png")

fig, axes = plt.subplots(1, 2, figsize=(15, 3.8))
for ax, data, title in [(axes[0], grid_rr, "Injuries RR"), (axes[1], grid_days, "Days lost RR")]:
    vals = data.to_numpy(dtype=float)
    ax.imshow(np.log2(vals), cmap=DIVERGING, vmin=-0.5, vmax=0.5, aspect="auto")
    ax.set_xticks(range(len(DEFENCE)), DEFENCE, rotation=15, ha="right")
    ax.set_yticks(range(len(ATTACK)), ATTACK)
    ax.grid(False)
    for (i, j), v in np.ndenumerate(vals):
        n = grid_n.to_numpy()[i, j]
        ax.text(j, i, f"{v:.2f}\n(n={int(n)})", ha="center", va="center", fontsize=8,
                color=MUTED if n < 40 else (INK if abs(np.log2(v)) < 0.35 else "white"))
    ax.set_title(f"{title}: attacking style (rows) × defensive style (columns)", loc="left")
fig.tight_layout()
grid_fig = save(fig, "05_attack_defence_grid.png")

# %% [markdown]
# ## Step 4. Body areas by style (within leagues)
#
# Leagues label injuries very differently (*unspecified muscle* is 29% of La Liga injuries, 7% of Premier League
# ones), so for each style and body area the share is taken **within each league**, relative to that league's share
# (1 = same), summarised by the median over leagues and the number of leagues above 1. A pattern in 4–5 leagues is a
# style pattern; one that flips is labelling. The pooled chi-square and Cramér's V give the overall size.

# %%
AREA_COLS = [c for c in ps.columns if c.startswith("area: ")]
AREAS = (ps[AREA_COLS].sum().sort_values(ascending=False).rename(index=lambda c: c[6:]).drop("unknown").index[:8].tolist())


def within_league_areas(col: str, order: list[str], data: pd.DataFrame = ps) -> tuple[pd.DataFrame, pd.DataFrame]:
    medians, above = {}, {}
    for a in AREAS:
        g = data.groupby(["league", col])[[f"area: {a}", "injuries"]].sum()
        lg = data.groupby("league")[[f"area: {a}", "injuries"]].sum()
        rel = (g[f"area: {a}"] / g.injuries).unstack().div(lg[f"area: {a}"] / lg.injuries, axis=0).reindex(columns=order)
        medians[a], above[a] = rel.median(), (rel > 1).sum()
    return pd.DataFrame(medians).loc[order], pd.DataFrame(above).loc[order]


def pooled_test(col: str, order: list[str], data: pd.DataFrame = ps) -> tuple[float, float]:
    known = data.groupby(col)[[f"area: {a}" for a in AREAS]].sum().loc[order]
    stat, p, dof, _ = chi2_contingency(known)
    return p, np.sqrt(stat / (known.to_numpy().sum() * (min(known.shape) - 1)))


body = {}
for name, (col, order) in GROUPINGS.items():
    data = ps[~ps.rare_style] if col == "style" else ps
    med, above = within_league_areas(col, order, data)
    p, v = pooled_test(col, order, data)
    body[name] = {"median": med, "above": above, "p": p, "V": v}
    print(f"\n{name}: pooled chi² p = {p:.2g}, Cramér's V = {v:.3f}")
    display(med.round(2))
    display(above)

# %%
fig, axes = plt.subplots(1, 3, figsize=(20, 4), gridspec_kw={"width_ratios": [1, 1, 0.55]})
for ax, name in zip(axes, ["attacking style", "defensive style", "formation"]):
    med, above = body[name]["median"], body[name]["above"]
    vals = med.to_numpy(dtype=float)
    ax.imshow(np.log2(vals), cmap=DIVERGING, vmin=-0.4, vmax=0.4, aspect="auto")
    ax.set_xticks(range(len(AREAS)), AREAS, rotation=40, ha="right")
    ax.set_yticks(range(len(med)), med.index)
    ax.grid(False)
    for (i, j), v in np.ndenumerate(vals):
        k = above.to_numpy()[i, j]
        strong = k >= 4 or k <= 1
        ax.text(j, i, f"{v:.2f}\n{k}/5", ha="center", va="center", fontsize=7.5, color=INK, fontweight="bold" if strong else "normal")
    ax.set_title(f"{name.capitalize()} (V = {body[name]['V']:.2f})", loc="left")
fig.suptitle("Body-area share relative to the league's share (median over leagues; x/5 = leagues above 1)", x=0.01, ha="left", fontsize=11)
fig.tight_layout()
area_fig = save(fig, "05_body_areas_by_style.png")

# %% [markdown]
# **Body areas across leagues and eras.** The research question also asks whether the body areas affected differ
# between leagues and change over time. For each league and era: injuries per 100 player-seasons in each area
# (frequency), each area's share of the injuries with a known area, and the share with no known area. Shares are
# compared within a league across eras; between leagues they mostly reflect how each league's injuries are labelled.

# %%
area_cols = [f"area: {a}" for a in AREAS]
g = ps.groupby(["league", "era"])
body_league = pd.concat({
    "per 100 player-seasons": (100 * g[area_cols].sum().div(g.size(), axis=0)).rename(columns=lambda c: c[6:]),
    "share of known": g[area_cols].sum().div(g.injuries.sum() - g["area: unknown"].sum(), axis=0).rename(columns=lambda c: c[6:]),
}, axis=1).reindex(pd.MultiIndex.from_product([LEAGUES, ERA_ORDER], names=["league", "era"]))
body_league[("unknown", "share of all")] = (g["area: unknown"].sum() / g.injuries.sum()).reindex(body_league.index)
rate_change = (body_league["per 100 player-seasons"].xs(ERA_ORDER[-1], level="era")
               - body_league["per 100 player-seasons"].xs(ERA_ORDER[0], level="era")).loc[LEAGUES]
all_leagues = ps.groupby("era")[area_cols].sum().div(ps.groupby("era").size(), axis=0).mul(100).rename(columns=lambda c: c[6:]).loc[ERA_ORDER]
assert body_league.notna().all().all()
display(body_league["per 100 player-seasons"].round(1))
display(all_leagues.round(1))
rate_change.round(1)

# %%
fig, axes = plt.subplots(1, 2, figsize=(18, 6.5), gridspec_kw={"width_ratios": [1.15, 1]})
shares = body_league["share of known"]
ax = axes[0]
ax.imshow(shares.to_numpy(dtype=float), cmap="Blues", vmin=0, vmax=0.45, aspect="auto")
ax.set_xticks(range(len(AREAS)), AREAS, rotation=40, ha="right")
ax.set_yticks(range(len(shares)), [f"{lg} {era}" for lg, era in shares.index])
ax.grid(False)
for (i, j), v in np.ndenumerate(shares.to_numpy(dtype=float)):
    ax.text(j, i, f"{v:.0%}", ha="center", va="center", fontsize=7, color="white" if v > 0.28 else INK)
for k in range(1, len(LEAGUES)):
    ax.axhline(k * len(ERA_ORDER) - 0.5, color=SURFACE, linewidth=3)
ax.set_title("Share of injuries with a known area, by league and era", loc="left")
ax = axes[1]
lim = np.abs(rate_change.to_numpy()).max()
ax.imshow(rate_change.to_numpy(dtype=float), cmap=DIVERGING, vmin=-lim, vmax=lim, aspect="auto")
ax.set_xticks(range(len(AREAS)), AREAS, rotation=40, ha="right")
ax.set_yticks(range(len(LEAGUES)), LEAGUES)
ax.grid(False)
for (i, j), v in np.ndenumerate(rate_change.to_numpy(dtype=float)):
    ax.text(j, i, f"{v:+.1f}", ha="center", va="center", fontsize=8, color=INK)
ax.set_title(f"Change in injuries per 100 player-seasons, {ERA_ORDER[0]} → {ERA_ORDER[-1]}", loc="left")
fig.tight_layout()
body_league_fig = save(fig, "05_body_areas_by_league_era.png")

# %% [markdown]
# ## Step 5. Seasons
#
# Injuries per player-season by season (with 95% CIs and calendar events) and the share of each attacking and
# defensive style per league over the seasons. Raw season rates mix real change with Transfermarkt's recording changes
# (Phase 0: the Premier League 2018-19 jump), so the unknown body-area share is shown with them.

# %%
by_season = summarise(ps, "season_key")
unknown_share = (ps.groupby("season_key")["area: unknown"].sum() / ps.groupby("season_key").injuries.sum()).rename("unknown body area")
season_league = ps.groupby(["season_key", "league"]).apply(lambda d: d.injuries.sum() / len(d), include_groups=False).unstack()[LEAGUES]
shares = {ph: pd.crosstab([clusters.league, clusters.season_key], clusters[col], normalize="index")[order]
          for ph, (col, order) in {"attack": ("attack_style", ATTACK), "defence": ("defence_style", DEFENCE)}.items()}
display(fmt(by_season)[["player-seasons", "injuries / player-season", "days lost / player-season", "severe share", "RR (95% CI)"]].join(unknown_share.round(3)))
season_league.round(3)

# %%
EVENTS = {"2019-20": "COVID restart", "2020-21": "congested season,\nfive subs", "2022-23": "mid-season\nWorld Cup", "2024-25": "new CL format"}
LABEL_Y = {"2019-20": 0.97, "2020-21": 0.85, "2022-23": 0.97, "2024-25": 0.97}
fig, ax = plt.subplots(figsize=(12, 4))
x = np.arange(len(by_season))
rate = by_season["injuries / player-season"]
ax.fill_between(x, rate * by_season["RR low"] / by_season["RR"], rate * by_season["RR high"] / by_season["RR"], color=SERIES[0], alpha=0.15, linewidth=0)
ax.plot(x, rate, color=SERIES[0], marker="o", markersize=6)
ax.set_xticks(x, by_season.index)
ax.set_ylabel("injuries > 7 days per player-season")
ax.set_ylim(0, rate.max() * 1.35)
for s, label in EVENTS.items():
    xi = list(by_season.index).index(s)
    ax.axvline(xi, color=MUTED, linewidth=1, linestyle=":")
    ax.text(xi + 0.05, ax.get_ylim()[1] * LABEL_Y[s], label, fontsize=8, color=MUTED, va="top")
ax.set_title("Injury frequency by season (all Big Five; band = 95% CI)", loc="left")
trend_fig = save(fig, "05_season_trend.png")

fig, axes = plt.subplots(2, 5, figsize=(20, 7.5), sharey=True)
for row, (ph, order) in enumerate([("attack", ATTACK), ("defence", DEFENCE)]):
    for ax, lg in zip(axes[row], LEAGUES):
        d = shares[ph].loc[lg].reindex(by_season.index).fillna(0)
        ax.stackplot(range(len(d)), d.T.to_numpy(), colors=SERIES[:4], edgecolor=SURFACE, linewidth=0.8)
        ax.set_title(f"{lg}: {ph}", loc="left")
        ax.set_xticks(range(0, len(d), 3), [d.index[i][2:] for i in range(0, len(d), 3)])
        ax.set_ylim(0, 1)
        ax.grid(False)
    axes[row, 0].set_ylabel("share of team-seasons")
    handles = [plt.Rectangle((0, 0), 1, 1, color=SERIES[i]) for i in range(4)]
    axes[row, 4].legend(handles, order, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=9)
fig.tight_layout()
shares_fig = save(fig, "05_style_shares_by_league.png")

# %% [markdown]
# ## Step 6. Leagues
#
# Rates per league (raw; partly recording) and each style's RR **within its own league** (its league's average = 1).
# A pattern that holds in several leagues is more convincing than one carried by a single league.

# %%
by_league = summarise(ps, "league").loc[LEAGUES]
within = {}
for name in ["attacking style", "defensive style"]:
    col, order = GROUPINGS[name]
    t = summarise(ps, ["league", col])
    within[name] = (t["RR"].unstack().reindex(index=LEAGUES, columns=order), t["team-seasons"].unstack().reindex(index=LEAGUES, columns=order))
display(fmt(by_league)[COLS])
for name, (rr, n) in within.items():
    print(name)
    display(rr.round(2))

# %%
fig, axes = plt.subplots(1, 2, figsize=(15, 3.8))
for ax, (name, (rr, n)) in zip(axes, within.items()):
    vals = rr.to_numpy(dtype=float)
    ax.imshow(np.log2(vals), cmap=DIVERGING, vmin=-0.6, vmax=0.6, aspect="auto")
    ax.set_xticks(range(rr.shape[1]), rr.columns, rotation=15, ha="right")
    ax.set_yticks(range(len(LEAGUES)), LEAGUES)
    ax.grid(False)
    for (i, j), v in np.ndenumerate(vals):
        k = n.to_numpy()[i, j]
        ax.text(j, i, "–" if np.isnan(v) else f"{v:.2f}\n(n={int(k)})", ha="center", va="center", fontsize=8,
                color=INK if np.isnan(v) or abs(np.log2(v)) < 0.45 else "white")
    ax.set_title(f"Injury RR by {name} within each league", loc="left")
fig.tight_layout()
league_fig = save(fig, "05_style_within_league.png")

# %% [markdown]
# ## Step 7. Adjusting step by step: season, team strength, age and position, matches played
#
# Possession and pressing styles are more common among **strong teams**, which also play **more matches** (European
# football). If a style's excess were only strength, squad make-up or match load, it would shrink as each is added to
# the expected value. Each row adds one adjustment to the one above; the per-match rows change the exposure from
# player-seasons to team matches. Read the **last row of each exposure** as the style's own association.

# %%
LADDER = [("per player-season", "league × season", ""), ("per player-season", "+ team strength", "_str"),
          ("per player-season", "+ age × position", "_full"), ("per team match", "league × season", "_match"),
          ("per team match", "+ team strength", "_match_str")]
ladder_rows, adjusted = [], {}
for name in ["attacking style", "defensive style", "formation"]:
    col, order = GROUPINGS[name]
    for exposure, adjustment, suffix in LADDER:
        t = summarise(ps.dropna(subset=[f"exp_inj{suffix}"]), col, suffix).loc[order]
        for style, r in t.iterrows():
            ladder_rows.append({"grouping": name, "style": style, "exposure": exposure, "adjustment": adjustment,
                                **r[["RR", "RR low", "RR high", "days RR", "days RR low", "days RR high",
                                     "excess / 100 player-seasons"]].to_dict()})
ladder = pd.DataFrame(ladder_rows)
for name in ["attacking style", "defensive style", "formation"]:
    t = ladder[ladder.grouping == name].assign(
        rr=lambda d: d.apply(lambda r: f"{r['RR']:.2f} ({r['RR low']:.2f}–{r['RR high']:.2f})", axis=1))
    adjusted[name] = t.pivot_table(index=["exposure", "adjustment"], columns="style", values="rr", aggfunc="first", sort=False)[GROUPINGS[name][1]]
    display(adjusted[name])
mix = {name: pd.concat([ps.groupby(GROUPINGS[name][0]).age.mean().round(1).rename("mean age"),
                        ps.groupby(GROUPINGS[name][0]).matches_all.mean().round(1).rename("team matches"),
                        pd.crosstab(ps[GROUPINGS[name][0]], ps.strength, normalize="index").round(2),
                        pd.crosstab(ps[GROUPINGS[name][0]], ps.position, normalize="index").round(2)], axis=1).loc[GROUPINGS[name][1]]
       for name in ["attacking style", "defensive style"]}
display(*mix.values())
display(fmt(summarise(ps.dropna(subset=["age_band"]), "age_band"))[["player-seasons", "injuries / player-season", "days lost / player-season", "severe share"]])
fmt(summarise(ps.dropna(subset=["position"]), "position"))[["player-seasons", "injuries / player-season", "days lost / player-season", "severe share"]]

# %%
# Figure: how each style's rate ratio moves as adjustments are added (the "style or schedule?" picture).
fig, axes = plt.subplots(1, 2, figsize=(14, 4.6), sharey=True)
steps = [f"{e}\n{a}" for e, a, _ in LADDER]
for ax, name in zip(axes, ["attacking style", "defensive style"]):
    t = ladder[ladder.grouping == name]
    for i, style in enumerate(GROUPINGS[name][1]):
        r = t[t["style"] == style].set_index(["exposure", "adjustment"]).loc[[(e, a) for e, a, _ in LADDER]]
        x = np.arange(len(LADDER)) + (i - 1.5) * 0.08
        ax.errorbar(x, r.RR, yerr=[r.RR - r["RR low"], r["RR high"] - r.RR], color=SERIES[i], marker="o", capsize=0,
                    linewidth=2, elinewidth=1.2, label=style)
    ax.axhline(1, color=MUTED, linestyle="--", linewidth=1)
    ax.axvspan(2.5, 4.5, color=GRID, alpha=0.5, zorder=0)
    ax.set_xticks(range(len(LADDER)), steps, fontsize=8)
    ax.set_title(name.capitalize(), loc="left")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
axes[0].set_ylabel("injury rate ratio (1 = expected)")
fig.suptitle("Style or schedule? Each style's injury rate ratio as team strength, squad make-up and matches played are taken into account",
             x=0.01, ha="left", fontsize=11)
fig.tight_layout()
ladder_fig = save(fig, "05_adjustment_ladder.png")

# %% [markdown]
# ## Step 8. Team strength and workload
#
# Styles follow team strength partly (Phase 4: eta² 0.39 attack, 0.34 defence). **Strength:** style RRs within each
# third of teams by points per match, against teams **of the same strength third** (expected from league × season ×
# strength), so a strong possession team is compared with other strong teams. **Workload:** player-seasons in the busiest third (share of matches on < 4 days'
# rest) vs the rest, overall and within each style.

# %%
ps["congestion"] = pd.qcut(ps.short_rest_share, 3, labels=["lightest third", "middle third", "busiest third"], duplicates="drop")
by_congestion = summarise(ps, "congestion")
strength_rr, congestion_rr = {}, {}
for name in ["attacking style", "defensive style"]:
    col, order = GROUPINGS[name]
    strength_rr[name] = summarise(ps, ["strength", col], "_str")["RR"].unstack().reindex(index=["weaker third", "middle third", "stronger third"], columns=order)
    congestion_rr[name] = summarise(ps, ["congestion", col])["RR"].unstack().reindex(index=["lightest third", "middle third", "busiest third"], columns=order)
    display(strength_rr[name].round(2))
    display(congestion_rr[name].round(2))
fmt(by_congestion)[COLS]

# %% [markdown]
# **Same club, with and without the style.** The strongest check on "style or club?" available without a model: for
# the clubs that played some seasons in a style and some not, their injury RR in the style's seasons is divided by
# their RR in their other seasons (so the club itself, its medical staff and its recording are held fixed), with a
# bootstrap over clubs. Then the seasons right after a club **switched into** or **out of** the style, against the
# season before: if the style itself raised injuries, switching in should raise the RR and switching out lower it.

# %%
SAME_CLUB_EXP = [("league × season", ""), ("+ team strength", "_str"), ("per team match, + strength", "_match_str")]
team_t = ps.groupby(["team_season", "club_id", "season", "attack_style", "defence_style"], observed=True)[
    ["injuries", "exp_inj", "exp_inj_str", "exp_inj_match_str"]].sum().reset_index()
same_rows, switch_rows = [], []
for name in ["attacking style", "defensive style"]:
    col, order = GROUPINGS[name]
    for style in order:
        t = team_t.assign(inside=team_t[col] == style)
        mixed = t.groupby("club_id").inside.transform(lambda x: x.any() and not x.all())
        w = t[mixed]
        row = {"grouping": name, "style": style, "clubs": w.club_id.nunique(), "style seasons": int(w.inside.sum()),
               "other seasons": int((~w.inside).sum())}
        for label, suffix in SAME_CLUB_EXP:
            c = w.groupby(["club_id", "inside"])[["injuries", f"exp_inj{suffix}"]].sum().unstack(fill_value=0)
            ratio = lambda d: (d[("injuries", True)].sum() / d[(f"exp_inj{suffix}", True)].sum()) / (
                d[("injuries", False)].sum() / d[(f"exp_inj{suffix}", False)].sum())
            rng = np.random.default_rng([SEED, zlib.crc32(f"same club|{style}|{suffix}".encode())])
            boot = [ratio(c.iloc[rng.integers(0, len(c), len(c))]) for _ in range(N_BOOT)]
            row[f"ratio, {label}"] = ratio(c)
            row[f"low, {label}"], row[f"high, {label}"] = np.percentile(boot, [2.5, 97.5])
        same_rows.append(row)
        s_ = t.sort_values(["club_id", "season"]).assign(rr=lambda d: d.injuries / d.exp_inj_str)
        s_["prev_inside"] = s_.groupby("club_id").inside.shift()
        s_["prev_rr"] = s_.groupby("club_id").rr.shift()
        s_ = s_[s_.groupby("club_id").season.shift() == s_.season - 1]
        for direction, mask in [("into", s_.inside & (s_.prev_inside == False)), ("out of", ~s_.inside & (s_.prev_inside == True))]:
            m = s_[mask]
            switch_rows.append({"grouping": name, "style": style, "switch": direction, "switches": len(m),
                                "RR season before (+ strength)": m.prev_rr.mean(), "RR season after (+ strength)": m.rr.mean(),
                                "change": (m.rr - m.prev_rr).mean()})
same_club = pd.DataFrame(same_rows).set_index(["grouping", "style"])
switches = pd.DataFrame(switch_rows).set_index(["grouping", "style", "switch"])
display(same_club.round(2))
switches.round(2)

# %%
# Figure: same club with and without each style (after team strength), and the change around style switches.
fig, axes = plt.subplots(1, 2, figsize=(14, 4.4), gridspec_kw={"width_ratios": [1.2, 1]})
ax = axes[0]
rows = same_club.reset_index()
y = np.arange(len(rows))[::-1]
for yi, (_, r) in zip(y, rows.iterrows()):
    color = SERIES[(ATTACK + DEFENCE).index(r["style"]) % 4]
    ax.plot([r["low, + team strength"], r["high, + team strength"]], [yi, yi], color=color, linewidth=2.5, solid_capstyle="round")
    ax.scatter(r["ratio, + team strength"], yi, color=color, s=50, zorder=3, edgecolors=SURFACE)
    ax.text(r["high, + team strength"] + 0.01, yi, f"{r['ratio, + team strength']:.2f} ({int(r['clubs'])} clubs)", va="center", fontsize=8)
ax.axvline(1, color=MUTED, linestyle="--", linewidth=1)
ax.axhline(3.5, color=GRID, linewidth=1)
ax.set_yticks(y, rows["style"])
ax.set_xlabel("injuries in the style's seasons ÷ the same clubs' other seasons (after team strength)")
ax.set_title("Same club, with and without the style", loc="left")
ax.grid(axis="y", visible=False)
ax = axes[1]
sw = switches.reset_index()
order = list(dict.fromkeys(sw["style"]))
for _, r in sw.iterrows():
    yv = len(order) - 1 - order.index(r["style"]) + (0.17 if r.switch == "into" else -0.17)
    before, after = r["RR season before (+ strength)"], r["RR season after (+ strength)"]
    color = SERIES[0] if r.switch == "into" else SERIES[1]
    ax.annotate("", xy=(after, yv), xytext=(before, yv), arrowprops={"arrowstyle": "-|>", "color": color, "linewidth": 2, "mutation_scale": 12})
    ax.scatter(before, yv, color=color, s=14, zorder=3)
    ax.text(max(before, after) + 0.01, yv, f"{before:.2f} → {after:.2f}", va="center", fontsize=7.5, color=MUTED)
values = sw[["RR season before (+ strength)", "RR season after (+ strength)"]].to_numpy()
ax.set_xlim(values.min() - 0.03, values.max() + 0.09)
ax.set_ylim(-0.6, len(order) - 0.4)
ax.axhline(3.5, color=GRID, linewidth=1)
ax.set_yticks(range(len(order))[::-1], order)
ax.axvline(1, color=MUTED, linestyle="--", linewidth=1)
ax.set_xlabel("rate ratio the season before → after (blue: switched into, orange: out of)")
ax.set_title("Rate ratio before and after a club switches style", loc="left")
ax.grid(axis="y", visible=False)
fig.tight_layout()
same_club_fig = save(fig, "05_same_club.png")

# %% [markdown]
# ## Step 9. Fitness absences (secondary outcome)
#
# *Fitness* absences (not injuries; mostly reconditioning) are recorded almost only in the Bundesliga, so they are
# compared by style within the Bundesliga.

# %%
bl = ps[ps.league == "Bundesliga"]
fitness = {}
for name in ["attacking style", "defensive style"]:
    col, order = GROUPINGS[name]
    f = bl.groupby(col).agg(player_seasons=("playerId", "size"), fitness_absences=("fitness_absences", "sum")).reindex(order)
    f["per 100 player-seasons"] = (100 * f.fitness_absences / f.player_seasons).round(1)
    fitness[name] = f
    display(f)

# %% [markdown]
# ## Step 10. Sensitivity checks
#
# The RR per style (against league × season) under each variation; a finding is robust if its direction holds in every
# row. Then the same RRs for the two **alternative clusterings** of Phase 4 (k = 3; style relative to the
# league-season), and days lost counted three ways.

# %%
def rr_variant(df: pd.DataFrame, col: str, order: list[str], count: str = "injuries") -> pd.Series:
    d = add_expected(df.assign(injuries=df[count]), ["league", "season"])
    return summarise(d, col)["RR"].reindex(order)


VARIANTS = {
    "main (> 7 days)": lambda d: (d, "injuries"),
    "≥ 900 minutes only": lambda d: (d[d.minutes >= 900], "injuries"),
    "severe only (> 28 days)": lambda d: (d, "severe"),
    "> 3 days (adds mild)": lambda d: (d.assign(more=d.injuries + d.mild_injuries), "more"),
    "multi-club players out": lambda d: (d[d.clubs_in_season == 1], "injuries"),
    "≥ 1 appearance only": lambda d: (d[d.appearances > 0], "injuries"),
    "COVID seasons out": lambda d: (d[~d.season_key.isin(COVID_SEASONS)], "injuries"),
}
sensitivity, robust = {}, {}
for name in ["attacking style", "defensive style", "formation"]:
    col, order = GROUPINGS[name]
    sensitivity[name] = pd.DataFrame({v: rr_variant(data, col, order, count) for v, (data, count) in
                                      ((v, f(ps)) for v, f in VARIANTS.items())}).T.round(2)
    signs = np.sign(sensitivity[name] - 1)
    robust[name] = [s for s in order if signs[s].nunique() == 1 and signs[s].iloc[0] != 0]
    display(sensitivity[name])
    print("same direction in every variant:", robust[name])

# %%
alt_clusterings = {}
for ph, col in [("attack", "attack_style"), ("defence", "defence_style")]:
    rows = {"main (k = 4)": summarise(ps, col)[["team-seasons", "RR", "RR low", "RR high"]],
            "k = 3": summarise(ps, f"{ph}_k3_style")[["team-seasons", "RR", "RR low", "RR high"]],
            "relative to league-season": summarise(ps, f"{ph}_rel_style")[["team-seasons", "RR", "RR low", "RR high"]],
            "relative, + team strength": summarise(ps, f"{ph}_rel_style", "_str")[["team-seasons", "RR", "RR low", "RR high"]]}
    alt_clusterings[ph] = pd.concat(rows, names=["clustering", "style"]).round(2)
    display(alt_clusterings[ph])
days_sensitivity = {}
for name in ["attacking style", "defensive style"]:
    col, order = GROUPINGS[name]
    days_sensitivity[name] = pd.DataFrame({
        label: summarise(add_expected(ps.assign(days_lost=ps[c]), ["league", "season"]), col)["days RR"].reindex(order)
        for label, c in [("overlaps merged (main)", "days_lost"), ("raw (overlaps counted twice)", "days_raw"),
                         (f"each injury capped at {DAYS_CAP} days", "days_capped")]}).T.round(2)
    display(days_sensitivity[name])
median_days = pd.concat({name: inj.merge(ps[KEY + [GROUPINGS[name][0]]], on=KEY).groupby(GROUPINGS[name][0]).days_merged.median()
                         .reindex(GROUPINGS[name][1]) for name in ["attacking style", "defensive style"]}).rename("median days per injury")
median_days.to_frame()

# %% [markdown]
# ## Step 11. Style cards: what each style looks like on the pitch
#
# Each style is described from its **clear members** (core): team-seasons whose fuzzy membership in their own style is
# at least 0.5 (Phase 4, fuzzy c-means memberships from the K-means centroids). Typical teams are the ones with the
# highest membership in each era. A card gives the defining traits in football terms, the matching numbers in real
# units against the all-team average, formation, strength, and the styles of the other phase it is most often paired with.

# %%
CLEAR = 0.5  # fuzzy membership from which a team-season is a clear member of its style (Phase 4)
RAW = {"attack_possession": ("deep_pm", "deep completions per match"), "attack_patience": ("slow_attack_share", "shots from slow, patient attacks"),
       "attack_verticality": ("fast_attack_share", "shots from fast attacks"), "attack_directness": ("outside_box_share", "shots from outside the box"),
       "defence_press": ("ppda", "PPDA (lower = more pressing)"), "defence_high_line": ("conceded_fast_share", "shots conceded from fast attacks"),
       "defence_territory_conceded": ("deep_against_pm", "deep completions conceded per match"), "defence_aggression": ("fouls_pm", "fouls per match")}
PHRASE = {"attack_possession": ("dominates the ball and plays in the opponent's half", "spends long spells without the ball"),
          "attack_patience": ("builds up slowly and patiently", "rarely builds up slowly"),
          "attack_verticality": ("attacks fast and vertically, on the break", "rarely attacks at speed"),
          "attack_directness": ("shoots from distance and relies on set plays", "works the ball into the box before shooting"),
          "defence_press": ("presses high and wins the ball back quickly", "sits off and lets the opponent have the ball"),
          "defence_high_line": ("holds a high line, exposed to counters", "keeps a deep, protected line"),
          "defence_territory_conceded": ("lets opponents near the box", "keeps opponents far from goal"),
          "defence_aggression": ("defends through fouls and duels, many cards", "defends cleanly, few fouls")}
ts = team.merge(features[["season", "club_id"] + [r for r, _ in RAW.values()]], on=["season", "club_id"])
for ph in ["attack", "defence"]:
    ts[f"{ph}_core"] = ts[f"{ph}_membership"] >= CLEAR
    ts[f"{ph}_dist"] = -ts[f"{ph}_membership"]  # sort key: highest membership first


def value(feature: str, v: float) -> str:
    return f"{100 * v:.0f}%" if feature.endswith("share") else f"{v:.1f}"


cards = {}
for ph, col, order, other in [("attack", "attack_style", ATTACK, "defence_style"), ("defence", "defence_style", DEFENCE, "attack_style")]:
    rows = []
    for name in order:
        s = ts[ts[col] == name]
        core = s[s[f"{ph}_core"]]
        cz = core[DIMS[ph]].mean()
        top = cz.abs().sort_values(ascending=False).index[:3]
        typical = (core.sort_values(f"{ph}_dist").groupby("era").head(2).assign(t=lambda d: d.club + " " + d.season_key)
                   .groupby("era").t.apply(", ".join).reindex(ERA_ORDER).fillna("–"))
        pairs = s[other].value_counts(normalize=True).head(2)
        rows.append({"style": name, "team-seasons": len(s), "core": f"{len(core)} ({len(core) / len(s):.0%})",
                     "how it plays": "; ".join(PHRASE[d][0 if cz[d] > 0 else 1] for d in top),
                     "in numbers (core)": "; ".join(f"{RAW[d][1]}: {value(RAW[d][0], core[RAW[d][0]].mean())} (all {value(RAW[d][0], ts[RAW[d][0]].mean())})" for d in top),
                     "back-three minutes": f"{100 * s.back_three_share.mean():.0f}%", "points/match": round(core.points_pm.mean(), 2),
                     "most often with": ", ".join(f"{k} ({v:.0%})" for k, v in pairs.items()),
                     **{f"typical {e}": typical[e] for e in ERA_ORDER}})
    cards[ph] = pd.DataFrame(rows).set_index("style")
    display(cards[ph])
ps = ps.merge(ts[["season", "club_id", "attack_core", "defence_core"]], on=["season", "club_id"], how="left")
core_check = {}
for ph, name in [("attack", "attacking style"), ("defence", "defensive style")]:
    col, order = GROUPINGS[name]
    core_t = summarise(ps[ps[f"{ph}_core"]], col).loc[order]
    core_check[name] = pd.DataFrame({"RR, all teams": results[name]["RR"], "RR, core teams": core_t["RR"],
                                     "days RR, all teams": results[name]["days RR"], "days RR, core teams": core_t["days RR"]}).round(2)
    display(core_check[name])

# %% [markdown]
# ## Step 12. How the ways of attacking and defending changed, and in what shape
#
# Each dimension's mean per era (2014–18, 2018–22, 2022–26), for all leagues and per league, with the shape: **rising**,
# **falling**, **peak** (up then down), **dip** (down then up) or **flat** (every step under 0.1 SD). Real-unit means
# show the same changes in football terms.

# %%
SHAPE_TOL = 0.1
ALL_DIMS = DIMS["attack"] + DIMS["defence"]


def shape(values: list[float]) -> str:
    steps = [0 if abs(d) < SHAPE_TOL else int(np.sign(d)) for d in np.diff(values)]
    if steps == [0, 0]:
        return "flat"
    if all(s >= 0 for s in steps):
        return "rising"
    if all(s <= 0 for s in steps):
        return "falling"
    return "peak" if steps == [1, -1] else "dip"


era_dims = ts.groupby(["league", "era"])[ALL_DIMS].mean()
era_all = ts.groupby("era")[ALL_DIMS].mean().loc[ERA_ORDER]
shapes = pd.DataFrame({lg: {d: shape(era_dims.loc[lg].loc[ERA_ORDER, d].tolist()) for d in ALL_DIMS} for lg in LEAGUES})
shapes.insert(0, "all leagues", [shape(era_all[d].tolist()) for d in ALL_DIMS])
raw_by_era = ts.groupby("era")[[r for r, _ in RAW.values()] + ["back_three_share"]].mean().loc[ERA_ORDER].T
raw_by_era.index = [RAW[d][1] for d in ALL_DIMS] + ["minutes in a back three"]
display(era_all.T.round(2).assign(shape=shapes["all leagues"]))
display(shapes)
raw_by_era.round(3)

# %%
LEAGUE_COLORS = dict(zip(LEAGUES, SERIES))
season_dims = ts.groupby(["season_key", "league"])[ALL_DIMS].mean()
seasons_x = sorted(ts.season_key.unique())
fig, axes = plt.subplots(2, 4, figsize=(18, 7), sharex=True, sharey=True)
for ax, d in zip(axes.flat, ALL_DIMS):
    for lg in LEAGUES:
        y = season_dims[d].xs(lg, level="league").reindex(seasons_x)
        ax.plot(range(len(y)), y, color=LEAGUE_COLORS[lg], linewidth=1.8, label=lg)
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ph, dim = d.split("_", 1)
    ax.set_title(f"{ph}: {dim.replace('_', ' ')} ({shapes.loc[d, 'all leagues']})", loc="left")
    ax.set_xticks(range(0, len(seasons_x), 3), [seasons_x[i][2:] for i in range(0, len(seasons_x), 3)])
axes[0, 0].legend(frameon=False, fontsize=8)
for ax in axes[:, 0]:
    ax.set_ylabel("mean score (z)")
fig.tight_layout()
dims_fig = save(fig, "05_style_dimensions_over_time.png")

# %% [markdown]
# ## Step 13. How teams move between styles
#
# For every club that played in its Big Five league in two consecutive seasons: its attacking (and defensive) style in
# season *t* and *t + 1*. The diagonal is how often a style is kept; the largest off-diagonal flows are the routes of
# change.

# %%
transitions = {}
for ph, col, order in [("attack", "attack_style", ATTACK), ("defence", "defence_style", DEFENCE)]:
    nxt = ts[["club_id", "season", col]].assign(season=lambda d: d.season - 1).rename(columns={col: "next"})
    moves = ts[["club_id", "season", "era", col]].merge(nxt, on=["club_id", "season"])
    t = pd.crosstab(moves[col], moves["next"]).loc[order, order]
    flows = t.stack().rename("clubs").reset_index().rename(columns={col: "from"})
    flows = flows[flows["from"] != flows["next"]].sort_values("clubs", ascending=False).head(5)
    transitions[ph] = {"share": t.div(t.sum(axis=1), axis=0), "flows": flows, "kept": np.trace(t.to_numpy()) / t.to_numpy().sum()}
    print(f"{ph}: {len(moves):,} consecutive pairs; style kept {transitions[ph]['kept']:.0%}")
    display((100 * transitions[ph]["share"]).round(0))
    display(flows)

# %% [markdown]
# ## Step 14. Style mix and injuries per era
#
# Share of team-seasons per style and era, and each style's injury RR per era against its league's **fixed** 12-season
# baseline, so change over time stays visible.

# %%
mix_era, rr_era, days_era = {}, {}, {}
for name in ["attacking style", "defensive style", "formation"]:
    col, order = GROUPINGS[name]
    mix_era[name] = pd.crosstab(clusters.era, clusters[col], normalize="index").loc[ERA_ORDER, order]
    t = summarise(ps, ["era", col])
    rr_era[name] = t["RR"].unstack().loc[ERA_ORDER, order]
    days_era[name] = t["days RR"].unstack().loc[ERA_ORDER, order]
    print(name)
    display((100 * mix_era[name]).round(1))
    display(rr_era[name].round(2))
by_era = summarise(ps, "era").loc[ERA_ORDER]
fmt(by_era)[COLS]

# %% [markdown]
# ## Step 15. How much of the injury trend comes from styles changing?
#
# **Kitagawa decomposition.** The overall rate is the share-weighted sum of cell rates; between two eras its change
# splits exactly into **style mix** (cell shares changed × average rate) and **within styles** (cell rates changed ×
# average share). Cells are league × **strength third** × combined style (attack × defence), so both phases count, and
# the part due to teams' strength mix changing (cells league × strength only) is taken out of the style mix: total
# change = strength mix + **style mix beyond strength** + within styles. The style mix ignoring strength is kept for
# comparison. The same is done with attacking style only and defensive style only, to see which phase's shift matters
# more. Outcomes per player-season: injuries, days lost, severe injuries, hamstring injuries, knee injuries.

# %%
OUTCOMES = {"injuries": "injuries", "days lost": "days_lost", "severe injuries": "severe",
            "hamstring injuries": "area: hamstring", "knee injuries": "area: knee"}
PAIRS = [(ERA_ORDER[0], ERA_ORDER[1]), (ERA_ORDER[1], ERA_ORDER[2]), (ERA_ORDER[0], ERA_ORDER[2])]
FIRST_LAST = f"{ERA_ORDER[0]} → {ERA_ORDER[2]}"


def decompose(df: pd.DataFrame, outcome: str, e0: str, e1: str, cells: list[str]) -> dict:
    def table(e):
        t = df[df.era == e].groupby(cells, observed=True).agg(n=(outcome, "size"), rate=(outcome, "mean"))
        return t.assign(w=t.n / t.n.sum())
    j = table(e0)[["w", "rate"]].join(table(e1)[["w", "rate"]], how="outer", lsuffix="0", rsuffix="1")
    j[["w0", "w1"]] = j[["w0", "w1"]].fillna(0)
    j["rate0"], j["rate1"] = j.rate0.fillna(j.rate1), j.rate1.fillna(j.rate0)
    total = (j.w1 * j.rate1).sum() - (j.w0 * j.rate0).sum()
    mix = ((j.w1 - j.w0) * (j.rate0 + j.rate1) / 2).sum()
    within = ((j.rate1 - j.rate0) * (j.w0 + j.w1) / 2).sum()
    assert abs(total - mix - within) < 1e-9
    return {"from": (j.w0 * j.rate0).sum(), "to": (j.w1 * j.rate1).sum(), "change": total, "from style mix": mix, "within styles": within}


def decompose_with_strength(df: pd.DataFrame, outcome: str, e0: str, e1: str, cells: list[str], base: list[str]) -> dict:
    """Style mix net of the strength mix: cells base × strength × style minus cells base × strength."""
    full = decompose(df, outcome, e0, e1, base + ["strength"] + cells)
    strength = decompose(df, outcome, e0, e1, base + ["strength"])
    plain = decompose(df, outcome, e0, e1, base + cells)
    out = {"from": full["from"], "to": full["to"], "change": full["change"],
           "from strength mix": strength["from style mix"],
           "from style mix": full["from style mix"] - strength["from style mix"],
           "within styles": full["within styles"], "style mix, strength ignored": plain["from style mix"]}
    assert abs(out["change"] - out["from strength mix"] - out["from style mix"] - out["within styles"]) < 1e-9
    return out


CELLS = {"combined style": ["style_group"], "attacking style": ["attack_style"], "defensive style": ["defence_style"]}
rows = []
for label, col in OUTCOMES.items():
    for e0, e1 in PAIRS:
        for by, cells in CELLS.items():
            rows.append({"outcome": label, "eras": f"{e0} → {e1}", "scope": "all leagues", "styles": by,
                         **decompose_with_strength(ps, col, e0, e1, cells, ["league"])})
            for lg in LEAGUES:
                rows.append({"outcome": label, "eras": f"{e0} → {e1}", "scope": lg, "styles": by,
                             **decompose_with_strength(ps[ps.league == lg], col, e0, e1, cells, [])})
decomposition = pd.DataFrame(rows)
main_dec = decomposition[(decomposition.scope == "all leagues") & (decomposition.styles == "combined style")]
phase_dec = decomposition[(decomposition.scope == "all leagues") & (decomposition.eras == FIRST_LAST)].pivot(
    index="outcome", columns="styles", values="from style mix").loc[list(OUTCOMES)]
display(main_dec.drop(columns=["scope", "styles"]).round(3))
display(phase_dec.round(3))
decomposition[(decomposition.eras == FIRST_LAST) & (decomposition.outcome == "injuries") & (decomposition.styles == "combined style")].round(3)

# %%
d = decomposition[(decomposition.eras == FIRST_LAST) & (decomposition.outcome == "injuries") & (decomposition.styles == "combined style")].set_index("scope").loc[["all leagues"] + LEAGUES]
fig, ax = plt.subplots(figsize=(10, 4))
y = np.arange(len(d))[::-1]
ax.barh(y + 0.27, d["from strength mix"], height=0.25, color=SERIES[2], label="from the strength mix changing")
ax.barh(y, d["from style mix"], height=0.25, color=SERIES[0], label="from the style mix changing (beyond strength)")
ax.barh(y - 0.27, d["within styles"], height=0.25, color=SERIES[1], label="within styles")
ax.scatter(d.change, y, color=INK, zorder=3, s=30, label="total change")
ax.axvline(0, color=MUTED, linewidth=1)
ax.set_yticks(y, d.index)
ax.set_xlabel(f"change in injuries per player-season, {FIRST_LAST}")
ax.set_title("Where the injury trend comes from", loc="left")
ax.grid(axis="y", visible=False)
ax.legend(frameon=False, fontsize=8, loc="lower right")
decomp_fig = save(fig, "05_trend_decomposition.png")

# %% [markdown]
# ## Step 16. Style dimensions vs injury outcomes across league-seasons
#
# For the 60 league-seasons: average style scores against injury outcomes, **within league** (both centred on the
# league's 12-season mean). These level correlations partly repeat shared long-run trends (including recording
# changes); the stricter version uses **season-to-season changes** within each league (n = 55). Aggregate association
# only.

# %%
ls_dims = ts.groupby(["league", "season_key"])[ALL_DIMS].mean()
g = ps.groupby(["league", "season_key"])
known = g.injuries.sum() - g["area: unknown"].sum()
ls_out = pd.DataFrame({
    "injuries / player-season": g.injuries.mean(), "days lost / player-season": g.days_lost.mean(),
    "severe share": g.severe.sum() / g.injuries.sum(), "hamstring share": g["area: hamstring"].sum() / known,
    "knee share": g["area: knee"].sum() / known,
    "muscle share": (g["area: hamstring"].sum() + g["area: unspecified muscle"].sum() + g["area: thigh"].sum()
                     + g["area: calf/achilles/lower leg"].sum()) / known,
})
centred = lambda t: t - t.groupby(level="league").transform("mean")
changes = lambda t: t.groupby(level="league").diff().dropna()
cd, co = centred(ls_dims), centred(ls_out)
dd, do = changes(ls_dims.sort_index()), changes(ls_out.sort_index())
link = pd.DataFrame({o: {d: cd[d].corr(co[o]) for d in ALL_DIMS} for o in co.columns}).round(2)
link_changes = pd.DataFrame({o: {d: dd[d].corr(do[o]) for d in ALL_DIMS} for o in do.columns}).round(2)
strongest = link.abs().stack().sort_values(ascending=False).head(6)
display(link)
display(link_changes)
strongest.rename("|r|").to_frame()

# %%
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for ax, (d, o) in zip(axes, strongest.index[:2]):
    for lg in LEAGUES:
        ax.scatter(cd.xs(lg, level="league")[d], co.xs(lg, level="league")[o], color=LEAGUE_COLORS[lg], s=40,
                   edgecolors=SURFACE, linewidths=1, label=lg)
    ax.set_xlabel(f"{d.replace('_', ' ')} (vs league's 12-season mean)")
    ax.set_ylabel(f"{o} (vs league mean)")
    ax.set_title(f"levels r = {link.loc[d, o]:+.2f}; season-to-season r = {link_changes.loc[d, o]:+.2f}", loc="left")
axes[0].legend(frameon=False, fontsize=8)
fig.tight_layout()
link_fig = save(fig, "05_style_injury_links.png")

# %% [markdown]
# ## Step 17. One story per league
#
# Each league's evolution in a few sentences from steps 12–15: which attacking and defensive styles grew and shrank,
# how the ways of playing changed, and what happened to injuries, split into the style-mix part and the within-style part.

# %%
stories = {}
first, last = ERA_ORDER[0], ERA_ORDER[2]
mix_league = {ph: pd.crosstab([clusters.league, clusters.era], clusters[col], normalize="index")[order]
              for ph, col, order in [("attack", "attack_style", ATTACK), ("defence", "defence_style", DEFENCE)]}


def shifts(ph: str, lg: str) -> str:
    m = mix_league[ph].loc[lg]
    ch = (m.loc[last] - m.loc[first]).sort_values()
    up, down = ch.index[-1], ch.index[0]
    return (f"{up} {100 * m.loc[first, up]:.0f}% → {100 * m.loc[last, up]:.0f}%, "
            f"{down} {100 * m.loc[first, down]:.0f}% → {100 * m.loc[last, down]:.0f}%")


for lg in LEAGUES:
    dec = decomposition[(decomposition.scope == lg) & (decomposition.eras == FIRST_LAST) & (decomposition.styles == "combined style")].set_index("outcome")
    inj, days, ham, knee = (dec.loc[o] for o in ["injuries", "days lost", "hamstring injuries", "knee injuries"])
    moved = [f"{d.split('_', 1)[1].replace('_', ' ')} ({d.split('_')[0]}) {shapes.loc[d, lg]}" for d in ALL_DIMS if shapes.loc[d, lg] != "flat"]
    b3 = ts[ts.league == lg].groupby("era").back_three_share.mean()
    stories[lg] = (
        f"**{lg}.** From {first} to {last}: attack {shifts('attack', lg)}; defence {shifts('defence', lg)}; "
        f"back-three minutes {100 * b3[first]:.0f}% → {100 * b3[last]:.0f}%. "
        + (f"Trends: {', '.join(moved)}. " if moved else "")
        + f"Injuries per player-season {inj['from']:.2f} → {inj['to']:.2f} ({inj.change:+.2f}: {inj['from style mix']:+.3f} from the style mix, "
        f"{inj['within styles']:+.3f} within styles); days lost {days['from']:.1f} → {days['to']:.1f}; hamstring injuries "
        f"{ham['from']:.3f} → {ham['to']:.3f} (style mix {ham['from style mix']:+.3f}); knee {knee['from']:.3f} → {knee['to']:.3f} "
        f"(style mix {knee['from style mix']:+.3f})."
    )
    display(Markdown(stories[lg]))

# %% [markdown]
# ## Step 18. Making results clearer without overfitting
#
# Four standard treatments, fixed in advance and not tuned on the injury outcomes:
# - **Shrinkage for small groups (empirical Bayes):** rate ratios of small cells (attack × defence combinations, a style
#   within one league) are noisy. Each cell's log RR is pulled towards the average of its family in proportion to its
#   uncertainty (bootstrap CI), with the between-cell spread estimated from the data (DerSimonian–Laird). Large,
#   precise cells barely move; tiny ones move most.
# - **Rolling averages:** 3-season centred rolling means of the season series, next to the raw values, to show the
#   trend without the season-to-season noise.
# - **Multiple testing (FDR):** each style × body-area pattern is tested by **permutation**: within each league-season,
#   team-seasons' style labels are shuffled (10,000 times, seed 42) and the style's excess of injuries in that area
#   (observed minus expected at the league-season's area share, among injuries with a known area) is compared with
#   its shuffled distribution. Shuffling whole team-seasons keeps injuries of one squad together, which a per-injury
#   test does not. Formation is tested once (back three; back four is its mirror), so 72 tests, corrected with
#   Benjamini–Hochberg; only q < 0.05 counts as a finding. The Mantel–Haenszel odds ratio (strata league × era) is the
#   effect size.
# - **Breakdowns:** each style's RR (against league × season) by position and by age band, to see who carries a
#   style's excess.

# %%
def shrink(t: pd.DataFrame, rr: str = "RR") -> pd.DataFrame:
    """Empirical-Bayes shrinkage of log rate ratios towards their precision-weighted mean (DerSimonian–Laird)."""
    y = np.log(t[rr])
    se = (np.log(t[f"{rr} high"]) - np.log(t[f"{rr} low"])) / (2 * 1.96)
    w = 1 / se ** 2
    mu = (w * y).sum() / w.sum()
    q = (w * (y - mu) ** 2).sum()
    tau2 = max(0.0, (q - (len(y) - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    weight = tau2 / (tau2 + se ** 2)
    return pd.DataFrame({f"{rr} raw": t[rr], f"{rr} shrunk": np.exp(mu + weight * (y - mu)), f"{rr} weight on own data": weight})


grid_shrunk = grid[["team-seasons"]].join(shrink(grid)).join(shrink(grid, "days RR"))
within_shrunk = {}
for name in ["attacking style", "defensive style"]:
    col, order = GROUPINGS[name]
    t = summarise(ps, ["league", col])
    within_shrunk[name] = t[["team-seasons"]].join(shrink(t))
display(grid_shrunk.round(2))
for name, t in within_shrunk.items():
    display(t["RR shrunk"].unstack().reindex(index=LEAGUES, columns=GROUPINGS[name][1]).round(2))

# %%
ROLL = 3
trend = by_season[["injuries / player-season", "days lost / player-season"]].join(unknown_share)
trend_rolling = trend.rolling(ROLL, center=True, min_periods=2).mean().add_suffix(f" ({ROLL}-season mean)")
league_rolling = season_league.rolling(ROLL, center=True, min_periods=2).mean()
display(trend.join(trend_rolling).round(3))
league_rolling.round(3)

# %%
N_PERM = 10_000  # p resolution 1e-4; BH over 72 tests needs p below 0.05 / 72 ≈ 7e-4 for the strongest pattern


def mh_odds_ratio(data: pd.DataFrame, col: str, style: str, area: str, strata: list[str]) -> float:
    """Mantel–Haenszel odds ratio of 'injury in this area' for 'this style' vs the rest (known areas only)."""
    num = den = 0.0
    for _, d in data.groupby(strata, observed=True):
        known = d.injuries - d["area: unknown"]
        a = d.loc[d[col] == style, f"area: {area}"].sum()
        b = known[d[col] == style].sum() - a
        c = d.loc[d[col] != style, f"area: {area}"].sum()
        dd = known[d[col] != style].sum() - c
        n = a + b + c + dd
        if n > 0:
            num += a * dd / n
            den += b * c / n
    return num / den


def benjamini_hochberg(p: pd.Series) -> pd.Series:
    order = p.sort_values()
    q = (order * len(p) / np.arange(1, len(p) + 1)).iloc[::-1].cummin().iloc[::-1].clip(upper=1)
    return q.reindex(p.index)


# Team-season table: known-area injuries and injuries per area; excess over the league-season's area share.
area_cols = [f"area: {a}" for a in AREAS]
teams_t = ps.groupby("team_season").agg(league=("league", "first"), season=("season", "first"),
                                        attack_style=("attack_style", "first"), defence_style=("defence_style", "first"),
                                        formation=("formation", "first"), injuries=("injuries", "sum"),
                                        unknown=("area: unknown", "sum"), **{c: (c, "sum") for c in area_cols})
teams_t["known"] = teams_t.injuries - teams_t.unknown
ls_share = teams_t.groupby(["league", "season"])[area_cols].transform("sum").div(
    teams_t.groupby(["league", "season"]).known.transform("sum"), axis=0)
excess = (teams_t[area_cols] - ls_share.mul(teams_t.known, axis=0)).to_numpy()
perm_rng = np.random.default_rng(SEED)
groups = list(teams_t.reset_index().groupby(["league", "season"]).indices.values())  # positions per league-season
perm_idx = np.tile(np.arange(len(teams_t), dtype=np.int32), (N_PERM, 1))
for b in range(N_PERM):
    for g in groups:
        perm_idx[b, g] = perm_rng.permutation(g)

TESTS = {"attacking style": ATTACK, "defensive style": DEFENCE, "formation": ["back three"]}
fdr_rows = []
for name, styles in TESTS.items():
    col = GROUPINGS[name][0]
    labels = teams_t[col].to_numpy()
    for style in styles:
        member = labels == style
        observed = excess[member].sum(axis=0)
        shuffled = np.stack([excess[member[perm_idx[b]]].sum(axis=0) for b in range(N_PERM)])
        p_perm = (1 + (np.abs(shuffled) >= np.abs(observed)).sum(axis=0)) / (N_PERM + 1)
        for i, area in enumerate(AREAS):
            fdr_rows.append({"grouping": name, "style": style, "area": area,
                             "MH odds ratio": mh_odds_ratio(ps, col, style, area, ["league", "era"]),
                             "excess injuries": observed[i], "p": p_perm[i],
                             "leagues above 1": int(body[name]["above"].loc[style, area])})
body_fdr = pd.DataFrame(fdr_rows)
assert len(body_fdr) == 72, len(body_fdr)
body_fdr["q (BH)"] = benjamini_hochberg(body_fdr.p)
body_fdr["finding"] = body_fdr["q (BH)"] < 0.05
body_findings = body_fdr[body_fdr.finding].sort_values(["grouping", "MH odds ratio"], ascending=[True, False])
print(f"{body_fdr.finding.sum()} of {len(body_fdr)} style × body-area patterns survive FDR (permutation, q < 0.05)")
body_findings.round(4)

# %%
breakdown_rows = []
for name in ["attacking style", "defensive style"]:
    col, order = GROUPINGS[name]
    for by in ["position", "age_band"]:
        t = summarise(ps.dropna(subset=[by]), [col, by])
        for (style, group), r in t.iterrows():
            breakdown_rows.append({"grouping": name, "style": style, "by": by, "group": str(group), "player-seasons": r["player-seasons"],
                                   "injuries / player-season": r["injuries / player-season"], "RR": r["RR"],
                                   "RR low": r["RR low"], "RR high": r["RR high"], "excess / 100 player-seasons": r["excess / 100 player-seasons"]})
breakdown = pd.DataFrame(breakdown_rows)
for name in ["attacking style", "defensive style"]:
    for by in ["position", "age_band"]:
        display(breakdown[(breakdown.grouping == name) & (breakdown.by == by)].pivot(index="style", columns="group", values="RR")
                .reindex(GROUPINGS[name][1]).round(2))

# %% [markdown]
# ## Step 19. Report

# %%
ps.to_parquet(OUT_DIR / "player_seasons.parquet", index=False)
# Result tables, for the Phase 6 dashboard.
TABLES = OUT_DIR / "tables"
TABLES.mkdir(exist_ok=True)
for name, t in results.items():
    t.to_csv(TABLES / f"rates_{name.replace(' ', '_')}.csv")
grid.to_csv(TABLES / "attack_defence_grid.csv")
for name, b in body.items():
    b["median"].to_csv(TABLES / f"body_median_{name.replace(' ', '_')}.csv")
    b["above"].to_csv(TABLES / f"body_above_{name.replace(' ', '_')}.csv")
by_season.join(unknown_share).to_csv(TABLES / "by_season.csv")
decomposition.to_csv(TABLES / "decomposition.csv", index=False)
pd.Series(stories, name="story").rename_axis("league").to_csv(TABLES / "league_stories.csv")
for ph, c in cards.items():
    c.to_csv(TABLES / f"cards_{ph}.csv")
grid_shrunk.to_csv(TABLES / "attack_defence_grid_shrunk.csv")
for name, t in within_shrunk.items():
    t.to_csv(TABLES / f"within_league_shrunk_{name.replace(' ', '_')}.csv")
trend.join(trend_rolling).to_csv(TABLES / "season_trend_rolling.csv")
league_rolling.to_csv(TABLES / "season_league_rolling.csv")
body_fdr.to_csv(TABLES / "body_areas_fdr.csv", index=False)
breakdown.to_csv(TABLES / "breakdown_position_age.csv", index=False)
body_league.to_csv(TABLES / "body_areas_by_league_era.csv")
ladder.to_csv(TABLES / "rr_adjustment_ladder.csv", index=False)
same_club.to_csv(TABLES / "same_club.csv")
switches.to_csv(TABLES / "style_switches.csv")
pd.concat(alt_clusterings, names=["phase"]).to_csv(TABLES / "rr_alternative_clusterings.csv")
pd.concat(days_sensitivity, names=["grouping"]).to_csv(TABLES / "days_sensitivity.csv")


def sig_list(t: pd.DataFrame, rr: str = "RR") -> str:
    lo, hi = f"{rr} low", f"{rr} high"
    s = t[(t[lo] > 1) | (t[hi] < 1)]
    return ", ".join(f"{i} {r:.2f}" for i, r in s[rr].items()) or "none"


text = ["# Phase 5: Injury analysis", "",
        f"Generated {date.today().isoformat()} by `notebooks/05_injury_analysis.ipynb`, where each step is shown with its checks.", "",
        "## Key numbers", "",
        f"- {len(ps):,} player-club-seasons, {int(ps.injuries.sum()):,} injuries > 7 days, {int(ps.days_lost.sum()):,} days lost."]
for name in ["attacking style", "defensive style", "formation"]:
    text.append(f"- {name.capitalize()}: injury RR CI excludes 1 for {sig_list(results[name])}; days RR for {sig_list(results[name], 'days RR')}; "
                f"robust in every sensitivity check: {', '.join(robust[name]) or 'none'}.")
text += ["", "## 1. Injuries by style", ""]
for name in GROUPINGS:
    text += [f"### {name.capitalize()}", "", md_table(fmt(results[name])[COLS].rename_axis(name)), ""]
text += ["Injury RR, attacking style (rows) × defensive style (columns):", "", md_table(grid_rr.round(2).rename_axis("attack \\ defence")), "",
         "Days lost RR:", "", md_table(grid_days.round(2).rename_axis("attack \\ defence")), "",
         f"![Rates](figures/{style_fig})", "", f"![Grid](figures/{grid_fig})", "",
         "## 2. Body areas by style (relative to the league's share; median over leagues, leagues above 1)", ""]
for name in ["attacking style", "defensive style", "formation"]:
    b = body[name]
    text += [f"### {name.capitalize()} (pooled chi² p = {b['p']:.2g}, Cramér's V = {b['V']:.3f})", "",
             md_table(b["median"].round(2).rename_axis(name)), "", md_table(b["above"].rename_axis(name)), ""]
text += [f"![Body areas](figures/{area_fig})", "",
         "### Body areas by league and era", "",
         "Injuries per 100 player-seasons by body area (all leagues):", "", md_table(all_leagues.round(1).rename_axis("era")), "",
         f"Change {ERA_ORDER[0]} → {ERA_ORDER[-1]} per league (injuries per 100 player-seasons):", "",
         md_table(rate_change.round(1).rename_axis("league")), "",
         "Share of injuries with a known area, and the share with no known area, by league and era:", "",
         md_table(body_league["share of known"].join(body_league[("unknown", "share of all")].rename("unknown (share of all)"))
                  .round(3).reset_index(), index=False), "",
         f"![Body areas by league and era](figures/{body_league_fig})", "", "## 3. Seasons", "",
         md_table(fmt(by_season)[["player-seasons", "injuries / player-season", "days lost / player-season", "severe share"]].join(unknown_share.round(3)).rename_axis("season")), "",
         f"![Trend](figures/{trend_fig})", "", f"![Shares](figures/{shares_fig})", "", "## 4. Leagues", "",
         md_table(fmt(by_league)[COLS].rename_axis("league")), ""]
for name, (rr, n) in within.items():
    text += [f"{name.capitalize()} RR within each league:", "", md_table(rr.round(2).rename_axis("league")), ""]
text += [f"![Within league](figures/{league_fig})", "", "## 5. Adjusting step by step (RR, 95% CI over clubs)", "",
         "Each row adds one adjustment; per-match rows use team matches (all competitions) as exposure.", ""]
for name, t in adjusted.items():
    text += [f"### {name.capitalize()}", "", md_table(t.reset_index(), index=False), ""]
for name, m in mix.items():
    text += [f"{name.capitalize()}: squad and team profile", "", md_table(m.rename_axis(name)), ""]
text += ["## 6. Team strength and workload", ""]
for name in strength_rr:
    text += [f"{name.capitalize()} RR within strength thirds:", "", md_table(strength_rr[name].round(2).rename_axis("strength")), "",
             f"{name.capitalize()} RR within congestion thirds:", "", md_table(congestion_rr[name].round(2).rename_axis("congestion")), ""]
text += ["By congestion:", "", md_table(fmt(by_congestion)[COLS].rename_axis("congestion")), "",
         "### Same club, with and without the style", "",
         "Injury RR in a style's seasons ÷ the same clubs' RR in their other seasons (95% CI over clubs):", "",
         md_table(same_club.round(2).reset_index(), index=False), "",
         "Seasons right after a club switched into or out of a style (RR against league × season × strength):", "",
         md_table(switches.round(2).reset_index(), index=False), "",
         "## 7. Fitness absences (Bundesliga, secondary outcome)", ""]
for name, f in fitness.items():
    text += [md_table(f.rename_axis(name)), ""]
text += ["## 8. Sensitivity checks (injury RR against league × season)", ""]
for name, t in sensitivity.items():
    text += [f"### {name.capitalize()}", "", md_table(t.rename_axis("variant")), ""]
text += ["### Alternative clusterings (Phase 4)", ""]
for ph, t in alt_clusterings.items():
    text += [f"{ph.capitalize()}:", "", md_table(t.reset_index(), index=False), ""]
text += ["### Days lost counted three ways (days RR)", ""]
for name, t in days_sensitivity.items():
    text += [f"{name.capitalize()}:", "", md_table(t.rename_axis("days lost")), ""]
text += ["Median days per injury (overlaps merged):", "", md_table(median_days.round(1).to_frame().rename_axis(["grouping", "style"])), ""]
text += ["## 9. Style cards (core team-seasons)", ""]
for ph, title in [("attack", "Attacking styles"), ("defence", "Defensive styles")]:
    text += [f"### {title}", ""]
    for name, c in cards[ph].iterrows():
        text.append(f"- **{name}** ({c['team-seasons']} team-seasons, core {c['core']}): {c['how it plays']}. {c['in numbers (core)']}. "
                    f"Back-three minutes {c['back-three minutes']}; points/match {c['points/match']}; most often with {c['most often with']}. "
                    f"Typical: {c['typical 2014–18']} | {c['typical 2018–22']} | {c['typical 2022–26']}.")
    text.append("")
text += ["Injury RR, all teams vs core teams only:", ""]
for name, t in core_check.items():
    text += [md_table(t.rename_axis(name)), ""]
text += ["## 10. How the ways of attacking and defending changed", "",
         md_table(era_all.T.round(2).assign(shape=shapes["all leagues"]).rename_axis("dimension (z)")), "",
         md_table(shapes.rename_axis("dimension")), "", md_table(raw_by_era.round(3).rename_axis("measure (all leagues)")), "",
         f"![Dimensions](figures/{dims_fig})", "", "## 11. How teams move between styles", ""]
for ph, tr in transitions.items():
    text += [f"{ph.title()}: style kept from one season to the next {tr['kept']:.0%}.", "",
             md_table((100 * tr["share"]).round(0).rename_axis(f"{ph} \u2192 next season")), "", md_table(tr["flows"], index=False), ""]
text += ["## 12. Style mix and injuries per era", ""]
for name in mix_era:
    text += [f"### {name.capitalize()}", "", md_table((100 * mix_era[name]).round(1).rename_axis("era")), "",
             "Injury RR per era (fixed league baselines):", "", md_table(rr_era[name].round(2).rename_axis("era")), ""]
text += ["## 13. Where the injury trend comes from (Kitagawa decomposition)", "",
         md_table(main_dec.drop(columns=["scope", "styles"]).round(3), index=False), "",
         f"Style-mix part, {FIRST_LAST}, by which phase's styles are used:", "", md_table(phase_dec.round(3).rename_axis("outcome")), "",
         f"![Decomposition](figures/{decomp_fig})", "",
         "## 14. Style dimensions vs injury outcomes (60 league-seasons, within league)", "",
         "Levels:", "", md_table(link.rename_axis("dimension")), "",
         "Season-to-season changes (n = 55):", "", md_table(link_changes.rename_axis("dimension")), "",
         f"![Links](figures/{link_fig})", "", "## 15. One story per league", "", *[f"{s}\n" for s in stories.values()], "",
         "## 16. Clearer results (fixed in advance, not tuned on outcomes)", "",
         "### Shrinkage of small cells (empirical Bayes)", "",
         "Attack × defence grid, raw vs shrunk injury RR (weight on own data: 1 = kept as is, 0 = fully pulled to the average):", "",
         md_table(grid_shrunk[["team-seasons", "RR raw", "RR shrunk", "RR weight on own data"]].round(2).rename_axis(["attack", "defence"])), "",
         *[x for name, t in within_shrunk.items() for x in (f"{name.capitalize()} RR within each league, shrunk:", "",
           md_table(t["RR shrunk"].unstack().reindex(index=LEAGUES, columns=GROUPINGS[name][1]).round(2).rename_axis("league")), "")],
         "### 3-season rolling averages", "", md_table(trend.join(trend_rolling).round(3).rename_axis("season")), "",
         f"### Body-area patterns surviving false-discovery-rate correction ({int(body_fdr.finding.sum())} of {len(body_fdr)}; permutation test within league-seasons; "
         "Mantel–Haenszel odds ratio over league × era, Benjamini–Hochberg q < 0.05)", "",
         md_table(body_findings[["grouping", "style", "area", "MH odds ratio", "q (BH)", "leagues above 1"]].round(4), index=False), "",
         "### Who carries a style's excess: RR by position and age band", "",
         *[x for name in ["attacking style", "defensive style"] for by in ["position", "age_band"] for x in (
           f"{name.capitalize()} × {by.replace('_', ' ')}:", "",
           md_table(breakdown[(breakdown.grouping == name) & (breakdown.by == by)].pivot(index="style", columns="group", values="RR")
                    .reindex(GROUPINGS[name][1]).round(2).rename_axis(name)), "")],
         "## 17. Outputs", "",
         f"- `data/{PHASE}/player_seasons.parquet`: the player-club-season table with styles, formation, strength, workload, age, position and injuries.", ""]
(REPORTS_DIR / "05_injury_analysis.md").write_text("\n".join(text), encoding="utf-8")
print("wrote", REPORTS_DIR / "05_injury_analysis.md")
