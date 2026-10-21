# Phase 3: Team-season features

Generated 2026-10-22 by `notebooks/03_features.ipynb`, where each step is shown with its checks.

## Key findings

- **1,170 team-seasons, 23 features, none missing.** League match counts agree between Understat and Football-Data.
- **Redundant pairs (|r| > 0.9):** 1; dropped rest_mean.
- **13 style features** form **4 attacking and 4 defensive dimensions**, clustered per phase in Phase 4; 22 features in all are standardised over all team-seasons (outcome and exposure features are kept for Phases 4–5, not clustered).

## 1. Features

| group | feature | role | status |
|---|---|---|---|
| pressing | ppda | style | kept |
| pressing | opp_ppda | style | kept |
| ball progression | deep_pm | style | kept |
| ball progression | deep_against_pm | style | kept |
| attack type and shape | fast_attack_share | style | kept |
| attack type and shape | slow_attack_share | style | kept |
| attack type and shape | conceded_fast_share | style | kept |
| attack type and shape | set_piece_share | style | kept |
| attack type and shape | outside_box_share | style | kept |
| attack type and shape | back_three_share | style | kept |
| physical intensity | fouls_pm | style | kept |
| physical intensity | fouled_pm | style | kept |
| physical intensity | cards_pm | style | kept |
| physical intensity | corners_for_pm | style | kept |
| physical intensity | corners_against_pm | style | kept |
| chance quality | npxg_pm | outcome | kept |
| chance quality | npxga_pm | outcome | kept |
| workload | matches_all | exposure | kept |
| workload | matches_europe | exposure | kept |
| workload | rest_mean | exposure | dropped (redundant) |
| workload | short_rest_share | exposure | kept |
| workload | rest_sd | exposure | kept |
| rotation | top14_share | exposure | kept |

## 2. Ranges (raw units)

| feature | mean | std | min | max |
|---|---|---|---|---|
| ppda | 10.89 | 2.31 | 5.5 | 19.0 |
| opp_ppda | 10.83 | 2.92 | 4.07 | 26.31 |
| deep_pm | 6.09 | 2.34 | 2.03 | 15.35 |
| deep_against_pm | 6.09 | 1.52 | 2.44 | 11.68 |
| fast_attack_share | 0.06 | 0.02 | 0.02 | 0.12 |
| slow_attack_share | 0.06 | 0.02 | 0.01 | 0.18 |
| conceded_fast_share | 0.06 | 0.02 | 0.02 | 0.16 |
| set_piece_share | 0.26 | 0.04 | 0.13 | 0.39 |
| outside_box_share | 0.38 | 0.06 | 0.23 | 0.54 |
| back_three_share | 0.23 | 0.3 | 0.0 | 1.0 |
| fouls_pm | 12.52 | 1.87 | 7.55 | 18.55 |
| fouled_pm | 12.52 | 1.79 | 7.68 | 18.92 |
| cards_pm | 2.23 | 0.51 | 1.0 | 3.97 |
| corners_for_pm | 4.92 | 0.87 | 2.97 | 8.44 |
| corners_against_pm | 4.92 | 0.88 | 2.0 | 7.5 |
| npxg_pm | 1.28 | 0.37 | 0.63 | 2.89 |
| npxga_pm | 1.28 | 0.29 | 0.52 | 2.4 |
| matches_all | 44.68 | 6.88 | 30.0 | 68.0 |
| matches_europe | 3.68 | 5.37 | 0.0 | 24.0 |
| rest_mean | 6.31 | 0.86 | 4.15 | 8.26 |
| short_rest_share | 0.21 | 0.11 | 0.0 | 0.52 |
| rest_sd | 3.23 | 0.38 | 2.07 | 4.61 |
| top14_share | 0.8 | 0.05 | 0.6 | 0.95 |

## 3. Phase-of-play dimensions (clustered per phase in Phase 4)

| phase | dimension | features (sign) |
|---|---|---|
| attack | possession | opp_ppda (+), deep_pm (+), corners_for_pm (+) |
| attack | patience | slow_attack_share (+) |
| attack | verticality | fast_attack_share (+) |
| attack | directness | outside_box_share (+), set_piece_share (+) |
| defence | press | ppda (−) |
| defence | high_line | conceded_fast_share (+) |
| defence | territory_conceded | deep_against_pm (+), corners_against_pm (+) |
| defence | aggression | fouls_pm (+), cards_pm (+) |

Not clustered: `back_three_share` (structure (formation), reported per style); `fouled_pm` (describes the opponent).

Correlations between the dimensions:

| dimension | attack_possession | attack_patience | attack_verticality | attack_directness | defence_press | defence_high_line | defence_territory_conceded | defence_aggression |
|---|---|---|---|---|---|---|---|---|
| attack_possession | 1.0 | 0.5 | -0.27 | -0.55 | 0.39 | 0.28 | -0.6 | -0.48 |
| attack_patience | 0.5 | 1.0 | -0.27 | -0.42 | 0.0 | 0.03 | -0.27 | -0.33 |
| attack_verticality | -0.27 | -0.27 | 1.0 | 0.04 | -0.14 | -0.08 | 0.24 | 0.1 |
| attack_directness | -0.55 | -0.42 | 0.04 | 1.0 | -0.04 | -0.03 | 0.27 | 0.31 |
| defence_press | 0.39 | 0.0 | -0.14 | -0.04 | 1.0 | 0.37 | -0.55 | 0.25 |
| defence_high_line | 0.28 | 0.03 | -0.08 | -0.03 | 0.37 | 1.0 | -0.28 | -0.08 |
| defence_territory_conceded | -0.6 | -0.27 | 0.24 | 0.27 | -0.55 | -0.28 | 1.0 | 0.07 |
| defence_aggression | -0.48 | -0.33 | 0.1 | 0.31 | 0.25 | -0.08 | 0.07 | 1.0 |

