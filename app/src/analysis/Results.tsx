import { useState } from 'react'
import { useResource } from './api'
import type { Row } from './api'
import { CiPlot, Heatmap, SplitBars, TrendChart } from './charts'
import { STYLE_COLORS } from './colors'
import { Rows } from './DataTable'

const TABS = ['Styles', 'Evolution', 'Injuries', 'Same club', 'Trends', 'Leagues'] as const
type Tab = (typeof TABS)[number]
const GROUPS = ['Defender', 'Midfielder', 'Forward', 'Goalkeeper', '≤21', '22–25', '26–29', '30+']
const OUTCOMES = ['injuries', 'days lost', 'severe injuries', 'hamstring injuries', 'knee injuries']
const fmt = (v: unknown, d = 2) => Number(v).toFixed(d)
const signed = (v: unknown, d = 1) => `${Number(v) >= 0 ? '+' : ''}${Number(v).toFixed(d)}`

export function Results() {
  const [tab, setTab] = useState<Tab>('Styles')
  const [phase, setPhase] = useState('attack')
  const [league, setLeague] = useState('All leagues')
  const [style, setStyle] = useState('')
  const [adjustment, setAdjustment] = useState('league × season')
  const [exposure, setExposure] = useState('per player-season')
  const [sameClub, setSameClub] = useState('ratio_strength')
  const [outcome, setOutcome] = useState('injuries')
  const [cells, setCells] = useState('combined style')
  // The export changes only when Phase 6 reruns: load once.
  const source = useResource<Record<string, Row[]>>('results-bundle')
  const data = source.data
  const styles = (data?.styles.filter((r) => r.phase === phase) || []).sort((a, b) => Number(a.order) - Number(b.order))
  const order = styles.map((s) => String(s.style))
  const color = (name: unknown) => STYLE_COLORS[Math.max(0, order.indexOf(String(name))) % STYLE_COLORS.length]
  const pick = (s: string) => setStyle(style === s ? '' : s)
  const on = (s: unknown) => !style || style === s
  const leagues = ['All leagues', 'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']
  const attack = (data?.styles.filter((r) => r.phase === 'attack') || []).sort((a, b) => Number(a.order) - Number(b.order)).map((s) => String(s.style))
  const defence = (data?.styles.filter((r) => r.phase === 'defence') || []).sort((a, b) => Number(a.order) - Number(b.order)).map((s) => String(s.style))

  return (
    <>
      <div className="analysis-notice">
        Association, not cause. Team strength and match load account for most of the initial difference between styles.
        Transfermarkt under-reports injuries and records them unevenly by league.
      </div>
      {source.error && <p className="analysis-alert" role="alert">{source.error}</p>}
      {!data && !source.error && <p role="status">Loading the Phase 6 results export…</p>}
      {data && (
        <>
          <div className="analysis-panel results-controls">
            <div className="analysis-toolbar">
              <div className="analysis-actions" role="tablist" aria-label="Result views">
                {TABS.map((t) => (
                  <button key={t} role="tab" className="btn btn-outline btn-sm" aria-selected={tab === t} aria-pressed={tab === t} onClick={() => setTab(t)}>{t}</button>
                ))}
              </div>
              <a className="btn btn-outline btn-sm" href="/analysis/report">Course report →</a>
            </div>
            <div className="analysis-toolbar">
              <label>Phase of play{' '}
                <select value={phase} onChange={(e) => { setPhase(e.target.value); setStyle('') }}>
                  <option value="attack">Attacking</option>
                  <option value="defence">Defensive</option>
                </select>
              </label>
              {['Styles', 'Evolution', 'Leagues'].includes(tab) && (
                <label>League{' '}
                  <select value={league} onChange={(e) => setLeague(e.target.value)}>
                    {leagues.map((l) => <option key={l}>{l}</option>)}
                  </select>
                </label>
              )}
              <div className="chart-legend" aria-label="Pick a style to follow it through every chart">
                {order.map((s) => (
                  <button key={s} aria-pressed={style === s} className={on(s) ? '' : 'is-dim'} onClick={() => pick(s)}>
                    <i style={{ background: color(s) }} />{s}
                  </button>
                ))}
                {style && <button className="text-link" onClick={() => setStyle('')}>Clear ×</button>}
              </div>
            </div>
          </div>

          {tab === 'Styles' && (
            <>
              <section className="analysis-panel">
                <h2>The style map</h2>
                <p className="analysis-muted">
                  Each dot is a team-season, placed by its four {phase === 'attack' ? 'attacking' : 'defensive'} dimensions (PCA,
                  for drawing only). Fainter dots belong to their style less clearly (fuzzy membership). Hover for the club;
                  click to follow its style.
                </p>
                <ClusterMap rows={data.cluster_map.filter((r) => r.phase === phase && (league === 'All leagues' || r.league === league))}
                  color={color} on={on} pick={pick} selected={style} />
              </section>
              <div className="style-cards">
                {styles.filter((s) => on(s.style)).map((s) => (
                  <article key={String(s.style)} className="analysis-panel style-card" style={{ borderTopColor: color(s.style) }}>
                    <div className="analysis-kicker">{String(s.team_seasons)} team-seasons · {String(s.core)} clear members</div>
                    <h2><button className="text-link" onClick={() => pick(String(s.style))}>{String(s.style)}</button></h2>
                    <p>{String(s.how)}</p>
                    <p className="analysis-muted">{String(s.numbers)}</p>
                    <dl>
                      <dt>Injuries vs league-season</dt>
                      <dd><b>{fmt(s.rr)}</b> ({fmt(s.rr_low)}–{fmt(s.rr_high)}) · {signed(s.excess_per_100)} per 100 player-seasons</dd>
                      <dt>Days lost</dt><dd>{fmt(s.days_rr)}</dd>
                      <dt>Points per match · back-three minutes</dt><dd>{String(s.points)} · {String(s.back_three)}</dd>
                      <dt>Most often with</dt><dd>{String(s.paired_with)}</dd>
                      <dt>Typical teams</dt>
                      <dd>
                        <span className="era">2014–18</span> {String(s.typical_2014_18)}<br />
                        <span className="era">2018–22</span> {String(s.typical_2018_22)}<br />
                        <span className="era">2022–26</span> {String(s.typical_2022_26)}
                      </dd>
                    </dl>
                  </article>
                ))}
              </div>
            </>
          )}

          {tab === 'Evolution' && (
            <>
              <section className="analysis-panel">
                <h2>How the style mix changed{league !== 'All leagues' ? ` · ${league}` : ''}</h2>
                <LineChart rows={data.style_shares.filter((r) => r.phase === phase && r.league === league && on(r.style))} series="style" value="share" color={color} percent />
              </section>
              <section className="analysis-panel">
                <h2>Style dimensions over time</h2>
                <LineChart rows={data.dimension_trends.filter((r) => r.phase === phase && r.league === league)} series="dimension" value="value" />
                <p className="analysis-muted">Mean score per season, standardised over all team-seasons (0 = the 12-season average).</p>
              </section>
            </>
          )}

          {tab === 'Injuries' && (
            <>
              <section className="analysis-panel">
                <h2>Style or schedule? Adjusting step by step</h2>
                <p className="analysis-muted">
                  Injury rate ratio as each adjustment is added. Most of the possession and pressing excess goes with team
                  strength and matches played; the last row of each exposure is the style's own association. Click a cell to
                  follow a style.
                </p>
                <Heatmap
                  corner="expected from"
                  rows={[...new Set(data.rr_ladder.filter((r) => r.grouping === phase).map((r) => `${r.exposure}: ${r.adjustment}`))]}
                  cols={order}
                  cell={(row, col) => {
                    const r = data.rr_ladder.find((x) => x.grouping === phase && x.style === col && `${x.exposure}: ${x.adjustment}` === row)
                    return r ? { value: Number(r.rr), label: fmt(r.rr), dim: !on(col), title: `${col}, ${row}: ${fmt(r.rr)} (95% CI ${fmt(r.rr_low)}–${fmt(r.rr_high)}); ${signed(r.excess_per_100)} per 100 player-seasons` } : null
                  }}
                  onPick={(_, col) => pick(col)}
                  caption="Rate ratios under each adjustment"
                />
              </section>
              <section className="analysis-panel">
                <div className="analysis-toolbar">
                  <h2>Rate ratios with 95% confidence intervals</h2>
                  <div className="analysis-actions">
                    <label>Exposure{' '}
                      <select value={exposure} onChange={(e) => { setExposure(e.target.value); setAdjustment('league × season') }}>
                        {[...new Set(data.rr_ladder.map((r) => String(r.exposure)))].map((v) => <option key={v}>{v}</option>)}
                      </select>
                    </label>
                    <label>Expected from{' '}
                      <select value={adjustment} onChange={(e) => setAdjustment(e.target.value)}>
                        {[...new Set(data.rr_ladder.filter((r) => r.exposure === exposure).map((r) => String(r.adjustment)))].map((v) => <option key={v}>{v}</option>)}
                      </select>
                    </label>
                  </div>
                </div>
                <CiPlot rows={data.rr_ladder.filter((r) => r.grouping === phase && r.exposure === exposure && r.adjustment === adjustment).map((r) => ({
                  label: String(r.style), value: Number(r.rr), low: Number(r.rr_low), high: Number(r.rr_high), color: color(r.style),
                  note: `${signed(r.excess_per_100)} per 100`, dim: !on(r.style), onClick: () => pick(String(r.style)),
                }))} />
                <p className="analysis-muted">1 = expected; bootstrap over clubs. Formation (back three vs back four) is about 1 in every version.</p>
              </section>
              <div className="analysis-grid-2">
                <section className="analysis-panel">
                  <h2>Attacking × defensive style</h2>
                  <p className="analysis-muted">Rate ratio per combination, shrunk towards the average by its uncertainty (hover for the raw value). Grey: fewer than 40 team-seasons.</p>
                  <Heatmap corner="attack \ defence" rows={attack} cols={defence}
                    cell={(a, d) => {
                      const r = data.grid.find((x) => x.attack === a && x.defence === d)
                      return r ? { value: Number(r.rr_shrunk), muted: Number(r.team_seasons) < 40, dim: !!style && style !== a && style !== d,
                        label: <>{fmt(r.rr_shrunk)}<small> n={String(r.team_seasons)}</small></>,
                        title: `${a} · ${d}: ${fmt(r.rr_shrunk)} shrunk, ${fmt(r.rr)} raw (${Math.round(Number(r.weight_own_data) * 100)}% weight on own data); days lost ${fmt(r.days_rr_shrunk)}` } : null
                    }} caption="Rate ratio by attacking and defensive style" />
                </section>
                <section className="analysis-panel">
                  <h2>Formation</h2>
                  <p className="analysis-muted">Back three (at least half of the minutes) against back four: no difference in injuries.</p>
                  <CiPlot rows={data.injury_rr.filter((r) => r.grouping === 'formation').map((r) => ({
                    label: String(r.style), value: Number(r.rr), low: Number(r.rr_low), high: Number(r.rr_high), color: 'var(--muted)',
                    note: `${Number(r.player_seasons).toLocaleString()} player-seasons`,
                  }))} />
                </section>
              </div>
              <section className="analysis-panel">
                  <h2>Where players get hurt</h2>
                  <p className="analysis-muted">Share of injuries in each area relative to the league's share (median over leagues); x/5 = leagues above 1. ★ = survives the permutation test after correction for 72 comparisons.</p>
                  <Heatmap corner="style" rows={order.filter(on)}
                    cols={[...new Set(data.body_areas.filter((r) => r.phase === phase).map((r) => String(r.area)))]}
                    cell={(s, a) => {
                      const r = data.body_areas.find((x) => x.phase === phase && x.style === s && x.area === a)
                      return r ? { value: Number(r.relative), strong: !!r.finding,
                        label: <>{r.finding ? '★ ' : ''}{fmt(r.relative)}<small> {String(r.leagues_above)}/5</small></>,
                        title: `${s}, ${a}: ${fmt(r.relative)}× the league's share; within-league odds ratio ${fmt(r.odds_ratio)}, q = ${Number(r.q) < 0.001 ? '< 0.001' : fmt(r.q, 3)}` } : null
                    }} onPick={(s) => pick(s)} caption="Body areas by style" />
              </section>
              <section className="analysis-panel">
                <h2>Who carries the excess: position and age</h2>
                <p className="analysis-muted">Rate ratio within each style by position and age band (against the league-season average for all players).</p>
                <Heatmap corner="style" rows={order.filter(on)} cols={GROUPS}
                  cell={(s, g) => {
                    const r = data.breakdown.find((x) => x.phase === phase && x.style === s && x.group === g)
                    return r ? { value: Number(r.rr), label: fmt(r.rr), title: `${s}, ${g}: ${fmt(r.rr)} (${fmt(r.rr_low)}–${fmt(r.rr_high)}); ${signed(r.excess_per_100)} per 100; ${Number(r.player_seasons).toLocaleString()} player-seasons` } : null
                  }} onPick={(s) => pick(s)} caption="Rate ratio by position and age band" />
              </section>
            </>
          )}

          {tab === 'Same club' && (
            <>
              <section className="analysis-panel">
                <div className="analysis-toolbar">
                  <div>
                    <h2>Same club, with and without the style</h2>
                    <p className="analysis-muted">
                      For clubs that played some seasons in a style and some not: their injury rate in the style's seasons ÷
                      their rate in their other seasons. The club, its medical staff and its recording stay the same.
                    </p>
                  </div>
                  <label>Compared against{' '}
                    <select value={sameClub} onChange={(e) => setSameClub(e.target.value)}>
                      <option value="ratio">league × season</option>
                      <option value="ratio_strength">+ team strength</option>
                      <option value="ratio_match">per team match, + strength</option>
                    </select>
                  </label>
                </div>
                <CiPlot unit="ratio" rows={data.same_club.filter((r) => r.phase === phase).map((r) => ({
                  label: String(r.style), value: Number(r[sameClub]), low: Number(r[`${sameClub}_low`]), high: Number(r[`${sameClub}_high`]),
                  color: color(r.style), dim: !on(r.style), onClick: () => pick(String(r.style)),
                  note: `${r.clubs} clubs`,
                }))} />
              </section>
              <section className="analysis-panel">
                <h2>Switching style</h2>
                <p className="analysis-muted">
                  Rate ratio (against teams of the same strength) the season before and the season after a club switched into or
                  out of a style. If the style itself raised injuries, switching in would raise the rate and switching out lower it.
                </p>
                <Heatmap corner="style" rows={order.filter(on)} cols={['into', 'out of']} mode="ratio"
                  cell={(s, w) => {
                    const r = data.style_switches.find((x) => x.phase === phase && x.style === s && x.switch === w)
                    return r ? { value: Number(r.after) / Number(r.before), label: <>{fmt(r.before)} → {fmt(r.after)}<small> n={String(r.switches)}</small></>,
                      title: `${String(r.switches)} switches ${w} ${s}: ${fmt(r.before)} → ${fmt(r.after)} (${signed(r.change, 2)})` } : null
                  }} onPick={(s) => pick(s)} caption="Rate ratio before and after a style switch" />
              </section>
            </>
          )}

          {tab === 'Trends' && (
            <>
              <section className="analysis-panel">
                <h2>Injuries per player-season</h2>
                <p className="analysis-muted">All leagues. Dots: single seasons with 95% CI band; line: 3-season rolling mean. Raw Transfermarkt records also reflect recording changes (Premier League 2018-19).</p>
                <TrendChart rows={data.season_trend.map((r) => ({ season: String(r.season), value: Number(r.injuries_per_ps), low: Number(r.low), high: Number(r.high), rolling: Number(r.injuries_rolling) }))} />
              </section>
              <section className="analysis-panel">
                <div className="analysis-toolbar">
                  <div>
                    <h2>Where the change between 2014–18 and 2022–26 comes from</h2>
                    <p className="analysis-muted">Kitagawa decomposition with cells league × strength × style: teams' strength mix, the style mix beyond strength, and change within styles. An upper bound on style's role, not a cause.</p>
                  </div>
                  <div className="analysis-actions">
                    <label>Outcome{' '}
                      <select value={outcome} onChange={(e) => setOutcome(e.target.value)}>{OUTCOMES.map((o) => <option key={o}>{o}</option>)}</select>
                    </label>
                    <label>Styles{' '}
                      <select value={cells} onChange={(e) => setCells(e.target.value)}>
                        {['combined style', 'attacking style', 'defensive style'].map((o) => <option key={o}>{o}</option>)}
                      </select>
                    </label>
                  </div>
                </div>
                <SplitBars digits={outcome === 'days lost' ? 2 : 3}
                  parts={[{ key: 'strength_mix', label: 'strength mix', color: 'var(--lg-pl)' }, { key: 'style_mix', label: 'style mix (beyond strength)', color: 'var(--site-fd)' }, { key: 'within_styles', label: 'within styles', color: 'var(--warn)' }]}
                  rows={['all leagues', ...leagues.slice(1)].map((scope) => {
                    const r = data.decomposition.find((x) => x.scope === scope && x.outcome === outcome && x.styles === cells)
                    return { label: scope, total: Number(r?.change ?? 0), values: { strength_mix: Number(r?.strength_mix ?? 0), style_mix: Number(r?.style_mix ?? 0), within_styles: Number(r?.within_styles ?? 0) } }
                  })} />
              </section>
            </>
          )}

          {tab === 'Leagues' && (
            <div className="league-stories">
              {data.league_stories.filter((r) => league === 'All leagues' || r.league === league).map((r) => {
                const d = data.decomposition.find((x) => x.scope === r.league && x.outcome === 'injuries' && x.styles === 'combined style')
                return (
                  <article className="analysis-panel" key={String(r.league)}>
                    <div className="analysis-kicker">League story</div>
                    <h2>{String(r.league)}</h2>
                    {d && (
                      <div className="analysis-kpis compact">
                        <div><strong>{fmt(d.from)} → {fmt(d.to)}</strong><span>injuries per player-season</span></div>
                        <div><strong>{signed(d.style_mix, 3)}</strong><span>from the style mix (beyond strength)</span></div>
                        <div><strong>{signed(d.within_styles, 3)}</strong><span>within styles</span></div>
                      </div>
                    )}
                    <p>{String(r.story).replace(/^[^.]+\.\s*/, '')}</p>
                  </article>
                )
              })}
            </div>
          )}
          <details className="analysis-panel">
            <summary>Data behind this view</summary>
            <Rows rows={(tab === 'Styles' ? data.styles : tab === 'Evolution' ? data.style_shares : tab === 'Injuries' ? data.rr_ladder : tab === 'Same club' ? data.same_club : tab === 'Trends' ? data.decomposition : data.league_stories)
              .filter((r) => (!r.phase || r.phase === phase) && (!r.grouping || r.grouping === phase || tab !== 'Injuries')).slice(0, 200)} />
          </details>
          <p className="analysis-muted">Source: Phase 6 export · <a href="/analysis/studio/phase-06/step-4">How it was built →</a></p>
        </>
      )}
    </>
  )
}

