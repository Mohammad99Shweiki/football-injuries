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

## 9. Style cards (core team-seasons)

- **Aggressive press and set pieces** (Direct and physical family; 178 team-seasons, core 86 (48%)): physical: many fouls, cards and duels; relies on set pieces; presses high and wins the ball back fast. fouls per match: 14.7 (all teams 12.5); shots from set pieces: 30% (all teams 26%); PPDA (lower = more pressing): 8.8 (all teams 10.9). Points/match 1.27, European matches 3.0. Typical: AS Monaco 2017-18, FC Toulouse 2016-17 | Cagliari Calcio 2018-19, CA Osasuna 2019-20 | Real Sociedad 2025-26, Cádiz CF 2023-24.
- **Controlled possession** (Dominant pressing family; 175 team-seasons, core 86 (49%)): dominates the ball and plays in the opponent's half; creates little from set pieces; defends deep, rarely caught on the break. deep completions per match: 7.6 (all teams 6.1); shots from set pieces: 23% (all teams 26%); shots conceded from fast attacks: 5% (all teams 6%). Points/match 1.79, European matches 7.3. Typical: Southampton FC 2014-15, Real Madrid 2015-16 | LOSC Lille 2021-22, Athletic Bilbao 2020-21 | Chelsea FC 2025-26, Stade Reims 2023-24.
- **Direct and physical** (Direct and physical family; 178 team-seasons, core 86 (48%)): shoots from distance; physical: many fouls, cards and duels; spends long spells without the ball. shots from outside the box: 46% (all teams 38%); fouls per match: 13.8 (all teams 12.5); deep completions per match: 4.7 (all teams 6.1). Points/match 1.14, European matches 0.9. Typical: GFC Ajaccio 2015-16, SM Caen 2017-18 | Rayo Vallecano 2018-19, FC Girondins Bordeaux 2018-19 | US Lecce 2022-23, Real Valladolid CF 2022-23.
- **Back three** (Back three family; 166 team-seasons, core 112 (67%)): plays with a back three; works the ball into the box; defends deep, rarely caught on the break. minutes in a back three: 87% (all teams 23%); shots from outside the box: 35% (all teams 38%); shots conceded from fast attacks: 6% (all teams 6%). Points/match 1.44, European matches 4.0. Typical: Genoa CFC 2017-18, Eintracht Frankfurt 2017-18 | TSG 1899 Hoffenheim 2020-21, Udinese Calcio 2021-22 | 1.FSV Mainz 05 2022-23, FC Toulouse 2025-26.
- **Counter-attacking** (Passive low block family; 132 team-seasons, core 62 (47%)): strikes on the break; spends long spells without the ball; sits off and lets the opponent play. shots from fast attacks: 9% (all teams 6%); deep completions per match: 4.7 (all teams 6.1); PPDA (lower = more pressing): 12.3 (all teams 10.9). Points/match 1.16, European matches 1.1. Typical: Angers SCO 2017-18, Stade Rennais FC 2014-15 | Hertha BSC 2019-20, Hertha BSC 2020-21 | UD Almería 2023-24, Angers SCO 2022-23.
- **Elite dominance** (Dominant pressing family; 114 team-seasons, core 77 (68%)): dominates the ball and plays in the opponent's half; holds a high line, exposed to counters; clean: few fouls and cards. deep completions per match: 11.1 (all teams 6.1); shots conceded from fast attacks: 8% (all teams 6%); fouls per match: 10.3 (all teams 12.5). Points/match 2.12, European matches 10.3. Typical: Inter Milan 2017-18, Paris Saint-Germain 2015-16 | Paris Saint-Germain 2021-22, Borussia Dortmund 2020-21 | Brighton & Hove Albion 2022-23, FC Barcelona 2025-26.
- **Passive low block** (Passive low block family; 227 team-seasons, core 109 (48%)): sits off and lets the opponent play; relies on set pieces; spends long spells without the ball. PPDA (lower = more pressing): 13.5 (all teams 10.9); shots from set pieces: 29% (all teams 26%); deep completions per match: 4.8 (all teams 6.1). Points/match 1.06, European matches 1.0. Typical: Crystal Palace 2017-18, West Bromwich Albion 2017-18 | Aston Villa 2021-22, Dijon FCO 2020-21 | FC Nantes 2022-23, VfL Wolfsburg 2024-25.

Injury RR, all teams vs core teams only:

