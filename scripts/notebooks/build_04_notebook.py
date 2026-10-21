"""Writes notebooks/04_clustering.ipynb: Phase 4 as a sequence of steps, each with notes, code and a check."""

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
# Phase 4: Clustering (data mining)

**Goal:** describe each team-season's **playing style per phase of play**, as football analysis does: how it
**attacks** (in possession) and how it **defends** (out of possession) (Fernandez-Navarro et al. 2016; Demir et al.).
Each phase is clustered with **K-means** on its four dimensions from Phase 3 (k chosen by elbow, silhouette,
Davies–Bouldin, Calinski–Harabasz, stability and interpretability) and compared with **hierarchical clustering
(Ward)**. A team-season's style is the pair, e.g. *Positional possession · High press, high line*. Formation (back
three) is reported per style, not clustered. Team strength and workload are shown, not clustered.

**Steps**
1. Phase dimensions
2. K-means for k = 2…10 per phase: quality measures, stability (bootstrap ARI and per-cluster Jaccard), Ward
3. Profiles at k = 4 per phase: centroids, typical teams, strength, workload, formation, leagues
4. Names (by rule) and the combined style; saved clusters
5. How the attacking and defensive styles combine
6. 2-D views (PCA, for visualisation only)
7. Report

**Input:** `data/03_features/` (phase dimensions, features), `us_team_matches` (points, strength check only).
**Outputs:** `data/04_clusters/`, `reports/04_clustering.md`, `reports/figures/04_*.png`.
''')

code('''
import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import Image, display
from matplotlib.colors import LinearSegmentedColormap
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score

sys.path.insert(0, str(Path.cwd().parent))  # project root, for the analysis package
from analysis.config import DATA_DIR, FIGURES_DIR, REPORTS_DIR, phase_dir
from analysis.load import league_from_understat, read_table
from analysis.report import md_table

pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 220)
pd.set_option("display.max_colwidth", 140)

PHASE = "04_clusters"
OUT_DIR = phase_dir(PHASE)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
SEED = 42
K_RANGE = range(2, 11)
N_INIT = 50  # K-means restarts per fit; the best (lowest inertia) is kept
N_BOOT = 50  # bootstrap resamples for stability
MIN_JACCARD = 0.6  # every cluster's mean bootstrap Jaccard at least this (Hennig 2007)
MIN_SHARE = 0.03  # no cluster smaller than 3% of team-seasons
MAIN_K = {"attack": 4, "defence": 4}  # agreed with the user after reading step 2 (see DECISIONS.md)
RARE_COMBINATION = 40  # combined styles with fewer team-seasons are flagged as rare
PHASES = ["attack", "defence"]

# Chart palette: validated reference palette (dataviz skill), categorical slots in fixed order.
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]
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
''')

# ---- step 1
md('''
## Step 1. Phase dimensions

Four attacking (possession, patience, verticality, directness) and four defensive (press, high line, territory
conceded, aggression) dimensions from Phase 3, each standardised.
''')
code('''
style_dims = pd.read_parquet(DATA_DIR / "03_features" / "style_dimensions.parquet")
features = pd.read_parquet(DATA_DIR / "03_features" / "team_season_features.parquet")
assert (style_dims[["season", "tm_club_id"]].to_numpy() == features[["season", "tm_club_id"]].to_numpy()).all()
DIMS = {ph: [c for c in style_dims.columns if c.startswith(f"{ph}_")] for ph in PHASES}
X = {ph: style_dims[cols].to_numpy() for ph, cols in DIMS.items()}
assert not any(np.isnan(x).any() for x in X.values())
style_dims[DIMS["attack"] + DIMS["defence"]].describe().round(2).T
''')

# ---- step 2
md('''
## Step 2. Choosing k per phase

For each phase and k: K-means with 50 starts (fixed seed), inertia (elbow), silhouette (higher better),
Davies–Bouldin (lower better), Calinski–Harabasz (higher better); **stability** by refitting on 50 bootstrap samples:
overall adjusted Rand index (ARI) and the **per-cluster Jaccard** (Hennig 2007: < 0.5 dissolves, ≥ 0.6 a pattern,
≥ 0.75 stable); and agreement with **Ward** (ARI). A k is usable when every cluster reaches Jaccard 0.6 and none is
under 3% of team-seasons.
''')
code('''
rng = np.random.default_rng(SEED)
boot_idx = [rng.integers(0, len(style_dims), len(style_dims)) for _ in range(N_BOOT)]
kmeans, summary_rows, jaccard = {}, [], {}