function ClusterMap({ rows, color, on, pick, selected }: {
  rows: Row[]; color: (s: unknown) => string; on: (s: unknown) => boolean; pick: (s: string) => void; selected: string
}) {
  const W = 900, H = 420, P = 24
  const xs = rows.map((r) => Number(r.pc1)), ys = rows.map((r) => Number(r.pc2))
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)]
  const x = (v: number) => P + ((v - x0) / Math.max(1e-9, x1 - x0)) * (W - 2 * P)
  const y = (v: number) => H - P - ((v - y0) / Math.max(1e-9, y1 - y0)) * (H - 2 * P)
  if (!rows.length) return <p className="analysis-muted">No team-seasons for this filter.</p>
  return (
    <svg className="cluster-chart" viewBox={`0 0 ${W} ${H}`} role="group" aria-label="Team-seasons by playing style">
      {rows.map((r, i) => (
        <circle key={i} cx={x(Number(r.pc1))} cy={y(Number(r.pc2))} r={selected === r.style ? 5 : 3.6}
          fill={on(r.style) ? color(r.style) : 'var(--muted)'} opacity={on(r.style) ? 0.25 + 0.7 * Number(r.membership) : 0.12}
          onClick={() => pick(String(r.style))}>
          <title>{`${r.club} · ${r.season} · ${r.league}\n${r.style}: membership ${fmt(r.membership)}\nNext: ${r.second_style} ${fmt(r.second_membership)}`}</title>
        </circle>
      ))}
    </svg>
  )
}

