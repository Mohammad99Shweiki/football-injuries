import { useState } from 'react'
import { useResource } from './api'
import type { Row } from './api'
import { CiPlot, Heatmap, SplitBars, TrendChart } from './charts'
import { STYLE_COLORS } from './colors'
import { Rows } from './DataTable'
import { More } from './More'

const TABS = ['Styles', 'Injury mix', 'Evolution', 'Injuries', 'Same club', 'Trends', 'Leagues'] as const
type Tab = (typeof TABS)[number]
const GROUPS = ['Defender', 'Midfielder', 'Forward', 'Goalkeeper', '≤21', '22–25', '26–29', '30+']
const FAMILIES = [['type', 'Type'], ['location', 'Location'], ['pattern', 'Type × location']] as const
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
  const [mixAdjusted, setMixAdjusted] = useState(false)
  const [family, setFamily] = useState<string>('type')
  // The export changes only when Phase 7 reruns: load once.
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
      {source.error && <p className="analysis-alert" role="alert">{source.error}</p>}
      {!data && !source.error && <p role="status">Loading the results…</p>}
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
                <p className="analysis-caption">Each dot is a team-season; fainter dots fit their style less clearly. Click to follow a style.</p>
                <ClusterMap rows={data.cluster_map.filter((r) => r.phase === phase && (league === 'All leagues' || r.league === league))}
                  color={color} on={on} pick={pick} selected={style} />
              </section>
              <div className="style-cards">
                {styles.filter((s) => on(s.style)).map((s) => (
                  <article key={String(s.style)} className="analysis-panel style-card" style={{ borderTopColor: color(s.style) }}>
                    <div className="analysis-kicker">{String(s.team_seasons)} team-seasons</div>
                    <h2><button className="text-link" onClick={() => pick(String(s.style))}>{String(s.style)}</button></h2>
                    <p>{String(s.how)}</p>
                    <p className="analysis-caption">e.g. {String(s.typical_2022_26)}</p>
                    <More label="Numbers">
                      <p className="analysis-muted">{String(s.numbers)}</p>
                      <dl>
                        <dt>Injuries vs league-season</dt>
                        <dd><b>{fmt(s.rr)}</b> ({fmt(s.rr_low)}–{fmt(s.rr_high)})</dd>
                        <dt>Points per match · back-three minutes</dt><dd>{String(s.points)} · {String(s.back_three)}</dd>
                        <dt>Most often with</dt><dd>{String(s.paired_with)}</dd>
                        <dt>Earlier examples</dt>
                        <dd><span className="era">2014–18</span> {String(s.typical_2014_18)}<br /><span className="era">2018–22</span> {String(s.typical_2018_22)}</dd>
                      </dl>
                    </More>
                  </article>
                ))}
              </div>
            </>
          )}

          {tab === 'Injury mix' && (() => {
            const mix = data.injury_mix || []
            const ratios = mix.filter((r) => r.kind === 'ratio' && r.phase === phase)
            const cats = [...new Set(ratios.filter((r) => r.family === family || r.family === 'severity').map((r) => String(r.category)))]
            const omni = mix.filter((r) => r.kind === 'omnibus' && r.phase === phase)
            const centres = mix.filter((r) => r.kind === 'centre')
            const groups = [...new Set(centres.map((r) => String(r.group)))]
            const shares = mix.filter((r) => r.kind === 'share' && r.phase === phase)
            const assoc = mix.find((r) => r.kind === 'association' && r.with === `${phase} style`)
            const chosen = mix.filter((r) => r.kind === 'k').find((r) => Number(r.k) === groups.length)
            return (
              <>
                <section className="analysis-panel">
                  <div className="analysis-toolbar">
                    <h2>What kind of injuries each style gets</h2>
                    <div className="analysis-actions">
                      <div className="segmented" role="group" aria-label="Injury categories">
                        {FAMILIES.map(([f, label]) => (
                          <button key={f} aria-pressed={family === f} onClick={() => setFamily(f)}>{label}</button>
                        ))}
                      </div>
                      <label className="check-label">
                        <input type="checkbox" checked={mixAdjusted} onChange={(e) => setMixAdjusted(e.target.checked)} /> account for team strength
                      </label>
                    </div>
                  </div>
                  <p className="analysis-caption">Injuries of each kind relative to the usual mix in the same leagues and seasons (1 = usual). ★ significant · ✓ still holds after team strength.</p>
                  <Heatmap
                    corner="style"
                    rows={order}
                    cols={cats}
                    cell={(st, c) => {
                      const r = ratios.find((x) => x.style === st && x.category === c)
                      if (!r) return null
                      const v = Number(mixAdjusted ? r.ratio_adjusted : r.ratio)
                      const mark = r.finding ? (r.robust ? '★✓' : '★') : ''
                      return { value: v, label: `${fmt(v)}${mark}`, strong: Boolean(r.finding), dim: !on(st),
                        title: `${st}, ${c}: ${r.observed} observed vs ${fmt(r.expected, 1)} expected; ratio ${fmt(r.ratio)} (95% CI ${fmt(r.low)}–${fmt(r.high)}), q = ${fmt(r.q, 3)}; with position and strength ${fmt(r.ratio_adjusted)} (${fmt(r.adjusted_low)}–${fmt(r.adjusted_high)})` }
                    }}
                    onPick={(st) => pick(st)}
                    caption="Injury mix by style"
                  />
                  <More label="Method and tests">
                    <p className="analysis-muted">
                      Profile ratio = a style's injuries of a category ÷ the number expected from that category's share among
                      injuries of the same league and season. 95% CIs from a bootstrap over clubs; ★ = Benjamini–Hochberg q &lt; 0.05
                      over all 184 tests (permutation within league-seasons); ✓ = the CI still excludes 1 with position and team
                      strength in the expected mix. Does the mix differ at all ({phase})?{' '}
                      {omni.map((r) => `${r.family} p ${Number(r.p) < 0.001 ? '< 0.001' : `= ${fmt(r.p, 3)}`}`).join(' · ')}.
                    </p>
                  </More>
                </section>
                <section className="analysis-panel">
                  <h2>Two injury profiles</h2>
                  <p className="analysis-caption">
                    Clustering team-seasons by their injury mix gives a muscle-heavy and a joint- and contact-heavy group.
                    {assoc ? ` The link with ${phase === 'attack' ? 'attacking' : 'defensive'} style is weak (V ${fmt(assoc.v)}, p = ${fmt(assoc.p, 3)}) and disappears within strength thirds (p = ${fmt(assoc.p_within_strength, 2)}).` : ''}
                  </p>
                  <Heatmap mode="z" corner="group" rows={groups} cols={order}
                    cell={(g, st) => {
                      const r = shares.find((x) => x.group === g && x.style === st)
                      return r ? { value: (Number(r.share) - 1 / groups.length) * 4, label: `${Math.round(Number(r.share) * 100)}%`, dim: !on(st) } : null
                    }} onPick={(_, st) => pick(st)} caption="Style shares per injury-profile group" />
                  <More label="Group centres and cluster quality">
                    <p className="analysis-muted">
                      K-means on each team-season's departure from its league-season's injury mix (team-seasons with at least 10
                      injuries).{chosen ? ` Silhouette ${fmt(chosen.silhouette)} vs ${fmt(chosen.null_silhouette)} for shuffled data; weakest cluster Jaccard ${fmt(chosen.min_jaccard)}.` : ''}
                    </p>
                    <Heatmap mode="z" corner="group" rows={groups} cols={[...new Set(centres.map((r) => String(r.feature)))]}
                      cell={(g, f) => {
                        const r = centres.find((x) => x.group === g && x.feature === f)
                        return r ? { value: Number(r.value), label: signed(r.value) } : null
                      }} caption="Injury-profile group centres" />
                  </More>
                </section>
              </>
            )
          })()}

          {tab === 'Evolution' && (
            <section className="analysis-panel">
              <h2>How the style mix changed{league !== 'All leagues' ? ` · ${league}` : ''}</h2>
              <LineChart rows={data.style_shares.filter((r) => r.phase === phase && r.league === league && on(r.style))} series="style" value="share" color={color} percent />
              <More label="Style dimensions over time">
                <p className="analysis-caption">Mean score per season (0 = the 12-season average).</p>
                <LineChart rows={data.dimension_trends.filter((r) => r.phase === phase && r.league === league)} series="dimension" value="value" />
              </More>
            </section>
          )}

          {tab === 'Injuries' && (
            <section className="analysis-panel">
              <div className="analysis-toolbar">
                <h2>How often players get injured</h2>
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
              <p className="analysis-caption">Injury rate vs the expected rate (1 = expected; 95% CI over clubs). Most of the excess goes once team strength is taken into account.</p>
              <CiPlot rows={data.rr_ladder.filter((r) => r.grouping === phase && r.exposure === exposure && r.adjustment === adjustment).map((r) => ({
                label: String(r.style), value: Number(r.rr), low: Number(r.rr_low), high: Number(r.rr_high), color: color(r.style),
                note: `${signed(r.excess_per_100)} per 100`, dim: !on(r.style), onClick: () => pick(String(r.style)),
              }))} />
              <More label="Every adjustment side by side">
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
              </More>
              <More label="Attacking × defensive combinations and formation">
                <p className="analysis-caption">Shrunk towards the average by uncertainty; grey: fewer than 40 team-seasons. Back three vs back four: no difference.</p>
                <Heatmap corner="attack \ defence" rows={attack} cols={defence}
                  cell={(a, d) => {
                    const r = data.grid.find((x) => x.attack === a && x.defence === d)
                    return r ? { value: Number(r.rr_shrunk), muted: Number(r.team_seasons) < 40, dim: !!style && style !== a && style !== d,
                      label: <>{fmt(r.rr_shrunk)}<small> n={String(r.team_seasons)}</small></>,
                      title: `${a} · ${d}: ${fmt(r.rr_shrunk)} shrunk, ${fmt(r.rr)} raw (${Math.round(Number(r.weight_own_data) * 100)}% weight on own data); days lost ${fmt(r.days_rr_shrunk)}` } : null
                  }} caption="Rate ratio by attacking and defensive style" />
                <CiPlot rows={data.injury_rr.filter((r) => r.grouping === 'formation').map((r) => ({
                  label: String(r.style), value: Number(r.rr), low: Number(r.rr_low), high: Number(r.rr_high), color: 'var(--muted)',
                  note: `${Number(r.player_seasons).toLocaleString()} player-seasons`,
                }))} />
              </More>
              <More label="Body areas (relative to the league)">
                <p className="analysis-caption">Median over leagues; x/5 = leagues above 1; ★ survives correction for 72 tests.</p>
                <Heatmap corner="style" rows={order.filter(on)}
                  cols={[...new Set(data.body_areas.filter((r) => r.phase === phase).map((r) => String(r.area)))]}
                  cell={(s, a) => {
                    const r = data.body_areas.find((x) => x.phase === phase && x.style === s && x.area === a)
                    return r ? { value: Number(r.relative), strong: !!r.finding,
                      label: <>{r.finding ? '★ ' : ''}{fmt(r.relative)}<small> {String(r.leagues_above)}/5</small></>,
                      title: `${s}, ${a}: ${fmt(r.relative)}× the league's share; within-league odds ratio ${fmt(r.odds_ratio)}, q = ${Number(r.q) < 0.001 ? '< 0.001' : fmt(r.q, 3)}` } : null
                  }} onPick={(s) => pick(s)} caption="Body areas by style" />
              </More>
              <More label="By position and age">
                <Heatmap corner="style" rows={order.filter(on)} cols={GROUPS}
                  cell={(s, g) => {
                    const r = data.breakdown.find((x) => x.phase === phase && x.style === s && x.group === g)
                    return r ? { value: Number(r.rr), label: fmt(r.rr), title: `${s}, ${g}: ${fmt(r.rr)} (${fmt(r.rr_low)}–${fmt(r.rr_high)}); ${signed(r.excess_per_100)} per 100; ${Number(r.player_seasons).toLocaleString()} player-seasons` } : null
                  }} onPick={(s) => pick(s)} caption="Rate ratio by position and age band" />
              </More>
            </section>
          )}

          {tab === 'Same club' && (
            <section className="analysis-panel">
              <div className="analysis-toolbar">
                <h2>Same club, with and without the style</h2>
                <label>Compared against{' '}
                  <select value={sameClub} onChange={(e) => setSameClub(e.target.value)}>
                    <option value="ratio">league × season</option>
                    <option value="ratio_strength">+ team strength</option>
                    <option value="ratio_match">per team match, + strength</option>
                  </select>
                </label>
              </div>
              <p className="analysis-caption">A club's injury rate in its seasons with the style ÷ its rate in its other seasons.</p>
              <CiPlot unit="ratio" rows={data.same_club.filter((r) => r.phase === phase).map((r) => ({
                label: String(r.style), value: Number(r[sameClub]), low: Number(r[`${sameClub}_low`]), high: Number(r[`${sameClub}_high`]),
                color: color(r.style), dim: !on(r.style), onClick: () => pick(String(r.style)),
                note: `${r.clubs} clubs`,
              }))} />
              <More label="Switching style: the season before and after">
                <p className="analysis-caption">If a style raised injuries, switching into it would raise the rate and switching out would lower it.</p>
                <Heatmap corner="style" rows={order.filter(on)} cols={['into', 'out of']} mode="ratio"
                  cell={(s, w) => {
                    const r = data.style_switches.find((x) => x.phase === phase && x.style === s && x.switch === w)
                    return r ? { value: Number(r.after) / Number(r.before), label: <>{fmt(r.before)} → {fmt(r.after)}<small> n={String(r.switches)}</small></>,
                      title: `${String(r.switches)} switches ${w} ${s}: ${fmt(r.before)} → ${fmt(r.after)} (${signed(r.change, 2)})` } : null
                  }} onPick={(s) => pick(s)} caption="Rate ratio before and after a style switch" />
              </More>
            </section>
          )}

          {tab === 'Trends' && (
            <section className="analysis-panel">
              <h2>Injuries per player-season</h2>
              <p className="analysis-caption">All leagues; dots are seasons, the line a 3-season mean.</p>
              <TrendChart rows={data.season_trend.map((r) => ({ season: String(r.season), value: Number(r.injuries_per_ps), low: Number(r.low), high: Number(r.high), rolling: Number(r.injuries_rolling) }))} />
              <More label="Where the change between 2014–18 and 2022–26 comes from">
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
                <p className="analysis-caption">Kitagawa decomposition (cells league × strength × style); an upper bound on style's role.</p>
                <SplitBars digits={outcome === 'days lost' ? 2 : 3}
                  parts={[{ key: 'strength_mix', label: 'strength mix', color: 'var(--lg-pl)' }, { key: 'style_mix', label: 'style mix (beyond strength)', color: 'var(--site-fd)' }, { key: 'within_styles', label: 'within styles', color: 'var(--warn)' }]}
                  rows={['all leagues', ...leagues.slice(1)].map((scope) => {
                    const r = data.decomposition.find((x) => x.scope === scope && x.outcome === outcome && x.styles === cells)
                    return { label: scope, total: Number(r?.change ?? 0), values: { strength_mix: Number(r?.strength_mix ?? 0), style_mix: Number(r?.style_mix ?? 0), within_styles: Number(r?.within_styles ?? 0) } }
                  })} />
              </More>
            </section>
          )}

          {tab === 'Leagues' && (
            <section className="analysis-panel">
              <h2>Body areas by league and era</h2>
              <p className="analysis-caption">Injuries per 100 player-seasons (orange above, blue below the league's 2014–18 level). Compare eras within a league.</p>
              <Heatmap corner="league · era"
                rows={data.body_league.filter((r) => league === 'All leagues' || r.league === league).map((r) => `${r.league} · ${r.era}`).filter((v, i, a) => a.indexOf(v) === i)}
                cols={[...new Set(data.body_league.map((r) => String(r.area)))]}
                cell={(row, area) => {
                  const [lg, era] = row.split(' · ')
                  const r = data.body_league.find((x) => x.league === lg && x.era === era && x.area === area)
                  const base = data.body_league.find((x) => x.league === lg && x.era === '2014–18' && x.area === area)
                  return r && base ? { value: Number(r.per_100) / Math.max(0.1, Number(base.per_100)), label: fmt(r.per_100, 1),
                    title: `${lg} ${era}, ${area}: ${fmt(r.per_100, 1)} per 100 player-seasons; ${Math.round(Number(r.share_known) * 100)}% of injuries with a known area; ${Math.round(Number(r.unknown_share) * 100)}% of all injuries have no known area` } : null
                }} caption="Injuries per 100 player-seasons by body area, league and era" />
              <More label="League stories">
                <div className="league-stories">
                  {data.league_stories.filter((r) => league === 'All leagues' || r.league === league).map((r) => (
                    <article key={String(r.league)}>
                      <h3>{String(r.league)}</h3>
                      <p>{String(r.story).replace(/^[^.]+\.\s*/, '')}</p>
                    </article>
                  ))}
                </div>
              </More>
            </section>
          )}
          <More label="Data behind this view">
            <Rows rows={(tab === 'Styles' ? data.styles : tab === 'Injury mix' ? (data.injury_mix || []).filter((r) => r.kind === 'ratio') : tab === 'Evolution' ? data.style_shares : tab === 'Injuries' ? data.rr_ladder : tab === 'Same club' ? data.same_club : tab === 'Trends' ? data.decomposition : data.league_stories)
              .filter((r) => (!r.phase || r.phase === phase) && (!r.grouping || r.grouping === phase || tab !== 'Injuries')).slice(0, 200)} />
          </More>
          <p className="analysis-caption">Association, not cause · Transfermarkt under-reports injuries · <a href="/analysis/studio/phase-07/step-4">How it was built →</a></p>
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
