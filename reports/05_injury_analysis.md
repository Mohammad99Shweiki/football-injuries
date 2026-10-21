# Phase 5: Injury analysis

Generated 2026-10-21 by `notebooks/05_injury_analysis.ipynb`, where each step is shown with its checks.

## Key numbers

- 36,525 player-club-seasons, 24,581 injuries > 7 days, 1,113,471 days lost.
- Attacking style: injury RR CI excludes 1 for Positional possession 1.24, Counter-attack 0.90, Direct play 0.95; days RR for Positional possession 1.09; robust in every sensitivity check: Positional possession, Counter-attack.
- Defensive style: injury RR CI excludes 1 for High press, high line 1.14, Aggressive duel press 0.93, Low block 0.94; days RR for none; robust in every sensitivity check: High press, high line, Low block.
- Formation: injury RR CI excludes 1 for none; days RR for none; robust in every sensitivity check: none.

## 1. Injuries by style

### Attacking style

| attacking style | player-seasons | team-seasons | injuries | injuries / player-season | per 1,000 min | days lost / player-season | severe share | excess / 100 player-seasons | excess days / player-season | RR (95% CI) | days RR (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Positional possession | 5417 | 174 | 4605 | 0.85 | 0.516 | 34.0 | 0.396 | 16.7 | 2.7 | 1.24 (1.18–1.30) | 1.09 (1.02–1.15) |
| Build-up into the box | 11095 | 355 | 7558 | 0.681 | 0.467 | 31.0 | 0.447 | 0.5 | 0.1 | 1.01 (0.97–1.04) | 1.00 (0.96–1.05) |
| Counter-attack | 8553 | 279 | 5113 | 0.598 | 0.442 | 29.2 | 0.474 | -6.8 | -1.3 | 0.90 (0.85–0.94) | 0.96 (0.90–1.02) |
| Direct play | 11460 | 362 | 7305 | 0.637 | 0.482 | 29.3 | 0.461 | -3.2 | -0.4 | 0.95 (0.91–0.99) | 0.99 (0.94–1.04) |

### Defensive style

| defensive style | player-seasons | team-seasons | injuries | injuries / player-season | per 1,000 min | days lost / player-season | severe share | excess / 100 player-seasons | excess days / player-season | RR (95% CI) | days RR (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| High press, high line | 7548 | 245 | 5683 | 0.753 | 0.471 | 32.1 | 0.427 | 9.5 | 1.0 | 1.14 (1.09–1.20) | 1.03 (0.98–1.09) |
| Compact mid-block | 8859 | 289 | 5839 | 0.659 | 0.44 | 27.8 | 0.414 | 1.8 | -0.8 | 1.03 (0.97–1.08) | 0.97 (0.92–1.03) |
| Aggressive duel press | 9059 | 286 | 5754 | 0.635 | 0.473 | 29.2 | 0.457 | -4.6 | 0.0 | 0.93 (0.89–0.98) | 1.00 (0.95–1.06) |
| Low block | 11059 | 350 | 7305 | 0.661 | 0.51 | 32.6 | 0.482 | -4.1 | -0.1 | 0.94 (0.90–0.98) | 1.00 (0.95–1.04) |

### Combined style

| combined style | player-seasons | team-seasons | injuries | injuries / player-season | per 1,000 min | days lost / player-season | severe share | excess / 100 player-seasons | excess days / player-season | RR (95% CI) | days RR (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Positional possession · High press, high line | 3254 | 104 | 2803 | 0.861 | 0.511 | 34.3 | 0.396 | 18.9 | 2.7 | 1.28 (1.20–1.36) | 1.09 (1.01–1.16) |
| Positional possession · Compact mid-block | 1745 | 57 | 1407 | 0.806 | 0.492 | 30.4 | 0.372 | 11.1 | 0.3 | 1.16 (1.07–1.26) | 1.01 (0.90–1.14) |
| Build-up into the box · High press, high line | 2207 | 72 | 1526 | 0.691 | 0.437 | 30.7 | 0.448 | 0.8 | -1.4 | 1.01 (0.93–1.11) | 0.96 (0.87–1.04) |
| Build-up into the box · Compact mid-block | 3580 | 117 | 2499 | 0.698 | 0.452 | 29.0 | 0.414 | 4.6 | -0.2 | 1.07 (1.00–1.14) | 0.99 (0.92–1.07) |
| Build-up into the box · Aggressive duel press | 1890 | 59 | 1257 | 0.665 | 0.475 | 28.2 | 0.419 | -1.2 | -0.2 | 0.98 (0.89–1.07) | 0.99 (0.88–1.11) |
| Build-up into the box · Low block | 3418 | 107 | 2276 | 0.666 | 0.504 | 34.7 | 0.499 | -3.1 | 1.5 | 0.96 (0.90–1.01) | 1.04 (0.96–1.13) |
| Counter-attack · Compact mid-block | 1483 | 49 | 735 | 0.496 | 0.348 | 24.3 | 0.468 | -9.5 | -2.8 | 0.84 (0.71–0.97) | 0.90 (0.75–1.04) |
| Counter-attack · Aggressive duel press | 2805 | 91 | 1639 | 0.584 | 0.431 | 28.1 | 0.473 | -7.8 | -1.3 | 0.88 (0.79–0.96) | 0.96 (0.85–1.06) |
| Counter-attack · Low block | 3520 | 114 | 2245 | 0.638 | 0.492 | 31.4 | 0.47 | -7.0 | -1.3 | 0.90 (0.83–0.97) | 0.96 (0.87–1.04) |
| Direct play · High press, high line | 1342 | 44 | 860 | 0.641 | 0.434 | 28.4 | 0.449 | 4.7 | 0.4 | 1.08 (0.95–1.22) | 1.01 (0.89–1.14) |
| Direct play · Compact mid-block | 2051 | 66 | 1198 | 0.584 | 0.43 | 26.0 | 0.427 | -2.9 | -1.4 | 0.95 (0.85–1.05) | 0.95 (0.84–1.07) |
| Direct play · Aggressive duel press | 4132 | 129 | 2622 | 0.635 | 0.484 | 29.2 | 0.464 | -5.9 | -0.0 | 0.91 (0.85–0.98) | 1.00 (0.92–1.09) |
| Direct play · Low block | 3935 | 123 | 2625 | 0.667 | 0.527 | 31.5 | 0.476 | -3.3 | -0.5 | 0.95 (0.88–1.02) | 0.98 (0.90–1.06) |

### Formation

| formation | player-seasons | team-seasons | injuries | injuries / player-season | per 1,000 min | days lost / player-season | severe share | excess / 100 player-seasons | excess days / player-season | RR (95% CI) | days RR (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| back three | 7016 | 220 | 5245 | 0.748 | 0.553 | 31.5 | 0.406 | 0.5 | -0.0 | 1.01 (0.97–1.05) | 1.00 (0.94–1.06) |
| back four | 29509 | 950 | 19336 | 0.655 | 0.456 | 30.2 | 0.458 | -0.1 | 0.0 | 1.00 (0.97–1.02) | 1.00 (0.97–1.03) |

Injury RR, attacking style (rows) × defensive style (columns):

| attack \ defence | High press, high line | Compact mid-block | Aggressive duel press | Low block |
|---|---|---|---|---|
| Positional possession | 1.28 | 1.16 | 1.44 | 1.18 |
| Build-up into the box | 1.01 | 1.07 | 0.98 | 0.96 |
| Counter-attack | 1.04 | 0.84 | 0.88 | 0.9 |
| Direct play | 1.08 | 0.95 | 0.91 | 0.95 |

Days lost RR:

| attack \ defence | High press, high line | Compact mid-block | Aggressive duel press | Low block |
|---|---|---|---|---|
| Positional possession | 1.09 | 1.01 | 1.58 | 1.16 |
| Build-up into the box | 0.96 | 0.99 | 0.99 | 1.04 |
| Counter-attack | 1.07 | 0.9 | 0.96 | 0.96 |
| Direct play | 1.01 | 0.95 | 1.0 | 0.98 |

![Rates](figures/05_rates_by_style.png)

![Grid](figures/05_attack_defence_grid.png)

## 2. Body areas by style (relative to the league's share; median over leagues, leagues above 1)

### Attacking style (pooled chi² p = 6.3e-08, Cramér's V = 0.036)

| attacking style | unspecified muscle | knee | hamstring | groin/adductor/hip | ankle | calf/achilles/lower leg | thigh | upper body |
|---|---|---|---|---|---|---|---|---|
| Positional possession | 1.19 | 0.92 | 1.08 | 1.04 | 1.04 | 1.08 | 0.87 | 0.99 |
| Build-up into the box | 1.02 | 0.99 | 1.07 | 0.96 | 1.12 | 1.01 | 0.85 | 0.92 |
| Counter-attack | 0.81 | 1.02 | 0.91 | 1.05 | 0.93 | 0.86 | 1.08 | 1.1 |
| Direct play | 0.92 | 1.08 | 0.96 | 1.0 | 0.92 | 0.96 | 1.0 | 1.01 |

| attacking style | unspecified muscle | knee | hamstring | groin/adductor/hip | ankle | calf/achilles/lower leg | thigh | upper body |
|---|---|---|---|---|---|---|---|---|
| Positional possession | 3 | 0 | 4 | 3 | 3 | 3 | 2 | 2 |
| Build-up into the box | 3 | 2 | 3 | 2 | 5 | 3 | 2 | 2 |
| Counter-attack | 1 | 5 | 2 | 4 | 1 | 1 | 3 | 5 |
| Direct play | 2 | 4 | 1 | 3 | 1 | 2 | 2 | 3 |

### Defensive style (pooled chi² p = 9.8e-22, Cramér's V = 0.051)

| defensive style | unspecified muscle | knee | hamstring | groin/adductor/hip | ankle | calf/achilles/lower leg | thigh | upper body |
|---|---|---|---|---|---|---|---|---|
| High press, high line | 1.09 | 0.94 | 1.05 | 1.04 | 1.04 | 0.96 | 0.97 | 1.08 |
| Compact mid-block | 1.02 | 0.97 | 1.06 | 1.05 | 1.04 | 0.91 | 1.03 | 0.96 |
| Aggressive duel press | 0.93 | 1.11 | 0.97 | 0.96 | 0.94 | 1.03 | 0.96 | 0.98 |
| Low block | 0.9 | 1.03 | 0.8 | 0.92 | 0.99 | 1.1 | 1.05 | 0.9 |

| defensive style | unspecified muscle | knee | hamstring | groin/adductor/hip | ankle | calf/achilles/lower leg | thigh | upper body |
|---|---|---|---|---|---|---|---|---|
| High press, high line | 4 | 0 | 4 | 5 | 3 | 1 | 2 | 3 |
| Compact mid-block | 5 | 1 | 3 | 3 | 3 | 1 | 4 | 1 |
| Aggressive duel press | 1 | 4 | 2 | 1 | 1 | 3 | 2 | 2 |
| Low block | 2 | 3 | 1 | 2 | 2 | 4 | 4 | 2 |

### Formation (pooled chi² p = 0.00069, Cramér's V = 0.036)

| formation | unspecified muscle | knee | hamstring | groin/adductor/hip | ankle | calf/achilles/lower leg | thigh | upper body |
|---|---|---|---|---|---|---|---|---|
| back three | 1.04 | 0.94 | 1.04 | 0.93 | 0.98 | 1.02 | 0.91 | 0.94 |
| back four | 0.97 | 1.01 | 0.98 | 1.01 | 1.01 | 1.0 | 1.02 | 1.01 |

| formation | unspecified muscle | knee | hamstring | groin/adductor/hip | ankle | calf/achilles/lower leg | thigh | upper body |
|---|---|---|---|---|---|---|---|---|
| back three | 3 | 2 | 3 | 1 | 1 | 3 | 2 | 2 |
| back four | 2 | 3 | 2 | 4 | 4 | 2 | 3 | 3 |

![Body areas](figures/05_body_areas_by_style.png)

## 3. Seasons

| season | player-seasons | injuries / player-season | days lost / player-season | severe share | unknown body area |
|---|---|---|---|---|---|
| 2014-15 | 2939 | 0.592 | 29.1 | 0.48 | 0.157 |
| 2015-16 | 3008 | 0.61 | 29.6 | 0.458 | 0.137 |
| 2016-17 | 3005 | 0.707 | 33.4 | 0.47 | 0.123 |
| 2017-18 | 2997 | 0.672 | 29.6 | 0.427 | 0.099 |
| 2018-19 | 2944 | 0.781 | 33.0 | 0.423 | 0.138 |
| 2019-20 | 3032 | 0.714 | 31.9 | 0.429 | 0.096 |
| 2020-21 | 3161 | 0.655 | 26.3 | 0.396 | 0.156 |
| 2021-22 | 3233 | 0.594 | 25.7 | 0.445 | 0.145 |
| 2022-23 | 3148 | 0.614 | 28.1 | 0.471 | 0.142 |
| 2023-24 | 3144 | 0.657 | 32.5 | 0.484 | 0.14 |
| 2024-25 | 3012 | 0.733 | 35.4 | 0.46 | 0.122 |
| 2025-26 | 2902 | 0.758 | 32.0 | 0.433 | 0.101 |

![Trend](figures/05_season_trend.png)

![Shares](figures/05_style_shares_by_league.png)

## 4. Leagues

| league | player-seasons | team-seasons | injuries | injuries / player-season | per 1,000 min | days lost / player-season | severe share | excess / 100 player-seasons | excess days / player-season | RR (95% CI) | days RR (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Premier League | 7524 | 240 | 5151 | 0.685 | 0.451 | 36.2 | 0.512 | 0.0 | 0.0 | 1.00 (0.95–1.05) | 1.00 (0.94–1.06) |
| La Liga | 7429 | 240 | 4451 | 0.599 | 0.402 | 26.9 | 0.448 | 0.0 | 0.0 | 1.00 (0.94–1.07) | 1.00 (0.93–1.06) |
| Serie A | 7787 | 240 | 6410 | 0.823 | 0.608 | 30.4 | 0.371 | 0.0 | 0.0 | 1.00 (0.96–1.04) | 1.00 (0.95–1.05) |
| Bundesliga | 6616 | 216 | 5227 | 0.79 | 0.593 | 37.7 | 0.474 | 0.0 | 0.0 | 1.00 (0.96–1.04) | 1.00 (0.95–1.05) |
| Ligue 1 | 7169 | 234 | 3342 | 0.466 | 0.334 | 21.5 | 0.452 | -0.0 | 0.0 | 1.00 (0.93–1.07) | 1.00 (0.93–1.08) |

Attacking style RR within each league:

| league | Positional possession | Build-up into the box | Counter-attack | Direct play |
|---|---|---|---|---|
| Premier League | 1.25 | 0.94 | 0.91 | 0.93 |
| La Liga | 1.61 | 1.01 | 0.88 | 0.89 |
| Serie A | 1.08 | 0.98 | 0.97 | 0.99 |
| Bundesliga | 1.08 | 1.01 | 0.95 | 1.01 |
| Ligue 1 | 1.47 | 1.17 | 0.71 | 0.9 |

Defensive style RR within each league:

| league | High press, high line | Compact mid-block | Aggressive duel press | Low block |
|---|---|---|---|---|
| Premier League | 1.16 | 1.03 | 1.08 | 0.9 |
| La Liga | 1.42 | 1.12 | 0.89 | 0.5 |
| Serie A | 0.95 | 1.08 | 0.94 | 1.02 |
| Bundesliga | 1.06 | 1.04 | 0.97 | 0.96 |
| Ligue 1 | 1.22 | 0.87 | 0.93 | 1.01 |

![Within league](figures/05_style_within_league.png)

## 5. Age and position

| attacking style | RR, league | RR, league × age × position | days RR, league | days RR, league × age × position | mean age | Defender | Forward | Goalkeeper | Midfielder |
|---|---|---|---|---|---|---|---|---|---|
| Positional possession | 1.24 | 1.27 | 1.09 | 1.11 | 25.7 | 0.34 | 0.26 | 0.09 | 0.31 |
| Build-up into the box | 1.01 | 1.02 | 1.0 | 1.01 | 25.7 | 0.34 | 0.28 | 0.08 | 0.3 |
| Counter-attack | 0.9 | 0.88 | 0.96 | 0.95 | 26.2 | 0.34 | 0.28 | 0.09 | 0.29 |
| Direct play | 0.95 | 0.94 | 0.99 | 0.98 | 26.0 | 0.33 | 0.29 | 0.08 | 0.3 |

| defensive style | RR, league | RR, league × age × position | days RR, league | days RR, league × age × position | mean age | Defender | Forward | Goalkeeper | Midfielder |
|---|---|---|---|---|---|---|---|---|---|
| High press, high line | 1.14 | 1.16 | 1.03 | 1.05 | 25.5 | 0.34 | 0.26 | 0.09 | 0.31 |
| Compact mid-block | 1.03 | 1.03 | 0.97 | 0.98 | 25.8 | 0.34 | 0.28 | 0.09 | 0.3 |
| Aggressive duel press | 0.93 | 0.93 | 1.0 | 1.0 | 26.1 | 0.34 | 0.28 | 0.09 | 0.3 |
| Low block | 0.94 | 0.93 | 1.0 | 0.99 | 26.1 | 0.34 | 0.29 | 0.08 | 0.29 |

| formation | RR, league | RR, league × age × position | days RR, league | days RR, league × age × position | mean age | Defender | Forward | Goalkeeper | Midfielder |
|---|---|---|---|---|---|---|---|---|---|
| back three | 1.01 | 1.01 | 1.0 | 1.0 | 25.9 | 0.35 | 0.26 | 0.09 | 0.3 |
| back four | 1.0 | 1.0 | 1.0 | 1.0 | 25.9 | 0.34 | 0.28 | 0.09 | 0.3 |

## 6. Team strength and workload

Attacking style RR within strength thirds:

| strength | Positional possession | Build-up into the box | Counter-attack | Direct play |
|---|---|---|---|---|
| middle third | 1.1 | 0.95 | 0.92 | 0.98 |
| stronger third | 1.25 | 1.1 | 1.0 | 1.09 |
| weaker third | 1.42 | 0.92 | 0.86 | 0.91 |

Attacking style RR within congestion thirds:

| congestion | Positional possession | Build-up into the box | Counter-attack | Direct play |
|---|---|---|---|---|
| busiest third | 1.29 | 1.05 | 1.06 | 1.16 |
| lightest third | 1.06 | 1.0 | 0.91 | 0.91 |
| middle third | 1.21 | 0.95 | 0.81 | 0.89 |

Defensive style RR within strength thirds:

| strength | High press, high line | Compact mid-block | Aggressive duel press | Low block |
|---|---|---|---|---|
| middle third | 1.12 | 0.93 | 0.92 | 0.95 |
| stronger third | 1.19 | 1.13 | 1.15 | 1.01 |
| weaker third | 0.81 | 0.91 | 0.86 | 0.93 |

Defensive style RR within congestion thirds:

| congestion | High press, high line | Compact mid-block | Aggressive duel press | Low block |
|---|---|---|---|---|
| busiest third | 1.23 | 1.13 | 1.13 | 0.95 |
| lightest third | 0.94 | 0.99 | 0.86 | 0.97 |
| middle third | 1.04 | 0.92 | 0.89 | 0.9 |

By congestion:

| congestion | player-seasons | team-seasons | injuries | injuries / player-season | per 1,000 min | days lost / player-season | severe share | excess / 100 player-seasons | excess days / player-season | RR (95% CI) | days RR (95% CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| lightest third | 12400 | 397 | 8048 | 0.649 | 0.521 | 29.7 | 0.455 | -4.1 | -0.5 | 0.94 (0.91–0.98) | 0.98 (0.94–1.03) |
| middle third | 11970 | 386 | 7200 | 0.602 | 0.437 | 28.5 | 0.459 | -5.3 | -1.6 | 0.92 (0.88–0.96) | 0.95 (0.90–1.00) |
| busiest third | 12155 | 387 | 9333 | 0.768 | 0.469 | 33.2 | 0.431 | 9.4 | 2.1 | 1.14 (1.10–1.18) | 1.07 (1.02–1.11) |

## 7. Fitness absences (Bundesliga, secondary outcome)

| attacking style | player_seasons | fitness_absences | per 100 player-seasons |
|---|---|---|---|
| Positional possession | 733 | 73 | 10.0 |
| Build-up into the box | 2244 | 235 | 10.5 |
| Counter-attack | 1957 | 198 | 10.1 |
| Direct play | 1682 | 214 | 12.7 |

| defensive style | player_seasons | fitness_absences | per 100 player-seasons |
|---|---|---|---|
| High press, high line | 1646 | 185 | 11.2 |
| Compact mid-block | 1149 | 115 | 10.0 |
| Aggressive duel press | 1198 | 136 | 11.4 |
| Low block | 2623 | 284 | 10.8 |

## 8. Sensitivity checks (injury RR)

### Attacking style

| variant | Positional possession | Build-up into the box | Counter-attack | Direct play |
|---|---|---|---|---|
| main (> 7 days) | 1.24 | 1.01 | 0.9 | 0.95 |
| ≥ 900 minutes only | 1.3 | 1.01 | 0.87 | 0.93 |
| severe only (> 28 days) | 1.09 | 1.0 | 0.94 | 1.0 |
| > 3 days (adds mild) | 1.3 | 1.01 | 0.88 | 0.93 |
| multi-club players out | 1.27 | 1.01 | 0.89 | 0.94 |
| COVID seasons out | 1.24 | 1.03 | 0.89 | 0.94 |

### Defensive style

| variant | High press, high line | Compact mid-block | Aggressive duel press | Low block |
|---|---|---|---|---|
| main (> 7 days) | 1.14 | 1.03 | 0.93 | 0.94 |
| ≥ 900 minutes only | 1.19 | 1.05 | 0.91 | 0.9 |
| severe only (> 28 days) | 1.05 | 0.96 | 1.0 | 0.99 |
| > 3 days (adds mild) | 1.19 | 1.04 | 0.91 | 0.92 |
| multi-club players out | 1.16 | 1.03 | 0.94 | 0.93 |
| COVID seasons out | 1.15 | 1.04 | 0.93 | 0.93 |

### Formation

| variant | back three | back four |
|---|---|---|
| main (> 7 days) | 1.01 | 1.0 |
| ≥ 900 minutes only | 1.02 | 0.99 |
| severe only (> 28 days) | 0.97 | 1.01 |
| > 3 days (adds mild) | 1.01 | 1.0 |
| multi-club players out | 1.01 | 1.0 |
| COVID seasons out | 1.02 | 0.99 |

## 9. Style cards (core team-seasons)

### Attacking styles

- **Positional possession** (174 team-seasons, core 118 (68%)): dominates the ball and plays in the opponent's half; builds up slowly and patiently; works the ball into the box before shooting. deep completions per match: 10.0 (all 6.1); shots from slow, patient attacks: 9% (all 6%); shots from outside the box: 33% (all 38%). Back-three minutes 23%; points/match 2.03; most often with High press, high line (60%), Compact mid-block (33%). Typical: SSC Napoli 2017-18, FC Barcelona 2014-15 | Atalanta BC 2021-22, FC Barcelona 2020-21 | Borussia Dortmund 2022-23, SSC Napoli 2022-23.
- **Build-up into the box** (355 team-seasons, core 148 (42%)): works the ball into the box before shooting; dominates the ball and plays in the opponent's half; builds up slowly and patiently. shots from outside the box: 34% (all 38%); deep completions per match: 6.8 (all 6.1); shots from slow, patient attacks: 6% (all 6%). Back-three minutes 29%; points/match 1.49; most often with Compact mid-block (33%), Low block (30%). Typical: Borussia Mönchengladbach 2017-18, Olympique Marseille 2016-17 | LOSC Lille 2021-22, Leicester City 2021-22 | TSG 1899 Hoffenheim 2023-24, AFC Bournemouth 2025-26.
- **Counter-attack** (279 team-seasons, core 193 (69%)): attacks fast and vertically, on the break; rarely builds up slowly; spends long spells without the ball. shots from fast attacks: 8% (all 6%); shots from slow, patient attacks: 4% (all 6%); deep completions per match: 4.6 (all 6.1). Back-three minutes 18%; points/match 1.15; most often with Low block (41%), Aggressive duel press (33%). Typical: Rayo Vallecano 2014-15, RCD Espanyol Barcelona 2014-15 | Burnley FC 2019-20, Dijon FCO 2019-20 | Cagliari Calcio 2023-24, RCD Mallorca 2023-24.
- **Direct play** (362 team-seasons, core 244 (67%)): shoots from distance and relies on set plays; rarely attacks at speed; spends long spells without the ball. shots from outside the box: 42% (all 38%); shots from fast attacks: 5% (all 6%); deep completions per match: 4.7 (all 6.1). Back-three minutes 22%; points/match 1.11; most often with Aggressive duel press (36%), Low block (34%). Typical: Swansea City 2014-15, Norwich City 2015-16 | Arminia Bielefeld 2021-22, AS Saint-Étienne 2020-21 | Genoa CFC 2023-24, Elche CF 2022-23.

### Defensive styles

- **High press, high line** (245 team-seasons, core 137 (56%)): holds a high line, exposed to counters; keeps opponents far from goal; presses high and wins the ball back quickly. shots conceded from fast attacks: 8% (all 6%); deep completions conceded per match: 4.6 (all 6.1); PPDA (lower = more pressing): 8.8 (all 10.9). Back-three minutes 18%; points/match 1.85; most often with Positional possession (42%), Build-up into the box (29%). Typical: Stade Rennais FC 2016-17, Real Sociedad 2017-18 | Atalanta BC 2018-19, FC Barcelona 2018-19 | Brighton & Hove Albion 2022-23, Juventus FC 2024-25.
- **Compact mid-block** (289 team-seasons, core 136 (47%)): keeps a deep, protected line; keeps opponents far from goal; defends cleanly, few fouls. shots conceded from fast attacks: 5% (all 6%); deep completions conceded per match: 5.2 (all 6.1); fouls per match: 12.3 (all 12.5). Back-three minutes 27%; points/match 1.58; most often with Build-up into the box (40%), Direct play (23%). Typical: SV Werder Bremen 2017-18, FC Girondins Bordeaux 2016-17 | Borussia Mönchengladbach 2019-20, Stade Rennais FC 2018-19 | Atlético de Madrid 2025-26, Stade Rennais FC 2023-24.
- **Aggressive duel press** (286 team-seasons, core 175 (61%)): defends through fouls and duels, many cards; presses high and wins the ball back quickly; holds a high line, exposed to counters. fouls per match: 14.8 (all 12.5); PPDA (lower = more pressing): 9.3 (all 10.9); shots conceded from fast attacks: 6% (all 6%). Back-three minutes 20%; points/match 1.24; most often with Direct play (45%), Counter-attack (32%). Typical: Inter Milan 2015-16, SV Werder Bremen 2015-16 | Real Betis Balompié 2019-20, Rayo Vallecano 2018-19 | Deportivo Alavés 2025-26, Rayo Vallecano 2025-26.
- **Low block** (350 team-seasons, core 231 (66%)): sits off and lets the opponent have the ball; lets opponents near the box; defends cleanly, few fouls. PPDA (lower = more pressing): 13.7 (all 10.9); deep completions conceded per match: 7.8 (all 6.1); fouls per match: 11.5 (all 12.5). Back-three minutes 27%; points/match 1.04; most often with Direct play (35%), Counter-attack (33%). Typical: Hull City 2014-15, SC Freiburg 2016-17 | Everton FC 2021-22, Brighton & Hove Albion 2018-19 | AJ Auxerre 2024-25, Stade Reims 2024-25.

Injury RR, all teams vs core teams only:

| attacking style | RR, all teams | RR, core teams | days RR, all teams | days RR, core teams |
|---|---|---|---|---|
| Positional possession | 1.24 | 1.25 | 1.09 | 1.08 |
| Build-up into the box | 1.01 | 1.06 | 1.0 | 1.03 |
| Counter-attack | 0.9 | 0.88 | 0.96 | 0.94 |
| Direct play | 0.95 | 0.93 | 0.99 | 1.0 |

| defensive style | RR, all teams | RR, core teams | days RR, all teams | days RR, core teams |
|---|---|---|---|---|
| High press, high line | 1.14 | 1.17 | 1.03 | 1.08 |
| Compact mid-block | 1.03 | 1.06 | 0.97 | 1.0 |
| Aggressive duel press | 0.93 | 0.96 | 1.0 | 1.03 |
| Low block | 0.94 | 0.94 | 1.0 | 0.97 |

## 10. How the ways of attacking and defending changed

| dimension (z) | 2014–18 | 2018–22 | 2022–26 | shape |
|---|---|---|---|---|
| attack_possession | -0.19 | 0.03 | 0.16 | rising |
| attack_patience | -0.65 | -0.02 | 0.68 | rising |
| attack_verticality | 0.09 | -0.02 | -0.07 | falling |
| attack_directness | 0.47 | 0.01 | -0.49 | falling |
| defence_press | 0.53 | -0.1 | -0.44 | falling |
| defence_high_line | 0.08 | -0.03 | -0.06 | falling |
| defence_territory_conceded | -0.08 | -0.02 | 0.1 | rising |
| defence_aggression | 0.24 | -0.05 | -0.2 | falling |

| dimension | all leagues | Premier League | La Liga | Serie A | Bundesliga | Ligue 1 |
|---|---|---|---|---|---|---|
| attack_possession | rising | rising | rising | peak | rising | rising |
| attack_patience | rising | rising | rising | rising | rising | rising |
| attack_verticality | falling | falling | falling | falling | rising | falling |
| attack_directness | falling | falling | falling | falling | falling | falling |
| defence_press | falling | falling | falling | falling | falling | falling |
| defence_high_line | falling | falling | falling | falling | rising | falling |
| defence_territory_conceded | rising | rising | dip | peak | rising | rising |
| defence_aggression | falling | dip | falling | falling | falling | falling |

| measure (all leagues) | 2014–18 | 2018–22 | 2022–26 |
|---|---|---|---|
| deep completions per match | 5.701 | 6.046 | 6.534 |
| shots from slow, patient attacks | 0.044 | 0.057 | 0.071 |
| shots from fast attacks | 0.062 | 0.06 | 0.06 |
| shots from outside the box | 0.413 | 0.376 | 0.344 |
| PPDA (lower = more pressing) | 9.66 | 11.116 | 11.894 |
| shots conceded from fast attacks | 0.062 | 0.061 | 0.06 |
| deep completions conceded per match | 5.701 | 6.045 | 6.534 |
| fouls per match | 13.314 | 12.376 | 11.866 |
| minutes in a back three | 0.134 | 0.257 | 0.311 |

![Dimensions](figures/05_style_dimensions_over_time.png)

## 11. How teams move between styles

Attack: style kept from one season to the next 53%.

| attack → next season | Positional possession | Build-up into the box | Counter-attack | Direct play |
|---|---|---|---|---|
| Positional possession | 73.0 | 24.0 | 0.0 | 3.0 |
| Build-up into the box | 16.0 | 58.0 | 10.0 | 16.0 |
| Counter-attack | 2.0 | 20.0 | 37.0 | 41.0 |
| Direct play | 4.0 | 21.0 | 24.0 | 51.0 |

| from | next | clubs |
|---|---|---|
| Counter-attack | Direct play | 87 |
| Direct play | Counter-attack | 64 |
| Direct play | Build-up into the box | 58 |
| Build-up into the box | Direct play | 47 |
| Build-up into the box | Positional possession | 46 |

Defence: style kept from one season to the next 55%.

| defence → next season | High press, high line | Compact mid-block | Aggressive duel press | Low block |
|---|---|---|---|---|
| High press, high line | 55.0 | 27.0 | 10.0 | 8.0 |
| Compact mid-block | 23.0 | 45.0 | 13.0 | 19.0 |
| Aggressive duel press | 10.0 | 20.0 | 56.0 | 14.0 |
| Low block | 7.0 | 17.0 | 10.0 | 66.0 |

| from | next | clubs |
|---|---|---|
| Compact mid-block | High press, high line | 60 |
| High press, high line | Compact mid-block | 58 |
| Compact mid-block | Low block | 50 |
| Aggressive duel press | Compact mid-block | 44 |
| Low block | Compact mid-block | 38 |

## 12. Style mix and injuries per era

### Attacking style

| era | Positional possession | Build-up into the box | Counter-attack | Direct play |
|---|---|---|---|---|
| 2014–18 | 6.4 | 17.3 | 36.2 | 40.1 |
| 2018–22 | 13.0 | 31.4 | 21.2 | 34.4 |
| 2022–26 | 25.4 | 42.5 | 14.0 | 18.1 |

Injury RR per era (fixed league baselines):

| era | Positional possession | Build-up into the box | Counter-attack | Direct play |
|---|---|---|---|---|
| 2014–18 | 1.18 | 1.03 | 0.9 | 0.95 |
| 2018–22 | 1.27 | 1.0 | 0.95 | 0.97 |
| 2022–26 | 1.25 | 1.0 | 0.83 | 0.92 |

### Defensive style

| era | High press, high line | Compact mid-block | Aggressive duel press | Low block |
|---|---|---|---|---|
| 2014–18 | 24.2 | 18.9 | 38.3 | 18.6 |
| 2018–22 | 19.9 | 28.6 | 21.4 | 30.1 |
| 2022–26 | 18.7 | 26.7 | 13.5 | 41.2 |

Injury RR per era (fixed league baselines):

| era | High press, high line | Compact mid-block | Aggressive duel press | Low block |
|---|---|---|---|---|
| 2014–18 | 1.07 | 0.95 | 0.97 | 0.82 |
| 2018–22 | 1.15 | 1.0 | 0.92 | 1.01 |
| 2022–26 | 1.22 | 1.11 | 0.83 | 0.94 |

### Formation

| era | back three | back four |
|---|---|---|
| 2014–18 | 8.2 | 91.8 |
| 2018–22 | 20.2 | 79.8 |
| 2022–26 | 28.2 | 71.8 |

Injury RR per era (fixed league baselines):

| era | back three | back four |
|---|---|---|
| 2014–18 | 0.9 | 0.97 |
| 2018–22 | 0.97 | 1.03 |
| 2022–26 | 1.06 | 1.0 |

## 13. Where the injury trend comes from (Kitagawa decomposition)

| outcome | eras | from | to | change | from style mix | within styles |
|---|---|---|---|---|---|---|
| injuries | 2014–18 → 2018–22 | 0.646 | 0.684 | 0.038 | 0.029 | 0.009 |
| injuries | 2018–22 → 2022–26 | 0.684 | 0.689 | 0.006 | 0.043 | -0.037 |
| injuries | 2014–18 → 2022–26 | 0.646 | 0.689 | 0.043 | 0.065 | -0.022 |
| days lost | 2014–18 → 2018–22 | 30.417 | 29.116 | -1.301 | -0.061 | -1.241 |
| days lost | 2018–22 → 2022–26 | 29.116 | 31.939 | 2.824 | 1.778 | 1.046 |
| days lost | 2014–18 → 2022–26 | 30.417 | 31.939 | 1.522 | 2.763 | -1.241 |
| severe injuries | 2014–18 → 2018–22 | 0.296 | 0.289 | -0.007 | -0.001 | -0.006 |
| severe injuries | 2018–22 → 2022–26 | 0.289 | 0.318 | 0.029 | 0.017 | 0.012 |
| severe injuries | 2014–18 → 2022–26 | 0.296 | 0.318 | 0.022 | 0.017 | 0.005 |
| hamstring injuries | 2014–18 → 2018–22 | 0.083 | 0.082 | -0.001 | -0.0 | -0.001 |
| hamstring injuries | 2018–22 → 2022–26 | 0.082 | 0.101 | 0.019 | 0.008 | 0.011 |
| hamstring injuries | 2014–18 → 2022–26 | 0.083 | 0.101 | 0.018 | 0.01 | 0.008 |
| knee injuries | 2014–18 → 2018–22 | 0.105 | 0.099 | -0.006 | -0.003 | -0.003 |
| knee injuries | 2018–22 → 2022–26 | 0.099 | 0.094 | -0.005 | 0.007 | -0.012 |
| knee injuries | 2014–18 → 2022–26 | 0.105 | 0.094 | -0.011 | 0.009 | -0.02 |

Style-mix part, 2014–18 → 2022–26, by which phase's styles are used:

| outcome | attacking style | combined style | defensive style |
|---|---|---|---|
| injuries | 0.073 | 0.065 | 0.01 |
| days lost | 1.421 | 2.763 | -0.176 |
| severe injuries | 0.013 | 0.017 | -0.004 |
| hamstring injuries | 0.015 | 0.01 | 0.002 |
| knee injuries | 0.01 | 0.009 | 0.001 |

![Decomposition](figures/05_trend_decomposition.png)

## 14. Style dimensions vs injury outcomes (60 league-seasons, within league)

Levels:

| dimension | injuries / player-season | days lost / player-season | severe share | hamstring share | knee share | muscle share |
|---|---|---|---|---|---|---|
| attack_possession | 0.09 | 0.01 | -0.02 | 0.08 | -0.32 | 0.43 |
| attack_patience | 0.2 | 0.13 | -0.06 | 0.05 | -0.55 | 0.64 |
| attack_verticality | -0.06 | -0.02 | 0.03 | 0.2 | 0.16 | -0.21 |
| attack_directness | -0.2 | -0.11 | 0.08 | -0.13 | 0.51 | -0.66 |
| defence_press | -0.09 | 0.04 | 0.1 | -0.06 | 0.51 | -0.49 |
| defence_high_line | -0.06 | -0.02 | 0.05 | 0.2 | 0.18 | -0.2 |
| defence_territory_conceded | 0.08 | 0.1 | 0.07 | 0.05 | -0.04 | 0.26 |
| defence_aggression | -0.05 | 0.13 | 0.16 | -0.11 | 0.39 | -0.38 |

Season-to-season changes (n = 55):

| dimension | injuries / player-season | days lost / player-season | severe share | hamstring share | knee share | muscle share |
|---|---|---|---|---|---|---|
| attack_possession | -0.02 | 0.19 | 0.22 | 0.11 | 0.22 | -0.05 |
| attack_patience | 0.06 | 0.0 | -0.03 | -0.23 | -0.13 | 0.06 |
| attack_verticality | 0.11 | 0.15 | 0.04 | -0.05 | 0.02 | -0.1 |
| attack_directness | -0.09 | -0.21 | -0.06 | -0.04 | -0.08 | -0.32 |
| defence_press | 0.01 | 0.1 | 0.01 | 0.01 | 0.08 | 0.01 |
| defence_high_line | 0.12 | 0.14 | 0.04 | -0.05 | 0.05 | -0.14 |
| defence_territory_conceded | 0.01 | 0.31 | 0.24 | 0.14 | 0.35 | -0.03 |
| defence_aggression | 0.04 | 0.26 | 0.13 | 0.12 | 0.02 | -0.23 |

![Links](figures/05_style_injury_links.png)

## 15. One story per league

**Premier League.** From 2014–18 to 2022–26: attack Positional possession 10% → 35%, Direct play 36% → 12%; defence Low block 49% → 54%, High press, high line 31% → 25%; back-three minutes 13% → 18%. Trends: possession (attack) rising, patience (attack) rising, verticality (attack) falling, directness (attack) falling, press (defence) falling, high line (defence) falling, territory conceded (defence) rising, aggression (defence) dip. Injuries per player-season 0.56 → 0.71 (+0.15: +0.054 from the style mix, +0.098 within styles); days lost 34.4 → 38.7; hamstring injuries 0.114 → 0.139 (style mix +0.011); knee 0.113 → 0.110 (style mix +0.014).

**La Liga.** From 2014–18 to 2022–26: attack Build-up into the box 18% → 48%, Counter-attack 48% → 16%; defence Compact mid-block 8% → 38%, Aggressive duel press 76% → 39%; back-three minutes 3% → 9%. Trends: possession (attack) rising, patience (attack) rising, verticality (attack) falling, directness (attack) falling, press (defence) falling, high line (defence) falling, territory conceded (defence) dip, aggression (defence) falling. Injuries per player-season 0.71 → 0.49 (-0.23: +0.050 from the style mix, -0.275 within styles); days lost 30.8 → 23.8; hamstring injuries 0.118 → 0.087 (style mix +0.017); knee 0.101 → 0.064 (style mix -0.004).

**Serie A.** From 2014–18 to 2022–26: attack Positional possession 8% → 28%, Direct play 48% → 30%; defence Compact mid-block 12% → 39%, Aggressive duel press 55% → 6%; back-three minutes 29% → 52%. Trends: possession (attack) peak, patience (attack) rising, verticality (attack) falling, directness (attack) falling, press (defence) falling, high line (defence) falling, territory conceded (defence) peak, aggression (defence) falling. Injuries per player-season 0.74 → 0.89 (+0.15: +0.056 from the style mix, +0.098 within styles); days lost 27.1 → 35.0; hamstring injuries 0.083 → 0.133 (style mix +0.014); knee 0.104 → 0.098 (style mix +0.010).

**Bundesliga.** From 2014–18 to 2022–26: attack Build-up into the box 14% → 51%, Direct play 44% → 6%; defence Low block 15% → 61%, Aggressive duel press 39% → 7%; back-three minutes 18% → 46%. Trends: possession (attack) rising, patience (attack) rising, verticality (attack) rising, directness (attack) falling, press (defence) falling, high line (defence) rising, territory conceded (defence) rising, aggression (defence) falling. Injuries per player-season 0.86 → 0.74 (-0.12: +0.082 from the style mix, -0.204 within styles); days lost 42.5 → 35.8; hamstring injuries 0.034 → 0.060 (style mix -0.003); knee 0.151 → 0.111 (style mix +0.005).

**Ligue 1.** From 2014–18 to 2022–26: attack Build-up into the box 12% → 41%, Counter-attack 41% → 9%; defence Low block 10% → 39%, High press, high line 38% → 20%; back-three minutes 5% → 32%. Trends: possession (attack) rising, patience (attack) rising, verticality (attack) falling, directness (attack) falling, press (defence) falling, high line (defence) falling, territory conceded (defence) rising, aggression (defence) falling. Injuries per player-season 0.37 → 0.60 (+0.23: +0.075 from the style mix, +0.152 within styles); days lost 18.4 → 26.2; hamstring injuries 0.059 → 0.079 (style mix +0.008); knee 0.060 → 0.086 (style mix +0.021).


## 16. Clearer results (fixed in advance, not tuned on outcomes)

### Shrinkage of small cells (empirical Bayes)

Attack × defence grid, raw vs shrunk injury RR (weight on own data: 1 = kept as is, 0 = fully pulled to the average):

| attack | defence | team-seasons | RR raw | RR shrunk | RR weight on own data |
|---|---|---|---|---|---|
| Build-up into the box | Aggressive duel press | 59 | 0.98 | 0.99 | 0.9 |
| Build-up into the box | Compact mid-block | 117 | 1.07 | 1.07 | 0.95 |
| Build-up into the box | High press, high line | 72 | 1.01 | 1.01 | 0.93 |
| Build-up into the box | Low block | 107 | 0.96 | 0.96 | 0.97 |
| Counter-attack | Aggressive duel press | 91 | 0.88 | 0.9 | 0.91 |
| Counter-attack | Compact mid-block | 49 | 0.84 | 0.88 | 0.79 |
| Counter-attack | High press, high line | 25 | 1.04 | 1.04 | 0.74 |
| Counter-attack | Low block | 114 | 0.9 | 0.91 | 0.95 |
| Direct play | Aggressive duel press | 129 | 0.91 | 0.92 | 0.94 |
| Direct play | Compact mid-block | 66 | 0.95 | 0.96 | 0.88 |
| Direct play | High press, high line | 44 | 1.08 | 1.07 | 0.85 |
| Direct play | Low block | 123 | 0.95 | 0.96 | 0.94 |
| Positional possession | Aggressive duel press | 7 | 1.44 | 1.42 | 0.95 |
| Positional possession | Compact mid-block | 57 | 1.16 | 1.15 | 0.94 |
| Positional possession | High press, high line | 104 | 1.28 | 1.27 | 0.95 |
| Positional possession | Low block | 6 | 1.18 | 1.14 | 0.72 |

Attacking style RR within each league, shrunk:

| league | Positional possession | Build-up into the box | Counter-attack | Direct play |
|---|---|---|---|---|
| Premier League | 1.23 | 0.95 | 0.93 | 0.94 |
| La Liga | 1.5 | 1.01 | 0.91 | 0.91 |
| Serie A | 1.08 | 0.98 | 0.98 | 1.0 |
| Bundesliga | 1.08 | 1.01 | 0.95 | 1.01 |
| Ligue 1 | 1.37 | 1.16 | 0.79 | 0.92 |

Defensive style RR within each league, shrunk:

| league | High press, high line | Compact mid-block | Aggressive duel press | Low block |
|---|---|---|---|---|
| Premier League | 1.13 | 1.03 | 1.04 | 0.91 |
| La Liga | 1.31 | 1.09 | 0.91 | 0.79 |
| Serie A | 0.97 | 1.07 | 0.95 | 1.02 |
| Bundesliga | 1.05 | 1.04 | 0.98 | 0.96 |
| Ligue 1 | 1.17 | 0.9 | 0.98 | 1.01 |

### 3-season rolling averages

| season | injuries / player-season | days lost / player-season | unknown body area | injuries / player-season (3-season mean) | days lost / player-season (3-season mean) | unknown body area (3-season mean) |
|---|---|---|---|---|---|---|
| 2014-15 | 0.592 | 29.08 | 0.157 | 0.601 | 29.317 | 0.147 |
| 2015-16 | 0.61 | 29.553 | 0.137 | 0.636 | 30.694 | 0.139 |
| 2016-17 | 0.707 | 33.448 | 0.123 | 0.663 | 30.853 | 0.12 |
| 2017-18 | 0.672 | 29.557 | 0.099 | 0.72 | 31.989 | 0.12 |
| 2018-19 | 0.781 | 32.963 | 0.138 | 0.722 | 31.481 | 0.111 |
| 2019-20 | 0.714 | 31.924 | 0.096 | 0.717 | 30.395 | 0.13 |
| 2020-21 | 0.655 | 26.298 | 0.156 | 0.654 | 27.985 | 0.132 |
| 2021-22 | 0.594 | 25.734 | 0.145 | 0.621 | 26.708 | 0.148 |
| 2022-23 | 0.614 | 28.093 | 0.142 | 0.622 | 28.763 | 0.142 |
| 2023-24 | 0.657 | 32.461 | 0.14 | 0.668 | 31.982 | 0.135 |
| 2024-25 | 0.733 | 35.391 | 0.122 | 0.716 | 33.272 | 0.121 |
| 2025-26 | 0.758 | 31.965 | 0.101 | 0.746 | 33.678 | 0.112 |

### Body-area patterns surviving false-discovery-rate correction (9 of 80; Cochran–Mantel–Haenszel test within leagues, Benjamini–Hochberg q < 0.05)

| grouping | style | area | MH odds ratio | q (BH) | leagues above 1 |
|---|---|---|---|---|---|
| attacking style | Positional possession | unspecified muscle | 1.2061 | 0.0009 | 3 |
| attacking style | Counter-attack | knee | 1.1339 | 0.041 | 5 |
| attacking style | Counter-attack | unspecified muscle | 0.872 | 0.017 | 1 |
| attacking style | Positional possession | knee | 0.818 | 0.0009 | 0 |
| defensive style | Aggressive duel press | knee | 1.2336 | 0.0005 | 4 |
| defensive style | High press, high line | knee | 0.8547 | 0.006 | 0 |
| defensive style | Low block | hamstring | 0.8521 | 0.0068 | 1 |
| defensive style | Aggressive duel press | unspecified muscle | 0.8425 | 0.0009 | 1 |
| defensive style | Low block | groin/adductor/hip | 0.8081 | 0.0009 | 2 |

### Who carries a style's excess: RR by position and age band

Attacking style × position:

| attacking style | Defender | Forward | Goalkeeper | Midfielder |
|---|---|---|---|---|
| Positional possession | 1.41 | 1.25 | 0.73 | 1.21 |
| Build-up into the box | 1.13 | 0.98 | 0.62 | 0.99 |
| Counter-attack | 0.98 | 0.9 | 0.58 | 0.89 |
| Direct play | 1.07 | 0.95 | 0.58 | 0.93 |

Attacking style × age band:

| attacking style | 22–25 | 26–29 | 30+ | ≤21 |
|---|---|---|---|---|
| Positional possession | 1.2 | 1.47 | 1.53 | 0.62 |
| Build-up into the box | 0.92 | 1.19 | 1.24 | 0.54 |
| Counter-attack | 0.85 | 0.99 | 1.03 | 0.54 |
| Direct play | 0.9 | 1.06 | 1.14 | 0.53 |

Defensive style × position:

| defensive style | Defender | Forward | Goalkeeper | Midfielder |
|---|---|---|---|---|
| High press, high line | 1.25 | 1.11 | 0.72 | 1.18 |
| Compact mid-block | 1.16 | 1.03 | 0.63 | 0.99 |
| Aggressive duel press | 1.08 | 0.87 | 0.59 | 0.92 |
| Low block | 1.04 | 0.99 | 0.57 | 0.9 |

Defensive style × age band:

| defensive style | 22–25 | 26–29 | 30+ | ≤21 |
|---|---|---|---|---|
| High press, high line | 1.11 | 1.31 | 1.43 | 0.61 |
| Compact mid-block | 0.97 | 1.22 | 1.27 | 0.49 |
| Aggressive duel press | 0.84 | 1.07 | 1.11 | 0.54 |
| Low block | 0.88 | 1.05 | 1.1 | 0.57 |

## 17. Outputs

- `data/05_injury_analysis/player_seasons.parquet`: the player-club-season table with styles, formation, strength, workload, age, position and injuries.
