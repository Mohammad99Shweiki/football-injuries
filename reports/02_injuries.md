# Phase 2: Injury cleaning and body-area mapping

Generated 2026-10-25 by `notebooks/02_injuries.ipynb`, where each step is shown with its checks.

## Key findings

- **24,555 injuries lasting more than 7 days** remain, tied to 15,731 player-seasons at Big Five clubs; 44.8% are severe (> 28 days).
- **Membership:** 36,525 player-club-seasons belong to a Big Five club-season (1,414 of them only through matches marked injured).
- **Non-injuries removed:** 5,492 records (2,381 over 7 days), kept separately below. *Fitness* absences stay out of the injury count and are a secondary outcome in Phase 5; 663 of 953 start within 3 days after an injury ended (reconditioning).
- **Mild injuries (4–7 days):** 5,180 kept separately for the > 3-day sensitivity check in Phase 5.
- **Unknown body area:** 12.8% of injuries overall; per season below.
- **Label map:** 315 labels; 127 labels cover 95% of injuries over 7 days. Reviewed file used; 5 labels differ from the proposal.

## 1. Steps and row counts

| step | operation | rows before | rows after | removed |
|---|---|---|---|---|
| 2.1 | drop records without a start date | 82075 | 82071 | 4 |
| 2.1 | drop exact repeats (player + start + end + label) | 82071 | 82068 | 3 |
| 2.4 | keep seasons 2014-15 to 2025-26 | 82068 | 71374 | 10694 |
| 2.4 | drop open injuries (no end date) | 71374 | 71195 | 179 |
| 2.6 | keep injuries at a Big Five club-season the player belongs to | 71195 | 37554 | 33641 |
| 2.8 | remove non-injuries (illness, fitness, rest, medical, not from football) | 37554 | 32062 | 5492 |
| 2.9 | keep injuries lasting more than 7 days (5,180 of 4–7 days kept separately as mild) | 32062 | 24555 | 7507 |
| 2.9b | days lost without double counting: 184 overlapping injuries lose 7,850 of 1,112,867 days | 24555 | 24555 | 0 |

Records by where the injury happened (step 6, all durations):

| scope | records |
|---|---|
| kept | 37554 |
| at a non-Big Five club | 32244 |
| no club match that season | 1256 |
| Big Five club, not a member | 141 |

## 2. Non-injuries

| reason | records | over_7_days | right_after_an_injury |
|---|---|---|---|
| fitness | 953 | 668 | 663 |
| illness | 4035 | 1560 | 84 |
| medical condition | 158 | 132 | 3 |
| not from football | 12 | 5 | 0 |
| rest | 334 | 16 | 13 |

## 3. Body areas (injuries > 7 days)

| body area | injuries | share |
|---|---|---|
| unspecified muscle | 4357 | 17.7% |
| knee | 3624 | 14.8% |
| hamstring | 3249 | 13.2% |
| unknown | 3142 | 12.8% |
| groin/adductor/hip | 2305 | 9.4% |
| ankle | 2155 | 8.8% |
| calf/achilles/lower leg | 1882 | 7.7% |
| thigh | 1069 | 4.4% |
| upper body | 1023 | 4.2% |
| foot/toe | 837 | 3.4% |
| back/spine | 533 | 2.2% |
| head/neck | 379 | 1.5% |

Injury type (tissue) by body area, injuries over 7 days (*unspecified*: the label names only a place):

