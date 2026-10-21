"""Phase 5 extension (steps 12-19): sharper style profiles and the evolution of styles vs injury trends.

Imported by build_05_notebook.py, which inserts these cells before the report step.
"""

STEPS = []


def md(text: str) -> None:
    STEPS.append(("markdown", text))


def code(text: str) -> None:
    STEPS.append(("code", text))


# ---- step 12
md('''
## Step 12. Style cards: what each style looks like on the pitch

Many team-seasons sit between two styles, so each style is described from its **core** team-seasons: those clearly
closer to their own style than to any other (distance to own centroid ≤ 80% of the distance to the next one).
Each card gives the three traits that set the style apart (largest centroid scores), the matching numbers in real
units against the all-team average, typical core teams in each era, and the family it belongs to at k = 4.
''')
code('''
CORE_RATIO = 0.8
ERAS = {range(2014, 2018): "2014–18", range(2018, 2022): "2018–22", range(2022, 2026): "2022–26"}
ERA_ORDER = list(ERAS.values())


def era_of(season: int) -> str:
    return next(label for years, label in ERAS.items() if season in years)


DIMS = ["dominance", "pressing", "counter", "high_line", "physical", "set_pieces", "long_shots", "back_three"]
RAW = {"dominance": ("deep_pm", "deep completions per match"), "pressing": ("ppda", "PPDA (lower = more pressing)"),
       "counter": ("fast_attack_share", "shots from fast attacks"), "high_line": ("conceded_fast_share", "shots conceded from fast attacks"),
       "physical": ("fouls_pm", "fouls per match"), "set_pieces": ("set_piece_share", "shots from set pieces"),
       "long_shots": ("outside_box_share", "shots from outside the box"), "back_three": ("back_three_share", "minutes in a back three")}
PHRASE = {"dominance": ("dominates the ball and plays in the opponent's half", "spends long spells without the ball"),
          "pressing": ("presses high and wins the ball back fast", "sits off and lets the opponent play"),
          "counter": ("strikes on the break", "rarely attacks fast"),
          "high_line": ("holds a high line, exposed to counters", "defends deep, rarely caught on the break"),
          "physical": ("physical: many fouls, cards and duels", "clean: few fouls and cards"),
          "set_pieces": ("relies on set pieces", "creates little from set pieces"),
          "long_shots": ("shoots from distance", "works the ball into the box"),
          "back_three": ("plays with a back three", "plays with a back four")}

style_dims = pd.read_parquet(DATA_DIR / "03_features" / "style_dimensions.parquet").rename(columns={"tm_club_id": "club_id"})
ts = (clusters.merge(style_dims[["season", "club_id"] + DIMS], on=["season", "club_id"])
      .merge(team[["season", "club_id", "points_pm", "matches_europe"]], on=["season", "club_id"])
      .merge(features[["season", "club_id"] + [r for r, _ in RAW.values()]], on=["season", "club_id"]))
ts["era"] = ts.season.map(era_of)
centroids = ts.groupby("cluster")[DIMS].mean()
dist = np.linalg.norm(ts[DIMS].to_numpy()[:, None, :] - centroids.to_numpy()[None, :, :], axis=2)
own = dist[np.arange(len(ts)), ts.cluster.to_numpy() - 1]
dist[np.arange(len(ts)), ts.cluster.to_numpy() - 1] = np.inf
ts["typicality"] = own / dist.min(axis=1)
ts["core"] = ts.typicality <= CORE_RATIO
ts["dist_own"] = own


def value(feature: str, v: float) -> str:
    return f"{100 * v:.0f}%" if feature.endswith("share") else f"{v:.1f}"


cards = []
for name in STYLE_ORDER:
    s = ts[ts.cluster_name == name]
    core = s[s.core]
    cz = core[DIMS].mean()
    top = cz.abs().sort_values(ascending=False).index[:3]
    traits = [PHRASE[d][0 if cz[d] > 0 else 1] for d in top]
    numbers = [f"{RAW[d][1]}: {value(RAW[d][0], core[RAW[d][0]].mean())} (all teams {value(RAW[d][0], ts[RAW[d][0]].mean())})" for d in top]
    typical = (core.sort_values("dist_own").groupby("era").head(2).assign(t=lambda d: d.club + " " + d.season_key)
               .groupby("era").t.apply(", ".join).reindex(ERA_ORDER).fillna("–"))
    cards.append({"style": name, "family (k = 4)": s.cluster_k4_name.mode()[0], "team-seasons": len(s),
                  "core": f"{len(core)} ({len(core) / len(s):.0%})", "how it plays": "; ".join(traits),
                  "in numbers (core)": "; ".join(numbers), "points/match": round(core.points_pm.mean(), 2),
                  "European matches": round(core.matches_europe.mean(), 1),
                  **{f"typical {e}": typical[e] for e in ERA_ORDER}})
cards = pd.DataFrame(cards).set_index("style")
ps = ps.merge(ts[["season", "club_id", "core", "era"]], on=["season", "club_id"], how="left")
cards
''')

