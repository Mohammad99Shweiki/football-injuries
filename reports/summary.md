# Playing Style and Injury Patterns in Europe's Big Five Football Leagues (2014/15–2025/26)

Master's data mining project, An-Najah National University. Summary of methods and results for the course report.
Every number below is produced by the notebooks in `notebooks/` (00–05) and checked by `notebooks/06_report.ipynb`;
decisions are logged in `docs/DECISIONS.md`, every preprocessing step with row counts in `docs/PREPROCESSING_LOG.md`.

## Abstract

We clustered all 1,170 team-seasons of the Premier League, La Liga, Serie A, Bundesliga and Ligue 1 from 2014/15 to
2025/26 by **playing style per phase of play**: an attacking style (K-means on possession, patience, verticality and
directness) and a defensive style (K-means on pressing, line height, territory conceded and aggression), each with
four clusters and compared against Ward clustering. Every player-season (36,525) inherits its team's styles, and
24,581 injuries lasting more than seven days from Transfermarkt were compared across styles, seasons and leagues.
Football changed markedly: patient positional possession grew from 6% to 25% of team-seasons, direct and
counter-attacking play shrank, pressing and fouling declined, and back-three systems rose from 13% to 31% of minutes.
Players in **positional-possession** teams had 24% more injuries than their league average (rate ratio 1.24, 95% CI
1.18–1.30), robust to age, position, team strength and every sensitivity check; high-press, high-line defending added
14%. The styles also differ in **where** players get hurt: after correcting for multiple comparisons, duel-heavy and
counter-attacking styles have more knee injuries and the low block fewer hamstring and groin injuries; possession and
pressing styles lean towards more hamstring injuries, but that tendency does not survive the correction. A Kitagawa
decomposition shows that the shift in attacking styles alone would have raised injuries by 0.073 per player-season
between 2014–18 and 2022–26, in every league, and accounts for more than half of the 22% rise in hamstring injuries.

## 1. Question and novelty

How do changes in playing style relate to injury frequency, severity (days lost) and body area, across seasons and
leagues? A 2026 study (Big Data and Cognitive Computing) linked possession to injury burden in the Big Five using
Transfermarkt. This project differs in three ways: styles are found by **clustering per phase of play** (attack and
defence separately, as in Fernandez-Navarro et al. 2016 and Demir et al.), **body-area patterns** are compared
within leagues, and the injury **trend** is decomposed into the part due to the changing style mix.

## 2. Data

Collected raw from three public sources and combined for the first time (`docs/scraper/scraper-spec.md`).

| Source | What | Volume |
|---|---|---|
| Understat | per-match PPDA, deep completions, xG (league data); per team-season attack speed, shot situations, formations, shot zones (team data) | 60 league-season + 1,170 team-season payloads |
| Football-Data.co.uk | per-match fouls, cards, corners, scores, dates | 60 CSVs, 21,589 matches |
| Transfermarkt | squads, injury histories, per-match player records (minutes, participation), fixtures in all competitions | 27,077 responses, 12,848 players, 82,075 injury records |

Raw responses are stored unchanged (`data/raw/`, ~17 GB); coverage is complete for all 60 league-seasons (Phase 0).

## 3. Preprocessing

| Step | What was done | Result |
|---|---|---|
| Integration (Phase 1) | Clubs matched across the three sources within each league-season (exact → normalised → fuzzy, one-to-one Hungarian assignment), verified on fixtures | 1,170 team-seasons; all 21,589 matches found in all three sources |
| Injury cleaning (Phase 2) | Dates and durations parsed; injuries tied to the club the player was at on the injury date (per-match records); Big Five membership (≥ 1 appearance or marked injured); 315 labels mapped to injury vs non-injury and 12 body areas (reviewed); summer-2020 season rule | 82,075 → 24,581 injuries > 7 days (13,588 moderate, 10,993 severe); 5,466 non-injuries and 5,180 mild injuries kept separately |
| Features (Phase 3) | Per team-season: pressing, ball progression, attack type and shape, physical intensity (style); npxG (outcome); matches, European games, short rest, rotation (exposure); global z-scores; correlated features combined into phase-of-play dimensions | 4 attacking + 4 defensive style dimensions; shots on target dropped (Serie A source error); rest gaps > 21 days excluded |

## 4. Method