## 3b. Strongest correlations between features

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
| fast_attack_share | 0.07 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 |
| slow_attack_share | 0.04 | 0.04 | 0.05 | 0.05 | 0.05 | 0.05 | 0.06 | 0.06 | 0.07 | 0.07 | 0.07 | 0.07 |
| conceded_fast_share | 0.07 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 | 0.06 |
| set_piece_share | 0.26 | 0.26 | 0.27 | 0.26 | 0.26 | 0.26 | 0.26 | 0.26 | 0.26 | 0.26 | 0.25 | 0.25 |
| outside_box_share | 0.43 | 0.41 | 0.4 | 0.4 | 0.39 | 0.38 | 0.36 | 0.36 | 0.35 | 0.35 | 0.33 | 0.34 |
| back_three_share | 0.09 | 0.09 | 0.15 | 0.21 | 0.23 | 0.23 | 0.28 | 0.28 | 0.3 | 0.3 | 0.31 | 0.34 |
| fouls_pm | 13.93 | 13.47 | 13.2 | 12.67 | 12.26 | 12.6 | 12.61 | 12.03 | 12.05 | 11.94 | 11.74 | 11.73 |
| fouled_pm | 13.93 | 13.47 | 13.2 | 12.67 | 12.26 | 12.6 | 12.61 | 12.03 | 12.05 | 11.94 | 11.74 | 11.73 |
| cards_pm | 2.3 | 2.33 | 2.22 | 2.12 | 2.22 | 2.35 | 2.1 | 2.27 | 2.27 | 2.33 | 2.19 | 2.14 |
| corners_for_pm | 5.04 | 5.05 | 4.96 | 4.98 | 5.02 | 5.04 | 4.73 | 4.89 | 4.8 | 4.92 | 4.81 | 4.78 |
| corners_against_pm | 5.04 | 5.05 | 4.96 | 4.98 | 5.02 | 5.04 | 4.73 | 4.89 | 4.8 | 4.92 | 4.82 | 4.78 |
| npxg_pm | 1.17 | 1.21 | 1.19 | 1.2 | 1.29 | 1.27 | 1.23 | 1.29 | 1.32 | 1.41 | 1.42 | 1.4 |
| npxga_pm | 1.17 | 1.21 | 1.19 | 1.2 | 1.29 | 1.27 | 1.23 | 1.29 | 1.32 | 1.41 | 1.42 | 1.4 |
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
| fast_attack_share | 0.07 | 0.06 | 0.06 | 0.06 | 0.06 |
| slow_attack_share | 0.05 | 0.06 | 0.05 | 0.06 | 0.06 |
| conceded_fast_share | 0.07 | 0.06 | 0.06 | 0.06 | 0.06 |
| set_piece_share | 0.27 | 0.26 | 0.26 | 0.26 | 0.25 |
| outside_box_share | 0.36 | 0.37 | 0.39 | 0.37 | 0.4 |
| back_three_share | 0.33 | 0.08 | 0.19 | 0.17 | 0.41 |
| fouls_pm | 12.4 | 13.35 | 12.7 | 10.79 | 13.37 |
| fouled_pm | 12.39 | 13.35 | 12.7 | 10.79 | 13.37 |
| cards_pm | 2.03 | 2.71 | 2.1 | 1.86 | 2.45 |
| corners_for_pm | 4.82 | 4.78 | 4.77 | 5.21 | 4.99 |
| corners_against_pm | 4.82 | 4.78 | 4.77 | 5.21 | 4.99 |
| npxg_pm | 1.39 | 1.24 | 1.22 | 1.33 | 1.24 |
| npxga_pm | 1.39 | 1.24 | 1.22 | 1.33 | 1.24 |
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
| 3.3 | Understat team statistics to style shares per team-season | 43813 | 1170 |
| 3.3 | Football-Data matches to team-matches (home + away) to team-seasons | 21589 | 1170 |
| 3.4 | TM club fixtures to club-season workload | 52275 | 1170 |
| 3.5 | player-club-season minutes to club-season rotation | 36525 | 1170 |
| 3.6 | feature groups joined to team-seasons | 1170 | 1170 |
| 3.9 | standardised 22 features over all team-seasons (dropped: rest_mean) | 1170 | 1170 |
| 3.11 | 13 style features combined into 4 attacking + 4 defensive dimensions (back-three share kept as structure) | 1170 | 1170 |

## 7. Outputs

- `data/03_features/team_season_features.parquet`: raw features and z-scores (`z_*`, the 22 kept features).
- `data/03_features/feature_roles.csv`: group, role (style / outcome / exposure) and status of every feature.
- `data/03_features/style_dimensions.parquet`: the 4 attacking and 4 defensive dimension scores and the back-three share per team-season (Phase 4 input).
