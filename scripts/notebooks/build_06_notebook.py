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
''')
code('''
cited = sorted(set(re.findall(r"figures/([\\w.-]+\\.png)", SUMMARY)))
missing = [f for f in cited if not (REPORTS_DIR / "figures" / f).exists()]
assert not missing, missing
print(f"{len(cited)} figures cited, all present:", ", ".join(cited))
''')

for i, cell in enumerate(cells):
    cell["id"] = f"report-{i:02d}"
meta = json.loads((ROOT / "notebooks/01_entities.ipynb").read_text())["metadata"]
nb = {"cells": cells, "metadata": meta, "nbformat": 4, "nbformat_minor": 5}
(ROOT / "notebooks/06_report.ipynb").write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
print(len(cells), "cells")
