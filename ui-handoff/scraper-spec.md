# Data Collection Spec: Big Five Leagues, Playing Style × Injuries (2014/15 – 2025/26)

Brief for an AI coding agent. Collect **raw** data from three public sources and store it unmodified on disk.

**Target total run time: about 1.5–2 hours.** Transfermarkt goes through its internal JSON API rather than HTML page scraping. The three sources are separate hosts and run in parallel.

---

## 1. Ground rules

- **Raw data is a course requirement.** Save every upstream response exactly as received (CSV/JSON/HTML). No cleaning, renaming, imputing or filtering during collection.
- Parsing into tables is a separate step and keeps the original values.
- **Leagues:** Premier League, La Liga, Serie A, Bundesliga, Ligue 1.
- **Seasons:** 2014/15 to 2025/26 (12 seasons).
- **Academic use only.** Cache everything, never re-download a stored response, and don't redistribute raw data.

### Identifiers

| Season | Football-Data code | Understat season | Transfermarkt `season_id` |
|---|---|---|---|
| 2014/15 … 2025/26 | `1415` … `2526` | `2014` … `2025` | `"2014"` … `"2025"` |

| League | Football-Data div | Understat league | Transfermarkt competition ID |
|---|---|---|---|
| Premier League | `E0` | `EPL` | `GB1` |
| La Liga | `SP1` | `La_liga` | `ES1` |
| Serie A | `I1` | `Serie_A` | `IT1` |
| Bundesliga | `D1` | `Bundesliga` | `L1` |
| Ligue 1 | `F1` | `Ligue_1` | `FR1` |

---

## 2. Layout and shared behaviour

```
project/
  collect/
    common.py            # disk cache, manifest, retries, rate limiter
    football_data.py
    understat.py
    transfermarkt.py     # uses transfermarkt-api SDK + recording transport
  parse/                 # raw -> tables (original values kept)
  data/raw/{football_data,understat,transfermarkt}/...
  data/tables/
  manifest.csv           # url, local_path, status, bytes, fetched_at, error
  run_all.py             # runs the three collectors concurrently
```

Shared behaviour:
- **Disk cache = resume.** Before any request, check whether a stored response exists; if so, use it. Re-running must cost almost nothing.
- **Manifest:** log every request, including failures.
- **Retries:** exponential backoff on 403, 429 and 5xx, up to 5 attempts, then log and continue.
- **Flags:** `--dry-run` and `--limit N` for testing.
- **Parallel run:** `run_all.py` launches the three collectors at the same time (asyncio tasks or processes). Each has its own rate limit, because they hit different hosts.

---

## 3. Football-Data.co.uk (~60 requests, ~2–3 min)

- **URL:** `https://www.football-data.co.uk/mmz4281/{season_code}/{div}.csv`
- 60 files in total. Throttle to 1 request every 2 s; the site returned HTTP 429 when hit too fast.
- Save the bytes as-is. Detect the encoding only when parsing.
- Columns differ between seasons, so parse to the union of columns.
- **Document, don't fix:** Serie A shot counts appear to include blocked shots from 2018/19 onwards.

---

## 4. Understat (~60–120 requests, ~5 min)

- **Pages:** `https://understat.com/league/{league}/{season}`
- **Needed:**
  - Team match history: date, h/a, xG, xGA, npxG, npxGA, `ppda` {att, def}, `ppda_allowed`, `deep`, `deep_allowed`, scored, missed, pts.
  - Player season data: id, name, team, position, games, minutes (`time`), xG, xA.
  - Match list.
- **Check which layout is live:** JSON embedded in `<script>` (`JSON.parse('...')` with hex escapes) or the internal XHR endpoint (reported as `/getLeagueData/{league}/{season}`). Save whichever raw payload holds the data.
- **Fallback:** `soccerdata.Understat`. Copy its cached raw files into `data/raw/understat/`.
- Throttle to 1 request per second. Don't compute PPDA here; keep `att` and `def` as given.

---

## 5. Transfermarkt via its JSON API (~20k requests, ~60–90 min)

### Approach
- Use **`transfermarkt-api`** (PyPI, v5.0.0, Python 3.12–3.13): `pip install transfermarkt-api`.
  - Since v4 it reads Transfermarkt's own JSON API (`tmapi.transfermarkt.technology`), the same API the website uses, instead of HTML pages.
  - It supports concurrent async calls (`max_concurrency`, default 10).
