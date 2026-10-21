"""Writes notebooks/06_report.ipynb: checks that reports/summary.md agrees with the data and that its figures exist."""

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
# Phase 6: Report material

`reports/summary.md` is the text for the course report. This notebook keeps it honest: it recomputes the headline
numbers from the phase outputs and checks them against the values written in the summary, and it checks that every
figure the summary cites exists.

**Steps**
1. Headline numbers recomputed from the data
2. Comparison with the summary
3. Figures cited by the summary
4. Data for the results dashboard
''')
code('''
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd().parent))  # project root, for the analysis package
from analysis.config import DATA_DIR, REPORTS_DIR

SUMMARY = (REPORTS_DIR / "summary.md").read_text(encoding="utf-8")
''')

md('''
## Step 1. Headline numbers recomputed from the data

Counts, style shares per era, raw rates by style and the league-adjusted rate ratios (point estimates; the CIs are
in the Phase 5 notebook).
''')
code('''
ps = pd.read_parquet(DATA_DIR / "05_injury_analysis" / "player_seasons.parquet")
clusters = pd.read_parquet(DATA_DIR / "04_clusters" / "team_season_clusters.parquet")
features = pd.read_parquet(DATA_DIR / "03_features" / "team_season_features.parquet")
era = lambda s: "2014–18" if s < 2018 else "2018–22" if s < 2022 else "2022–26"
clusters["era"] = clusters.season.map(era)


def rr(df: pd.DataFrame, by: str, col: str = "injuries", exp: str = "exp_inj") -> pd.Series:
    g = df.groupby(by)[[col, exp]].sum()
    return (g[col] / g[exp]).round(2)


numbers = {
    "team-seasons": len(clusters), "player-club-seasons": len(ps), "injuries > 7 days": int(ps.injuries.sum()),
    "positional possession share 2014–18 (%)": round(100 * (clusters[clusters.era == "2014–18"].attack_style == "Positional possession").mean()),
    "positional possession share 2022–26 (%)": round(100 * (clusters[clusters.era == "2022–26"].attack_style == "Positional possession").mean()),
    "back-three minutes 2014–18 (%)": round(100 * features[features.season < 2018].back_three_share.mean()),
    "back-three minutes 2022–26 (%)": round(100 * features[features.season >= 2022].back_three_share.mean()),
    "RR positional possession": rr(ps, "attack_style")["Positional possession"],
    "RR counter-attack": rr(ps, "attack_style")["Counter-attack"],
    "RR high press, high line": rr(ps, "defence_style")["High press, high line"],
    "RR low block": rr(ps, "defence_style")["Low block"],
    "days RR positional possession": rr(ps, "attack_style", "days_lost", "exp_days")["Positional possession"],
    "injuries / player-season 2014–18": round(ps[ps.era == "2014–18"].injuries.mean(), 3),
    "injuries / player-season 2022–26": round(ps[ps.era == "2022–26"].injuries.mean(), 3),
}
pd.Series(numbers, name="value").to_frame()
''')

md('''
## Step 2. Comparison with the summary

Each number must appear in `summary.md` exactly as recomputed (as written there).
''')
code('''
EXPECTED_TEXT = {
    "team-seasons": "1,170 team-seasons", "player-club-seasons": "36,525", "injuries > 7 days": "24,581",
    "positional possession share 2014–18 (%)": "from {}% to", "positional possession share 2022–26 (%)": "to {}% of team-seasons",
    "back-three minutes 2014–18 (%)": "rose from {}%", "back-three minutes 2022–26 (%)": "to {}% of minutes",
    "RR positional possession": "rate ratio {:.2f}", "RR counter-attack": "**{:.2f} (", "RR high press, high line": "**{:.2f} (",
    "RR low block": "**{:.2f} (", "days RR positional possession": "**{:.2f} (",
    "injuries / player-season 2014–18": "from {:.3f}", "injuries / player-season 2022–26": "to {:.3f} per player-season",
}
rows = []
for key, pattern in EXPECTED_TEXT.items():
    value = numbers[key]
    text = pattern.format(value) if "{" in pattern else pattern
    rows.append({"number": key, "value": value, "looked for": text, "in summary": text in SUMMARY})