| body area | fracture/bone | impact | ligament/joint | muscle | other | tendon | unspecified | all |
|---|---|---|---|---|---|---|---|---|
| ankle | 25 | 35 | 566 | 0 | 7 | 0 | 1522 | 2155 |
| back/spine | 11 | 9 | 0 | 0 | 90 | 0 | 423 | 533 |
| calf/achilles/lower leg | 129 | 34 | 0 | 1350 | 2 | 326 | 41 | 1882 |
| foot/toe | 203 | 74 | 4 | 0 | 0 | 29 | 527 | 837 |
| groin/adductor/hip | 0 | 24 | 0 | 1676 | 276 | 0 | 329 | 2305 |
| hamstring | 0 | 0 | 0 | 3244 | 0 | 5 | 0 | 3249 |
| head/neck | 102 | 100 | 0 | 0 | 2 | 0 | 175 | 379 |
| knee | 10 | 99 | 1246 | 0 | 68 | 78 | 2123 | 3624 |
| thigh | 4 | 342 | 0 | 723 | 0 | 0 | 0 | 1069 |
| unknown | 112 | 1009 | 302 | 0 | 42 | 124 | 1553 | 3142 |
| unspecified muscle | 0 | 15 | 0 | 4342 | 0 | 0 | 0 | 4357 |
| upper body | 246 | 64 | 20 | 83 | 6 | 0 | 604 | 1023 |
| all | 842 | 1805 | 2138 | 11418 | 493 | 562 | 7297 | 24555 |

Injuries whose label describes an operation (surgery flag): 559, by body area:

| body area | injuries with surgery |
|---|---|
| knee | 234 |
| unknown | 104 |
| ankle | 92 |
| groin/adductor/hip | 67 |
| foot/toe | 23 |
| calf/achilles/lower leg | 21 |
| head/neck | 17 |
| upper body | 1 |

## 4. Coverage per season

| season | injuries > 7 d | severe | unknown body area | unspecified muscle | surgery |
|---|---|---|---|---|---|
| 2014-15 | 1741 | 835 | 15.7% | 12.8% | 48 |
| 2015-16 | 1832 | 841 | 13.5% | 14.4% | 37 |
| 2016-17 | 2120 | 997 | 12.2% | 18.4% | 47 |
| 2017-18 | 2014 | 861 | 9.9% | 21.6% | 28 |
| 2018-19 | 2295 | 972 | 13.6% | 18.0% | 40 |
| 2019-20 | 2166 | 930 | 9.6% | 17.4% | 54 |
| 2020-21 | 2070 | 821 | 15.6% | 21.2% | 51 |
| 2021-22 | 1915 | 853 | 14.3% | 18.9% | 48 |
| 2022-23 | 1932 | 910 | 14.1% | 15.5% | 50 |
| 2023-24 | 2065 | 1001 | 13.9% | 17.2% | 53 |
| 2024-25 | 2206 | 1016 | 12.1% | 17.7% | 59 |
| 2025-26 | 2199 | 952 | 10.1% | 18.5% | 44 |

## 5. Coverage per league

| league | injuries > 7 d | severe | unknown body area | unspecified muscle | surgery |
|---|---|---|---|---|---|
| Bundesliga | 5218 | 2475 | 10.3% | 22.6% | 152 |
| La Liga | 4447 | 1995 | 6.6% | 29.1% | 34 |
| Ligue 1 | 3338 | 1510 | 9.1% | 7.4% | 51 |
| Premier League | 5148 | 2634 | 13.7% | 6.6% | 149 |
| Serie A | 6404 | 2375 | 20.3% | 20.3% | 173 |

## 6. Outputs

- `mappings/injury_label_map.csv`: the reviewed label map (in git). Reviewed file used; 5 labels differ from the proposal.
- `data/02_injuries/injuries_clean.parquet`: 24,555 injuries > 7 days with club-season, severity, body area and surgery flag.
- `data/02_injuries/injuries_mild.parquet`: 5,180 injuries of 4–7 days (sensitivity check only).
- `data/02_injuries/non_injuries.parquet`: 5,492 removed non-injury records with reason and `after_injury` flag.
- `data/02_injuries/player_club_seasons.parquet`: 36,525 player-club-seasons (membership, appearances, minutes), the denominator for Phase 5.
- `data/02_injuries/player_matches.parquet`: every player's club matches from the raw files (cache).
- `data/02_injuries/preprocessing_counts.csv`: the row counts above.