def bootstrap(x: np.ndarray, ref: np.ndarray, k: int) -> tuple[list[float], np.ndarray]:
    aris, jac = [], np.zeros((N_BOOT, k))
    for b, idx in enumerate(boot_idx):
        fit = KMeans(n_clusters=k, n_init=10, random_state=SEED + b).fit(x[idx])
        aris.append(adjusted_rand_score(ref, fit.predict(x)))
        inside = np.unique(idx)
        both = np.zeros((k, k))
        np.add.at(both, (ref[inside], fit.predict(x[inside])), 1)
        jac[b] = (both / (both.sum(axis=1, keepdims=True) + both.sum(axis=0, keepdims=True) - both)).max(axis=1)
    return aris, jac.mean(axis=0)


for ph, x in X.items():
    for k in K_RANGE:
        km = KMeans(n_clusters=k, n_init=N_INIT, random_state=SEED).fit(x)
        kmeans[(ph, k)] = km
        aris, jac = bootstrap(x, km.labels_, k)
        jaccard[(ph, k)] = jac
        ward = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(x)
        summary_rows.append({
            "phase": ph, "k": k, "inertia": km.inertia_, "silhouette": silhouette_score(x, km.labels_),
            "davies_bouldin": davies_bouldin_score(x, km.labels_), "calinski_harabasz": calinski_harabasz_score(x, km.labels_),
            "stability (mean ARI)": np.mean(aris), "min cluster Jaccard": jac.min(),
            "Ward vs K-means (ARI)": adjusted_rand_score(km.labels_, ward), "smallest cluster": np.bincount(km.labels_).min(),
        })
summary = pd.DataFrame(summary_rows)
summary["usable"] = (summary["min cluster Jaccard"] >= MIN_JACCARD) & (summary["smallest cluster"] >= MIN_SHARE * len(style_dims)) & (summary.k >= 3)
for ph in PHASES:
    assert summary.query("phase == @ph and k == @MAIN_K[@ph]").usable.all(), f"k = {MAIN_K[ph]} not usable for {ph}"
summary.round(3)
''')
code('''
fig, axes = plt.subplots(2, 5, figsize=(19, 6.4), sharex=True)
measures = [("inertia", "Inertia (elbow)"), ("silhouette", "Silhouette ↑"), ("davies_bouldin", "Davies–Bouldin ↓"),
            ("calinski_harabasz", "Calinski–Harabasz ↑"), ("min cluster Jaccard", "Weakest cluster (Jaccard) ↑")]
for row, ph in enumerate(PHASES):
    d = summary[summary.phase == ph]
    for ax, (col, title) in zip(axes[row], measures):
        ax.plot(d.k, d[col], color=SERIES[row], marker="o", markersize=6)
        ax.axvline(MAIN_K[ph], color=MUTED, linewidth=1, linestyle=":")
        ax.set_title(f"{ph}: {title}", loc="left")
        ax.set_xticks(list(K_RANGE))
    axes[row, 4].axhline(MIN_JACCARD, color=MUTED, linewidth=1, linestyle="--")
for ax in axes[1]:
    ax.set_xlabel("k")
fig.tight_layout()
quality_fig = save(fig, "04_k_selection.png")

fig, axes = plt.subplots(1, 2, figsize=(14, 4))
for ax, ph in zip(axes, PHASES):
    dendrogram(linkage(X[ph], method="ward"), truncate_mode="lastp", p=30, ax=ax, color_threshold=0,
               above_threshold_color=MUTED, no_labels=True)
    ax.set_title(f"Ward dendrogram, {ph} (last 30 merges)", loc="left")
    ax.set_ylabel("merge distance")
    ax.grid(axis="x", visible=False)
fig.tight_layout()
dendro_fig = save(fig, "04_dendrograms.png")
''')

# ---- step 3
md('''
## Step 3. Profiles at k = 4 per phase

