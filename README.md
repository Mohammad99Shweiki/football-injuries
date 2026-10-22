# Big Five leagues: playing style × injuries (2014/15 – 2025/26)

Collects **raw** data from Football-Data.co.uk, Understat and Transfermarkt for the Premier League, La Liga,
Serie A, Bundesliga and Ligue 1, stores every upstream response unmodified, then parses it into tables that keep
the original values (`scraper/`). The analysis (`analysis/`, `notebooks/`) clusters team-seasons by playing style
and compares injuries across clusters, seasons and leagues; see `docs/ANALYSIS_PLAN.md`.

## Repository layout

```
docs/          ANALYSIS_PLAN.md, DECISIONS.md, PREPROCESSING_LOG.md, scraper/ (spec, dashboard handoff), ui/ (design brief)
scraper/       step 1, data collection (finished): collect/, parse/, validate.py, serve.py, Docker files
app/           the dashboard (React): step 1 scraping (run console, validation); step 2 analysis (Progress, Studio, Clustering, Results, Reviews, Logs, Report)
analysis/      step 2, analysis:
  phases/        p00_audit.py … p06_report.py: one script per phase, cells in the `# %%` format (source of truth)
  run.py         runs phases step by step, records checks/log rows/outputs in data/NN_*/_run.json, staleness
  api.py         /api/analysis/* for the dashboard (mounted by scraper/serve.py)
  steps.py       reads phase scripts into steps; builds notebooks
  config.py load.py report.py audit.py   shared code
notebooks/     one notebook per phase, generated from analysis/phases/ (scripts/notebooks/build_notebook.py)
mappings/      hand-reviewed inputs (team map, injury label map, approvals.json), tracked in git
data/          git-ignored, all generated:
  raw/           scraper downloads (read only)
  scraper_run/   scraper run state: manifest, live status, last run, smoke test
  tables/        parsed tables (python -m parse)
  00_audit/ … 06_report/   output of each analysis phase, with its run record _run.json
reports/       NN_*.md per phase, summary.md (course report text), figures/NN_*.png
```

Data flows one way: `raw → tables → 00 → 01 → … → 06 → reports`. Phase N writes only to `data/NN_*/` and `reports/`.

## Analysis

```sh
uv sync --group analysis
uv run --group analysis python -m analysis.run status      # each phase: last run, stale or up to date (and why)
uv run --group analysis python -m analysis.run all         # rerun stale phases in order, stop at the first failure
uv run --group analysis python -m analysis.run 05 --until 7   # one phase, up to a step
uv run --group analysis python scripts/notebooks/build_notebook.py   # regenerate notebooks from analysis/phases/
```

Rebuild everything from the raw data: `cd scraper && uv run python -m parse && cd .. && uv run --group analysis python -m analysis.run all --force`.
Every random step is seeded (`analysis.config.SEED`); each run record keeps the git commit, seed and input hashes.

Academic use only. Raw data and tables (`data/`) are git-ignored and must not be redistributed.

## Setup

```sh
brew install uv          # or see https://docs.astral.sh/uv/
uv sync                  # Python 3.13 + dependencies (transfermarkt-api pinned to 5.0.0)
```

## Docker (easiest)

Needs only Docker Desktop. One image (Python 3.13 on Debian slim) holds the collectors, parsers, analysis dependencies and the built dashboard. The scientific Python dependencies make this larger than the earlier scraping-only image.

```sh
cd scraper
docker compose up --build -d                  # dashboard at http://127.0.0.1:8765
docker compose logs -f                        # collector logs
docker compose stop                           # stop; progress is kept, `up -d` continues
docker compose run --rm app --headless --limit 2   # terminal-only run, any run_all.py flags
```

- **Data:** the repository's `data/` is mounted into the container. Raw files, tables and run state stay on your machine and survive rebuilds. Local and Docker runs share them.
- **Run state:** manifest, live status, last run and smoke-test results go to `data/scraper_run/` (local and Docker alike; `MANIFEST_PATH` overrides the manifest).
- **Localhost only:** the port is published to `127.0.0.1` only, because the dashboard has no login.

## Usage

Scraper commands run from `scraper/`:

```sh
cd scraper
(cd ../app && npm install && npm run build)    # once: build the dashboard (needs Node.js)
uv run --group analysis python run_all.py    # dashboard at http://127.0.0.1:8765; start runs from there
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

React + Vite (TypeScript) in `app/`, built from the design handoff in `docs/scraper/dashboard-handoff/` (`HANDOFF.md`, `design/`); design tokens are in `app/src/styles/tokens.css`.
`scraper/serve.py` (standard library, bound to 127.0.0.1 only) serves `app/dist` plus the API (the analysis routes `/api/analysis/*` are listed in `analysis/api.py`; start the server with `uv run --group analysis python run_all.py` for table pages):

| Route | What |
|---|---|
| `GET /api/status` | live run status, polled every second (also written to `data/scraper_run/status.json`) |
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

