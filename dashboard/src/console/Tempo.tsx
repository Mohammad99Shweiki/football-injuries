import type { Limiter } from '../api/types'
import { CurveArrow } from '../components/ChalkArrow'
import { Eyebrow } from '../components/Eyebrow'
import { MiniIcon } from '../components/Icons'
import { clock, fmt } from '../lib/format'

const START_CONCURRENCY = 4
const IDLE: Limiter = {
  concurrency: START_CONCURRENCY, phase: 1, req_per_s: 0, target: '~4 req/s', clean_streak: 0, rampup_needs: 500,
  history_rps: Array(30).fill(null), backoff_until: null, last_backoff: null,
}

/** 04 Tempo: the Transfermarkt rate limiter. */
export function Tempo({ limiter }: { limiter: Limiter | null }) {
  const l = limiter ?? IDLE
  const history = l.history_rps
  const firstZero = history.findIndex((v) => v === 0)
  const backoff = l.last_backoff
  const trend = history.filter((v): v is number => v !== null)
  const label = trend.length
    ? `Throughput bar chart, last ${trend.length} minutes: from ${trend[0]} to ${trend[trend.length - 1]} requests per second${firstZero >= 0 ? ', with a pause at zero' : ''}`
    : 'Throughput bar chart: no run yet'
  return (
    <section aria-label="Rate limiter" className="tempo panel-base">
      <div className="section-head">
        <Eyebrow number="04" label="Tempo" icon="gauge" />
        <h2>Transfermarkt rate limiter</h2>
      </div>
      <div className="tempo-stats">
        <div className="stat-box">
          <div className="stat-box-label"><MiniIcon size={14}><path d="M4 7h16M4 12h16M4 17h16" /></MiniIcon>Concurrency</div>
          <div className="stat-box-value">{l.concurrency}</div>
          <div className="stat-box-sub">Phase {l.phase} (started at {START_CONCURRENCY})</div>
        </div>
        <div className="stat-box">
          <div className="stat-box-label"><MiniIcon size={14}><path d="M13 3L5 13h6l-1 8 8-10h-6z" /></MiniIcon>Throughput</div>
          <div className="stat-box-value">{l.req_per_s.toFixed(1)}<span> req/s</span></div>
          <div className="stat-box-sub">Target {l.target}</div>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div className="muted" style={{ fontSize: 12 }}>Requests per second, last 30 min</div>
        <div className="spark-wrap">
          {firstZero >= 0 && (
            <div aria-hidden="true" className="spark-note" style={{ left: `${Math.max(0, (firstZero / history.length) * 100 - 14)}%` }}>
              <span>{backoff ? 'WAF pause' : 'paused'}</span>
              <CurveArrow />
            </div>
          )}
          <div role="img" aria-label={label} className="spark">
            {history.map((v, i) => {
              const minutesAgo = history.length - 1 - i
              return (
                <div
                  key={i}
                  title={v === null ? `${minutesAgo} min ago: no run` : `${minutesAgo === 0 ? 'this minute' : `${minutesAgo} min ago`}: ${v} req/s`}
                  style={{
                    height: v === null ? '3px' : `${Math.max(3, Math.round((v / 8) * 72))}px`,
                    background: v === null ? 'rgba(228,231,222,0.12)' : v === 0 ? 'var(--warn)' : 'var(--run)',
                  }}
                />
              )
            })}
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div className="muted" style={{ fontSize: 12 }}>Clean responses since last back-off</div>
        <div className="streak">{fmt(l.clean_streak)} <span className="muted">(ramp-up needs {l.rampup_needs})</span></div>
      </div>
      {backoff ? (
        <div className="callout warn">
          <b>Back-off at {clock(backoff.at_elapsed_s)}</b>
          <div>
            {backoff.status ?? 'Error'}
            {backoff.waf_action && <> with <code>x-amzn-waf-action: {backoff.waf_action}</code></>}
            {' '}→ paused {backoff.paused_s} s, concurrency {backoff.concurrency_from} → {backoff.concurrency_to}.
          </div>
        </div>
      ) : (
        <div className="callout ok">
          <b>No back-offs so far</b>
          <div>No 403, 429 or WAF challenge yet. On one: pause 60 s and halve concurrency.</div>
        </div>
      )}
    </section>
  )
}
