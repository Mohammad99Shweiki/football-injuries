import type { DodItem } from '../api/types'
import { Eyebrow } from '../components/Eyebrow'
import { MAGNET } from '../data/magnets'

const CHECK = 'M5 12l5 5L19 7'
const DASH = 'M6 12h12'

/** 05 Full-time whistle: definition of done + documented quirks. */
export function FullTime({ dod, quirks }: { dod: DodItem[]; quirks: string[] }) {
  return (
    <section aria-label="Definition of done" className="dod panel panel-base">
      <div className="section-head">
        <Eyebrow number="05" label="Full-time whistle" icon="clock" />
        <h2>Definition of done</h2>
      </div>
      {dod.map((d) => {
        const done = d.state === 'done'
        return (
          <div key={d.title} className="dod-item">
            <span aria-hidden="true" className="dod-magnet mag" style={{ background: done ? MAGNET.ok : MAGNET.fail }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d={done ? CHECK : DASH} /></svg>
            </span>
            <div className="dod-text">
              <b>{d.title}</b>
              <span>{done ? 'Done' : d.status}</span>
            </div>
          </div>
        )
      })}
      {quirks.map((q) => <div key={q} className="quirks">Documented, not fixed: {q}</div>)}
    </section>
  )
}
