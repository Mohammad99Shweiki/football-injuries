# Preprocessing log

Every cleaning and preprocessing step applied to the data, in order. One row per operation.
Choices behind a step are in `DECISIONS.md`; this log records what was done to which data and how many rows it touched.

**Type** (KDD preprocessing step): cleaning · integration · transformation · reduction.
Raw data (`data/raw/`) is never changed: every step reads a table and writes a new output.

## Step 0: Parsing (scraper, before the analysis)

| # | Date | Type | Input | Operation | Rows affected | Output | Where |
|---|---|---|---|---|---|---|---|
| 0.1 | 2026-10-20 | transformation | `data/raw/` (60 CSV, 60 JSON, 27,077 TM JSON) | Raw responses parsed into flat tables. Every value kept as original text; every row keeps `source_file`. Nested JSON fields flattened (`ppda.att`, …). | All | `data/tables/*.csv` (9 tables) | `scraper/parse/` |
| 0.2 | 2026-10-20 | reduction | TM per-match player records | Aggregated to player × season × competition × club (appearances, minutes, participation states), as TM has no such table. | 632,170 rows out | `tm_player_stats` | `scraper/parse/` |
| 0.3 | 2026-10-20 | integration | TM per-match player records | Club fixtures built as the union of all squad players' matches, deduplicated on club + game. | 52,275 rows out | `tm_fixtures` | `scraper/parse/` |

| 0.4 | 2026-10-21 | transformation | `data/raw/understat/team/` (1,170 getTeamData payloads, new) | Team-season statistics flattened to long format: one row per team-season × block × category, values as original text. All 1,170 team-seasons have all attack-speed and situation categories. | 43,813 rows | `data/tables/us_team_stats.csv` | `scraper/parse/understat.py` |

## Phase 0: Data audit

No data changed. Quality problems found here are handled in later phases (see `reports/00_data_audit.md`).

## Phase 1: Entity resolution (integration)