# ---- step 13
md('''
## Step 13. Core teams only

If a style's injury pattern comes from the style itself, it should be at least as clear among its **core** teams
(clear examples of the style) as among all its teams, borderline ones included.
''')
code('''
core_check = pd.DataFrame({
    "RR, all teams": by_style["RR"], "RR, core teams": summarise(ps[ps.core], "cluster_name").loc[STYLE_ORDER, "RR"],
    "days RR, all teams": by_style["days RR"], "days RR, core teams": summarise(ps[ps.core], "cluster_name").loc[STYLE_ORDER, "days RR"],
}).round(2)
core_check["share of player-seasons in core teams"] = ps.groupby("cluster_name").core.mean().loc[STYLE_ORDER].round(2)
core_check
''')

# ---- step 14
md('''
## Step 14. How the ways of playing changed, and in what shape

Each style dimension averaged per era (2014–18, 2018–22, 2022–26) for all leagues and for each league, with the shape
of the change: **rising**, **falling**, **peak** (up then down), **dip** (down then up) or **flat** (every step smaller
than 0.1 standard deviations). Raw-unit season means show the same changes in football terms.
''')
code('''
SHAPE_TOL = 0.1


def shape(values: list[float]) -> str:
    steps = [0 if abs(d) < SHAPE_TOL else int(np.sign(d)) for d in np.diff(values)]
    if steps == [0, 0]:
        return "flat"
    if all(x >= 0 for x in steps):
        return "rising"
    if all(x <= 0 for x in steps):
        return "falling"
    return "peak" if steps == [1, -1] else "dip"


era_dims = ts.groupby(["league", "era"])[DIMS].mean()
era_all = ts.groupby("era")[DIMS].mean().loc[ERA_ORDER]
shapes = pd.DataFrame({lg: {d: shape(era_dims.loc[lg].loc[ERA_ORDER, d].tolist()) for d in DIMS} for lg in LEAGUES})
shapes.insert(0, "all leagues", [shape(era_all[d].tolist()) for d in DIMS])
raw_cols = [r for r, _ in RAW.values()]
raw_by_era = ts.groupby("era")[raw_cols].mean().loc[ERA_ORDER].T
raw_by_era.index = [RAW[d][1] for d in DIMS]
display(era_all.T.round(2).assign(shape=shapes["all leagues"]))
display(shapes)
raw_by_era.round(3)
''')
code('''
# Figure: each dimension's season mean per league (one panel per dimension, one line per league).
LEAGUE_COLORS = dict(zip(LEAGUES, SERIES))
season_dims = ts.groupby(["season_key", "league"])[DIMS].mean()
fig, axes = plt.subplots(2, 4, figsize=(18, 7), sharex=True, sharey=True)
seasons_x = sorted(ts.season_key.unique())
for ax, d in zip(axes.flat, DIMS):
    for lg in LEAGUES:
        y = season_dims[d].xs(lg, level="league").reindex(seasons_x)
        ax.plot(range(len(y)), y, color=LEAGUE_COLORS[lg], linewidth=1.8, label=lg)
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.set_title(f"{d.replace('_', ' ')} ({shapes.loc[d, 'all leagues']})", loc="left")
    ax.set_xticks(range(0, len(seasons_x), 3), [seasons_x[i][2:] for i in range(0, len(seasons_x), 3)])
axes[0, 0].legend(frameon=False, fontsize=8)
for ax in axes[:, 0]:
    ax.set_ylabel("mean score (z)")
fig.tight_layout()
dims_fig = save(fig, "05_style_dimensions_over_time.png")
''')

