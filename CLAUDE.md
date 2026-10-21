# Project: Playing Style × Injuries in Europe's Big Five Leagues (2014/15–2025/26)

Master's data mining course project (An-Najah National University). **Solo project.** The scraping is done; next come preprocessing, clustering and analysis.

Read `ANALYSIS_PLAN.md` for the step-by-step plan. `ui-handoff/scraper-spec.md` describes how the raw data was collected.

Run analysis code with the `analysis` dependency group (kept out of the Docker image):
`uv run --group analysis python -c "from src import audit; audit.run()"`, or execute a notebook with
`cd notebooks && uv run --group analysis jupyter nbconvert --to notebook --execute --inplace 00_audit.ipynb`.

## Working style
- Keep answers short and precise. Explain decisions briefly, without long write-ups.
- Work phase by phase as laid out in `ANALYSIS_PLAN.md`. Stop at the end of each phase for my review.
- Ask before any choice that changes results. Defaults are in "Open decisions" below.
- Log every decision in `DECISIONS.md` (date, decision, reason).

## Hard rules
- **Never modify anything in `data/raw/`.** Raw data is a course requirement. All outputs go to `data/interim/`, `data/processed/` or `reports/`.
- **Clustering is the only data mining algorithm** (course constraint). Descriptive statistics, rates, confidence intervals and simple significance tests are fine for comparing groups. No classification or regression models as the main method.
- Reproducible: fixed random seeds; every step is a script or notebook that can be re-run from the raw data.

## Decisions (locked)
| Item | Decision |
|---|---|
| Topic | How changes in playing style relate to injury frequency, severity and body area; compared across seasons and leagues |
| Leagues | Premier League, La Liga, Serie A, Bundesliga, Ligue 1 |
| Seasons | 2014/15 – 2025/26 (12 seasons) |
| Algorithm | Clustering: K-means (k by elbow + silhouette), compared with hierarchical (Ward) |
| Unit | **Hybrid:** cluster **team-seasons** (~1,150 rows) by style + workload; each **player-season** inherits its team's cluster; injuries analysed at player-season level |
| Injury scope | Injuries keeping a player out **more than 7 days** |
| Sources | Understat (style: PPDA, deep, xG), Football-Data.co.uk (shots, fouls, cards, corners, dates), Transfermarkt (injuries, squads, minutes, fixtures, age, position) |

## Data (verified in Phase 0, 2026-10-21; details in `reports/00_data_audit.md`)
`data/` is git-ignored. Re-create with the scraper (`docker compose up`, see README) then `python -m parse`.
- `data/raw/` (read only, ~17 GB, 27,197 files, all fetched OK):
  - `football_data/{1415…2526}/{E0,SP1,I1,D1,F1}.csv`: 60 CSVs (utf-8-sig).
  - `understat/{EPL,La_liga,Serie_A,Bundesliga,Ligue_1}/{2014…2025}.json`: 60 getLeagueData payloads.
  - `transfermarkt/competition/{GB1,ES1,IT1,L1,FR1}/club__season=YYYY.json` (60), `club/{id}/squad__season=YYYY.json` (1,170),
    `player/{id}/{injury,performance-game}.json` (25,696, for 12,848 players), plus `clubs__*`/`players__*` lookups.
- `data/tables/*.csv`: parsed, every value as original text; every row has `source_file`. Load with `src.load.read_table`.