Development: run `uv run --group analysis python run_all.py` and `npm run dev` in `app/`; Vite proxies `/api` to the server.

Screenshot checks against fake data use your installed Chrome through playwright-core:
```sh
npm run build && npx vite preview --port 4173 &
node scripts/screens.mjs <outDir>
```
The script covers widths 375/768/1280/1440 and all 7 Chalky states.

## One app: Scraping → Analysis

The existing tactics-board app now has shared navigation between **01 Scraping** and **02 Analysis**.
Old `/` and `/validation` links still work; the canonical scraping routes are `/scraping` and `/scraping/validation`.
No data or phase scripts were moved. The new React screens live in `app/src/analysis/` and use the existing server.

| Route | What you can do |
|---|---|
| `/analysis` | View phase status, stale reasons and exported headline counts; run stale phases in order |
| `/analysis/studio/phase-02/step-1` | Walk through phase steps, inspect checks, previews, logs, tables, figures and source; run a phase or through a step |
| `/analysis/clustering` | How k was chosen (quality measures vs k), cluster centres, agreement with Ward/GMM/consensus, sensitivity clusterings |
| `/analysis/results` | Styles (map, cards), evolution, injuries (adjustment ladder, CIs, attack × defence, body areas, position/age), same club and style switches, trends with decomposition, league stories; pick a style to follow it everywhere |
| `/analysis/reviews` | Open a mapping, compare it with the phase's proposal and its flagged rows, then approve the current file hash with a note |
| `/analysis/logs` | Search decisions and preprocessing operations |
| `/analysis/report` | Checklist before freezing a version, Finalise (writes `reports/releases/<date>-<sha>/manifest.json`), the summary and phase reports, every figure |

Tables support server-side search, sorting, 50-row pages and CSV download. Mapping edits remain in the tracked CSV files;
approving a file records its date and hash, and rejects approval if the file changed since it was opened. Approvals
(`mappings/approvals.json`) are not phase inputs, so approving never makes a phase stale; editing a mapping does.
Run controls are disabled while scraping is active. The server also rejects overlapping scraping and analysis starts.
Running through a step reruns preceding steps in that phase because they share a Python namespace.
The UI does not automatically approve reviews or change the selected clustering parameters. Run all currently uses
the existing runner's staleness/failure rules; review approvals are recorded separately, rather than added as new execution gates.

Docker now includes analysis and mounts `mappings/`, `docs/`, and `reports/` alongside `data/`, so approvals and generated
reports survive rebuilds. Local startup: build `app/`, then run `uv run --group analysis python run_all.py` from `scraper/`.

Verification:
```sh
.venv/bin/python -m unittest discover -s tests -v
cd app && npm run build && npm run lint
# Start the local server first; the browser check performs read-only UI interactions.
npx playwright-core install chromium
DASHBOARD_URL=http://127.0.0.1:8765 node scripts/analysis-smoke.mjs
```
`CHROME_PATH` can select an existing Chrome executable. The smoke check covers 1440, 768 and 375 px.

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
  serve.py             dashboard server (app/dist, scraping API, mounts analysis/api.py)
data/raw/{football_data,understat,transfermarkt}/
data/tables/
data/scraper_run/    manifest.csv (source, url, local_path, status, http_status, bytes, fetched_at, error; network requests only), status.json, last_run.json, smoke.json
```

## Raw storage

| Source | Raw file | Content |
|---|---|---|
| Football-Data | `data/raw/football_data/{1415..2526}/{E0,SP1,I1,D1,F1}.csv` | response bytes as received |
| Understat | `data/raw/understat/{league}/{2014..2025}.json` (U1) | response bytes as received |
| Understat | `data/raw/understat/team/{league}/{season}/{team_id}.json` (U2) | response bytes as received |
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

That's one request per league-season (60 in total, step **U1**), throttled to 1 request per second. The soccerdata
fallback was not needed.

**Understat team statistics (U2, added 2026-10-21).** `https://understat.com/getTeamData/{team}/{season}` (the team
page's XHR; `{team}` is the Understat team title with spaces as underscores) returns `{dates, players, statistics}`.
`statistics` holds season totals for league matches in blocks: `attackSpeed` (Fast / Standard / Normal / Slow),
`situation` (open play, corners, set pieces, direct free kicks, penalties), `formation` (with minutes played),
`shotZone`, `gameState`, `timing` and `result`, each with shots, goals and xG for and against. One request per
team-season (1,170), team list taken from the U1 payload, 1 request per second. Note: when every other source replays
from disk, Transfermarkt's replay holds the shared event loop for a few minutes before U2 requests start.

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
| `us_team_stats` | team-season × block × category | U2 statistics, long format: `block` (e.g. `attackSpeed`), `category` (e.g. `Fast`), shots, goals, xG and `against.*`; formations also `time` |
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