**Clustering (the data mining step).** For each phase, K-means (50 starts, seed 42) for k = 2…10, judged by elbow,
silhouette, Davies–Bouldin, Calinski–Harabasz, bootstrap stability (mean ARI and per-cluster Jaccard, Hennig 2007)
and interpretability, and compared with Ward hierarchical clustering. k = 4 was chosen for both phases (attack:
silhouette 0.22, weakest cluster Jaccard 0.64; defence: 0.21 and 0.80). k = 3 loses the modern styles and k = 5
produces dissolving clusters. Ward agrees moderately (ARI 0.39 attack, 0.35 defence): styles form a continuum, and
the clusters are useful divisions of it. Clusters are named by rule (Figure 1). Two further clustering methods check
this: a Gaussian mixture model (its BIC prefers k = 2 in both phases, again a continuum) and a consensus clustering of
bootstrap K-means, bootstrap GMM and Ward partitions, which reproduces K-means closely (ARI 0.89 attack, 0.92
defence). Each team-season also gets a **fuzzy membership** (0–1) in every style from the K-means centroids
(fuzzy c-means memberships, m = 2); ≥ 0.5 in its own style makes it a clear member (703 attack, 679 defence).

**Injury analysis.** Unit: player-club-season. Rates: injuries and days lost per player-season, injuries per 1,000
minutes, severe share. Because Transfermarkt records injuries at very different rates per league, groups are compared
by a **league-adjusted rate ratio** (observed ÷ expected at the league's average; indirect standardisation), with 95%
confidence intervals from 1,000 bootstrap resamples of team-seasons; absolute excess injuries per 100
player-seasons are shown next to each ratio. Body-area patterns are tested within leagues (Cochran–Mantel–Haenszel)
and corrected for the 80 comparisons (Benjamini–Hochberg, q < 0.05); small attack × defence cells are shrunk towards
the average (empirical Bayes); season trends are shown with 3-season rolling means. All of these were fixed before
looking at their results. Trends: three eras (2014–18, 2018–22, 2022–26), style transitions between
seasons, and a Kitagawa decomposition of injury changes into style mix and within-style change. No regression or
classification model is used (course constraint).

## 5. Results

### 5.1 The playing styles

| Phase | Style | How it plays (core teams) | Typical team-seasons |
|---|---|---|---|
| Attack | **Positional possession** | dominates the ball, slow patient build-up; 10.0 deep completions per match (all teams 6.1) | Barcelona 14-15, Inter 17-18, Real Madrid 21-22, Napoli 22-23 |
| Attack | **Build-up into the box** | moderate possession, works the ball into the box; 34% of shots from outside the box (38%) | Gladbach 17-18, Lille 21-22, Leicester 21-22, Nice 25-26 |
| Attack | **Counter-attack** | little of the ball, fast vertical attacks; 8% of shots from fast attacks (6%) | Stoke 16-17, Burnley 19-20, Cagliari 23-24 |
| Attack | **Direct play** | long-range shots and set plays; 41% of shots from outside the box | Swansea 14-15, Saint-Étienne 20-21, Genoa 23-24 |
| Defence | **High press, high line** | PPDA 8.9 (10.9), exposed to counters | Atalanta 18-19, PSG 21-22, Brighton 22-23 |
| Defence | **Compact mid-block** | protected line, concedes little, clean | Gladbach 19-20, Rennes 23-24, Atlético 25-26 |
| Defence | **Aggressive duel press** | presses through fouls and duels; 14.8 fouls per match (12.5) | Betis 19-20, Verona 21-22, Alavés 25-26 |
| Defence | **Low block** | sits deep; PPDA 13.6, 7.8 deep completions conceded | Freiburg 16-17, Everton 21-22, Girona 25-26 |

Positional possession pairs with the high press in 60% of its team-seasons (PSG 21-22, Brighton 22-23, Napoli
22-23); counter-attack and direct play pair with the low block or the aggressive duel press. Formation is not a style:
back-three minutes are similar across styles (18–29%).

*Figure 1: `figures/04_centroids.png` (style centroids per phase); `figures/04_pca.png` (PCA view).*

### 5.2 How football changed

| Measure (all leagues) | 2014–18 | 2018–22 | 2022–26 | Shape |
|---|---|---|---|---|
| Shots from slow, patient attacks | 4.4% | 5.7% | 7.1% | rising in every league |
| Deep completions per match | 5.7 | 6.0 | 6.5 | rising |
| Shots from outside the box | 41% | 38% | 34% | falling in every league |
| PPDA (higher = less pressing) | 9.7 | 11.1 | 11.9 | pressing falling in every league |
| Fouls per match | 13.3 | 12.4 | 11.9 | falling |
| Minutes in a back three | 13% | 26% | 31% | rising in every league |

Style mix: Positional possession 6% → 25% of team-seasons and Build-up into the box 17% → 42%, while Direct play
40% → 18% and Counter-attack 36% → 14%; Low block 19% → 41%, Aggressive duel press 38% → 13%, High press steady at
about 20%. Clubs keep their attacking style from one season to the next about half the time.

*Figure 2: `figures/05_style_shares_by_league.png` (style shares per league over time);
`figures/05_style_dimensions_over_time.png`.*

### 5.3 Injuries by style

| Style | Injuries / player-season | Days lost / player-season | Injury RR (95% CI) | Days-lost RR (95% CI) |
|---|---|---|---|---|
| Positional possession | 0.85 | 34.0 | **1.24 (1.18–1.30)** | **1.09 (1.02–1.15)** |
| Build-up into the box | 0.68 | 31.0 | 1.01 (0.97–1.04) | 1.00 (0.96–1.05) |
| Counter-attack | 0.60 | 29.2 | **0.90 (0.85–0.94)** | 0.96 (0.90–1.02) |
| Direct play | 0.64 | 29.3 | **0.95 (0.91–0.99)** | 0.99 (0.94–1.04) |
| High press, high line | 0.75 | 32.1 | **1.14 (1.09–1.20)** | 1.03 (0.98–1.09) |
| Compact mid-block | 0.66 | 27.8 | 1.03 (0.97–1.08) | 0.97 (0.92–1.03) |
| Aggressive duel press | 0.64 | 29.2 | **0.93 (0.89–0.98)** | 1.00 (0.95–1.06) |
| Low block | 0.66 | 32.6 | **0.94 (0.90–0.98)** | 1.00 (0.95–1.04) |
| Back three / back four | – | – | 1.01 / 1.00 | – |

- **The possession effect belongs to the attacking phase:** Positional possession is above 1 with every defensive
  style (1.16–1.28 in the common combinations), and above its league average in all five leagues (1.08–1.61).
- It is **not squad make-up** (1.27 adjusted for league × age × position) and **not only team strength** (1.25 among
  the strongest third of teams, 1.10 in the middle third).
- Robust in every sensitivity check (≥ 900 minutes, injuries > 3 days, multi-club players out, COVID seasons out),
  but **smaller for severe injuries** (1.09), which are reported more reliably.
- Busy schedules matter on their own: players in the busiest third of teams by short rest have RR 1.14.

*Figure 3: `figures/05_rates_by_style.png`; `figures/05_attack_defence_grid.png`.*

### 5.4 Where players get hurt

Body-area patterns that survive the within-league test after false-discovery-rate correction (9 of 80):
- **Knee:** more with the aggressive duel press (odds ratio 1.23; above the league in 4/5 leagues) and counter-attack
  (1.13; 5/5); fewer with Positional possession (0.82) and the high press (0.85).
- **Low block:** fewer hamstring (0.85) and groin (0.81) injuries.
- Positional possession: more unspecified muscle injuries (1.21).

Patterns seen in at least 4 of 5 leagues but **not** significant after correction (shown as tendencies only): more
hamstring injuries with Positional possession and the high press, more groin injuries with the high press, more knee
injuries with direct play. The overall effect is small (Cramér's V 0.04–0.05).

*Figure 4: `figures/05_body_areas_by_style.png`.*

### 5.5 Injury trends and the style shift

Injuries rose from 0.646 to 0.689 per player-season and days lost from 30.4 to 31.9 between 2014–18 and 2022–26
(Figure 5). The Kitagawa decomposition:

| Outcome per player-season | Change | From the style mix | Within styles |
|---|---|---|---|
| Injuries | +0.043 | +0.065 | −0.022 |
| Days lost | +1.5 | +2.8 | −1.2 |
| Hamstring injuries | +0.018 (+22%) | +0.010 | +0.008 |
| Knee injuries | −0.011 | +0.009 | −0.020 |

The style-mix part comes almost entirely from the **attacking** shift (+0.073 injuries, against +0.010 from the
defensive shift), and it is positive **in every league** (+0.05 to +0.08). The within-style part differs by league,
partly because of recording changes.

*Figure 5: `figures/05_season_trend.png` (with calendar events); `figures/05_trend_decomposition.png`.*

### 5.6 Leagues

- **Premier League:** positional possession 10% → 35%; injuries 0.56 → 0.71, of which +0.05 from the style mix.
- **La Liga:** counter-attack 48% → 16%, aggressive duel press 76% → 39%; injuries fell (0.71 → 0.49) within styles,
  although the style mix pushed them up (+0.05).
- **Serie A:** the back three became the norm (29% → 52% of minutes), aggressive duel press 55% → 6%; injuries
  0.74 → 0.89, hamstring injuries 0.083 → 0.133.
- **Bundesliga:** low block 15% → 61%, direct play 44% → 6%; injuries fell within styles.
- **Ligue 1:** build-up into the box 12% → 41%, counter-attack 41% → 9%; injuries 0.37 → 0.60.

*Figure 6: `figures/05_style_within_league.png` (style RR within each league).*

## 6. Discussion

A plausible reading, not measured here (no tracking data): possession-dominant teams, which pair it with a high
press and a high line, are likely to make more high-speed actions and repeated sprints in the opponent's half and
play more matches (European football), all known risk factors for muscle injuries (their hamstring and groin excess
is only a tendency here); direct,
counter-attacking and duel-heavy football is likely to involve more contact and decelerations, consistent with more
knee injuries. As the Big Five moved towards patient possession, the mix of styles shifted towards the more
injury-prone one, enough to raise injury rates in every league even while rates within styles changed little. The
link holds between styles and across eras, not season to season (within-league season-to-season correlations
|r| ≤ 0.3), so other long-run changes (sports science, calendars, recording) move in parallel.

## 7. Limitations

- **Transfermarkt under-reports injuries** (about 0.63 per player-season vs 1.5–2.5 in clinical studies) and records
  them unevenly by league and over time (Premier League 2018-19 jump; rising share of unknown body areas). League-
  adjusted rates and within-league checks reduce, but cannot remove, this.
- **Coverage bias:** injuries at famous clubs are probably recorded more completely; the possession effect shrinks for
  severe, better-reported injuries (1.24 → 1.09).
- **Style proxies:** Understat and Football-Data give team-level match statistics; tracking and event data (pressing
  height, crossing, width, long balls, running load) are not available, so some literature styles (crossing, wide vs
  narrow possession) cannot be measured.
- **League matches only** for style; workload uses all competitions. No training load or exposure data; injuries on
  international duty cannot be separated.
- **Association, not causation:** styles go with team strength (eta² 0.39 attack, 0.34 defence) and calendar; results
  are checked within strength thirds and leagues, but unmeasured factors remain.
- **Clusters on a continuum:** silhouette about 0.2 and moderate Ward agreement; borderline teams are assigned to the
  nearer style (core-only checks give the same results).

## 8. Reproducing

```sh
cd scraper && docker compose up --build        # collect raw data (or reuse data/raw) and parse to data/tables
cd notebooks && for nb in 00_audit 01_entities 02_injuries 03_features 04_clustering 05_injury_analysis 06_report; do
  uv run --group analysis jupyter nbconvert --to notebook --execute --inplace $nb.ipynb; done
```

The notebooks are generated from `scripts/notebooks/build_0*_notebook.py`; each step has a note, the code and a check.

## Interactive results

An interactive dashboard shows the clusters and results: a cluster map of all team-seasons per phase of play, the style
cards, style shares and dimensions over time per league, injury rate ratios, the attack × defence grid, body areas, the
injury trend, the decomposition and the league stories: https://claude.ai/artifact/PzWvuXE97B84QyZy6q4qnN (private
until shared). Its data files are exported by `notebooks/06_report.ipynb` (step 4) to `data/06_report/dashboard/`;
the page source is `scripts/dashboard/index.html`.

## Figures for the report

| # | File | Shows |
|---|---|---|
| 1 | `figures/04_centroids.png` | Attacking and defensive style centroids |
| 2 | `figures/05_style_shares_by_league.png` | Style shares per league over time |
| 3 | `figures/05_rates_by_style.png`, `figures/05_attack_defence_grid.png` | Injury and days-lost rate ratios by style |
| 4 | `figures/05_body_areas_by_style.png` | Body areas by style, within leagues |
| 5 | `figures/05_season_trend.png`, `figures/05_trend_decomposition.png` | Injury trend with calendar events; decomposition |
| 6 | `figures/05_style_within_league.png` | Style effect within each league |
| A1 | `figures/04_k_selection.png`, `figures/04_dendrograms.png` | Choosing k; Ward |
| A2 | `figures/05_style_dimensions_over_time.png` | Style dimensions per league and season |
| A3 | `figures/00_injury_records_per_season.png` | Raw injury records (audit) |

## References

- Demir, Şahin & Üre. *How do football teams play? A deep embedded clustering approach to reveal playing styles.*
- Dupont et al. (2010). *Effect of 2 soccer matches in a week on physical performance and injury rate.* AJSM.
- Fernandez-Navarro, Fradua, Zubillaga, Ford & McRobert (2016). *Attacking and defensive styles of play in soccer.*
  Journal of Sports Sciences 34(24), 2195–2204.
- Fuller et al. (2006). *Consensus statement on injury definitions and data collection procedures in football.*
- Hennig (2007). *Cluster-wise assessment of cluster stability.* Computational Statistics & Data Analysis.
- Hoenig et al. (2022). *Analysis of more than 20,000 injuries in European professional football by using a citizen
  science-based approach.*
- Kitagawa (1955). *Components of a difference between two rates.* JASA.
- Plakias et al. (2025). *A grounded theory for professional soccer teams' playing styles: towards a consensus.*
  Int J Sports Sci Coaching 20(1), 159–172.
