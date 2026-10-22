# Data dictionary

Every variable used in the analysis: definition or formula, unit, source and missing values. Code: `analysis/phases/`.
Season keys: `2014-15` (Understat and Transfermarkt use the start year, 2014; Football-Data `1415`).

## 1. Team-season features (Phase 3, `data/03_features/team_season_features.parquet`, 1,170 rows, no missing values)

| Variable | Definition / formula | Unit | Source | Role |
|---|---|---|---|---|
| `ppda` | Opponent passes allowed per defensive action in the opponent's 60% of the pitch, season total: Σ passes ÷ Σ defensive actions (not the mean of match values) | passes per action (lower = more pressing) | Understat league data, `ppda.att`, `ppda.def` | style (defence: press, sign −) |
| `opp_ppda` | Same, for the opponent's pressing on this team: Σ `ppda_allowed.att` ÷ Σ `ppda_allowed.def` | passes per action (higher = the team keeps the ball under less pressure) | Understat | style (attack: possession) |
| `deep_pm` | Passes completed within 20 yards of the opponent's goal (excluding crosses), Understat's definition, per match | completions per match | Understat `deep` | style (attack: possession) |
| `deep_against_pm` | Deep completions allowed, per match | completions per match | Understat `deep_allowed` | style (defence: territory conceded) |
| `fast_attack_share` | Shots from fast attacks ÷ all shots | share 0–1 | Understat team data, `attackSpeed` = Fast | style (attack: verticality) |
| `slow_attack_share` | Shots from slow attacks ÷ all shots | share 0–1 | Understat `attackSpeed` = Slow | style (attack: patience) |
| `conceded_fast_share` | Shots conceded from fast attacks ÷ all shots conceded | share 0–1 | Understat `attackSpeed`, against | style (defence: high line) |
| `set_piece_share` | Shots from corners, set pieces and direct free kicks ÷ all shots | share 0–1 | Understat `situation` | style (attack: directness) |
| `outside_box_share` | Shots from outside the box ÷ all shots | share 0–1 | Understat `shotZone` | style (attack: directness) |
| `back_three_share` | Minutes in an Understat formation starting with 3 (3-4-3, 3-5-2, …) ÷ all minutes | share 0–1 | Understat `formation`, `time` | structure, not clustered |
| `fouls_pm` | Fouls committed per league match | fouls per match | Football-Data `HF`/`AF` | style (defence: aggression) |
| `fouled_pm` | Fouls suffered per match | fouls per match | Football-Data | not clustered (describes the opponent) |
| `cards_pm` | Yellow cards + 2 × red cards per match | card points per match | Football-Data `HY`, `HR`, `AY`, `AR` | style (defence: aggression) |
| `corners_for_pm` | Corners won per match | corners per match | Football-Data `HC`/`AC` | style (attack: possession) |
| `corners_against_pm` | Corners conceded per match | corners per match | Football-Data | style (defence: territory conceded) |
| `npxg_pm`, `npxga_pm` | Non-penalty expected goals for / against per match | expected goals per match | Understat | outcome (not clustered) |
| `matches_all` | Matches in all competitions | matches per season | Transfermarkt fixtures | exposure |
| `matches_europe` | Champions League and Europa League matches | matches per season | Transfermarkt fixtures (competition type 10, 13) | exposure |
| `short_rest_share` | Share of matches played on fewer than 4 days' rest (gaps over 21 days left out) | share 0–1 | Transfermarkt fixtures | exposure |
| `rest_sd` | Standard deviation of days between matches | days | Transfermarkt fixtures | exposure |
| `top14_share` | Share of league minutes played by the 14 most-used players | share 0–1 | Transfermarkt per-match records | exposure (rotation) |
| `rest_mean` | Mean days between matches | days | Transfermarkt fixtures | dropped (r = −0.90 with `short_rest_share`) |

## 2. Phase-of-play dimensions (Phase 3, `style_dimensions.parquet`, clustered in Phase 4)

