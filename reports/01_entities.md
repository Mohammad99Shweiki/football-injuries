# Phase 1: Entity resolution

Generated 2026-10-22 by `notebooks/01_entities.ipynb`, where each step is shown with its checks.

## Key findings

- **Every team-season maps.** 1,170 TM team-seasons, each with one Football-Data name and one Understat team (167 clubs). No source name points to two clubs, and no team-season is duplicated.
- **Fixtures confirm the map.** Of 21,589 Football-Data and 21,589 Understat league matches, 21,589 and 21,589 are found in TM with the same home and away club. Scores differ only for 4 awarded results.
- **Names:** 8 club rows score below 75 on names alone or have two rows, and are listed below for review; the fixture check is the stronger evidence for them.
- **Seasons:** canonical key `"2014-15"`. League matches played after 30 June are labelled with the earlier season by every source (the 2019-20 COVID restart ran into July and August 2020), so the date rule (1 July – 30 June) and the season label disagree there. Phase 2 must attribute injuries to club-seasons by squad membership, not by the date rule alone.

## 1. Method

1. **Team-seasons per source:** TM `tm_clubs`; Football-Data home and away names per league-season; Understat `team_id` and title.
2. **Names, within each league-season:** exact match, then equal after normalising (accents, legal forms such as FC/SC/AC, founding years and Football-Data abbreviations removed), each fixed only when unambiguous. The rest are fuzzy: the mean of `rapidfuzz` token-set and token-sort ratios, assigned one-to-one (Hungarian algorithm), so a club can't take two names in one league-season.
3. **Club level:** the league-season matches are collapsed to one row per club in `mappings/team_map.csv`. A row is flagged for review if its worst name score is below 75 or a club has more than one row (a source uses two names or ids for it).
4. **Fixture check (independent of names):** each Football-Data and Understat league match is translated to TM club ids and looked up in TM's fixtures by league, season, home and away club; score and date are compared.

## 2. Results

### Clubs and team-seasons

| source | clubs | team-seasons | team-seasons mapped |
|---|---|---|---|
| Transfermarkt | 167 | 1170 | 1170 |
| Football-Data | 167 | 1170 | 1170 |
| Understat | 168 | 1170 | 1170 |

### How names matched (club rows)

| method (worst over seasons) | Football-Data | Understat |
|---|---|---|
| exact | 8 | 27 |
| normalised | 104 | 99 |
| fuzzy | 56 | 42 |

### For review: name score below 75

Each club is called by its Transfermarkt name (`club`); the other two columns are the names the sources use, kept as join keys.

| tm_club_id | club | fd_name | fd_score | us_name | us_score | leagues | n_seasons |
|---|---|---|---|---|---|---|---|
| 3 | 1.FC Köln | FC Koln | 100.0 | FC Cologne | 54.5 | Bundesliga | 10 |
| 44 | Hertha BSC | Hertha | 87.5 | Hertha Berlin | 72.3 | Bundesliga | 9 |
| 23826 | RB Leipzig | RB Leipzig | 100.0 | RasenBallsport Leipzig | 72.4 | Bundesliga | 10 |
| 714 | RCD Espanyol Barcelona | Espanol | 56.0 | Espanyol | 80.8 | La Liga | 10 |
| 14171 | Thonon Évian Grand Genève FC | Evian Thonon Gaillard | 71.1 | Evian Thonon Gaillard | 71.1 | Ligue 1 | 1 |
| 130 | Parma Calcio 1913 | Parma | 100.0 | Parma | 100.0 | Serie A | 1 |
| 130 | Parma Calcio 1913 | Parma | 100.0 | Parma Calcio 1913 | 100.0 | Serie A | 5 |
| 4172 | Pisa Sporting Club | Pisa | 73.5 | Pisa | 73.5 | Serie A | 1 |

### Clubs with more than one row (a source uses two names or ids)

| tm_club_id | club | fd_name | us_team_id | us_name | first_season | last_season |
|---|---|---|---|---|---|---|
| 130 | Parma Calcio 1913 | Parma | 204 | Parma | 2014-15 | 2014-15 |
| 130 | Parma Calcio 1913 | Parma | 230 | Parma Calcio 1913 | 2018-19 | 2025-26 |

Parma went bankrupt in 2015 and was refounded; Understat gives the new club a new id, while TM keeps one club. Both rows are kept, so each Understat team-season still maps to TM club 130.

### Fixture check

| source | matches | unmapped_team | found_in_tm | same_score | same_date | date_off_1_day | date_off_more |
|---|---|---|---|---|---|---|---|
| Football-Data | 21589 | 0 | 21589 | 21587 | 21583 | 6 | 0 |
| Understat | 21589 | 0 | 21589 | 21585 | 21430 | 154 | 5 |

- `found_in_tm`: same league-season, home and away club in TM. `same_score`: also the same final score.
- Dates: TM stores kick-off in UTC; a one-day difference is a time-zone shift, not a different match. Understat's few larger gaps are postponed matches listed under another date.
- Matches failing a check are in `data/01_entities/fixture_mismatches.csv` (11 rows).

Score differences. All are awarded results, where a source keeps either the score on the pitch or the awarded score; the teams agree in every case:

| league | season | date | home | away | source | source score | TM score |
|---|---|---|---|---|---|---|---|
| Serie A | 2016-17 | 2016-08-28 | US Sassuolo | Delfino Pescara 1936 | Understat | 2-1 | 0-3 |
| Ligue 1 | 2016-17 | 2017-04-16 | SC Bastia | Olympique Lyon | Football-Data | 0-3 | 0-0 |
| Ligue 1 | 2016-17 | 2017-04-16 | SC Bastia | Olympique Lyon | Understat | 0-3 | 0-0 |
| Serie A | 2020-21 | 2020-09-19 | Hellas Verona | AS Roma | Football-Data | 0-0 | 3-0 |
| Serie A | 2020-21 | 2020-09-19 | Hellas Verona | AS Roma | Understat | 0-0 | 3-0 |
| Bundesliga | 2024-25 | 2024-12-14 | 1.FC Union Berlin | VfL Bochum | Understat | 1-1 | 0-2 |

## 3. Seasons

One key across sources, `season = "2014-15"` … `"2025-26"` (`analysis.load.season_key`): Football-Data `season_code` 1415, Understat and TM start year 2014. TM's injury `seasonId` agrees with the date season for 98.3% of in-window injuries (Phase 0).

League matches whose date season (1 July – 30 June) differs from the source's own label:

| source | matches | date season ≠ label | share | where |
|---|---|---|---|---|
| Transfermarkt | 21589 | 221 | 1.0% | La Liga 2019-20: 57, Premier League 2019-20: 66, Serie A 2019-20: 98 |
| Football-Data | 21589 | 221 | 1.0% | La Liga 2019-20: 57, Premier League 2019-20: 66, Serie A 2019-20: 98 |
| Understat | 21589 | 221 | 1.0% | La Liga 2019-20: 57, Premier League 2019-20: 66, Serie A 2019-20: 98 |

## 4. Outputs

- `mappings/team_map.csv`: the reviewed club map (tracked in git). Used as is.
- `data/01_entities/team_map_proposed.csv`: the automatic proposal. Differences from the reviewed map: 0.
- `data/01_entities/team_seasons.csv`: one row per team-season (`league, season_key, season, tm_club_id, club, fd_name, us_team_id, us_name`), the join key for Phase 3.