# ---- step 15
md('''
## Step 15. How teams move between styles

For every club that played in its Big Five league in two consecutive seasons: its style in season *t* and in *t + 1*.
The diagonal is how often a style is kept; the largest off-diagonal flows are the main routes of change.
''')
code('''
nxt = ts[["club_id", "season", "cluster_name"]].assign(season=lambda d: d.season - 1).rename(columns={"cluster_name": "next style"})
moves = ts.merge(nxt, on=["club_id", "season"]).rename(columns={"cluster_name": "style"})
transitions = pd.crosstab(moves["style"], moves["next style"]).loc[STYLE_ORDER, STYLE_ORDER]
transition_share = transitions.div(transitions.sum(axis=1), axis=0)
kept = pd.Series(np.diag(transition_share), index=STYLE_ORDER, name="kept next season")
flows = (transitions.stack().rename("clubs").reset_index().query("style != `next style`")
         .sort_values("clubs", ascending=False).head(8))
kept_by_era = moves.assign(same=moves["style"] == moves["next style"]).groupby("era").same.mean().loc[ERA_ORDER]
print(f"{len(moves):,} consecutive club-season pairs; style kept: {np.trace(transitions.to_numpy()) / transitions.to_numpy().sum():.0%}")
display((100 * transition_share).round(0))
display(kept.round(2).to_frame())
display(kept_by_era.round(2).rename("style kept, by era of the first season").to_frame())
flows
''')

# ---- step 16
md('''
## Step 16. Style mix and injuries per era

The share of team-seasons in each style per era, and each style's injury rate per era as a rate ratio against its
league's **fixed** baseline (the 12-season average), so changes over time stay visible.
''')
code('''
mix_era = pd.crosstab(ts.era, ts.cluster_name, normalize="index").loc[ERA_ORDER, STYLE_ORDER]
mix_league_era = pd.crosstab([ts.league, ts.era], ts.cluster_name, normalize="index")[STYLE_ORDER]
era_style = summarise(ps, ["era", "cluster_name"])
rr_era = era_style["RR"].unstack().loc[ERA_ORDER, STYLE_ORDER]
days_era = era_style["days RR"].unstack().loc[ERA_ORDER, STYLE_ORDER]
by_era = summarise(ps, "era").loc[ERA_ORDER]
display((100 * mix_era).round(1))
display(rr_era.round(2))
display(days_era.round(2))
fmt(by_era)
''')

