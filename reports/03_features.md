# Phase 3: Team-season features

Generated 2026-10-21 by `notebooks/03_features.ipynb`, where each step is shown with its checks.

## Key findings

- **1,170 team-seasons, 17 features, none missing.** League match counts agree between Understat and Football-Data.
- **Redundant pairs (|r| > 0.9):** 1; dropped rest_mean.
- **16 features** go into clustering, standardised over all team-seasons.

## 1. Features

| group | feature | status |
|---|---|---|
| pressing | ppda | kept |
| pressing | opp_ppda | kept |
| attacking approach | deep_pm | kept |
| attacking approach | deep_against_pm | kept |
| attacking approach | npxg_pm | kept |
| attacking approach | npxga_pm | kept |
| physical intensity | fouls_pm | kept |
| physical intensity | fouled_pm | kept |
| physical intensity | cards_pm | kept |
| physical intensity | corners_for_pm | kept |
| physical intensity | corners_against_pm | kept |
| workload | matches_all | kept |
| workload | matches_europe | kept |
| workload | rest_mean | dropped (redundant) |
| workload | short_rest_share | kept |
| workload | rest_sd | kept |
| rotation | top14_share | kept |

## 2. Ranges (raw units)

| feature | mean | std | min | max |
|---|---|---|---|---|
| ppda | 10.89 | 2.31 | 5.5 | 19.0 |
| opp_ppda | 10.83 | 2.92 | 4.07 | 26.31 |
| deep_pm | 6.09 | 2.34 | 2.03 | 15.35 |
| deep_against_pm | 6.09 | 1.52 | 2.44 | 11.68 |
| npxg_pm | 1.28 | 0.37 | 0.63 | 2.89 |
| npxga_pm | 1.28 | 0.29 | 0.52 | 2.4 |
| fouls_pm | 12.52 | 1.87 | 7.55 | 18.55 |
| fouled_pm | 12.52 | 1.79 | 7.68 | 18.92 |
| cards_pm | 2.23 | 0.51 | 1.0 | 3.97 |
| corners_for_pm | 4.92 | 0.87 | 2.97 | 8.44 |
| corners_against_pm | 4.92 | 0.88 | 2.0 | 7.5 |
| matches_all | 44.68 | 6.88 | 30.0 | 68.0 |
| matches_europe | 3.68 | 5.37 | 0.0 | 24.0 |
| rest_mean | 6.31 | 0.86 | 4.15 | 8.26 |
| short_rest_share | 0.21 | 0.11 | 0.0 | 0.52 |
| rest_sd | 3.23 | 0.38 | 2.07 | 4.61 |
| top14_share | 0.8 | 0.05 | 0.6 | 0.95 |

## 3. Strongest correlations

| feature_a | feature_b | r |
|---|---|---|
| rest_mean | short_rest_share | -0.902 |
| matches_all | rest_mean | -0.894 |
| matches_all | matches_europe | 0.882 |
| deep_pm | npxg_pm | 0.881 |
| matches_all | short_rest_share | 0.834 |
| matches_europe | rest_mean | -0.833 |
| deep_against_pm | npxga_pm | 0.828 |
| matches_europe | short_rest_share | 0.769 |
| opp_ppda | deep_pm | 0.751 |
| opp_ppda | npxg_pm | 0.736 |
| deep_against_pm | corners_against_pm | 0.707 |
| deep_pm | corners_for_pm | 0.693 |

## 4. Season means