For each phase: centroids, per-cluster stability, the team-seasons closest to each centroid, team strength (points
and npxG per match), workload, the share of minutes in a back three and the league mix.
''')
code('''
um = read_table("us_team_matches")
points = (um.assign(league=um.league.map(league_from_understat), season=um.season.astype(int), pts=um.pts.astype(float))
          .groupby(["league", "season", "team_id"]).pts.mean().rename("points_pm").reset_index().rename(columns={"team_id": "us_team_id"}))
keys = pd.read_csv(DATA_DIR / "01_entities" / "team_seasons.csv", dtype={"tm_club_id": str, "us_team_id": str})
roles = pd.read_csv(DATA_DIR / "03_features" / "feature_roles.csv")
EXPOSURE = roles[(roles.role == "exposure") & (roles.status == "kept")].feature.tolist()
base = (features.drop(columns="back_three_share").join(style_dims.drop(columns=["league", "season", "season_key", "tm_club_id", "club"]))
        .merge(keys[["league", "season", "tm_club_id", "us_team_id"]], on=["league", "season", "tm_club_id"])
        .merge(points, on=["league", "season", "us_team_id"], how="left"))
assert base.points_pm.notna().all() and len(base) == len(style_dims)


def eta_squared(values: pd.Series, groups: pd.Series) -> float:
    grand = values.mean()
    between = sum(len(v) * (v.mean() - grand) ** 2 for _, v in values.groupby(groups))
    return between / ((values - grand) ** 2).sum()


profiles = {}
for ph in PHASES:
    k, km = MAIN_K[ph], kmeans[(ph, MAIN_K[ph])]
    df = base.assign(cluster=km.labels_ + 1)
    dist = np.linalg.norm(X[ph] - km.cluster_centers_[km.labels_], axis=1)
    g = df.groupby("cluster")
    profiles[ph] = {
        "df": df,
        "centroid": g[DIMS[ph]].mean().rename(columns=lambda c: c.split("_", 1)[1]),
        "context": pd.concat([g.size().rename("n"), pd.Series(jaccard[(ph, k)].round(2), index=range(1, k + 1), name="Jaccard"),
                              g.points_pm.mean().round(2).rename("points/match"), g.npxg_pm.mean().round(2).rename("npxG/match"),
                              g.back_three_share.mean().round(2).rename("back-three minutes"), g[EXPOSURE].mean().round(2)], axis=1),
        "examples": (df.assign(dist=dist).sort_values("dist").groupby("cluster").head(4)
                     .assign(team=lambda d: d.club + " " + d.season_key).groupby("cluster").team.apply(", ".join)),
        "leagues": pd.crosstab(df.cluster, df.league, normalize="index").round(2),
        "eta2_points": eta_squared(df.points_pm, df.cluster),
    }
for ph, p in profiles.items():
    print(f"\\n==================== {ph}, k = {MAIN_K[ph]} (points eta² = {p['eta2_points']:.2f}) ====================")
    display(p["centroid"].round(2))
    display(pd.concat([p["context"], p["examples"].rename("closest to centroid")], axis=1))
    display(p["leagues"])
''')

# ---- step 4
md('''
## Step 4. Names and the combined style

Names come from football analysis vocabulary and are given **by rule** (applied in order, each picking among the
clusters not yet named), so they stay with the right cluster if K-means numbers them differently.

| Phase | Name | Rule | Meaning |
|---|---|---|---|
| attack | Positional possession | highest possession | dominates the ball, patient build-up |
| attack | Counter-attack | highest verticality | little of the ball, fast vertical attacks |
| attack | Direct play | highest directness | long-range shots and set plays, low possession |
| attack | Build-up into the box | the rest | moderate possession, works the ball into the box |
| defence | High press, high line | highest high line | presses high, line exposed to counters |
| defence | Low block | most territory conceded | sits deep, lets the opponent near the box |
| defence | Aggressive duel press | highest aggression | presses through fouls and duels |
| defence | Compact mid-block | the rest | medium press, low line, concedes little |
''')
code('''
NAMING = {
    "attack": [("Positional possession", "possession", "max"), ("Counter-attack", "verticality", "max"),
               ("Direct play", "directness", "max"), ("Build-up into the box", None, None)],
    "defence": [("High press, high line", "high_line", "max"), ("Low block", "territory_conceded", "max"),
                ("Aggressive duel press", "aggression", "max"), ("Compact mid-block", None, None)],
}