# ---- step 17
md('''
## Step 17. How much of the injury trend comes from styles changing?

**Kitagawa decomposition.** The overall rate is the share-weighted sum of the rates in each cell (league × style).
Between two eras, its change splits exactly into:
- **style mix:** the change in each cell's share × its average rate (more players in styles with higher rates);
- **within styles:** the change in each cell's rate × its average share (the same styles getting more or fewer injuries).

Done for injuries, days lost, severe injuries and the two body areas with consistent style patterns (hamstring,
knee), per player-season, for all leagues together and for each league.
''')
code('''
OUTCOMES = {"injuries": "injuries", "days lost": "days_lost", "severe injuries": "severe",
            "hamstring injuries": "area: hamstring", "knee injuries": "area: knee"}


def decompose(df: pd.DataFrame, outcome: str, e0: str, e1: str, cells: list[str]) -> dict:
    def table(e):
        d = df[df.era == e]
        t = d.groupby(cells, observed=True).agg(n=(outcome, "size"), rate=(outcome, "mean"))
        return t.assign(w=t.n / t.n.sum())
    a, b = table(e0), table(e1)
    j = a[["w", "rate"]].join(b[["w", "rate"]], how="outer", lsuffix="0", rsuffix="1")
    j[["w0", "w1"]] = j[["w0", "w1"]].fillna(0)
    j["rate0"] = j.rate0.fillna(j.rate1)
    j["rate1"] = j.rate1.fillna(j.rate0)
    total = (j.w1 * j.rate1).sum() - (j.w0 * j.rate0).sum()
    mix = ((j.w1 - j.w0) * (j.rate0 + j.rate1) / 2).sum()
    within = ((j.rate1 - j.rate0) * (j.w0 + j.w1) / 2).sum()
    assert abs(total - mix - within) < 1e-9
    return {"from": (j.w0 * j.rate0).sum(), "to": (j.w1 * j.rate1).sum(), "change": total, "from style mix": mix, "within styles": within}


PAIRS = [(ERA_ORDER[0], ERA_ORDER[1]), (ERA_ORDER[1], ERA_ORDER[2]), (ERA_ORDER[0], ERA_ORDER[2])]
rows = []
for label, col in OUTCOMES.items():
    for e0, e1 in PAIRS:
        rows.append({"outcome": label, "eras": f"{e0} → {e1}", "scope": "all leagues",
                     **decompose(ps, col, e0, e1, ["league", "cluster_name"])})
        for lg in LEAGUES:
            rows.append({"outcome": label, "eras": f"{e0} → {e1}", "scope": lg,
                         **decompose(ps[ps.league == lg], col, e0, e1, ["cluster_name"])})
decomposition = pd.DataFrame(rows)
decomposition["mix share of change"] = decomposition["from style mix"] / decomposition.change
first_last = f"{ERA_ORDER[0]} → {ERA_ORDER[2]}"
display(decomposition[(decomposition.scope == "all leagues")].round(3))
decomposition[(decomposition.eras == first_last) & (decomposition.outcome == "injuries")].round(3)
''')
code('''
# Figure: change in injuries per player-season, first to last era, split into style mix and within styles.
d = decomposition[(decomposition.eras == first_last) & (decomposition.outcome == "injuries")].set_index("scope").loc[["all leagues"] + LEAGUES]
fig, ax = plt.subplots(figsize=(10, 4))
y = np.arange(len(d))[::-1]
ax.barh(y + 0.18, d["from style mix"], height=0.34, color=SERIES[0], label="from the style mix changing")
ax.barh(y - 0.18, d["within styles"], height=0.34, color=SERIES[1], label="within styles")
ax.scatter(d.change, y, color=INK, zorder=3, s=30, label="total change")
ax.axvline(0, color=MUTED, linewidth=1)
ax.set_yticks(y, d.index)
ax.set_xlabel(f"change in injuries per player-season, {first_last}")
ax.set_title("Where the injury trend comes from", loc="left")
ax.grid(axis="y", visible=False)
ax.legend(frameon=False, fontsize=8, loc="lower right")
decomp_fig = save(fig, "05_trend_decomposition.png")
''')