| feature | 2014-15 | 2015-16 | 2016-17 | 2017-18 | 2018-19 | 2019-20 | 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ppda | 9.12 | 9.13 | 9.86 | 10.53 | 10.91 | 10.89 | 11.44 | 11.21 | 11.45 | 12.16 | 11.96 | 12.02 |
| opp_ppda | 9.03 | 9.03 | 9.77 | 10.51 | 10.9 | 10.82 | 11.39 | 11.24 | 11.4 | 12.07 | 11.91 | 11.97 |
| deep_pm | 5.44 | 5.69 | 5.74 | 5.93 | 6.05 | 5.82 | 6.04 | 6.27 | 6.51 | 6.77 | 6.42 | 6.44 |
| deep_against_pm | 5.44 | 5.69 | 5.74 | 5.93 | 6.05 | 5.81 | 6.04 | 6.27 | 6.51 | 6.77 | 6.42 | 6.44 |
| npxg_pm | 1.17 | 1.21 | 1.19 | 1.2 | 1.29 | 1.27 | 1.23 | 1.29 | 1.32 | 1.41 | 1.42 | 1.4 |
| npxga_pm | 1.17 | 1.21 | 1.19 | 1.2 | 1.29 | 1.27 | 1.23 | 1.29 | 1.32 | 1.41 | 1.42 | 1.4 |
| fouls_pm | 13.93 | 13.47 | 13.2 | 12.67 | 12.26 | 12.6 | 12.61 | 12.03 | 12.05 | 11.94 | 11.74 | 11.73 |
| fouled_pm | 13.93 | 13.47 | 13.2 | 12.67 | 12.26 | 12.6 | 12.61 | 12.03 | 12.05 | 11.94 | 11.74 | 11.73 |
| cards_pm | 2.3 | 2.33 | 2.22 | 2.12 | 2.22 | 2.35 | 2.1 | 2.27 | 2.27 | 2.33 | 2.19 | 2.14 |
| corners_for_pm | 5.04 | 5.05 | 4.96 | 4.98 | 5.02 | 5.04 | 4.73 | 4.89 | 4.8 | 4.92 | 4.81 | 4.78 |
| corners_against_pm | 5.04 | 5.05 | 4.96 | 4.98 | 5.02 | 5.04 | 4.73 | 4.89 | 4.8 | 4.92 | 4.82 | 4.78 |
| matches_all | 44.92 | 45.2 | 44.85 | 45.13 | 45.0 | 42.8 | 44.24 | 44.61 | 44.73 | 44.08 | 45.36 | 45.23 |
| matches_europe | 3.36 | 3.53 | 3.21 | 3.43 | 3.45 | 3.24 | 3.31 | 3.55 | 3.69 | 3.72 | 4.96 | 4.8 |
| rest_mean | 6.39 | 6.3 | 6.42 | 6.36 | 6.37 | 5.93 | 5.96 | 6.54 | 5.91 | 6.62 | 6.5 | 6.41 |
| short_rest_share | 0.2 | 0.21 | 0.2 | 0.21 | 0.2 | 0.27 | 0.26 | 0.21 | 0.2 | 0.17 | 0.17 | 0.19 |
| rest_sd | 3.23 | 3.23 | 3.33 | 3.33 | 3.26 | 3.28 | 3.14 | 3.6 | 2.6 | 3.26 | 3.21 | 3.25 |
| top14_share | 0.81 | 0.8 | 0.8 | 0.8 | 0.81 | 0.81 | 0.8 | 0.79 | 0.8 | 0.8 | 0.8 | 0.8 |

## 5. League means

| feature | Bundesliga | La Liga | Ligue 1 | Premier League | Serie A |
|---|---|---|---|---|---|
| ppda | 11.28 | 9.92 | 10.99 | 11.33 | 10.95 |
| opp_ppda | 11.19 | 9.83 | 10.91 | 11.33 | 10.93 |
| deep_pm | 6.47 | 5.69 | 5.41 | 6.87 | 6.03 |
| deep_against_pm | 6.47 | 5.69 | 5.41 | 6.87 | 6.03 |
| npxg_pm | 1.39 | 1.24 | 1.22 | 1.33 | 1.24 |
| npxga_pm | 1.39 | 1.24 | 1.22 | 1.33 | 1.24 |
| fouls_pm | 12.4 | 13.35 | 12.7 | 10.79 | 13.37 |
| fouled_pm | 12.39 | 13.35 | 12.7 | 10.79 | 13.37 |
| cards_pm | 2.03 | 2.71 | 2.1 | 1.86 | 2.45 |
| corners_for_pm | 4.82 | 4.78 | 4.77 | 5.21 | 4.99 |
| corners_against_pm | 4.82 | 4.78 | 4.77 | 5.21 | 4.99 |
| matches_all | 41.08 | 46.51 | 43.15 | 47.94 | 44.32 |
| matches_europe | 3.86 | 4.07 | 2.98 | 4.0 | 3.51 |
| rest_mean | 6.51 | 6.08 | 6.62 | 5.96 | 6.39 |
| short_rest_share | 0.18 | 0.25 | 0.17 | 0.26 | 0.17 |
| rest_sd | 3.11 | 3.27 | 3.27 | 3.23 | 3.23 |
| top14_share | 0.82 | 0.78 | 0.81 | 0.8 | 0.79 |

## 6. Steps and row counts

| step | operation | rows in | rows out |
|---|---|---|---|
| 3.2 | Understat team-matches aggregated to team-seasons | 43178 | 1170 |
| 3.3 | Football-Data matches to team-matches (home + away) to team-seasons | 21589 | 1170 |
| 3.4 | TM club fixtures to club-season workload | 52275 | 1170 |
| 3.5 | player-club-season minutes to club-season rotation | 36525 | 1170 |
| 3.6 | feature groups joined to team-seasons | 1170 | 1170 |
| 3.9 | standardised 16 features over all team-seasons (dropped: rest_mean) | 1170 | 1170 |

## 7. Outputs

- `data/03_features/team_season_features.parquet`: raw features and z-scores (`z_*`, the 16 kept features).
