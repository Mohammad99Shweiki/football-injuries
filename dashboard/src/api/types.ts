// Data contract between serve.py and the dashboard (ui-handoff/HANDOFF.md section 2, plus the agreed extras).

export type Phase = 'idle' | 'running' | 'paused' | 'finished'
export type SourceKey = 'fd' | 'us' | 'tm'
export type SourceRunState = 'queued' | 'running' | 'paused' | 'done' | 'failed'
export type CellState = 'queued' | 'running' | 'done' | 'failed'

export interface Flags {
  dry_run: boolean
  limit: number | null
}

export interface SourceStatus {
  state: SourceRunState
  done: number
  total: number
  total_is_estimate: boolean
  rate: string
  cache_hits: number
  failed: number
  note: string
}

export interface TmStep {
  id: 'T1' | 'T2' | 'T3' | 'T4' | 'T5'
  label: string
  call: string
  done: number
  total: number
  total_is_estimate: boolean
  sub: string
  state: 'queued' | 'running' | 'done'
}

export interface Backoff {
  at_elapsed_s: number
  status: number | null
  waf_action: string
  paused_s: number
  concurrency_from: number
  concurrency_to: number
}

export interface Limiter {
  concurrency: number
  phase: number
  req_per_s: number
  target: string
  clean_streak: number
  rampup_needs: number
  history_rps: (number | null)[]
  backoff_until: string | null
  last_backoff: Backoff | null
}

export interface LogRow {
  fetched_at_elapsed_s: number
  source: SourceKey
  url: string
  status: number | null
  bytes: number
  result: string
}

export interface Finding {
  key: string
  state: 'confirmed' | 'verify' | 'failed'
  title: string
  detail: string
}

export interface Status {
  phase: Phase
  mode: 'full' | 'smoke'
  started_at: string | null
  finished_at: string | null
  elapsed_s: number
  eta_s: number | null
  target_s: [number, number]
  flags: Flags
  sources: Record<SourceKey, SourceStatus>
  tm_steps: TmStep[]
  tm_unique_players: number
  limiter: Limiter
  coverage: Record<SourceKey, CellState[][]>
  coverage_detail: Record<SourceKey, string[][]>
  manifest_tail: LogRow[]
  smoke_test: Finding[]
}

export interface SummaryTile {
  label: string
  value: string
  sub: string
  state: 'pass' | 'attention'
}

export interface Failure {
  id: string
  source: SourceKey
  url: string
  code: number | null
  why: string
  attempts: number
}

export interface ClubsRow {
  league: number
  expected: string
  found_ok: number
  of: number
  fixtures_ok: number
  fixtures_of: number
}

export interface DodItem {
  title: string
  state: 'done' | 'open'
  status: string
}

export interface Validation {
  finished_at: string | null
  run_time_s: number | null
  attention: number
  summary: SummaryTile[]
  matches: {
    found: Record<'fd' | 'us', (number | null)[][]>
    expected: number[][]
    known_exceptions: { league: number; season: number; note: string }[]
  }
  failures: Failure[]
  clubs: ClubsRow[]
  injuries_per_season: number[]
  zero_injury_players: number
  players_total: number
  dod: DodItem[]
  documented_quirks: string[]
}

export type ControlAction = 'start' | 'smoke_test' | 'pause' | 'resume' | 'requeue'
