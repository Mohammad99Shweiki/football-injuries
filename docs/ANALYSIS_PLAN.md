# Analysis Plan

Work one phase at a time. At the end of each phase, give a short summary (what was done, key numbers, issues found, decisions needed) and **stop for review**.

Structure:
```
analysis/phases/  # p00_audit.py … p06_report.py: each phase's steps as `# %%` cells (note + code + check), source of truth
analysis/         # run.py (runner, run records, staleness), api.py (dashboard API), steps.py, shared config/load/report
notebooks/        # 00_audit … 06_report, generated from analysis/phases/, run top to bottom
mappings/       # hand-reviewed CSVs (tracked in git): team_map, injury_label_map, non-injury labels
data/raw/, data/tables/          # scraper output, read only
data/00_audit/ … data/06_report/   # each phase's output (analysis.config.phase_dir) and its run record _run.json
reports/        # NN_*.md per phase, figures/NN_*.png
docs/DECISIONS.md, docs/PREPROCESSING_LOG.md
```
Phase N writes only to `data/NN_*/` and reads only from `data/tables/`, `mappings/` and earlier phase folders.
Stack: Python, pandas, numpy, scikit-learn, scipy, matplotlib/seaborn, rapidfuzz (name matching).

---

## Phase 0: Data audit
- Inventory `data/raw` and `data/tables`: files, row counts, columns, encodings. Update the **Data** section of `CLAUDE.md` with the actual layout.
- **Coverage checks:**
  - League matches per league-season: 380, Bundesliga 306, Ligue 1 306 from 2023/24 and ~279 in 2019/20.
  - Clubs per league-season.
  - Squads per club-season.
- **Missingness:** per table and per column, plus duplicates.
- **Injuries:** counts per season and per league, share of missing or unknown days, and the number of distinct raw injury labels.
- **Output:** `reports/00_data_audit.md`.

## Phase 1: Entity resolution
- **Teams:** build `mappings/team_map.csv` (one row per club: TM club_id, Understat name, Football-Data name). Match by exact name, then fuzzy matching within the same league-season. List anything uncertain for manual review. Every team-season in all three sources must map.
- **Players:** the player-level analysis uses Transfermarkt only (injuries, squads, minutes), so no cross-source player matching is needed. Match to Understat players only if a specific feature requires it.
- **Seasons:** one canonical key, `season = "2014-15"` … `"2025-26"`, across all sources. Date-based season for injuries runs 1 July to 30 June; check it against TM's own season label.

## Phase 2: Injury cleaning and body-area mapping
- **Parse:** from/until dates, `days` as an integer (handle "?" and ongoing injuries), and games missed.
- **Exclude** non-injuries (illness, flu, COVID, quarantine, rest), keeping a separate count. Confirm the exclusion list with me.
- **Severity filter:** `days > 7`. Keep severity bands for analysis: 8–28 days (moderate) and > 28 days (severe). Injuries of 4–7 days (mild) are kept in a separate file for a sensitivity check.
- **Body-area mapping:** create `mappings/injury_label_map.csv` with the raw label, frequency, class (injury / non-injury), body_area, surgery flag and notes. (Injury type dropped 2026-10-21, see DECISIONS.)
  - **Body area:** hamstring, thigh (other/quad), groin/adductor/hip, knee, calf/achilles/lower leg, ankle, foot/toe, back/spine, head/neck, upper body, unspecified muscle, unknown.
  - Propose mappings ordered by frequency so that the labels covering ≥ 95% of injuries are mapped. **I review the CSV before it's applied.**
- **Attribution:** link each injury to the player's club-season on the injury date (from squads and dates).
- **Output:** `data/02_injuries/injuries_clean.parquet`, plus a report of coverage and the share of unknown body areas per season.

## Phase 3: Team-season features
Use one row per team-season (~1,150). Use per-match rates.

| Group | Features | Source |
|---|---|---|
| Pressing | PPDA (Σatt/Σdef), opponent PPDA | Understat |
| Attacking approach | deep completions for and against per match, npxG per match, npxGA per match | Understat |
| Physical intensity | fouls committed and suffered per match, cards per match (yellow + 2×red), corners | Football-Data |
| Workload | total matches in all competitions, European matches, mean rest days, share of matches with < 4 days rest, rest-day variability (gaps > 21 days left out) | TM fixtures |

Shooting volume (shots on target) was dropped on 2026-10-21; `rest_mean` was dropped as redundant (see DECISIONS).
| Rotation | squad minutes concentration (share of minutes by the top 14 players, or HHI) | TM player stats |

- Check correlations, drop redundant features (|r| > 0.9), and document the final feature set.
- Standardise globally (z-scores over all team-seasons).
- **Output:** `data/03_features/team_season_features.parquet`.

## Phase 4: Clustering
- **K-means**, k = 2…10, with several random initialisations and a fixed seed. Report elbow (inertia), silhouette, Davies–Bouldin and Calinski–Harabasz for each k. Choose k from these plus interpretability.
- **Hierarchical (Ward)** at the same k: show the dendrogram and the adjusted Rand index against K-means.
- **Stability:** bootstrap resampling: mean ARI and per-cluster Jaccard (Hennig 2007); usable k = every cluster ≥ 0.6.
- **Two variants:** with and without outcome features (npxG/npxGA), to test whether clusters are about style or team strength. Pick one with me. *Done 2026-10-21: style only, clustered per phase of play (attacking k = 4, defensive k = 4; style = the pair; formation reported, not clustered; see DECISIONS).*
- **Profiling:** cluster centroids in original units, a radar or heatmap, a descriptive name for each cluster, and example teams.
- **Output:** `data/04_clusters/team_season_clusters.parquet`, `reports/04_clustering.md` and figures (PCA 2D scatter for visualisation only).

## Phase 5: Injury analysis (player-season level)
- **Player-season table:** player, club, season, league, age, position group, minutes in all competitions, team cluster, injury count (> 7 days), days lost, and counts by body area and severity.
- **Rates:**
  - injuries per player-season
  - injuries per 1,000 match minutes
  - days lost per player-season
  - each with bootstrap 95% confidence intervals
- **Compare:**
  1. Rates by **cluster**.
  2. Body-area distribution by cluster: cluster × body-area heatmap and a chi-square test.
  3. Trends over **seasons**: overall rates, and cluster shares per season per league (stacked area chart).
  4. Differences between **leagues**: rates and body-area mix per league; whether the cluster effect holds within each league.
  5. Breakdowns by **age group and position**, to check that cluster differences aren't just driven by squad age or position mix.
  6. **Team strength bands** (points per match terciles) and **workload** (exposure features from Phase 3): whether style differences hold within strength bands and how congestion relates to injuries within each style.
- **Sensitivity checks:**
  - ≥ 900-minute players only
  - severe (> 28 days) only
  - multi-club players excluded
  - COVID seasons excluded
  - injuries > 3 days (adding the mild 4–7 day band)
  - core team-seasons only (clear members of their style)
- **Secondary outcome:** *Fitness* absences (non-injuries, mostly reconditioning) per cluster, read mainly within the Bundesliga where they are recorded.
- **Added after the methods review (2026-10-21):** nested expected values (league × season → + team strength → + age ×
  position) and per-team-match exposure; bootstrap over clubs; same club with and without each style, and style
  switches; body areas by permutation test with Benjamini–Hochberg; Kitagawa cells league × strength × style;
  sensitivity clusterings (k = 3, style relative to the league-season); days lost with overlapping absences merged.
- **Output:** `data/05_injury_analysis/player_seasons.parquet`, `data/05_injury_analysis/tables/`, `reports/05_injury_analysis.md` and figures.

## Phase 6: Report material
- **Key figures:**
  - cluster shares over time per league
  - injury rate by cluster
  - cluster × body-area heatmap
  - injury trend with calendar events annotated
  - league comparison
- **Limitations:** Transfermarkt under-reporting, proxies for physical load, league-only style data from Understat, no training exposure data, and association rather than causation.
- **Output:** `reports/summary.md` (checked against the data by `p06_report.py`), figures ready for the course report, and
  the results files for the dashboard (`data/06_report/dashboard/`).

## Status (2026-10-22)
All phases done and reviewed; framing: "style or schedule?" (possession's excess is mostly team strength and match
load). Remaining: the analysis screens of the dashboard (step 2 in `app/`), from `docs/ui/analysis-studio-design-brief.md`.
