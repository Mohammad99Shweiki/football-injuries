import type { ReactNode } from 'react'
import { shade } from './colors'

export interface HeatCell {
  value: number
  label: ReactNode
  title?: string
  muted?: boolean
  dim?: boolean
  strong?: boolean
}

/** Rows × columns of shaded cells (a table, so it stays readable and scrolls on small screens). */
export function Heatmap({
  rows, cols, cell, mode = 'ratio', corner = '', onPick, caption,
}: {
  rows: string[]
  cols: string[]
  cell: (row: string, col: string) => HeatCell | null
  mode?: 'ratio' | 'z'
  corner?: string
  onPick?: (row: string, col: string) => void
  caption?: string
}) {
  return (
    <div className="table-scroll" tabIndex={0} role="region" aria-label={caption || corner || 'Heatmap'}>
      <table className="heat-table">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr><th scope="col">{corner}</th>{cols.map((c) => <th key={c} scope="col">{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r}>
              <th scope="row">{r}</th>
              {cols.map((c) => {
                const v = cell(r, c)
                if (!v) return <td key={c} className="heat-empty">—</td>
                return (
                  <td
                    key={c}
                    title={v.title}
                    className={`${v.muted ? 'heat-muted' : ''} ${v.dim ? 'heat-dim' : ''} ${v.strong ? 'heat-strong' : ''} ${onPick ? 'heat-pick' : ''}`}
                    style={v.muted ? undefined : { background: shade(v.value, mode) }}
                    onClick={onPick ? () => onPick(r, c) : undefined}
                  >
                    {v.label}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export interface CiRow {
  label: string
  value: number
  low: number
  high: number
  color?: string
  note?: string
  dim?: boolean
  onClick?: () => void
}

/** Dot-and-whisker rows on a shared ratio axis with the reference line at 1. */
export function CiPlot({ rows, domain = [0.7, 1.4], unit = 'rate ratio' }: { rows: CiRow[]; domain?: [number, number]; unit?: string }) {
  const lo = Math.min(domain[0], ...rows.map((r) => r.low)) - 0.02
  const hi = Math.max(domain[1], ...rows.map((r) => r.high)) + 0.02
  const W = 520, L = 8, R = 8
  const x = (v: number) => L + ((v - lo) / (hi - lo)) * (W - L - R)
  const ticks = [0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8].filter((t) => t >= lo && t <= hi)
  return (
    <div className="ci-plot">
      {rows.map((r) => (
        <div key={r.label} className={`ci-row ${r.dim ? 'is-dim' : ''}`}>
          {r.onClick ? <button className="text-link ci-label" onClick={r.onClick}>{r.label}</button> : <span className="ci-label">{r.label}</span>}
          <svg viewBox={`0 0 ${W} 28`} preserveAspectRatio="none" role="img"
            aria-label={`${r.label}: ${unit} ${r.value.toFixed(2)}, 95% CI ${r.low.toFixed(2)} to ${r.high.toFixed(2)}`}>
            {ticks.map((t) => <line key={t} x1={x(t)} x2={x(t)} y1="2" y2="26" stroke={t === 1 ? 'var(--muted)' : 'var(--line)'} strokeDasharray={t === 1 ? '3 3' : undefined} vectorEffect="non-scaling-stroke" />)}
            <line x1={x(r.low)} x2={x(r.high)} y1="14" y2="14" stroke={r.color || 'var(--chalk)'} strokeWidth="3" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
            <circle cx={x(r.value)} cy="14" r="6" fill={r.color || 'var(--chalk)'} stroke="var(--board)" strokeWidth="1.5" />
          </svg>
          <span className="ci-value"><b>{r.value.toFixed(2)}</b> <small>({r.low.toFixed(2)}–{r.high.toFixed(2)}){r.note ? ` · ${r.note}` : ''}</small></span>
        </div>
      ))}
      <div className="ci-row ci-axis" aria-hidden="true">
        <span />
        <svg viewBox={`0 0 ${W} 16`} preserveAspectRatio="none">
          {ticks.map((t) => <text key={t} x={x(t)} y="12" textAnchor="middle">{t.toFixed(1)}</text>)}
        </svg>
        <span />
      </div>
    </div>
  )
}

const EVENTS = [
  { season: '2019-20', label: 'COVID stop, restart' },
  { season: '2020-21', label: 'congested season, 5 subs' },
  { season: '2022-23', label: 'mid-season World Cup' },
  { season: '2024-25', label: 'new Champions League' },
]

/** Season series: single seasons as dots with their CI band, a 3-season rolling line, calendar events. */
export function TrendChart({ rows }: { rows: { season: string; value: number; low?: number; high?: number; rolling?: number }[] }) {
  if (!rows.length) return <p className="analysis-muted">No data.</p>
  const W = 900, H = 320, L = 48, R = 16, T = 58, B = 34
  const vals = rows.flatMap((r) => [r.value, r.low ?? r.value, r.high ?? r.value])
  const lo = Math.min(...vals) * 0.95, hi = Math.max(...vals) * 1.03
  const x = (i: number) => L + (i / Math.max(1, rows.length - 1)) * (W - L - R)
  const y = (v: number) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B)
  const band = rows.every((r) => r.low != null)
    ? `M${rows.map((r, i) => `${x(i)},${y(r.high!)}`).join('L')}L${[...rows].reverse().map((r, i) => `${x(rows.length - 1 - i)},${y(r.low!)}`).join('L')}Z`
    : ''
  const ticks = [lo, (lo + hi) / 2, hi]
  return (
    <svg className="line-chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Injuries per player-season by season, with 95% CI and 3-season rolling mean">
      {ticks.map((t) => (
        <g key={t}>
          <line x1={L} x2={W - R} y1={y(t)} y2={y(t)} stroke="var(--line)" />
          <text x={L - 6} y={y(t) + 4} textAnchor="end">{t.toFixed(2)}</text>
        </g>
      ))}
      {EVENTS.map((e) => {
        const i = rows.findIndex((r) => r.season === e.season)
        if (i < 0) return null
        const row = EVENTS.indexOf(e) % 2 // alternate rows so neighbouring labels never overlap
        return (
          <g key={e.season}>
            <line x1={x(i)} x2={x(i)} y1={T - 26 + row * 18} y2={H - B} stroke="var(--annotation)" strokeDasharray="2 4" opacity="0.6" />
            <text x={x(i)} y={T - 30 + row * 18} textAnchor="middle" className="chart-event">{e.label}</text>
          </g>
        )
      })}
      {band && <path d={band} fill="var(--site-fd)" opacity="0.14" />}
      {rows[0].rolling != null && (
        <polyline fill="none" stroke="var(--site-fd)" strokeWidth="2.5" strokeLinejoin="round"
          points={rows.map((r, i) => `${x(i)},${y(r.rolling!)}`).join(' ')} />
      )}
      {rows.map((r, i) => (
        <circle key={r.season} cx={x(i)} cy={y(r.value)} r="4.5" fill="var(--board)" stroke="var(--site-fd)" strokeWidth="2">
          <title>{`${r.season}: ${r.value.toFixed(3)}${r.low != null ? ` (95% CI ${r.low.toFixed(2)}–${r.high!.toFixed(2)})` : ''}${r.rolling != null ? `\n3-season mean ${r.rolling.toFixed(3)}` : ''}`}</title>
        </circle>
      ))}
      {rows.map((r, i) => (i % 2 === 0 || i === rows.length - 1) && (
        <text key={r.season} x={x(i)} y={H - 10} textAnchor="middle">{r.season}</text>
      ))}
    </svg>
  )
}

/** Horizontal grouped bars around zero (decomposition parts per row), one shared scale. */
export function SplitBars({ rows, parts, digits = 3 }: {
  rows: { label: string; total: number; values: Record<string, number> }[]
  parts: { key: string; label: string; color: string }[]
  digits?: number
}) {
  const max = Math.max(0.001, ...rows.flatMap((r) => [Math.abs(r.total), ...parts.map((p) => Math.abs(r.values[p.key] ?? 0))]))
  const pct = (v: number) => `${(50 * Math.abs(v)) / max}%`
  return (
    <div className="split-bars">
      <div className="chart-legend">
        {parts.map((p) => <span key={p.key}><i style={{ background: p.color }} />{p.label}</span>)}
        <span><i className="total-mark" />total change</span>
      </div>
      {rows.map((r) => (
        <div key={r.label} className="split-row">
          <span className="split-label">{r.label}</span>
          <div className="split-track">
            <i className="split-zero" />
            {parts.map((p, n) => {
              const v = r.values[p.key] ?? 0
              return (
                <span key={p.key} className="split-bar" title={`${p.label}: ${v >= 0 ? '+' : ''}${v.toFixed(digits)}`}
                  style={{ background: p.color, width: pct(v), top: `${4 + n * 9}px`, left: v >= 0 ? '50%' : undefined, right: v < 0 ? '50%' : undefined }} />
              )
            })}
            <span className="split-total" style={{ left: `calc(50% + ${(50 * r.total) / max}%)` }} title={`total ${r.total >= 0 ? '+' : ''}${r.total.toFixed(digits)}`} />
          </div>
          <span className="split-value">{r.total >= 0 ? '+' : ''}{r.total.toFixed(digits)}</span>
        </div>
      ))}
    </div>
  )
}

/** A small line chart of one measure against k, one line per phase, with the chosen k marked. */
export function MetricVsK({ title, rows, chosen = 4, better }: {
  title: string
  rows: { phase: string; k: number; value: number }[]
  chosen?: number
  better: 'higher' | 'lower'
}) {
  const W = 260, H = 150, L = 34, R = 8, T = 10, B = 24
  const ks = [...new Set(rows.map((r) => r.k))].sort((a, b) => a - b)
  const vals = rows.map((r) => r.value)
  const lo = Math.min(...vals), hi = Math.max(...vals)
  const x = (k: number) => L + ((k - ks[0]) / Math.max(1, ks[ks.length - 1] - ks[0])) * (W - L - R)
  const y = (v: number) => T + (1 - (v - lo) / Math.max(1e-9, hi - lo)) * (H - T - B)
  const colors: Record<string, string> = { attack: 'var(--site-fd)', defence: 'var(--warn)' }
  return (
    <figure className="metric-card">
      <figcaption>{title} <small>({better} is better)</small></figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${title} by number of clusters`}>
        <line x1={x(chosen)} x2={x(chosen)} y1={T} y2={H - B} stroke="var(--annotation)" strokeDasharray="3 3" />
        <text x={L - 4} y={y(hi) + 4} textAnchor="end">{hi >= 100 ? hi.toFixed(0) : hi.toFixed(2)}</text>
        <text x={L - 4} y={y(lo) + 4} textAnchor="end">{lo >= 100 ? lo.toFixed(0) : lo.toFixed(2)}</text>
        {Object.entries(colors).map(([ph, c]) => {
          const pts = rows.filter((r) => r.phase === ph).sort((a, b) => a.k - b.k)
          return (
            <g key={ph}>
              <polyline fill="none" stroke={c} strokeWidth="2" points={pts.map((p) => `${x(p.k)},${y(p.value)}`).join(' ')} />
              {pts.map((p) => <circle key={p.k} cx={x(p.k)} cy={y(p.value)} r={p.k === chosen ? 4.5 : 2.5} fill={c}><title>{`${ph}, k = ${p.k}: ${p.value}`}</title></circle>)}
            </g>
          )
        })}
        {ks.map((k) => <text key={k} x={x(k)} y={H - 8} textAnchor="middle">{k}</text>)}
      </svg>
    </figure>
  )
}
