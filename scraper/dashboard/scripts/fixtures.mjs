// Fake API payloads for screenshot checks, built from the sample numbers in docs/scraper/dashboard-handoff/design/*.dc.html.
const seasons = 12
const grid = (fn) => Array.from({ length: 5 }, (_, li) => Array.from({ length: seasons }, (_, si) => fn(li * 12 + si, li, si)))

export function status({ progress = 61, phase = 'running', backoff = false, failed = 0, dry = false } = {}) {
  const tmTotal = 21000
  const tmDone = Math.round((tmTotal * progress) / 100)
  const usDone = Math.min(60, Math.round((60 * progress) / 70))
  const minutes = [3.8,4.0,4.1,3.9,4.0,4.2,4.0,4.1,3.9,4.0,4.1,4.0,0,0,3.6,3.9,4.0,4.1,5.2,6.1,6.6,6.3,6.8,6.4,6.2,6.7,6.5,6.3,6.6,6.4]
  return {
    phase, mode: 'full', started_at: '2026-10-20T10:00:00Z', finished_at: phase === 'finished' ? '2026-10-20T11:46:00Z' : null,
    elapsed_s: 2472, eta_s: phase === 'running' ? 2280 : null, target_s: [5400, 7200],
    flags: { dry_run: dry, limit: null },
    sources: {
      fd: { state: 'done', done: 60, total: 60, total_is_estimate: false, rate: '1 / 2 s', cache_hits: 0, failed: 0, note: 'Bytes saved as received. Documented quirk: Serie A shots include blocked shots from 2018/19.' },
      us: { state: usDone === 60 ? 'done' : phase === 'paused' ? 'paused' : 'running', done: usDone, total: 60, total_is_estimate: false, rate: '1 / s', cache_hits: 0, failed: 0, note: 'Live layout: XHR endpoint getLeagueData, one request per league-season.' },
      tm: { state: progress >= 100 ? 'done' : phase === 'paused' ? 'paused' : 'running', done: tmDone, total: tmTotal, total_is_estimate: progress < 100, rate: '8 conc · ~6.4/s', cache_hits: 1212, failed, note: 'Record + replay transport. SDK cache=None; responses keyed by method + full URL.' },
    },
    tm_steps: [
      { id: 'T1', label: 'Clubs per league-season', call: 'competition_clubs(comp_id, season_id)', done: 60, total: 60, total_is_estimate: false, sub: 'done', state: 'done' },
      { id: 'T2', label: 'Squads per club-season', call: 'club_squad(club_id, season_id)', done: 1150, total: 1150, total_is_estimate: false, sub: 'done', state: 'done' },
      { id: 'T3', label: 'Injury history', call: 'player_injuries(player_id)', done: 5610, total: 9640, total_is_estimate: false, sub: 'full history, 1 request each', state: 'running' },
      { id: 'T4', label: 'Player stats', call: 'player_performance_games(player_id)', done: 4930, total: 9640, total_is_estimate: false, sub: 'running', state: 'running' },
      { id: 'T5', label: 'Fixtures, all competitions', call: 'built from T4 records', done: 4930, total: 9640, total_is_estimate: false, sub: 'built from T4 — no requests', state: 'running' },
    ],
    tm_unique_players: 9640,
    limiter: {
      concurrency: 8, phase: 2, req_per_s: 6.4, target: '6–8 req/s', clean_streak: 1284, rampup_needs: 500,
      history_rps: minutes, backoff_until: backoff ? new Date(Date.now() + 60000).toISOString() : null,
      last_backoff: { at_elapsed_s: 1390, status: 429, waf_action: 'challenge', paused_s: 60, concurrency_from: 8, concurrency_to: 4 },
    },
    coverage: {
      fd: grid(() => 'done'),
      us: grid((i) => (i < 44 ? 'done' : i < 46 ? 'running' : 'queued')),
      tm: grid((i) => (i === 17 ? 'failed' : i < 30 ? 'done' : i < 34 ? 'running' : 'queued')),
    },
    coverage_detail: { fd: grid(() => ''), us: grid(() => ''), tm: grid((i) => (i < 30 ? '760 / 760 players' : '412 / 760 players')) },
    manifest_tail: [
      { fetched_at_elapsed_s: 2472, source: 'tm', url: 'https://tmapi.transfermarkt.technology/player/418560/injury', status: 200, bytes: 3912, result: 'Fetched' },
      { fetched_at_elapsed_s: 2472, source: 'tm', url: 'https://tmapi.transfermarkt.technology/player/357662/performance-game', status: 200, bytes: 18240, result: 'Fetched' },
      { fetched_at_elapsed_s: 2471, source: 'us', url: 'https://understat.com/getLeagueData/Bundesliga/2021', status: 200, bytes: 1204331, result: 'Fetched' },
      { fetched_at_elapsed_s: 2471, source: 'tm', url: 'https://tmapi.transfermarkt.technology/player/28003/injury', status: 200, bytes: 5108, result: 'Replayed from disk' },
      { fetched_at_elapsed_s: 2470, source: 'tm', url: 'https://tmapi.transfermarkt.technology/club/1041/squad?season=2019', status: 200, bytes: 41776, result: 'Fetched' },
      { fetched_at_elapsed_s: 2470, source: 'us', url: 'https://understat.com/getLeagueData/Bundesliga/2020', status: 200, bytes: 1198050, result: 'Fetched' },
      { fetched_at_elapsed_s: 1390, source: 'tm', url: 'https://tmapi.transfermarkt.technology/player/88755/injury', status: 429, bytes: 0, result: "WAF action 'challenge' (HTTP 429) — retry 1/5" },
      { fetched_at_elapsed_s: 124, source: 'fd', url: 'https://www.football-data.co.uk/mmz4281/2526/F1.csv', status: 200, bytes: 58912, result: 'Fetched' },
      { fetched_at_elapsed_s: 120, source: 'fd', url: 'https://www.football-data.co.uk/mmz4281/2526/D1.csv', status: 200, bytes: 50110, result: 'Fetched' },
    ],
    smoke_test: [
      { key: 't2_season', state: 'confirmed', title: 'T2 returns the past squad', detail: "Club 11, season 2016: 42 members, all marked 'historical' — the 2016/17 squad, not today's." },
      { key: 't3_pagination', state: 'confirmed', title: 'T3 injury history in one response', detail: '20 players, up to 31 injuries each, all in a single response.' },
      { key: 't4_minutes', state: 'confirmed', title: 'T4 includes minutes', detail: 'playedMinutes recorded in 18,686 of 18,688 matches played.' },
      { key: 't5_fixtures', state: 'confirmed', title: 'T5 fixtures come from T4 records', detail: 'All competitions with dates; no spielplan HTML needed.' },
    ],
  }
}

