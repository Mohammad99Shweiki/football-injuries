import type { Finding } from '../api/types'
import { Eyebrow } from '../components/Eyebrow'

const PENDING: Finding[] = [
  { key: 't2_season', state: 'verify', title: 'T2 returns the past squad', detail: 'Run the smoke test to check this on Arsenal (11), season 2016.' },
  { key: 't3_pagination', state: 'verify', title: 'T3 injury history in one response', detail: 'Run the smoke test to check this.' },
  { key: 't4_minutes', state: 'verify', title: 'T4 includes minutes', detail: 'Run the smoke test to check minutes in the raw JSON.' },
  { key: 't5_fixtures', state: 'verify', title: 'T5 fixtures come from T4 records', detail: 'Run the smoke test to check this.' },
]
const PILL = { confirmed: ['ok', 'Confirmed'], verify: ['warn', 'Verify'], failed: ['warn', 'Failed'] } as const

/** 07 Scouting notes: smoke-test findings. */
export function Scouting({ findings }: { findings: Finding[] }) {
  const items = findings.length ? findings : PENDING
  return (
    <section aria-label="Smoke test findings" className="scouting panel-base">
      <div className="section-head">
        <Eyebrow number="07" label="Scouting notes" icon="clipboard" />
        <h2>Smoke test findings</h2>
        <div className="hand-note sm">one league-season, 20 players → README</div>
      </div>
      {items.map((k) => {
        const [cls, text] = PILL[k.state]
        return (
          <div key={k.key} className="finding">
            <span className={`pill ${cls}`}>{text}</span>
            <div className="finding-text">
              <b>{k.title}</b>
              <div>{k.detail}</div>
            </div>
          </div>
        )
      })}
    </section>
  )
}
