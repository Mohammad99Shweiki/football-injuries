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