export function validation() {
  const expected = Array.from({ length: 5 }, (_, li) => Array.from({ length: 12 }, (_, si) => (li === 3 ? 306 : li === 4 ? (si === 5 ? 279 : si >= 9 ? 306 : 380) : 380)))
  const found = expected.map((row, li) => row.map((v, si) => (li === 2 && si === 3 ? 379 : v)))
  return {
    finished_at: '2026-10-20T11:46:00Z', run_time_s: 6360, attention: 2,
    summary: [
      { label: 'Football-Data CSVs', value: '60 / 60', sub: 'Union of columns at parse time', state: 'pass' },
      { label: 'Understat league-seasons', value: '60 / 60', sub: 'XHR getLeagueData payloads', state: 'pass' },
      { label: 'Transfermarkt requests', value: '20,861', sub: '3 failed · 2 suspicious bodies', state: 'attention' },
      { label: 'Parsed tables', value: '9 / 9', sub: 'Original values + source_file', state: 'pass' },
    ],
    matches: { found: { fd: found, us: expected }, expected, known_exceptions: [{ league: 4, season: 5, note: 'COVID, stopped early' }] },
    failures: [
      { id: 'm:1', source: 'tm', url: 'https://tmapi.transfermarkt.technology/player/88755/injury', code: 429, why: 'WAF challenge after 5 tries', attempts: 5 },
      { id: 'm:2', source: 'tm', url: 'https://tmapi.transfermarkt.technology/player/241641/performance-game', code: 503, why: 'Upstream error', attempts: 5 },
      { id: 'm:3', source: 'tm', url: 'https://tmapi.transfermarkt.technology/club/1041/squad?season=2016', code: 403, why: 'x-amzn-waf-action: block', attempts: 5 },
      { id: 'f:4', source: 'tm', url: 'https://tmapi.transfermarkt.technology/player/502670/injury', code: 200, why: 'Body 2 bytes — likely empty', attempts: 1 },
      { id: 'f:5', source: 'us', url: 'https://understat.com/getLeagueData/Serie_A/2017', code: 200, why: 'missing or empty keys', attempts: 1 },
    ],
    clubs: [0, 1, 2, 3, 4].map((li) => ({ league: li, expected: li === 3 ? '18 every season' : li === 4 ? '20, then 18 from 2023/24' : '20 every season', found_ok: 12, of: 12, fixtures_ok: li === 2 ? 238 : 240, fixtures_of: li === 3 || li === 4 ? 228 : 240 })),
    injuries_per_season: [1820, 1905, 1960, 2010, 2085, 1790, 2240, 2310, 2280, 2350, 2400, 2190],
    zero_injury_players: 3412, players_total: 9640,
    dod: [
      { title: '60 Football-Data CSVs and 60 Understat league-seasons saved raw', state: 'done', status: 'Done' },
      { title: 'Transfermarkt T1–T5 complete, manifest clean', state: 'open', status: '5 entries to re-queue' },
      { title: '9 tables parsed with original values', state: 'done', status: 'Done' },
      { title: 'Validation report passes, exceptions documented', state: 'open', status: 'Serie A 2017/18 has 379 of 380 matches' },
      { title: 'README: endpoint behaviour, concurrency, run time', state: 'open', status: 'Run time and final settings still to fill in' },
    ],
    documented_quirks: ['Serie A shot counts include blocked shots from 2018/19.'],
  }
}