| style | RR, all teams | RR, core teams | days RR, all teams | days RR, core teams | share of player-seasons in core teams |
|---|---|---|---|---|---|
| Aggressive press and set pieces | 0.97 | 0.95 | 1.04 | 1.11 | 0.49 |
| Controlled possession | 1.14 | 1.19 | 1.06 | 1.02 | 0.49 |
| Direct and physical | 0.9 | 0.84 | 0.94 | 0.9 | 0.49 |
| Back three | 1.0 | 1.0 | 0.97 | 0.97 | 0.68 |
| Counter-attacking | 0.89 | 0.93 | 0.97 | 0.98 | 0.46 |
| Elite dominance | 1.25 | 1.25 | 1.08 | 1.07 | 0.67 |
| Passive low block | 0.95 | 0.93 | 0.97 | 0.93 | 0.48 |

## 10. How the ways of playing changed

| dimension (z) | 2014–18 | 2018–22 | 2022–26 | shape |
|---|---|---|---|---|
| dominance | -0.22 | 0.02 | 0.2 | rising |
| pressing | 0.53 | -0.1 | -0.44 | falling |
| counter | 0.09 | -0.02 | -0.07 | falling |
| high_line | 0.08 | -0.03 | -0.06 | falling |
| physical | 0.36 | -0.07 | -0.3 | falling |
| set_pieces | 0.05 | 0.05 | -0.11 | falling |
| long_shots | 0.62 | -0.03 | -0.6 | falling |
| back_three | -0.33 | 0.08 | 0.26 | rising |

Shape per league:

| dimension | all leagues | Premier League | La Liga | Serie A | Bundesliga | Ligue 1 |
|---|---|---|---|---|---|---|
| dominance | rising | rising | rising | rising | rising | rising |
| pressing | falling | falling | falling | falling | falling | falling |
| counter | falling | falling | falling | falling | rising | falling |
| high_line | falling | falling | falling | falling | rising | falling |
| physical | falling | dip | falling | falling | falling | falling |
| set_pieces | falling | peak | peak | rising | falling | falling |
| long_shots | falling | falling | falling | falling | falling | falling |
| back_three | rising | rising | rising | rising | rising | rising |

In real units (all leagues):

| measure | 2014–18 | 2018–22 | 2022–26 |
|---|---|---|---|
| deep completions per match | 5.701 | 6.046 | 6.534 |
| PPDA (lower = more pressing) | 9.66 | 11.116 | 11.894 |
| shots from fast attacks | 0.062 | 0.06 | 0.06 |
| shots conceded from fast attacks | 0.062 | 0.061 | 0.06 |
| fouls per match | 13.314 | 12.376 | 11.866 |
| shots from set pieces | 0.261 | 0.261 | 0.255 |
| shots from outside the box | 0.413 | 0.376 | 0.344 |
| minutes in a back three | 0.134 | 0.257 | 0.311 |

![Dimensions over time](figures/05_style_dimensions_over_time.png)

## 11. How teams move between styles

| style → next season | Aggressive press and set pieces | Controlled possession | Direct and physical | Back three | Counter-attacking | Elite dominance | Passive low block |
|---|---|---|---|---|---|---|---|
| Aggressive press and set pieces | 48.0 | 13.0 | 17.0 | 4.0 | 7.0 | 2.0 | 10.0 |
| Controlled possession | 3.0 | 48.0 | 4.0 | 10.0 | 7.0 | 16.0 | 11.0 |
| Direct and physical | 19.0 | 11.0 | 42.0 | 8.0 | 10.0 | 1.0 | 9.0 |
| Back three | 6.0 | 6.0 | 6.0 | 59.0 | 6.0 | 6.0 | 13.0 |
| Counter-attacking | 8.0 | 6.0 | 10.0 | 11.0 | 30.0 | 3.0 | 32.0 |
| Elite dominance | 1.0 | 26.0 | 1.0 | 6.0 | 2.0 | 62.0 | 2.0 |
| Passive low block | 6.0 | 10.0 | 5.0 | 12.0 | 12.0 | 4.0 | 52.0 |

Largest moves between styles:

| style | next style | clubs |
|---|---|---|
| Counter-attacking | Passive low block | 29 |
| Direct and physical | Aggressive press and set pieces | 27 |
| Elite dominance | Controlled possession | 26 |
| Controlled possession | Elite dominance | 25 |
| Aggressive press and set pieces | Direct and physical | 25 |
| Aggressive press and set pieces | Controlled possession | 19 |
| Passive low block | Counter-attacking | 18 |
| Passive low block | Back three | 18 |

## 12. Style mix and injuries per era