Each dimension is the mean of its features' z-scores (standardised over all 1,170 team-seasons, signed as shown),
then re-standardised (mean 0, SD 1), so every dimension weighs the same in Euclidean distance.

| Dimension | Features (sign) |
|---|---|
| `attack_possession` | `opp_ppda` (+), `deep_pm` (+), `corners_for_pm` (+) |
| `attack_patience` | `slow_attack_share` (+) |
| `attack_verticality` | `fast_attack_share` (+) |
| `attack_directness` | `outside_box_share` (+), `set_piece_share` (+) |
| `defence_press` | `ppda` (−) |
| `defence_high_line` | `conceded_fast_share` (+) |
| `defence_territory_conceded` | `deep_against_pm` (+), `corners_against_pm` (+) |
| `defence_aggression` | `fouls_pm` (+), `cards_pm` (+) |

`style_dimensions_relative.parquet`: the same dimensions centred within each league-season and re-standardised
(sensitivity clustering only).

## 3. Clusters (Phase 4, `data/04_clusters/team_season_clusters.parquet`, 1,170 rows)

| Variable | Definition |
|---|---|
| `attack_style`, `defence_style` | K-means (k = 4, 50 starts, seed 42) cluster per phase, named by rule |
| `style` | `attack_style · defence_style`; `rare_style` = combination with fewer than 40 team-seasons |
| `attack_membership`, `defence_membership` | Fuzzy c-means membership (m = 2) in the own style, from the K-means centroids, 0–1; ≥ 0.5 = clear member |
| `*_second_style`, `*_second_membership` | The style with the next-highest membership |
| `*_gmm_p`, `*_gmm_style`, `*_consensus_style` | Gaussian mixture probability and style; consensus-clustering style (checks) |
| `*_k3_style`, `*_rel_style` | Sensitivity clusterings: k = 3 (labelled by majority k = 4 style); K-means on relative dimensions |
| `back_three` | `back_three_share` ≥ 0.5 |

## 4. Injuries (Phase 2, `data/02_injuries/injuries_clean.parquet`, 24,581 rows)

| Variable | Definition | Unit | Missing |
|---|---|---|---|
| `playerId`, `club_id`, `season` | Player, the Big Five club he was at on the injury date (per-match records), season of the start date (summer-2020 rule) | ids | none |
| `start`, `end` | Absence dates as recorded by Transfermarkt | date | none (179 open injuries dropped) |
| `days` | `end − start` | days | none |
| `days_merged` | Days not already covered by an earlier-starting injury of the same player (used for days lost) | days | none |
| `severity` | moderate 8–28 days, severe > 28 days (mild 4–7 days kept in `injuries_mild.parquet`) | band | none |
| `body_area` | From the reviewed label map (`mappings/injury_label_map.csv`), 12 areas + unknown | category | 10–16% unknown per season |
| `surgery` | Label describes an operation | yes/no | none |
| `multi_club_season` | The player was at two clubs that season | flag | none |

## 5. Player-club-seasons (Phase 5, `data/05_injury_analysis/player_seasons.parquet`, 36,525 rows)

| Variable | Definition | Missing |
|---|---|---|
| `appearances`, `minutes` | Appearances and minutes for the club in all competitions | none |
| `age`, `age_band` | Age on 1 January of the season; ≤21, 22–25, 26–29, 30+ | 21 (no date of birth) |
| `position` | Goalkeeper, Defender, Midfielder, Forward (Transfermarkt squad) | none |
| `strength` | Thirds of the team's league points per match over all team-seasons | none |
| `injuries`, `days_lost`, `severe`, `area: …` | Injuries > 7 days that season for the club; days lost (`days_merged`); severe count; counts per body area | none (0 if no injury) |
| `exp_inj`, `exp_inj_str`, `exp_inj_full`, `exp_inj_match`, `exp_inj_match_str` | Expected injuries under each reference (league × season; + strength; + age × position; per team match; per team match + strength) | `exp_inj_full` missing for the 21 without age |