| # | Date | Type | Input | Operation | Rows affected | Output | Where |
|---|---|---|---|---|---|---|---|
| 1.1 | 2026-10-21 | transformation | `fd_matches.season_code`, Understat/TM season | One season key: Football-Data `"1415"` → start year 2014; Understat and TM already use 2014; canonical label `"2014-15"`. | All rows | `season`, `season_key` columns | `01_entities.ipynb` step 1, `load.season_key` |
| 1.2 | 2026-10-21 | cleaning | `fd_matches.Date` | Two date formats parsed: `dd/mm/yyyy` and `dd/mm/yy`. | 15,045 + 6,544 = 21,589 | match dates | `01_entities.ipynb` step 8 |
| 1.3 | 2026-10-21 | cleaning | `us_matches` | Unplayed fixtures (`isResult = false`, Ligue 1 2019-20 cancelled for COVID) dropped. | 101 of 21,690 dropped | 21,589 matches | `01_entities.ipynb` step 8 |
| 1.4 | 2026-10-21 | cleaning | `tm_fixtures` | Kept Big Five league games only; each game appears once per club, so duplicates on `game_id` removed and the home side put first. | 52,275 → 43,178 league rows → 21,589 games | TM league matches | `01_entities.ipynb` step 8 |
| 1.5 | 2026-10-21 | cleaning | Team names, all sources | Normalised for matching only: accents removed, lower case, punctuation removed, Football-Data abbreviations expanded (Ath, Nott'm, St, …), legal forms and founding years dropped. Original names are kept. | 167 TM, 167 FD, 168 Understat names | (comparison only) | `01_entities.ipynb` step 2 |
| 1.6 | 2026-10-21 | integration | TM, FD and Understat team-seasons (1,170 each) | Teams matched within each league-season: exact, then normalised, then fuzzy with one-to-one assignment (Hungarian). Club rows by worst method: FD 8 exact / 104 normalised / 56 fuzzy; Understat 27 / 99 / 42. | 1,170 × 2 team-seasons, all mapped | `mappings/team_map.csv` (168 rows) | `01_entities.ipynb` steps 3–5 |
| 1.7 | 2026-10-21 | integration | Team map | One name per club, `club` = Transfermarkt's name. FD and Understat names kept only as join keys. | 167 clubs | `club` column | `01_entities.ipynb` step 1 |
| 1.8 | 2026-10-21 | integration | Team map + TM team-seasons | Team-season table built from the reviewed map: one row per team-season with TM id, `club`, FD name and Understat id. | 1,170 rows, 0 missing, 0 duplicates | `data/01_entities/team_seasons.csv` | `01_entities.ipynb` step 7 |
| 1.9 | 2026-10-21 | cleaning (conflict check) | FD and Understat matches vs TM fixtures | Each match looked up in TM by mapped home and away club. All found. Conflicts found and **left as they are**: 4 awarded results (score differs), date gaps (6 FD and 154 Understat by 1 day from UTC times; 5 Understat postponed matches). | 21,589 × 2 checked; 11 mismatch rows | `data/01_entities/fixture_mismatches.csv` | `01_entities.ipynb` step 9 |
| 1.10 | 2026-10-21 | cleaning (conflict check) | Match dates vs season labels | 221 matches of 2019-20 played in July–August 2020 (COVID restart) carry the 2019-20 label in all sources. Labels kept; affects injury attribution in Phase 2. | 221 of 21,589 | report only | `01_entities.ipynb` step 10 |

## Phase 2: Injury cleaning and body-area mapping (cleaning + transformation)

| # | Date | Type | Input | Operation | Rows affected | Output | Where |
|---|---|---|---|---|---|---|---|
| 2.1 | 2026-10-21 | cleaning | `tm_injuries` (82,075) | Parsed start/end dates, `days` (= end − start, checked on every row) and games missed. Dropped records without a start date and exact repeats (player + start + end + label); several diagnoses on one absence kept (482 records). | 82,075 → 82,068 (4 no start, 3 repeats) | injuries | `02_injuries.ipynb` step 1 |
| 2.2 | 2026-10-21 | integration | raw `performance-game` (12,848 files, read only) | Each player's club matches (date, club, competition, season, participation state). National-team games and "played for a different team" rows left out for club placement. | 6,890,581 rows → 6,165,063 club rows | `data/02_injuries/player_matches.parquet` | step 2 |
| 2.3 | 2026-10-21 | transformation | injuries | Season by date (1 July – 30 June); summer 2020: injuries up to the player's club's last 2019-20 match stay in 2019-20. Agrees with TM `seasonId` for 98.6%. | 467 of 705 July–August 2020 records kept in 2019-20 | `season` | step 3 |
| 2.4 | 2026-10-21 | cleaning | injuries | Kept seasons 2014-15 to 2025-26; dropped open injuries (no end date, no expected return). | 82,068 → 71,374 → 71,195 (10,694 outside window, 179 open) | injuries | step 4 |
| 2.5 | 2026-10-21 | integration | injuries + club matches | Club on the injury date: last club match on or before it in the same season (65,484), else first match after (4,455); none found for 1,256. | 71,195 records placed | `club_id`, `club_from` | step 5 |
| 2.6 | 2026-10-21 | integration | `tm_player_stats`, club matches, `01_entities/team_seasons` | Big Five membership: player-club-season with ≥ 1 appearance (35,111) or ≥ 1 match marked injured (1,414). 3,785 player-club-seasons at two Big Five clubs in a season. | 36,525 player-club-seasons (34,626 player-seasons) | `data/02_injuries/player_club_seasons.parquet` | step 6 |
| 2.7 | 2026-10-21 | reduction | injuries | Kept injuries at a Big Five club-season the player belongs to. Dropped: at a non-Big Five club 32,244; no club match that season 1,256; Big Five club but not a member 141. | 71,195 → 37,554 | injuries | step 6 |
| 2.8 | 2026-10-21 | transformation | 315 injury labels | Label map by ordered keyword rules, then reviewed: class (injury / non-injury with reason), body area (12 groups), surgery flag (559 injuries > 7 days). No injury type. 127 labels cover 95% of injuries > 7 days. | 315 labels | `mappings/injury_label_map.csv` (reviewed) | step 7 |
| 2.9 | 2026-10-21 | cleaning | injuries + label map | Removed non-injuries, kept separately: illness 4,035, fitness 953, rest 334, medical condition 132, not from football 12. Flag `after_injury` = starts within 3 days after an injury ended (fitness 664, illness 84, rest 13, medical 3). | 37,554 → 32,088 (5,466) | `data/02_injuries/non_injuries.parquet` | step 8 |
| 2.10 | 2026-10-21 | reduction | injuries | Kept injuries lasting more than 7 days (main data). Injuries of 4–7 days (mild) kept in a separate file for the > 3-day sensitivity check; 2,327 of 0–3 days dropped. | 32,088 → 24,581 (7,507 out: 5,180 mild kept separately, 2,327 dropped) | injuries; `data/02_injuries/injuries_mild.parquet` | step 9 |
| 2.11 | 2026-10-21 | transformation | injuries | Severity bands: moderate 8–28 days (13,588), severe > 28 days (10,993). League, `season_key`, `club` and multi-club flag added from Phase 1 and step 6. | 24,581 | `data/02_injuries/injuries_clean.parquet` | step 9 |

## Phase 3: Team-season features (transformation + reduction)

| # | Date | Type | Input | Operation | Rows affected | Output | Where |
|---|---|---|---|---|---|---|---|
| 3.1 | 2026-10-21 | transformation | `us_team_matches` (43,178) | Aggregated to team-seasons: PPDA = Σ passes allowed / Σ defensive actions, opponent PPDA likewise; deep completions for and against, npxG, npxGA per match. | 43,178 → 1,170 | Understat features | `03_features.ipynb` step 2 |
| 3.2 | 2026-10-21 | transformation | `fd_matches` (21,589) | Each match split into home and away team rows (43,178), aggregated per team-season: fouls committed and suffered, cards (yellow + 2 × red), corners for and against per match; means over matches with the statistic (3 matches lack them). Shots on target computed but not used. | 21,589 → 1,170 | Football-Data features | step 3 |
| 3.3 | 2026-10-21 | transformation | `tm_fixtures` (52,275) | Per club-season, all official competitions: matches, European/international club matches (types 10 and 13), rest days between consecutive matches; 369 gaps > 21 days (breaks) left out of rest features. | 52,275 → 1,170 | workload features | step 4 |
| 3.4 | 2026-10-21 | transformation | `02_injuries/player_club_seasons` (36,525) | Share of club minutes (all competitions) played by its top 14 players (HHI checked, r = 0.98). | 36,525 → 1,170 | rotation feature | step 5 |
| 3.5 | 2026-10-21 | integration | the four feature tables + team-season keys | Joined on Phase 1 keys; 23 features (after the 2026-10-21 rework with Understat team statistics), none missing; league match counts agree between Understat and Football-Data. | 1,170 | features | step 6 |
| 3.6 | 2026-10-21 | reduction | 23 features | Dropped `rest_mean` (\|r\| > 0.9 with `short_rest_share`). | 23 → 22 features | — | steps 8–9 |
| 3.7 | 2026-10-21 | transformation | 22 features | Z-scores over all 1,170 team-seasons (global standardisation). Raw values kept alongside. Roles: 15 style (clustered via 3.9), 2 outcome, 5 exposure. | 1,170 | `data/03_features/team_season_features.parquet` | step 9 |
| 3.8 | 2026-10-21 | transformation | `us_team_stats` (43,813) | Six style shares per team-season (fast/slow attack, conceded fast attack, set pieces, outside-box shots, back-three minutes). | 43,813 → 1,170 | style features | `03_features.ipynb` step 3 |
| 3.9 | 2026-10-21 | transformation | 15 style features (z-scores) | Combined into 8 equal-weight style dimensions (signed mean, re-standardised); every style feature used once. | 1,170 | `data/03_features/style_dimensions.parquet` | step 11 |

## Phase 5: Injury analysis (pattern evaluation)

| # | Date | Type | Input | Operation | Rows affected | Output | Where |
|---|---|---|---|---|---|---|---|
| 5.1 | 2026-10-21 | integration | `02_injuries/player_club_seasons` (36,525), clusters, Phase 3 exposure, points per match, `tm_squads` | Player-club-season table: team style (k = 7, k = 4), strength third, workload, position (all players) and age on 1 January of the season (21 missing DOB), injuries > 7 days aggregated per player-club-season (24,581 → all matched), days lost, severe, surgery, counts by body area, mild injuries (5,180) and fitness absences (953). | 36,525 rows, 10,340 players, 1,170 team-seasons | `data/05_injury_analysis/player_seasons.parquet` | `05_injury_analysis.ipynb` step 1 |
| 5.2 | 2026-10-21 | transformation | player-seasons | Expected injuries and days lost per player-season: league mean (indirect standardisation) and league × age band × position mean. | 36,525 (36,504 with age) | `exp_*` columns | step 2 |
| 5.3 | 2026-10-21 | transformation | team-season style dimensions + clusters | Typicality per team-season (own-centroid distance ÷ next-centroid distance); core = ≤ 0.8: 618 of 1,170 team-seasons; era label per season. | 1,170 | `core`, `era` columns | `05_injury_analysis.ipynb` step 12 |
| 5.4 | 2026-10-21 | reduction | 1,170 team-seasons; player-seasons | League-season aggregates for the style–injury links (dimension means, injury outcomes per league-season). | 1,170 → 60; 36,525 → 60 | in-notebook tables | step 18 |