| Table | Rows | Grain / key |
|---|---|---|
| `fd_matches` | 21,589 | league match: `league, season_code (1415), HomeTeam, AwayTeam`; 187 cols, most are betting odds |
| `us_matches` | 21,690 | Understat match `id` (101 unplayed Ligue 1 2019-20, `isResult=false`) |
| `us_team_matches` | 43,178 | team × league match: `league (EPL…), season (2014), team_id, date`; PPDA att/def, deep, npxG |
| `us_player_seasons` | 32,574 | Understat player × team × league-season |
| `tm_clubs` | 1,170 | club-season: `competition_id (GB1…), season_param, club_id` |
| `tm_squads` | 42,238 | squad member: `season_param, club_id, playerId`; DOB, position, position_group. Lists include unused youth/loanees (up to 88) |
| `tm_injuries` | 82,075 | whole careers; event = `playerId, start, end, name`. `injuryId` is a **type code**, not an event id. 71,375 in window |
| `tm_player_stats` | 632,170 | `player_id, season_id, competition_id, club_id`: appearances, minutes, all competitions, whole careers |
| `tm_fixtures` | 52,275 | `club_id, game_id`: all competitions of collected club-seasons (built from squad players' games) |

Season keys differ per source: FD `season_code` "1415", Understat/TM start year "2014"; canonical key `"2014-15"` (`src.load.season_key`).
`scraper-spec.md` is at `ui-handoff/scraper-spec.md`.

## Known data caveats
- **Serie A** shot counts on Football-Data appear to include blocked shots from 2018/19 onwards → prefer shots on target.
- **Ligue 1:** 20 teams until 2022/23, 18 from 2023/24. 2019/20 stopped early (COVID), with about 279 matches. Bundesliga has 18 teams.
- **Understat** covers league matches only. Season PPDA = Σatt / Σdef, not the mean of match PPDAs.
- **Transfermarkt injuries** are under-reported (Hoenig et al. 2022: ~0.63 injuries per player-season vs 1.5–2.5 in clinical studies). Severe injuries are reported more reliably. About a third of records may lack a body location. This is why the scope is > 7 days, and why the share of "unknown" body area is reported per season.
- The Transfermarkt injury table also contains non-injuries (illness, flu, COVID/quarantine, rest), and injuries picked up on international duty can't be separated out.
- **Calendar events** to annotate in time-trend charts: the COVID restart and congested 2020/21, five substitutes (from 2020; the Premier League made it permanent from 2022/23), the mid-season World Cup (Nov–Dec 2022), and the new Champions League format (2024/25).
- **Novelty:** a 2026 paper (Big Data and Cognitive Computing) links possession to injury burden in the big five using Transfermarkt. This project differs through clustering of styles and body-area patterns; keep that angle explicit.

## Open decisions (defaults: confirm with me when reached)
1. Non-injury absences (illness, flu, COVID, quarantine, rest): **exclude** from the injury analysis, count separately.
2. Player-season inclusion: **≥ 1 appearance**, with a sensitivity check at ≥ 900 minutes.
3. Players at two clubs in one season: assign each injury to the club the player was at on the injury date; flag these players for a sensitivity check.
4. Feature scaling: **standardise globally across all team-seasons**, not within season, so that changes over time and differences between leagues are preserved.
5. Team strength: clusters may reflect quality (good teams press more and create more xG). Compare clustering with and without outcome-type features (xG, xGA); decide after seeing both.

## Final proposal text (for reference)
**Title:** Playing Style and Injury Patterns in Europe's Big Five Football Leagues (2014/15–2025/26)

This project applies clustering (K-means, with the number of clusters chosen by the elbow method and silhouette score, compared against hierarchical clustering) to team-seasons from the Premier League, La Liga, Serie A, Bundesliga and Ligue 1 between 2014/15 and 2025/26. Teams are grouped by playing style and workload: pressing intensity, attacking approach, physical intensity and fixture congestion. Each player-season then takes its team's cluster, and injuries lasting more than seven days are compared across clusters, seasons and leagues by frequency, severity and body area. The objective is to find whether changes in how football is played coincide with changes in how often players get injured and which body areas are affected, and whether these patterns differ between leagues.

The data is collected raw from three public sources and combined for the first time. Understat (understat.com) provides match-level pressing (PPDA), deep completions and expected goals. Football-Data.co.uk (football-data.co.uk) provides match-level shots, fouls, cards, corners and dates. Transfermarkt (transfermarkt.com) provides player injury histories, minutes in all competitions, age and position. Preprocessing includes matching teams and players across sources, mapping free-text injury descriptions to body areas, aggregating matches into team-seasons, building workload features, and normalizing before clustering.