def name_clusters(centroids: pd.DataFrame, rules: list) -> dict[int, str]:
    remaining, names = list(centroids.index), {}
    for name, dim, how in rules:
        if dim is None:
            assert len(remaining) == 1
            pick = remaining[0]
        else:
            col = centroids.loc[remaining, dim]
            pick = col.idxmax() if how == "max" else col.idxmin()
        names[pick] = name
        remaining.remove(pick)
    return names


NAMES = {ph: name_clusters(profiles[ph]["centroid"], NAMING[ph]) for ph in PHASES}
ORDER = {ph: [n for n, _, _ in NAMING[ph]] for ph in PHASES}
out = base[["league", "season", "season_key", "tm_club_id", "club", "back_three_share"]].assign(
    attack_cluster=profiles["attack"]["df"].cluster, attack_style=profiles["attack"]["df"].cluster.map(NAMES["attack"]),
    defence_cluster=profiles["defence"]["df"].cluster, defence_style=profiles["defence"]["df"].cluster.map(NAMES["defence"]))
out["style"] = out.attack_style + " · " + out.defence_style
counts = out["style"].value_counts()
out["rare_style"] = out["style"].map(counts) < RARE_COMBINATION
out["back_three"] = out.back_three_share >= 0.5
assert out.notna().all().all()
out.to_parquet(OUT_DIR / "team_season_clusters.parquet", index=False)
summary.to_csv(OUT_DIR / "k_selection.csv", index=False)
for ph in PHASES:
    display(pd.Series(NAMES[ph], name=f"{ph} style").to_frame())
print(f"saved {len(out)} team-seasons; {(~out.rare_style).sum()} in {counts[counts >= RARE_COMBINATION].size} combined styles "
      f"with ≥ {RARE_COMBINATION} team-seasons, {out.rare_style.sum()} in rare ones")
''')

# ---- step 5
md('''
## Step 5. How the attacking and defensive styles combine

Team-seasons, points per match and back-three minutes per combination. Typical teams are the ones closest to the
combination's centre in both phases.
''')
code('''
combo = pd.crosstab(out.attack_style, out.defence_style).loc[ORDER["attack"], ORDER["defence"]]
both = np.hstack([X["attack"], X["defence"]])
combo_rows = []
for style, g in out.groupby("style"):
    centre = both[g.index].mean(axis=0)
    d = np.linalg.norm(both[g.index] - centre, axis=1)
    typical = g.assign(d=d).sort_values("d").head(4).apply(lambda r: f"{r.club} {r.season_key}", axis=1)
    combo_rows.append({"style": style, "team-seasons": len(g), "rare": len(g) < RARE_COMBINATION,
                       "points/match": round(base.loc[g.index, "points_pm"].mean(), 2),
                       "back-three minutes": round(g.back_three_share.mean(), 2), "typical": ", ".join(typical)})
combos = pd.DataFrame(combo_rows).sort_values("team-seasons", ascending=False).set_index("style")
display(combo)
combos
''')
code('''
# Figure: centroid heatmaps per phase (rows named), side by side.
fig, axes = plt.subplots(1, 2, figsize=(15, 3.6))
for ax, ph in zip(axes, PHASES):
    cz = profiles[ph]["centroid"].rename(index=NAMES[ph]).loc[ORDER[ph]]
    ax.imshow(cz.to_numpy(), cmap=DIVERGING, vmin=-2, vmax=2, aspect="auto")
    ax.set_xticks(range(cz.shape[1]), [c.replace("_", " ") for c in cz.columns], rotation=30, ha="right")
    ax.set_yticks(range(cz.shape[0]), cz.index)
    ax.grid(False)
    for (i, j), v in np.ndenumerate(cz.to_numpy()):
        ax.text(j, i, f"{v:+.1f}", ha="center", va="center", fontsize=9, color="white" if abs(v) > 1.3 else INK)
    ax.set_title(f"{ph.title()} styles: centroids (z)", loc="left")
fig.tight_layout()
heat_fig = save(fig, "04_centroids.png")
''')

# ---- step 6
md('''
## Step 6. 2-D views

