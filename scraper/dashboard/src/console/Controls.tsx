import { useState } from 'react'
import type { Flags, Phase } from '../api/types'
import { Eyebrow } from '../components/Eyebrow'
import { LeagueSticker } from '../components/Sticker'
import { LEAGUES } from '../data/leagues'

interface Props {
  phase: Phase
  activeFlags: Flags | null
  busy: boolean
  onStart: (flags: Flags) => void
  onSmoke: (flags: Flags) => void
  onPause: () => void
  onResume: () => void
}

/** 01 Scope + run controls. Flags can only change before a run starts; the first button is Start / Pause / Resume. */
export function Controls({ phase, activeFlags, busy, onStart, onSmoke, onPause, onResume }: Props) {
  const [dryRun, setDryRun] = useState(false)
  const [limit, setLimit] = useState('')
  const active = phase === 'running' || phase === 'paused'
  const limitValue = limit.trim() === '' ? null : Number(limit)
  const limitInvalid = limitValue !== null && (!Number.isInteger(limitValue) || limitValue < 1)
  const flags: Flags = { dry_run: dryRun, limit: limitInvalid ? null : limitValue }
  const shown = active && activeFlags ? activeFlags : { dry_run: dryRun, limit: limitValue }

  const primary = phase === 'running'
    ? { label: 'Pause', onClick: onPause }
    : phase === 'paused'
      ? { label: 'Resume', onClick: onResume }
      : { label: phase === 'finished' ? 'Start new run' : 'Start run', onClick: () => onStart(flags) }

  return (
    <section aria-label="Run controls" className="controls panel-base">
      <div className="scope">
        <div className="section-head">
          <Eyebrow number="01" label="Scope" icon="target" />
          <div className="scope-title">5 leagues × 12 seasons = 60 league-seasons</div>
        </div>
        <div className="league-badges">
          {LEAGUES.map((l, i) => (
            <div key={l.name} className="league-badge mag" title={`${l.name} — Football-Data ${l.fd} · Understat ${l.us} · Transfermarkt ${l.tm}`}>
              <LeagueSticker league={i} />
              <div className="league-badge-text">
                <b>{l.name}</b>
                <span>{l.fd} · {l.us} · {l.tm}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="flags">
        <div className="flag">
          <label>
            <input
              type="checkbox" aria-describedby="hint-dry" checked={shown.dry_run} disabled={active}
              onChange={(e) => setDryRun(e.target.checked)}
            />
            <span className="mono">--dry-run</span>
          </label>
          <div id="hint-dry" className="helper">Plans every request and checks the cache, but sends nothing. Shows what a real run would fetch.</div>
        </div>
        <div className="flag">
          <label>
            <span className="mono">--limit</span>
            <input
              type="number" min={1} step={1} placeholder="N" aria-describedby="hint-limit" aria-invalid={limitInvalid}
              value={active && activeFlags ? (activeFlags.limit ?? '') : limit} disabled={active}
              onChange={(e) => setLimit(e.target.value)}
            />
          </label>
          <div id="hint-limit" className={`helper ${limitInvalid ? 'error' : ''}`}>
            {limitInvalid
              ? 'Use a whole number of 1 or more, or leave it blank.'
              : 'Most league-seasons each collector may take. Try 1 for a quick test; leave blank for the full run.'}
          </div>
        </div>
        <div className="actions">
          <button
            type="button" className="btn btn-outline" onClick={primary.onClick}
            aria-disabled={busy || (!active && limitInvalid)} disabled={busy || (!active && limitInvalid)}
          >
            {primary.label}
          </button>
          <button
            type="button" className="btn btn-primary" onClick={() => onSmoke(flags)}
            aria-disabled={active || busy} disabled={active || busy}
          >
            Run smoke test
          </button>
        </div>
      </div>
    </section>
  )
}