- **Run the SDK locally.** Do **not** use the hosted demo at `transfermarkt-api.fly.dev`, which is limited to 2 requests per 3 s.
- **Raw capture:** pass a custom `httpx.AsyncBaseTransport` that combines record and replay:
  - On a request, look for a stored response on disk (keyed by method + full URL). If found, return it (replay).
  - Otherwise fetch it, persist method, full URL, status, relevant headers (including `x-amzn-waf-action`), the decoded body and `fetched_at` to `data/raw/transfermarkt/...`, then return it.
  - This gives raw JSON plus free resume. The repo's `examples/transports.py` (Recording/ReplayTransport) is the reference pattern; when rebuilding responses from disk, drop the content-encoding and content-length headers.
  - Use `cache=None` in the SDK; the disk store replaces its in-memory cache.
- **SDK models are only for navigation**, e.g. pulling club and player IDs out of responses. The stored raw JSON is the dataset.
- The SDK does no retries or rate limiting itself; the transport handles both.

### Rate limiting (inside the transport)
- Start with **4 concurrent requests and ~4 requests/s overall**.
- After 500 clean responses, raise to 8 concurrent and ~6–8 requests/s.
- On 403, 429, or an `x-amzn-waf-action` header indicating a challenge or block: pause 60 s, halve concurrency, and continue.

### Steps

Confirm the exact SDK method names in its method table. Expected names are listed below.

| Step | Call | Count | Output |
|---|---|---|---|
| T1 | `competition_clubs(comp_id, season_id=...)` | 60 | club IDs per league-season |
| T2 | `club_players(club_id, season_id=...)` | ~1,150 | squad per club-season → unique player IDs (~9–10k) |
| T3 | player injuries `(player_id, page)` | ~10k | full career injury history: 15 per page, request the next page while a page is full |
| T4 | player stats `(player_id)` | ~9–10k | one call per player: stats per season, competition and club (expect minutes; **verify**) |
| T5 | fixtures (see below) | ~1,150–2,300 | all matches per club-season, all competitions, with dates |

**T2 check:** the docs say `club_players` returns the current squad by default and the selected season's squad when `season_id` is given. Confirm on one past season, e.g. Arsenal `11`, 2016.

**T5 fixtures:**
- First test the player matches endpoint (`/players/{id}/matches?season_id=`, 50 per page) on one regular starter. If it returns his team's matches in **all competitions** with dates, call it for one regular player per club-season and paginate.
- If it doesn't, fall back to the website fixtures page `https://www.transfermarkt.com/x/spielplan/verein/{club_id}/saison_id/{season}`: ~1,150 HTML pages at 1 request per 2 s, about 40 min. These are saved raw too.

### Order and smoke test
1. Run T1 → T2 for **one league-season**, then T3 and T4 for 20 of its players, then a T5 test. Inspect the raw JSON.
2. Confirm minutes in T4, the season behaviour in T2, pagination in T3, and the T5 choice. Record the findings in the README.
3. Full run: T1 → T2, then T3, T4 and T5 together, with unique player IDs deduplicated before T3 and T4.

**Estimate:** ~21k requests at ~5 requests/s on average is about 70 min, plus the smoke test.

---

## 6. Parse to tables (`data/tables/`, original values as text, plus a `source_file` column)

| Table | Grain | From |
|---|---|---|
| `fd_matches` | match | Football-Data |
| `us_team_matches` | team × match | Understat |
| `us_player_seasons` | player × league-season | Understat |
| `tm_clubs` | club × league-season | T1 |
| `tm_squads` | player × club × season | T2 |
| `tm_injuries` | injury event | T3 |
| `tm_player_stats` | player × season × competition × club | T4 |
| `tm_fixtures` | club × match | T5 |

Out of scope here (done later in preprocessing): cross-source name matching, mapping injuries to body areas, season and severity filtering (> 7 days out), aggregation, normalisation.

---

## 7. Validation report (print after each run)

- **League matches per season:**
  - Premier League, La Liga, Serie A: 380.
  - Bundesliga: 306.
  - Ligue 1: 380 until 2022/23, 306 from 2023/24; **2019/20 stopped early (COVID), ~279 matches is expected.**
- **Clubs per league-season:** 20, except Bundesliga 18 and Ligue 1 18 from 2023/24.
- **Failed manifest entries:** list them and retry them.
- **Suspiciously small or empty bodies,** or WAF challenge responses: delete and re-queue.
- **Injuries:** count per season. Players with zero injuries are normal; report the count.

## 8. Definition of done
- [ ] 60 Football-Data CSVs, and 60 Understat league-seasons saved raw.
- [ ] Transfermarkt T1–T5 complete, raw JSON/HTML on disk, manifest clean.
- [ ] 8 tables parsed with original values.
- [ ] Validation report passes, with known exceptions documented.
- [ ] README lists the verified endpoint behaviour, final concurrency settings and total run time.