PCA of each phase's four dimensions, **only to draw** the clusters. Marker shapes and labels carry identity
alongside colour.
''')
code('''
fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))
for ax, ph in zip(axes, PHASES):
    pca = PCA(n_components=2, random_state=SEED).fit(X[ph])
    xy, ev = pca.transform(X[ph]), pca.explained_variance_ratio_
    labels = profiles[ph]["df"].cluster.to_numpy()
    for i, name in enumerate(ORDER[ph]):
        c = next(c for c, n in NAMES[ph].items() if n == name)
        m = labels == c
        ax.scatter(xy[m, 0], xy[m, 1], s=14, color=SERIES[i], marker=MARKERS[i], alpha=0.6, edgecolors=SURFACE,
                   linewidths=0.4, label=name)
        cx, cy = xy[m].mean(axis=0)
        ax.text(cx, cy, str(i + 1), ha="center", va="center", fontsize=11, fontweight="bold", color=INK,
                bbox={"boxstyle": "circle,pad=0.25", "facecolor": SURFACE, "edgecolor": SERIES[i], "linewidth": 2})
    ax.set_xlabel(f"PC1 ({ev[0]:.0%} of variance)")
    ax.set_ylabel(f"PC2 ({ev[1]:.0%} of variance)")
    ax.set_title(f"{ph.title()} styles", loc="left")
    ax.legend(frameon=False, fontsize=8, markerscale=1.5, loc="best")
fig.tight_layout()
pca_fig = save(fig, "04_pca.png")
''')

# ---- step 7
md('''
## Step 7. Report
''')
code('''
cols = ["phase", "k", "silhouette", "davies_bouldin", "calinski_harabasz", "stability (mean ARI)", "min cluster Jaccard",
        "Ward vs K-means (ARI)", "smallest cluster", "usable"]
text = [
    "# Phase 4: Clustering",
    "",
    f"Generated {date.today().isoformat()} by `notebooks/04_clustering.ipynb`, where each step is shown with its checks.",
    "",
    "## Approach",
    "",
    "Playing style per **phase of play** (Fernandez-Navarro et al. 2016; Demir et al.): attacking style from four "
    "attacking dimensions, defensive style from four defensive dimensions, each clustered with K-means (k = 4) and "
    "checked against Ward. A team-season's style is the pair. Formation (back three) is reported, not clustered.",
    "",
    "## 1. Choosing k",
    "",
    md_table(summary[cols].round(3), index=False),
    "",
    f"![k selection](figures/{quality_fig})",
    "",
    f"![Ward dendrograms](figures/{dendro_fig})",
    "",
]
for ph in PHASES:
    p = profiles[ph]
    ctx = pd.concat([p["context"], p["examples"].rename("closest to centroid")], axis=1)
    ctx.insert(0, "style", ctx.index.map(NAMES[ph]))
    cen = p["centroid"].copy()
    cen.insert(0, "style", cen.index.map(NAMES[ph]))
    text += [f"## {2 if ph == 'attack' else 3}. {ph.title()} styles (k = {MAIN_K[ph]})", "",
             f"Share of team strength (points per match) explained: eta² = {p['eta2_points']:.2f}.", "",
             md_table(ctx.rename_axis("cluster")), "", "Centroids (z):", "", md_table(cen.round(2).rename_axis("cluster")), "",
             "League mix:", "", md_table(p["leagues"].rename(index=NAMES[ph]).rename_axis("style")), ""]
text += ["## 4. Combined styles", "", md_table(combo.rename_axis("attack \\\\ defence")), "",
         md_table(combos.rename_axis("style")), "", f"![Centroids](figures/{heat_fig})", "", f"![PCA](figures/{pca_fig})", ""]
(REPORTS_DIR / "04_clustering.md").write_text("\\n".join(text), encoding="utf-8")
print("wrote", REPORTS_DIR / "04_clustering.md")
''')

for i, cell in enumerate(cells):
    cell["id"] = f"clustering-{i:02d}"
meta = json.loads((ROOT / "notebooks/01_entities.ipynb").read_text())["metadata"]
nb = {"cells": cells, "metadata": meta, "nbformat": 4, "nbformat_minor": 5}
(ROOT / "notebooks/04_clustering.ipynb").write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
print(len(cells), "cells")