function LineChart({ rows, series, value, color, percent }: {
  rows: Row[]; series: string; value: string; color?: (name: unknown) => string; percent?: boolean
}) {
  const seasons = [...new Set(rows.map((r) => String(r.season)))].sort()
  const groups = [...new Set(rows.map((r) => String(r[series])))]
  if (!rows.length) return <p className="analysis-muted">No matching data.</p>
  const values = rows.map((r) => Number(r[value]))
  const min = Math.min(0, ...values), max = Math.max(...values, 0.01)
  const x = (s: string) => 55 + (seasons.indexOf(s) / Math.max(1, seasons.length - 1)) * 780
  const y = (v: number) => 250 - ((v - min) / (max - min)) * 210
  const c = (g: string, i: number) => color?.(g) || STYLE_COLORS[i % STYLE_COLORS.length]
  const label = (v: number) => (percent ? `${Math.round(v * 100)}%` : v.toFixed(2))
  return (
    <>
      <svg className="line-chart" viewBox="0 0 900 300" role="img" aria-label={`${value.replaceAll('_', ' ')} by season`}>
        {[min, (min + max) / 2, max].map((t) => (
          <g key={t}><line x1="55" x2="850" y1={y(t)} y2={y(t)} stroke="var(--line)" /><text x="48" y={y(t) + 4} textAnchor="end">{label(t)}</text></g>
        ))}
        {groups.map((g, i) => {
          const pts = rows.filter((r) => r[series] === g).sort((a, b) => String(a.season).localeCompare(String(b.season)))
          return (
            <g key={g}>
              <polyline fill="none" stroke={c(g, i)} strokeWidth="2.5" points={pts.map((r) => `${x(String(r.season))},${y(Number(r[value]))}`).join(' ')} />
              {pts.map((r) => (
                <circle key={String(r.season)} cx={x(String(r.season))} cy={y(Number(r[value]))} r="3.5" fill={c(g, i)}>
                  <title>{`${g} · ${r.season}: ${percent ? `${(Number(r[value]) * 100).toFixed(1)}%` : Number(r[value]).toFixed(2)}`}</title>
                </circle>
              ))}
            </g>
          )
        })}
        {seasons.filter((_, i) => i % 2 === 0 || i === seasons.length - 1).map((s) => <text key={s} x={x(s)} y="280" textAnchor="middle">{s}</text>)}
      </svg>
      <div className="chart-legend">{groups.map((g, i) => <span key={g}><i style={{ background: c(g, i) }} />{g}</span>)}</div>
    </>
  )
}
