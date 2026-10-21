# Phase 5: Injury analysis

Generated 2026-10-21 by `notebooks/05_injury_analysis.ipynb`, where each step is shown with its checks.

## Key numbers

- 36,525 player-club-seasons, 24,581 injuries > 7 days, 1,113,471 days lost.
- Styles whose injury RR CI excludes 1: Controlled possession 1.14, Direct and physical 0.90, Counter-attacking 0.89, Elite dominance 1.25, Passive low block 0.95.
- Styles whose days-lost RR CI excludes 1: Elite dominance 1.08.
- Observed vs expected injuries across styles: chi² = 306.4, df = 6, p = 3.5e-63.
- Body-area mix by style: chi² = 244.0, df = 60, p = 4.9e-24, Cramér's V = 0.044.
- Same direction in every sensitivity check: Aggressive press and set pieces, Controlled possession, Direct and physical, Counter-attacking, Elite dominance, Passive low block.

## 1. Injuries by style (k = 7)

| style | player-seasons | team-seasons | injuries | injuries / player-season | per 1,000 min | days lost / player-season | severe share | RR (95% CI) | days RR (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| Aggressive press and set pieces | 5454 | 178 | 3377 | 0.619 | 0.438 | 30.1 | 0.461 | 0.97 (0.91–1.04) | 1.04 (0.96–1.12) |
| Controlled possession | 5370 | 175 | 3972 | 0.74 | 0.464 | 31.4 | 0.434 | 1.14 (1.08–1.20) | 1.06 (1.00–1.13) |
| Direct and physical | 5567 | 178 | 3367 | 0.605 | 0.448 | 26.9 | 0.459 | 0.90 (0.85–0.95) | 0.94 (0.88–1.00) |
| Back three | 5313 | 166 | 3918 | 0.737 | 0.537 | 30.4 | 0.392 | 1.00 (0.94–1.04) | 0.97 (0.91–1.03) |
| Counter-attacking | 4196 | 132 | 2463 | 0.587 | 0.461 | 29.3 | 0.49 | 0.89 (0.83–0.95) | 0.97 (0.90–1.05) |
| Elite dominance | 3587 | 114 | 3009 | 0.839 | 0.504 | 35.3 | 0.417 | 1.25 (1.17–1.32) | 1.08 (1.01–1.17) |
| Passive low block | 7038 | 227 | 4475 | 0.636 | 0.473 | 31.3 | 0.485 | 0.95 (0.89–1.00) | 0.97 (0.91–1.04) |

![Rates by style](figures/05_rates_by_style.png)

## 2. Body areas by style

| style | unspecified muscle | knee | hamstring | unknown | groin/adductor/hip | ankle | calf/achilles/lower leg | thigh | upper body | foot/toe | back/spine | head/neck |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Aggressive press and set pieces | 20.6 | 16.3 | 11.8 | 11.5 | 9.6 | 8.2 | 7.0 | 3.2 | 4.6 | 4.0 | 2.0 | 1.3 |
| Controlled possession | 18.0 | 13.7 | 15.6 | 10.6 | 10.0 | 9.1 | 8.7 | 3.8 | 3.5 | 2.9 | 2.1 | 1.9 |
| Direct and physical | 18.3 | 15.6 | 12.6 | 16.6 | 8.7 | 7.3 | 6.6 | 4.5 | 3.7 | 3.4 | 1.8 | 1.0 |
| Back three | 19.2 | 13.8 | 12.7 | 15.1 | 8.8 | 7.9 | 8.0 | 3.7 | 3.8 | 3.0 | 2.3 | 1.7 |
| Counter-attacking | 17.7 | 14.9 | 11.6 | 12.1 | 9.0 | 9.4 | 6.5 | 5.4 | 5.0 | 3.6 | 2.8 | 2.0 |
| Elite dominance | 17.5 | 13.8 | 15.1 | 10.2 | 9.9 | 10.4 | 7.5 | 4.8 | 4.1 | 3.1 | 2.4 | 1.2 |
| Passive low block | 13.8 | 15.2 | 12.6 | 13.5 | 9.5 | 9.3 | 8.4 | 5.3 | 4.6 | 3.8 | 2.0 | 1.7 |

Standardised residuals (known areas):

| style | unspecified muscle | knee | hamstring | groin/adductor/hip | ankle | calf/achilles/lower leg | thigh | upper body | foot/toe | back/spine | head/neck |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Aggressive press and set pieces | 3.5 | 2.0 | -2.5 | 0.2 | -1.4 | -1.6 | -3.5 | 1.1 | 1.7 | -1.0 | -1.4 |
| Controlled possession | -0.2 | -2.3 | 3.5 | 0.8 | 0.2 | 2.0 | -2.0 | -2.3 | -1.9 | -0.5 | 1.4 |
| Direct and physical | 1.9 | 2.2 | -0.1 | -0.6 | -2.2 | -1.6 | 0.9 | -1.0 | 0.4 | -1.1 | -2.2 |
| Back three | 2.8 | -0.9 | -0.3 | -0.7 | -1.5 | 1.3 | -1.6 | -0.7 | -1.1 | 0.9 | 0.8 |
| Counter-attacking | -0.3 | 0.0 | -2.4 | -0.8 | 1.0 | -2.3 | 2.5 | 2.0 | 0.5 | 2.1 | 1.9 |
| Elite dominance | -0.9 | -1.9 | 2.2 | 0.4 | 2.5 | -0.8 | 0.7 | -0.6 | -1.1 | 0.7 | -1.7 |
| Passive low block | -6.1 | 1.0 | -0.9 | 0.5 | 1.4 | 2.0 | 3.3 | 1.7 | 1.7 | -0.7 | 1.0 |

![Body areas](figures/05_body_areas_by_style.png)

Within each league (style's share relative to its league's share; median over leagues, and leagues above 1):

| style | unspecified muscle | knee | hamstring | groin/adductor/hip | ankle | calf/achilles/lower leg | thigh |
|---|---|---|---|---|---|---|---|
| Aggressive press and set pieces | 0.92 | 0.99 | 0.92 | 0.96 | 0.95 | 0.96 | 0.94 |
| Controlled possession | 1.08 | 0.98 | 1.05 | 0.99 | 1.02 | 1.09 | 0.75 |
| Direct and physical | 0.93 | 1.16 | 0.97 | 1.05 | 0.95 | 0.88 | 1.03 |
| Back three | 1.03 | 0.94 | 0.94 | 0.91 | 0.9 | 1.11 | 0.87 |
| Counter-attacking | 0.89 | 1.09 | 0.98 | 1.03 | 1.13 | 0.93 | 1.21 |
| Elite dominance | 1.19 | 0.88 | 1.11 | 1.11 | 1.04 | 1.0 | 0.74 |
| Passive low block | 0.89 | 1.0 | 0.84 | 0.96 | 0.97 | 0.99 | 1.26 |

| style | unspecified muscle | knee | hamstring | groin/adductor/hip | ankle | calf/achilles/lower leg | thigh |
|---|---|---|---|---|---|---|---|
| Aggressive press and set pieces | 0 | 2 | 1 | 2 | 0 | 2 | 1 |
| Controlled possession | 4 | 2 | 4 | 2 | 4 | 4 | 1 |
| Direct and physical | 1 | 5 | 1 | 3 | 2 | 0 | 3 |
| Back three | 3 | 2 | 2 | 1 | 2 | 4 | 0 |
| Counter-attacking | 1 | 3 | 2 | 4 | 3 | 1 | 4 |
| Elite dominance | 4 | 1 | 5 | 3 | 4 | 2 | 2 |
| Passive low block | 2 | 3 | 1 | 1 | 2 | 2 | 4 |

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

![Season trend](figures/05_season_trend.png)

![Style shares](figures/05_style_shares_by_league.png)

## 4. Leagues

| league | player-seasons | team-seasons | injuries | injuries / player-season | per 1,000 min | days lost / player-season | severe share | RR (95% CI) | days RR (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| Premier League | 7524 | 240 | 5151 | 0.685 | 0.451 | 36.2 | 0.512 | 1.00 (0.95–1.06) | 1.00 (0.94–1.06) |
| La Liga | 7429 | 240 | 4451 | 0.599 | 0.402 | 26.9 | 0.448 | 1.00 (0.93–1.07) | 1.00 (0.93–1.06) |
| Serie A | 7787 | 240 | 6410 | 0.823 | 0.608 | 30.4 | 0.371 | 1.00 (0.96–1.04) | 1.00 (0.95–1.05) |
| Bundesliga | 6616 | 216 | 5227 | 0.79 | 0.593 | 37.7 | 0.474 | 1.00 (0.96–1.04) | 1.00 (0.95–1.05) |
| Ligue 1 | 7169 | 234 | 3342 | 0.466 | 0.334 | 21.5 | 0.452 | 1.00 (0.94–1.06) | 1.00 (0.93–1.07) |

Style RR within each league:

| league | Aggressive press and set pieces | Controlled possession | Direct and physical | Back three | Counter-attacking | Elite dominance | Passive low block |
|---|---|---|---|---|---|---|---|
| Premier League | 1.04 | 1.09 | 0.8 | 0.87 | 0.77 | 1.24 | 0.94 |
| La Liga | 0.93 | 1.24 | 0.97 | 1.04 | 0.83 | 1.49 | 0.65 |
| Serie A | 0.99 | 1.07 | 0.9 | 1.06 | 0.92 | 0.9 | 1.14 |
| Bundesliga | 1.0 | 1.04 | 1.2 | 0.89 | 1.01 | 1.09 | 0.97 |
| Ligue 1 | 1.01 | 1.22 | 0.7 | 1.03 | 0.83 | 1.64 | 0.97 |

![Within league](figures/05_style_within_league.png)

## 5. Age and position

| style | RR, league-adjusted | RR, league × age × position | days RR, league-adjusted | days RR, league × age × position | mean age | Defender | Forward | Goalkeeper | Midfielder |
|---|---|---|---|---|---|---|---|---|---|
| Aggressive press and set pieces | 0.97 | 0.97 | 1.04 | 1.04 | 25.9 | 0.33 | 0.29 | 0.09 | 0.29 |
| Controlled possession | 1.14 | 1.16 | 1.06 | 1.07 | 25.7 | 0.34 | 0.28 | 0.08 | 0.3 |
| Direct and physical | 0.9 | 0.89 | 0.94 | 0.94 | 26.0 | 0.34 | 0.28 | 0.08 | 0.31 |
| Back three | 1.0 | 0.99 | 0.97 | 0.97 | 25.9 | 0.35 | 0.26 | 0.09 | 0.31 |
| Counter-attacking | 0.89 | 0.89 | 0.97 | 0.97 | 25.9 | 0.33 | 0.29 | 0.09 | 0.29 |
| Elite dominance | 1.25 | 1.29 | 1.08 | 1.11 | 25.4 | 0.34 | 0.25 | 0.09 | 0.31 |
| Passive low block | 0.95 | 0.93 | 0.97 | 0.95 | 26.2 | 0.34 | 0.29 | 0.09 | 0.29 |

## 6. Team strength and workload

Style RR within thirds of team strength (points per match):

| strength | Aggressive press and set pieces | Controlled possession | Direct and physical | Back three | Counter-attacking | Elite dominance | Passive low block |
|---|---|---|---|---|---|---|---|
| middle third | 1.05 | 1.01 | 0.87 | 0.93 | 0.92 | 1.05 | 0.97 |
| stronger third | 1.12 | 1.18 | 0.98 | 1.08 | 0.97 | 1.27 | 1.04 |
| weaker third | 0.82 | 1.18 | 0.89 | 0.98 | 0.86 | 0.78 | 0.92 |

By congestion (share of matches on < 4 days' rest, thirds over player-seasons):

| congestion | player-seasons | team-seasons | injuries | injuries / player-season | per 1,000 min | days lost / player-season | severe share | RR (95% CI) | days RR (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| lightest third | 12400 | 397 | 8048 | 0.649 | 0.521 | 29.7 | 0.455 | 0.94 (0.91–0.97) | 0.98 (0.94–1.03) |
| middle third | 11970 | 386 | 7200 | 0.602 | 0.437 | 28.5 | 0.459 | 0.92 (0.88–0.96) | 0.95 (0.90–1.00) |
| busiest third | 12155 | 387 | 9333 | 0.768 | 0.469 | 33.2 | 0.431 | 1.14 (1.10–1.18) | 1.07 (1.02–1.11) |

## 7. Fitness absences (Bundesliga, secondary outcome)

| style | player_seasons | fitness_absences | per 100 player-seasons |
|---|---|---|---|
| Aggressive press and set pieces | 1237 | 142 | 11.5 |
| Controlled possession | 455 | 31 | 6.8 |
| Direct and physical | 403 | 61 | 15.1 |
| Back three | 1189 | 144 | 12.1 |
| Counter-attacking | 980 | 98 | 10.0 |
| Elite dominance | 804 | 99 | 12.3 |
| Passive low block | 1548 | 145 | 9.4 |

## 8. Sensitivity checks (injury RR by style)

| variant | Aggressive press and set pieces | Controlled possession | Direct and physical | Back three | Counter-attacking | Elite dominance | Passive low block |
|---|---|---|---|---|---|---|---|
| main (> 7 days) | 0.97 | 1.14 | 0.9 | 1.0 | 0.89 | 1.25 | 0.95 |
| ≥ 900 minutes only | 0.95 | 1.15 | 0.87 | 1.01 | 0.87 | 1.33 | 0.9 |
| severe only (> 28 days) | 0.99 | 1.1 | 0.98 | 0.93 | 0.97 | 1.09 | 0.97 |
| > 3 days (adds mild) | 0.97 | 1.16 | 0.86 | 1.01 | 0.87 | 1.31 | 0.93 |
| multi-club players out | 0.97 | 1.15 | 0.89 | 1.0 | 0.89 | 1.26 | 0.93 |
| COVID seasons out | 0.97 | 1.17 | 0.89 | 1.01 | 0.89 | 1.27 | 0.92 |

k = 4 robustness check:

| style (k = 4) | player-seasons | team-seasons | injuries | injuries / player-season | per 1,000 min | days lost / player-season | severe share | RR (95% CI) | days RR (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| Back three | 6478 | 203 | 4763 | 0.735 | 0.544 | 31.0 | 0.405 | 0.99 (0.95–1.03) | 0.97 (0.92–1.03) |
| Direct and physical | 10674 | 345 | 6451 | 0.604 | 0.431 | 28.0 | 0.459 | 0.93 (0.89–0.97) | 0.99 (0.94–1.04) |
| Dominant pressing | 8015 | 258 | 6398 | 0.798 | 0.492 | 34.0 | 0.426 | 1.21 (1.15–1.26) | 1.09 (1.03–1.14) |
| Passive low block | 11358 | 364 | 6969 | 0.614 | 0.461 | 30.0 | 0.485 | 0.93 (0.88–0.97) | 0.96 (0.91–1.01) |

## 9. Outputs

- `data/05_injury_analysis/player_seasons.parquet`: the player-club-season table with style, strength, workload, age, position and injuries.