check = pd.DataFrame(rows).set_index("number")
assert check["in summary"].all(), check[~check["in summary"]]
check
''')

md('''
## Step 3. Figures cited by the summary
4. Data for the results dashboard
''')
code('''
cited = sorted(set(re.findall(r"figures/([\\w.-]+\\.png)", SUMMARY)))
missing = [f for f in cited if not (REPORTS_DIR / "figures" / f).exists()]
assert not missing, missing
print(f"{len(cited)} figures cited, all present:", ", ".join(cited))
''')

md('''
## Step 4. Data for the results dashboard

The interactive dashboard (an Artifact) shows only numbers from these files, built here from the phase outputs:
style profiles and the cluster map (PCA of each phase's dimensions, for drawing only), style shares and dimension
means per season, injury rate ratios, the attack × defence grid, body areas, the season trend, the decomposition and
the league stories. Written to `data/06_report/dashboard/` as JSON row lists.
''')
code('''
import json
from sklearn.decomposition import PCA
from analysis.config import phase_dir

OUT = phase_dir("06_report") / "dashboard"
OUT.mkdir(exist_ok=True)
T = DATA_DIR / "05_injury_analysis" / "tables"
style_dims = pd.read_parquet(DATA_DIR / "03_features" / "style_dimensions.parquet")
ATTACK = ["Positional possession", "Build-up into the box", "Counter-attack", "Direct play"]
DEFENCE = ["High press, high line", "Compact mid-block", "Aggressive duel press", "Low block"]
PHASES = {"attack": ("attack_style", ATTACK), "defence": ("defence_style", DEFENCE)}
LEAGUES = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
r = lambda x, n=3: None if pd.isna(x) else round(float(x), n)
files = {}

# Cluster map: PCA of each phase's four dimensions (drawing only).
rows = []
for ph, (col, order) in PHASES.items():
    dims = [c for c in style_dims.columns if c.startswith(f"{ph}_")]
    xy = PCA(n_components=2, random_state=42).fit_transform(style_dims[dims].to_numpy())
    for (_, t), (x, y) in zip(clusters.iterrows(), xy):
        rows.append({"phase": ph, "style": t[col], "league": t.league, "club": t.club, "season": t.season_key, "pc1": r(x), "pc2": r(y)})
files["cluster_map"] = rows

# Style profiles: cards from Phase 5 plus each style's injury rate ratios.
rows = []
for ph, (col, order) in PHASES.items():
    cards = pd.read_csv(T / f"cards_{ph}.csv", index_col=0)
    rates = pd.read_csv(T / f"rates_{'attacking' if ph == 'attack' else 'defensive'}_style.csv", index_col=0)
    for i, style in enumerate(order):
        c, q = cards.loc[style], rates.loc[style]
        rows.append({"phase": ph, "style": style, "order": i, "team_seasons": int(c["team-seasons"]), "core": c["core"],
                     "how": c["how it plays"], "numbers": c["in numbers (core)"], "back_three": c["back-three minutes"],
                     "points": r(c["points/match"], 2), "paired_with": c["most often with"],
                     "typical_2014_18": c["typical 2014–18"], "typical_2018_22": c["typical 2018–22"], "typical_2022_26": c["typical 2022–26"],
                     "rr": r(q["RR"], 2), "rr_low": r(q["RR low"], 2), "rr_high": r(q["RR high"], 2), "days_rr": r(q["days RR"], 2)})
files["styles"] = rows

# Style shares per season (all leagues and each league).
rows = []
for ph, (col, order) in PHASES.items():
    for league, d in [("All leagues", clusters)] + [(lg, clusters[clusters.league == lg]) for lg in LEAGUES]:
        share = pd.crosstab(d.season_key, d[col], normalize="index").reindex(columns=order, fill_value=0)
        rows += [{"league": league, "season": s, "phase": ph, "style": st, "share": r(share.loc[s, st])} for s in share.index for st in order]
files["style_shares"] = rows

# Dimension means per season (all leagues and each league).
dim_cols = [c for c in style_dims.columns if c.startswith(("attack_", "defence_"))]
rows = []
for league, d in [("All leagues", style_dims)] + [(lg, style_dims[style_dims.league == lg]) for lg in LEAGUES]:
    m = d.groupby("season_key")[dim_cols].mean()
    rows += [{"league": league, "season": s, "phase": c.split("_")[0], "dimension": c.split("_", 1)[1].replace("_", " "), "value": r(m.loc[s, c])}
             for s in m.index for c in dim_cols]
files["dimension_trends"] = rows

# Injury rate ratios by style and formation.
rows = []
for grouping, file, order in [("attack", "attacking_style", ATTACK), ("defence", "defensive_style", DEFENCE), ("formation", "formation", ["back three", "back four"])]:
    t = pd.read_csv(T / f"rates_{file}.csv", index_col=0).loc[order]
    rows += [{"grouping": grouping, "style": st, "order": i, "player_seasons": int(q["player-seasons"]),
              "injuries_per_ps": r(q["injuries / player-season"]), "days_per_ps": r(q["days lost / player-season"], 1),
              "severe_share": r(q["severe share"]), "rr": r(q["RR"]), "rr_low": r(q["RR low"]), "rr_high": r(q["RR high"]),
              "days_rr": r(q["days RR"]), "days_rr_low": r(q["days RR low"]), "days_rr_high": r(q["days RR high"])} for i, (st, q) in enumerate(t.iterrows())]
files["injury_rr"] = rows

g = pd.read_csv(T / "attack_defence_grid.csv")
files["grid"] = [{"attack": q.attack_style, "defence": q.defence_style, "rr": r(q.RR, 2), "days_rr": r(q["days RR"], 2),
                  "team_seasons": int(q["team-seasons"])} for _, q in g.iterrows()]

rows = []
for ph, file in [("attack", "attacking_style"), ("defence", "defensive_style")]:
    med = pd.read_csv(T / f"body_median_{file}.csv", index_col=0)
    above = pd.read_csv(T / f"body_above_{file}.csv", index_col=0)
    rows += [{"phase": ph, "style": st, "area": a, "relative": r(med.loc[st, a], 2), "leagues_above": int(above.loc[st, a])}
             for st in med.index for a in med.columns]
files["body_areas"] = rows

bs = pd.read_csv(T / "by_season.csv", index_col=0)
files["season_trend"] = [{"season": s, "injuries_per_ps": r(q["injuries / player-season"]),
                          "low": r(q["injuries / player-season"] * q["RR low"] / q["RR"]), "high": r(q["injuries / player-season"] * q["RR high"] / q["RR"]),
                          "days_per_ps": r(q["days lost / player-season"], 1), "unknown_area_share": r(q["unknown body area"])} for s, q in bs.iterrows()]

dec = pd.read_csv(T / "decomposition.csv")
dec = dec[dec.eras == "2014–18 → 2022–26"]
files["decomposition"] = [{"scope": q.scope, "outcome": q.outcome, "styles": q.styles, "from": r(q["from"]), "to": r(q.to),
                           "change": r(q.change), "style_mix": r(q["from style mix"]), "within_styles": r(q["within styles"])} for _, q in dec.iterrows()]

st = pd.read_csv(T / "league_stories.csv")
files["league_stories"] = [{"league": q.league, "story": q.story.replace("**", "")} for q in st.itertuples()]

for name, rows in files.items():
    (OUT / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
pd.Series({n: len(v) for n, v in files.items()}, name="rows").to_frame().assign(
    kb=[round((OUT / f"{n}.json").stat().st_size / 1024, 1) for n in files])
''')

for i, cell in enumerate(cells):
    cell["id"] = f"report-{i:02d}"
meta = json.loads((ROOT / "notebooks/01_entities.ipynb").read_text())["metadata"]
nb = {"cells": cells, "metadata": meta, "nbformat": 4, "nbformat_minor": 5}
(ROOT / "notebooks/06_report.ipynb").write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
print(len(cells), "cells")
