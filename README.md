# Big Five leagues: playing style × injuries (2014/15 – 2025/26)

Collects **raw** data from Football-Data.co.uk, Understat and Transfermarkt for the Premier League, La Liga,
Serie A, Bundesliga and Ligue 1, stores every upstream response unmodified, then parses it into tables that keep
the original values (`scraper/`). The analysis (`analysis/`, `notebooks/`) clusters team-seasons by playing style
and compares injuries across clusters, seasons and leagues; see `docs/ANALYSIS_PLAN.md`.

## Repository layout

```
docs/          ANALYSIS_PLAN.md, DECISIONS.md, scraper/ (scraper-spec.md, dashboard-handoff/)
scraper/       stage 1, data collection (finished): collect/, parse/, validate.py, dashboard/, Docker files
analysis/      stage 2, analysis code: config.py (paths, leagues), load.py, then one module per phase
notebooks/     one thin notebook per phase: 00_audit.ipynb, 01_entities.ipynb, ...
mappings/      hand-reviewed inputs (team map, injury label map), tracked in git
data/          git-ignored, all generated:
  raw/           scraper downloads (read only)
  tables/        parsed tables (python -m parse)
  01_entities/ … 05_injury_analysis/   output of each analysis phase
reports/       NN_*.md per phase, figures/NN_*.png
```

Data flows one way: `raw → tables → 01 → 02 → … → reports`. Phase N writes only to `data/NN_*/`.

Academic use only. Raw data and tables (`data/`, `manifest.csv`) are git-ignored and must not be redistributed.

## Setup

```sh
brew install uv          # or see https://docs.astral.sh/uv/
uv sync                  # Python 3.13 + dependencies (transfermarkt-api pinned to 5.0.0)
```

## Docker (easiest)

Needs only Docker Desktop. One image (~176 MB, Python 3.13 on Alpine) holds the collectors, parsers and the built dashboard.

```sh
cd scraper
docker compose up --build -d                  # dashboard at http://127.0.0.1:8765
docker compose logs -f                        # collector logs
docker compose stop                           # stop; progress is kept, `up -d` continues
docker compose run --rm app --headless --limit 2   # terminal-only run, any run_all.py flags
```

- **Data:** the repository's `data/` is mounted into the container. Raw files, tables and run state stay on your machine and survive rebuilds. Local and Docker runs share them.
- **Manifest:** in Docker the manifest is written to `data/manifest.csv` (`MANIFEST_PATH`); local runs use `./manifest.csv`.
- **Localhost only:** the port is published to `127.0.0.1` only, because the dashboard has no login.

## Usage

Scraper commands run from `scraper/`:

```sh
cd scraper
(cd dashboard && npm install && npm run build)   # once: build the dashboard (needs Node.js)
uv run python run_all.py                     # dashboard at http://127.0.0.1:8765; start runs from there
uv run python run_all.py --start             # dashboard + start a full run right away
uv run python run_all.py --headless          # no dashboard: collect -> retry -> parse -> validate in the terminal
uv run python run_all.py --headless --dry-run --limit 2   # what would be fetched for 2 league-seasons

# Individual steps
uv run python -m collect.football_data [--leagues E0 --seasons 2016-2018]
uv run python -m collect.understat
uv run python -m collect.transfermarkt --leagues EPL --seasons 2016 --players 20   # smoke test
uv run python -m parse [--only tm_injuries]
uv run python validate.py [--fix]            # --fix deletes suspicious raw files so they are re-fetched
```

`--leagues` accepts any source's ID (`EPL`, `E0`, `GB1`, ...); `--seasons` takes start years (`2016`, `2014-2016`).
Re-running is cheap: every stored response is reused, and only missing ones are fetched.

## Dashboard

React + Vite (TypeScript) in `dashboard/`, built from the design handoff in `docs/scraper/dashboard-handoff/` (`HANDOFF.md`, `design/`); design tokens are in `dashboard/src/styles/tokens.css`.
`serve.py` (standard library, bound to 127.0.0.1 only) serves `dashboard/dist` plus the API:

| Route | What |
|---|---|
| `GET /api/status` | live run status, polled every second (also written to `data/status.json`) |
| `GET /api/validation` | validation report JSON (same checks as `validate.py`) |
| `POST /api/control` | `start`, `smoke_test`, `pause`, `resume`, `requeue` |

- **Run console** (`/`): controls, collectors, Transfermarkt steps, rate limiter, coverage board, match log, smoke-test findings.
- **Validation report** (`/validation`).
- **Mascot QA sheet** (`/?debug=mascot`).

Differences from the handoff, agreed during the build:
- T5 is shown as built from T4, with no requests of its own.
- `--limit` counts league-seasons.
- A Start run button sits in the Pause slot when no run is active.
- Live totals replace the fixed estimates.
- Extras: an ETA, the progress % in the browser tab title, a fixtures check in Team sheets, an FD/Understat toggle on the Results sheet, and hover details on the coverage magnets and tempo bars.

Development: run `uv run python run_all.py` and `npm run dev` in `dashboard/`; Vite proxies `/api` to the server.

Screenshot checks against fake data use your installed Chrome through playwright-core:
```sh
npm run build && npx vite preview --port 4173 &
node scripts/screens.mjs <outDir>
```
The script covers widths 375/768/1280/1440 and all 7 Chalky states.

## Scraper layout

```
scraper/
  collect/
    config.py          leagues, seasons, paths, expected counts
    common.py          Selection/CLI, Collector interface, Manifest, RateLimiter, AdaptiveThrottle, RetryPolicy, FileFetcher
    football_data.py   FootballDataCollector
    understat.py       UnderstatCollector
    transfermarkt.py   ResponseStore + RecordReplayTransport (httpx) + TransfermarktCollector (T1-T4)
  parse/               one TableBuilder per table; python -m parse writes data/tables/*.csv
  validate.py          validation report (one Check class per check)
  run_all.py           orchestration
  serve.py             dashboard server
  dashboard/           React app
data/raw/{football_data,understat,transfermarkt}/
data/tables/
manifest.csv         source, url, local_path, status, http_status, bytes, fetched_at, error (network requests only)
```

## Raw storage

| Source | Raw file | Content |
|---|---|---|
| Football-Data | `data/raw/football_data/{1415..2526}/{E0,SP1,I1,D1,F1}.csv` | response bytes as received |
| Understat | `data/raw/understat/{league}/{2014..2025}.json` | response bytes as received |
| Transfermarkt | `data/raw/transfermarkt/<url path>__<query>.json` | `{method, url, status, headers, fetched_at, body}`; `body` is the decoded upstream JSON text |

Transfermarkt batch routes (`/players?ids[]=…`, `/clubs?ids[]=…`) are stored as `players__<sha1 of query>.json`.

## Verified endpoint behaviour (2026-10-20)

Checked live during the smoke test (`--leagues EPL --seasons 2016 --players 20`).

**Football-Data.** `https://www.football-data.co.uk/mmz4281/{code}/{div}.csv` redirects (302) to the host without
`www`; redirects are followed. Throttled to 1 request per 2 s.

**Understat.** The league page no longer embeds `JSON.parse('…')` data. `js/league.min.js` loads everything via
XHR from `https://understat.com/getLeagueData/{league}/{season}`, which returns `{teams, players, dates}`:
- `teams[id].history` holds per-match `h_a, xG, xGA, npxG, npxGA, ppda{att,def}, ppda_allowed{att,def}, deep, deep_allowed, scored, missed, xpts, result, date, pts`.
- `players` holds season rows with `id, player_name, team_title, position, games, time, xG, xA, …`.
- `dates` is the match list.

That's one request per league-season (60 in total), throttled to 1 request per second. The soccerdata fallback was
not needed.

**Transfermarkt** (`tmapi.transfermarkt.technology`, through `transfermarkt-api` 5.0.0).

The collector calls the SDK's low-level client (`Transfermarkt._client`, a `TfmktClient`) rather than its
high-level methods, because the high-level methods add many requests or assemble data locally:

