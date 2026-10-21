// Derives what the console shows from a status snapshot. Pure functions: easy to test with a fake feed.
import type { CellState, Phase, SourceKey, SourceRunState, Status } from '../api/types'
import { MAGNET } from '../data/magnets'

export function overallProgress(status: Status): number {
  const sources = Object.values(status.sources)
  const done = sources.reduce((a, s) => a + s.done, 0)
  const total = sources.reduce((a, s) => a + s.total, 0)
  return total > 0 ? Math.min(100, Math.floor((done / total) * 100)) : 0
}

export function isBackingOff(status: Status): boolean {
  return !!status.limiter.backoff_until && Date.parse(status.limiter.backoff_until) > Date.now()
}

export function failuresRemain(status: Status): boolean {
  return status.phase === 'finished' && Object.values(status.sources).some((s) => s.failed > 0)
}

export const PILL: Record<SourceRunState, { cls: string; text: string; magnet: string | null }> = {
  queued: { cls: 'idle', text: 'Queued', magnet: null },
  running: { cls: 'run', text: 'Running', magnet: MAGNET.run },
  paused: { cls: 'warn', text: 'Paused', magnet: MAGNET.fail },
  done: { cls: 'ok', text: 'Done', magnet: MAGNET.ok },
  failed: { cls: 'warn', text: 'Failed', magnet: MAGNET.fail },
}

export function headerStatus(phase: Phase, status: Status | null): { text: string; magnet: string | null } {
  if (!status || phase === 'idle') return { text: 'Ready · 3 collectors', magnet: null }
  if (phase === 'paused') return { text: 'Paused', magnet: MAGNET.fail }
  if (phase === 'finished') return { text: status.flags.dry_run ? 'Dry run finished' : 'Finished', magnet: MAGNET.ok }
  const running = Object.values(status.sources).filter((s) => s.state === 'running').length
  return { text: `Running · ${running} collector${running === 1 ? '' : 's'}`, magnet: MAGNET.ok }
}

export const CELL_NAMES: Record<CellState, string> = {
  done: 'Saved raw', running: 'In progress', queued: 'Queued', failed: 'Failed, retry queued',
}

export function cellStyle(state: CellState) {
  const magnet = state === 'done' ? MAGNET.ok : state === 'running' ? MAGNET.run : state === 'failed' ? MAGNET.fail : null
  return { magnet, mark: state === 'failed' ? '!' : '' }
}

export function countCells(status: Status, source: SourceKey, state: CellState): number {
  return status.coverage[source].flat().filter((c) => c === state).length
}