| era | Aggressive press and set pieces | Controlled possession | Direct and physical | Back three | Counter-attacking | Elite dominance | Passive low block |
|---|---|---|---|---|---|---|---|
| 2014–18 | 25.8 | 9.4 | 30.9 | 4.1 | 11.7 | 7.9 | 10.2 |
| 2018–22 | 13.8 | 17.3 | 11.7 | 15.8 | 10.5 | 8.4 | 22.4 |
| 2022–26 | 6.0 | 18.1 | 2.8 | 22.8 | 11.7 | 13.0 | 25.6 |

Injury RR per style and era (fixed league baselines):

| era | Aggressive press and set pieces | Controlled possession | Direct and physical | Back three | Counter-attacking | Elite dominance | Passive low block |
|---|---|---|---|---|---|---|---|
| 2014–18 | 1.02 | 1.08 | 0.93 | 0.92 | 0.85 | 1.17 | 0.77 |
| 2018–22 | 0.97 | 1.13 | 0.86 | 0.94 | 0.92 | 1.28 | 1.04 |
| 2022–26 | 0.77 | 1.18 | 0.61 | 1.05 | 0.89 | 1.27 | 0.93 |

## 13. Where the injury trend comes from (Kitagawa decomposition)

| outcome | eras | from | to | change | from style mix | within styles | mix share of change |
|---|---|---|---|---|---|---|---|
| injuries | 2014–18 → 2018–22 | 0.646 | 0.684 | 0.038 | 0.032 | 0.005 | 0.856 |
| injuries | 2018–22 → 2022–26 | 0.684 | 0.689 | 0.006 | 0.018 | -0.013 | 3.297 |
| injuries | 2014–18 → 2022–26 | 0.646 | 0.689 | 0.043 | 0.062 | -0.019 | 1.436 |
| days lost | 2014–18 → 2018–22 | 30.417 | 29.116 | -1.301 | -0.867 | -0.434 | 0.667 |
| days lost | 2018–22 → 2022–26 | 29.116 | 31.939 | 2.824 | 0.552 | 2.271 | 0.196 |
| days lost | 2014–18 → 2022–26 | 30.417 | 31.939 | 1.522 | 1.745 | -0.223 | 1.146 |
| severe injuries | 2014–18 → 2018–22 | 0.296 | 0.289 | -0.007 | -0.006 | -0.001 | 0.913 |
| severe injuries | 2018–22 → 2022–26 | 0.289 | 0.318 | 0.029 | 0.006 | 0.022 | 0.224 |
| severe injuries | 2014–18 → 2022–26 | 0.296 | 0.318 | 0.022 | 0.019 | 0.003 | 0.857 |
| hamstring injuries | 2014–18 → 2018–22 | 0.083 | 0.082 | -0.001 | -0.001 | 0.0 | 1.328 |
| hamstring injuries | 2018–22 → 2022–26 | 0.082 | 0.101 | 0.019 | 0.003 | 0.016 | 0.146 |
| hamstring injuries | 2014–18 → 2022–26 | 0.083 | 0.101 | 0.018 | 0.008 | 0.01 | 0.451 |
| knee injuries | 2014–18 → 2018–22 | 0.105 | 0.099 | -0.006 | -0.002 | -0.004 | 0.317 |
| knee injuries | 2018–22 → 2022–26 | 0.099 | 0.094 | -0.005 | 0.0 | -0.006 | -0.083 |
| knee injuries | 2014–18 → 2022–26 | 0.105 | 0.094 | -0.011 | 0.001 | -0.012 | -0.113 |

![Decomposition](figures/05_trend_decomposition.png)

## 14. Style dimensions vs injury outcomes (within-league correlations, 60 league-seasons)

| dimension | injuries / player-season | days lost / player-season | severe share | hamstring share | knee share | muscle share |
|---|---|---|---|---|---|---|
| dominance | 0.15 | 0.04 | -0.09 | 0.05 | -0.57 | 0.59 |
| pressing | -0.09 | 0.04 | 0.1 | -0.06 | 0.51 | -0.49 |
| counter | -0.06 | -0.02 | 0.03 | 0.2 | 0.16 | -0.21 |
| high_line | -0.06 | -0.02 | 0.05 | 0.2 | 0.18 | -0.2 |
| physical | -0.04 | 0.14 | 0.11 | -0.14 | 0.41 | -0.4 |
| set_pieces | 0.11 | 0.13 | -0.07 | -0.17 | 0.11 | -0.34 |
| long_shots | -0.29 | -0.19 | 0.13 | -0.08 | 0.56 | -0.63 |
| back_three | 0.23 | 0.07 | -0.14 | 0.1 | -0.59 | 0.51 |

