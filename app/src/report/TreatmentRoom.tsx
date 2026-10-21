import { CurveArrow } from '../components/ChalkArrow'
import { Eyebrow } from '../components/Eyebrow'
import { SEASON_LABELS } from '../data/leagues'
import { fmt } from '../lib/format'

const COVID_INDEX = 5
const BAR_MAX = 176

/** 04 Treatment room: injury events per season (T3). */
export function TreatmentRoom({ perSeason, zero, players }: { perSeason: number[]; zero: number; players: number }) {
  const max = Math.max(1, ...perSeason)
  const first = perSeason[0], last = perSeason[perSeason.length - 1]
  return (
    <section aria-label="Injuries per season" className="treatment panel panel-base">
      <div className="results-head">
        <div className="section-head">
          <Eyebrow number="04" label="Treatment room" icon="cross" />
          <h2>Injury events per season (T3)</h2>
          <div className="section-sub">Players with zero injuries are normal: <span className="mono" style={{ color: 'var(--chalk)' }}>{fmt(zero)}</span> of {fmt(players)}.</div>
        </div>
      </div>
      <div style={{ position: 'relative' }}>
        <div aria-hidden="true" className="spark-note" style={{ left: '41%', top: -2 }}>
          <span>COVID-shortened</span>
          <CurveArrow />
        </div>
        <div role="img" aria-label={`Bar chart of injury events per season, 2014/15 to 2025/26: ${fmt(first)} in 2014/15, ${fmt(last)} in 2025/26`} className="inj-chart">
          {perSeason.map((v, i) => (
            <div key={SEASON_LABELS[i]} className="inj-col">
              <span>{fmt(v)}</span>
              <div
                className="inj-bar"
                title={`${SEASON_LABELS[i]}: ${fmt(v)} injury events`}
                style={{ height: `${Math.round((v / max) * BAR_MAX)}px`, background: i === COVID_INDEX ? 'var(--warn)' : 'var(--run)' }}
              />
            </div>
          ))}
        </div>
      </div>
      <div className="inj-axis">{SEASON_LABELS.map((s) => <span key={s}>{s}</span>)}</div>
    </section>
  )
}