# ---- step 18
md('''
## Step 18. Style dimensions vs injury outcomes across league-seasons

For the 60 league-seasons: the league's average style scores against its injury outcomes. Leagues differ in how
they record injuries, so the correlations are **within league** (both sides centred on the league's own 12-season
mean): they ask whether *a league's seasons with more of a style trait had more of an injury outcome*. Many traits
and injury labels both drift over the 12 seasons, so these level correlations partly repeat a shared time trend
(including recording changes). The stricter version correlates **season-to-season changes** within each league
(n = 55): does a league's injury outcome move in the same season its style moves? Aggregate association only.
''')
code('''
ls_dims = ts.groupby(["league", "season_key"])[DIMS].mean()
g = ps.groupby(["league", "season_key"])
known = g.injuries.sum() - g["area: unknown"].sum()
ls_out = pd.DataFrame({
    "injuries / player-season": g.injuries.mean(), "days lost / player-season": g.days_lost.mean(),
    "severe share": g.severe.sum() / g.injuries.sum(),
    "hamstring share": g["area: hamstring"].sum() / known, "knee share": g["area: knee"].sum() / known,
    "muscle share": (g["area: hamstring"].sum() + g["area: unspecified muscle"].sum() + g["area: thigh"].sum()
                     + g["area: calf/achilles/lower leg"].sum()) / known,
})
centred = lambda t: t - t.groupby(level="league").transform("mean")
cd, co = centred(ls_dims), centred(ls_out)
link = pd.DataFrame({o: {d: cd[d].corr(co[o]) for d in DIMS} for o in co.columns}).round(2)
changes = lambda t: t.groupby(level="league").diff().dropna()
dd, do = changes(ls_dims.sort_index()), changes(ls_out.sort_index())
link_changes = pd.DataFrame({o: {d: dd[d].corr(do[o]) for d in DIMS} for o in do.columns}).round(2)
strongest = link.abs().stack().sort_values(ascending=False).head(6)
display(link)
display(strongest.rename("|r|").to_frame())
link_changes
''')
code('''
# Figure: the two strongest within-league links as scatter plots (each dot a league-season, coloured by league).
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for ax, (d, o) in zip(axes, strongest.index[:2]):
    for lg in LEAGUES:
        ax.scatter(cd.xs(lg, level="league")[d], co.xs(lg, level="league")[o], color=LEAGUE_COLORS[lg], s=40,
                   edgecolors=SURFACE, linewidths=1, label=lg)
    ax.set_xlabel(f"{d.replace('_', ' ')} (vs league's 12-season mean)")
    ax.set_ylabel(f"{o} (vs league mean)")
    ax.set_title(f"r = {link.loc[d, o]:+.2f}", loc="left")
axes[0].legend(frameon=False, fontsize=8)
fig.tight_layout()
link_fig = save(fig, "05_style_injury_links.png")
''')

# ---- step 19
md('''
## Step 19. One story per league

Each league's evolution in a few sentences, assembled from steps 14–17: which styles grew and shrank, which ways of
playing changed and how, and what happened to injuries, split into the part from the style mix and the part within
styles.
''')
code('''
def pct_pts(x: float) -> str:
    return f"{100 * x:+.0f} pts"


stories = {}
first, last = ERA_ORDER[0], ERA_ORDER[2]
for lg in LEAGUES:
    m = mix_league_era.loc[lg]
    change = (m.loc[last] - m.loc[first]).sort_values()
    grew = [f"{s} ({100 * m.loc[first, s]:.0f}% → {100 * m.loc[last, s]:.0f}%)" for s in change.index[::-1][:2] if change[s] > 0.02]
    shrank = [f"{s} ({100 * m.loc[first, s]:.0f}% → {100 * m.loc[last, s]:.0f}%)" for s in change.index[:2] if change[s] < -0.02]
    moved = [f"{d.replace('_', ' ')} {shapes.loc[d, lg]}" for d in DIMS if shapes.loc[d, lg] != "flat"]
    dec = decomposition[(decomposition.scope == lg) & (decomposition.eras == first_last)].set_index("outcome")
    inj, days = dec.loc["injuries"], dec.loc["days lost"]
    ham, knee = dec.loc["hamstring injuries"], dec.loc["knee injuries"]
    stories[lg] = (
        f"**{lg}.** From {first} to {last}, " + (", ".join(grew) + " grew" if grew else "no style grew much")
        + ("; " + ", ".join(shrank) + " shrank" if shrank else "") + ". "
        + (f"Ways of playing: {', '.join(moved)}. " if moved else "")
        + f"Injuries per player-season went from {inj['from']:.2f} to {inj['to']:.2f} ({inj.change:+.2f}): "
        f"{inj['from style mix']:+.3f} from the style mix, {inj['within styles']:+.3f} within styles. "
        f"Days lost per player-season {days['from']:.1f} → {days['to']:.1f}; hamstring injuries per player-season "
        f"{ham['from']:.3f} → {ham['to']:.3f} (style mix {ham['from style mix']:+.3f}); knee {knee['from']:.3f} → {knee['to']:.3f} "
        f"(style mix {knee['from style mix']:+.3f})."
    )
for s in stories.values():
    display(Markdown(s))
''')