Season-to-season changes (within league, n = 55; removes slow shared trends):

| dimension | injuries / player-season | days lost / player-season | severe share | hamstring share | knee share | muscle share |
|---|---|---|---|---|---|---|
| dominance | 0.0 | -0.16 | -0.04 | -0.19 | -0.25 | 0.02 |
| pressing | 0.01 | 0.1 | 0.01 | 0.01 | 0.08 | 0.01 |
| counter | 0.11 | 0.15 | 0.04 | -0.05 | 0.02 | -0.1 |
| high_line | 0.12 | 0.14 | 0.04 | -0.05 | 0.05 | -0.14 |
| physical | 0.06 | 0.23 | 0.04 | 0.07 | -0.03 | -0.12 |
| set_pieces | 0.02 | -0.1 | -0.01 | -0.12 | -0.08 | -0.29 |
| long_shots | -0.15 | -0.23 | -0.07 | 0.06 | -0.04 | -0.18 |
| back_three | 0.0 | 0.01 | 0.02 | 0.2 | -0.23 | 0.02 |

![Links](figures/05_style_injury_links.png)

## 15. One story per league

**Premier League.** From 2014–18 to 2022–26, Passive low block (30% → 38%), Back three (4% → 11%) grew; Direct and physical (18% → 0%), Counter-attacking (12% → 5%) shrank. Ways of playing: dominance rising, pressing falling, counter falling, high line falling, physical dip, set pieces peak, long shots falling, back three rising. Injuries per player-season went from 0.56 to 0.71 (+0.15): +0.041 from the style mix, +0.112 within styles. Days lost per player-season 34.4 → 38.7; hamstring injuries per player-season 0.114 → 0.139 (style mix +0.004); knee 0.113 → 0.110 (style mix +0.003).

**La Liga.** From 2014–18 to 2022–26, Passive low block (1% → 25%), Controlled possession (9% → 26%) grew; Aggressive press and set pieces (48% → 18%), Direct and physical (24% → 8%) shrank. Ways of playing: dominance rising, pressing falling, counter falling, high line falling, physical falling, set pieces peak, long shots falling, back three rising. Injuries per player-season went from 0.71 to 0.49 (-0.23): +0.128 from the style mix, -0.353 within styles. Days lost per player-season 30.8 → 23.8; hamstring injuries per player-season 0.118 → 0.087 (style mix +0.014); knee 0.101 → 0.064 (style mix +0.014).

**Serie A.** From 2014–18 to 2022–26, Back three (12% → 49%), Passive low block (0% → 15%) grew; Direct and physical (59% → 5%), Counter-attacking (10% → 8%) shrank. Ways of playing: dominance rising, pressing falling, counter falling, high line falling, physical falling, set pieces rising, long shots falling, back three rising. Injuries per player-season went from 0.74 to 0.89 (+0.15): +0.116 from the style mix, +0.038 within styles. Days lost per player-season 27.1 → 35.0; hamstring injuries per player-season 0.083 → 0.133 (style mix +0.024); knee 0.104 → 0.098 (style mix +0.004).

**Bundesliga.** From 2014–18 to 2022–26, Back three (4% → 28%), Passive low block (12% → 29%) grew; Aggressive press and set pieces (47% → 4%), Direct and physical (15% → 0%) shrank. Ways of playing: dominance rising, pressing falling, counter rising, high line rising, physical falling, set pieces falling, long shots falling, back three rising. Injuries per player-season went from 0.86 to 0.74 (-0.12): -0.010 from the style mix, -0.112 within styles. Days lost per player-season 42.5 → 35.8; hamstring injuries per player-season 0.034 → 0.060 (style mix +0.009); knee 0.151 → 0.111 (style mix -0.027).

**Ligue 1.** From 2014–18 to 2022–26, Back three (0% → 22%), Controlled possession (9% → 23%) grew; Direct and physical (38% → 1%), Aggressive press and set pieces (28% → 3%) shrank. Ways of playing: dominance rising, pressing falling, counter falling, high line falling, physical falling, set pieces falling, long shots falling, back three rising. Injuries per player-season went from 0.37 to 0.60 (+0.23): +0.014 from the style mix, +0.212 within styles. Days lost per player-season 18.4 → 26.2; hamstring injuries per player-season 0.059 → 0.079 (style mix -0.012); knee 0.060 → 0.086 (style mix +0.008).


## 16. Outputs

- `data/05_injury_analysis/player_seasons.parquet`: the player-club-season table with style, strength, workload, age, position and injuries.
