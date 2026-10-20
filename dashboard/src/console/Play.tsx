import type { Status, TmStep } from '../api/types'
import { DownArrow } from '../components/ChalkArrow'
import { Eyebrow } from '../components/Eyebrow'
import { BAR, MAGNET } from '../data/magnets'
import { fmt, fmtTotal, pct } from '../lib/format'

const PLACEHOLDER: TmStep[] = [
  { id: 'T1', label: 'Clubs per league-season', call: 'competition_clubs(comp_id, season_id)', done: 0, total: 0, total_is_estimate: true, sub: 'queued', state: 'queued' },
  { id: 'T2', label: 'Squads per club-season', call: 'club_squad(club_id, season_id)', done: 0, total: 0, total_is_estimate: true, sub: 'queued', state: 'queued' },
  { id: 'T3', label: 'Injury history', call: 'player_injuries(player_id)', done: 0, total: 0, total_is_estimate: true, sub: 'full history, 1 request each', state: 'queued' },
  { id: 'T4', label: 'Player stats', call: 'player_performance_games(player_id)', done: 0, total: 0, total_is_estimate: true, sub: 'queued', state: 'queued' },
  { id: 'T5', label: 'Fixtures, all competitions', call: 'built from T4 records', done: 0, total: 0, total_is_estimate: true, sub: 'built from T4 — no requests', state: 'queued' },
]

/** 03 The play: Transfermarkt T1-T5 with chalk arrows between T1->T2 and T2->T3. */
export function Play({ status }: { status: Status | null }) {
  const steps = status?.tm_steps ?? PLACEHOLDER
  const known = (n: number) => (n > 0 ? fmt(n) : '…')
  const notes: Record<string, string> = {
    T1: `${known(steps[0].total)} league-seasons → ${known(steps[1].total)} club-seasons`,
    T2: `dedupe → ${known(status?.tm_unique_players ?? 0)} unique players, then T3–T5 together`,
  }
  return (
    <section aria-label="Transfermarkt pipeline" className="play-panel panel-base">
      <div className="play-head">
        <div className="section-head">
          <Eyebrow number="03" label="The play" icon="play" />
          <h2>Transfermarkt steps</h2>
        </div>
        <div className="play-unique">Unique player IDs: <b>{status?.tm_unique_players ? fmt(status.tm_unique_players) : '—'}</b></div>
      </div>
      {steps.map((t) => (
        <div key={t.id} style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="step">
            <div
              className={`step-magnet mag ${t.state === 'queued' ? 'queued' : ''}`}
              style={t.state === 'queued' ? undefined : { background: t.state === 'done' ? MAGNET.ok : MAGNET.run }}
            >
              {t.id}
            </div>
            <div className="step-main">
              <div className="step-title">
                <b>{t.label}</b>
                <code>{t.call}</code>
              </div>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${pct(t.done, t.total)}%`, background: t.state === 'done' ? BAR.ok : BAR.run }} />
              </div>
            </div>
            <div className="step-count">
              {t.total > 0 ? `${fmt(t.done)} / ${fmtTotal(t.total, t.total_is_estimate)}` : '—'}
              <div>{t.sub}</div>
            </div>
          </div>
          {notes[t.id] && (
            <div className="step-note">
              <DownArrow />
              <span className="hand-note">{notes[t.id]}</span>
            </div>
          )}
        </div>
      ))}
    </section>
  )
}