| Step | Spec call | Upstream route used | Finding |
|---|---|---|---|
| T1 | `competition_clubs` | `/competition/{id}/club?season=` | 1 request per league-season. Club names come from the batch route `/clubs?ids[]=`. |
| T2 | `club_players` | `/club/{id}/squad?season=` | The SDK's `club_players` also fetches each member's transfer history (~40 extra requests per club), so the collector uses `club_squad` directly. `season` works: Arsenal (11) 2016 returns 42 `historical` members, while the current squad has 24. Player records come from the batch route `/players?ids[]=`, 100 per request. |
| T3 | `player_injuries(id, page)` | `/player/{id}/injury` | Upstream returns the **full injury history in one response**. The SDK's 15-per-page split is local, so pagination is not needed (1 request per player). |
| T4 | `player_stats(id)` | `/player/{id}/performance-game` | One record per match of the player's clubs, including `playedMinutes` (**minutes verified**), goals, cards and `participationState` (`played`, `in squad`, `not in squad`, `injured`, `absent`, …). |
| T5 | player matches / spielplan | (same as T4) | `/players/{id}/matches` in the SDK is built from the same `performance-game` route. It includes **all competitions with dates**, and also the club's matches the player missed: for Özil 2016/17 there are 55 Arsenal matches (38 PL, 8 CL, 6 FA Cup, 3 League Cup). Fixtures are therefore the union over all squad members' T4 records, with **no extra requests**, and the HTML spielplan fallback is not needed. |

Squads list ~37 players per club-season (historical registrations), more than the spec's estimate, so the unique
player count is higher too.

### Rate limiting (inside `RecordReplayTransport`)

- Start at 4 concurrent requests and 4 req/s. After every 500 clean responses, rate and concurrency double, capped at **8 concurrent / 7 req/s**.
- On 403, 429, any `x-amzn-waf-action` header or an empty 202 challenge: pause everything for 60 s and halve concurrency and rate.
- On 5xx and network errors: exponential backoff (2 s, 4 s, 8 s, …), 5 attempts, then log to the manifest and continue.
- Only 200 and 404 responses are stored. Blocks and errors are never written to the raw store.

Final settings and total run time: _fill in after the full run_.

## Tables (`data/tables/`)

All values are original text. JSON numbers and booleans keep their JSON spelling and null is empty. Every row
carries `source_file`.

| Table | Grain | Notes |
|---|---|---|
| `fd_matches` | match | Union of columns across seasons. Also has `league`, `season_code` and `source_encoding`. Blank padding lines are skipped. |
| `us_team_matches` | team × match | Nested fields are flattened as `ppda.att`, `ppda.def`, … |
| `us_player_seasons` | player × league-season | |
| `us_matches` | match | Understat match list (extra table, as the spec asks for the match list) |
| `tm_clubs` | club × league-season | |
| `tm_squads` | player × club × season | Player attributes are today's values (name, DOB, height, foot, position). |
| `tm_injuries` | injury event | Full career, all seasons. `durationDetails.days` is upstream's value, one less than the website's inclusive count. |
| `tm_player_stats` | player × season × competition × club | **Aggregated** from T4 match records, since no upstream table exists. `appearances` counts `played`; `state_*` counts every participation state (e.g. `state_injured`). National-team competitions are kept (filter by `competition_type_id` 11/17/19/20). |
| `tm_fixtures` | club × match | Only the collected club-seasons, all competitions, deduplicated on club + game. |

## Validation and known exceptions

`validate.py` checks:
- league matches per season (Football-Data, Understat);
- clubs per league-season (Transfermarkt);
- league fixtures per club-season;
- failed manifest entries;
- suspicious raw files;
- injuries per season.

Known exceptions:
- **Ligue 1 2019/20:** 279 matches (COVID), and 27–28 league matches per club.
- **Ligue 1 from 2023/24:** 18 clubs, 306 matches.
- **Serie A shots** (Football-Data) appear to include blocked shots from 2018/19 onwards. Documented here, not fixed.
- **Players with zero injuries** are normal; their count is reported.

Out of scope here (later preprocessing): cross-source name matching, mapping injuries to body areas, season and
severity filtering, aggregation and normalisation.
