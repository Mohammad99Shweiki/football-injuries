import { useState } from 'react'
import { useResource } from './api'
import type { Row } from './api'
import { Rows } from './DataTable'

const palette = [
  'var(--site-fd)',
  'var(--lg-pl)',
  'var(--annotation)',
  'var(--warn)',
]
export function Results() {
  const [tab, setTab] = useState('Styles')
  const [phase, setPhase] = useState('attack')
  const [league, setLeague] = useState('All leagues')
  const [style, setStyle] = useState('')
  const [adjustment, setAdjustment] = useState('league × season')
  const [exposure, setExposure] = useState('per player-season')
  const source = useResource<Record<string, Row[]>>('results-bundle', 15000)
  const data = source.data
  const styles = data?.styles.filter((r) => r.phase === phase) || []
  const color = (name: unknown) =>
    palette[
      Math.max(
        0,
        styles.findIndex((s) => s.style === name),
      ) % palette.length
    ]
  const matches = (r: Row) =>
    (!r.phase || r.phase === phase) &&
    (!r.grouping || r.grouping === phase) &&
    (!style || r.style === style) &&
    (!r.league || r.league === league)
  const selectStyle = (s: string) => setStyle(style === s ? '' : s)
  const leagues = [
    'All leagues',
    ...new Set(data?.cluster_map.map((r) => String(r.league)) || []),
  ]
  const filtered = (name: string) => data?.[name]?.filter(matches) || []
  return (
    <>
      <div className="analysis-notice">
        Association, not cause. Team strength and match load account for much of
        the initial difference. Transfermarkt under-reports injuries.
      </div>
      {source.error && (
        <p className="analysis-alert" role="alert">
          {source.error}
        </p>
      )}
      {!data && !source.error && (
        <p role="status">Loading the Phase 6 results export…</p>
      )}
      {data && (
        <>
          <div className="analysis-panel">
            <div className="analysis-toolbar">
              <div className="analysis-actions">
                {['Styles', 'Evolution', 'Injuries', 'Trends', 'Leagues'].map(
                  (t) => (
                    <button
                      key={t}
                      className="btn btn-outline"
                      aria-pressed={tab === t}
                      onClick={() => setTab(t)}
                    >
                      {t}
                    </button>
                  ),
                )}
              </div>
              <a
                className="btn btn-outline btn-sm"
                href="/api/analysis/reports/summary.md"
                target="_blank"
                rel="noreferrer"
              >
                Course report ↗
              </a>
            </div>
            <div className="analysis-toolbar">
              <label>
                Phase of play{' '}
                <select
                  value={phase}
                  onChange={(e) => {
                    setPhase(e.target.value)
                    setStyle('')
                  }}
                >
                  <option value="attack">Attacking</option>
                  <option value="defence">Defensive</option>
                </select>
              </label>
              {['Styles', 'Evolution', 'Leagues'].includes(tab) && (
                <label>
                  League{' '}
                  <select
                    value={league}
                    onChange={(e) => setLeague(e.target.value)}
                  >
                    {leagues.map((l) => (
                      <option key={l}>{l}</option>
                    ))}
                  </select>
                </label>
              )}
              <label>
                Style{' '}
                <select
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                >
                  <option value="">All styles</option>
                  {styles.map((s) => (
                    <option key={String(s.style)}>{String(s.style)}</option>
                  ))}
                </select>
              </label>
              {style && (
                <button className="text-link" onClick={() => setStyle('')}>
                  Clear style ×
                </button>
              )}
            </div>
            <p className="analysis-muted">
              {tab === 'Styles'
                ? 'League filters the map; style profiles summarise all leagues.'
                : tab === 'Injuries' || tab === 'Trends'
                  ? 'Comparisons summarise all leagues.'
                  : tab === 'Leagues'
                    ? 'League stories summarise both phases.'
                    : 'Dimensions summarise the selected league and phase.'}
            </p>
          </div>
          {tab === 'Styles' && (
            <>
              <section className="analysis-panel">
                <h2>The style map</h2>
                <p className="analysis-muted">
                  Each dot is a team-season. Hover for club and membership;
                  click to select its style. Axes show a 2D PCA projection.
                </p>
                <svg
                  className="cluster-chart"
                  viewBox="0 0 900 400"
                  role="group"
                  aria-label="Team-seasons by playing style"
                >
                  <path d="M450 20V380M20 200H880" stroke="var(--line)" />
                  {data.cluster_map
                    .filter(
                      (r) =>
                        r.phase === phase &&
                        (league === 'All leagues' || r.league === league),
                    )
                    .map((r, i) => (
                      <circle
                        key={i}
                        cx={450 + Number(r.pc1) * 50}
                        cy={200 - Number(r.pc2) * 42}
                        r={style === r.style ? 5 : 3.5}
                        fill={color(r.style)}
                        opacity={
                          style && r.style !== style
                            ? 0.1
                            : Math.max(0.25, Number(r.membership))
                        }
                        tabIndex={0}
                        role="button"
                        aria-label={`${r.club} ${r.season}: ${r.style}, membership ${r.membership}`}
                        onClick={() => selectStyle(String(r.style))}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault()
                            selectStyle(String(r.style))
                          }
                        }}
                      >
                        <title>{`${r.club} · ${r.season}\n${r.style}: ${r.membership}\nNext: ${r.second_style} ${r.second_membership}`}</title>
                      </circle>
                    ))}
                </svg>
                <div className="chart-legend">
                  {styles.map((s) => (
                    <button
                      key={String(s.style)}
                      onClick={() => selectStyle(String(s.style))}
                    >
                      <i style={{ background: color(s.style) }} />
                      {String(s.style)}
                    </button>
                  ))}
                </div>
              </section>
              <div className="style-cards">
                {styles
                  .filter((s) => !style || s.style === style)
                  .map((s) => (
                    <article
                      key={String(s.style)}
                      className="analysis-panel style-card"
                      style={{ borderTopColor: color(s.style) }}
                    >
                      <div className="analysis-kicker">
                        {String(s.team_seasons)} TEAM-SEASONS · {String(s.core)}{' '}
                        CLEAR MEMBERS
                      </div>
                      <h2>
                        <button
                          className="text-link"
                          onClick={() => selectStyle(String(s.style))}
                        >
                          {String(s.style)}
                        </button>
                      </h2>
                      <p>{String(s.how)}</p>
                      <p className="analysis-muted">{String(s.numbers)}</p>
                      <dl>
                        <dt>Common partner</dt>
                        <dd>{String(s.paired_with)}</dd>
                        <dt>Typical teams · 2022–26</dt>
                        <dd>{String(s.typical_2022_26)}</dd>
                      </dl>
                    </article>
                  ))}
              </div>
            </>
          )}
          {tab === 'Evolution' && (
            <>
              <section className="analysis-panel">
                <h2>How the style mix changed</h2>
                <LineChart
                  rows={filtered('style_shares')}
                  series="style"
                  value="share"
                  color={color}
                  percent
                />
                <details>
                  <summary>View data</summary>
                  <Rows rows={filtered('style_shares')} />
                </details>
              </section>
              <section className="analysis-panel">
                <h2>Style dimensions over time</h2>
                <LineChart
                  rows={data.dimension_trends.filter(
                    (r) => r.phase === phase && r.league === league,
                  )}
                  series="dimension"
                  value="value"
                />
                <p className="analysis-muted">
                  Globally standardised dimensions; zero is the full-sample
                  average.
                </p>
              </section>
            </>
          )}
          {tab === 'Injuries' && (
            <>
              <section className="analysis-panel">
                <h2>Style or schedule? Follow the adjustments</h2>
                <div className="analysis-toolbar">
                  <label>
                    Exposure{' '}
                    <select
                      value={exposure}
                      onChange={(e) => {
                        setExposure(e.target.value)
                        setAdjustment('league × season')
                      }}
                    >
                      {[
                        ...new Set(
                          data.rr_ladder.map((r) => String(r.exposure)),
                        ),
                      ].map((v) => (
                        <option key={v}>{v}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Adjustment{' '}
                    <select
                      value={adjustment}
                      onChange={(e) => setAdjustment(e.target.value)}
                    >
                      {[
                        ...new Set(
                          data.rr_ladder
                            .filter((r) => r.exposure === exposure)
                            .map((r) => String(r.adjustment)),
                        ),
                      ].map((v) => (
                        <option key={v}>{v}</option>
                      ))}
                    </select>
                  </label>
                </div>
                <div>
                  {filtered('rr_ladder')
                    .filter(
                      (r) =>
                        r.adjustment === adjustment && r.exposure === exposure,
                    )
                    .map((r) => (
                      <div key={String(r.style)} className="rr-row">
                        <button
                          className="text-link"
                          onClick={() => selectStyle(String(r.style))}
                        >
                          {String(r.style)}
                        </button>
                        <svg
                          viewBox="0 0 250 36"
                          role="img"
                          aria-label={`Rate ratio ${r.rr}, 95% confidence interval ${r.rr_low} to ${r.rr_high}`}
                        >
                          <path
                            d="M125 0V36"
                            stroke="var(--muted)"
                            strokeDasharray="3 3"
                          />
                          <path
                            d={`M${Number(r.rr_low) * 125} 18H${Number(r.rr_high) * 125}`}
                            stroke={color(r.style)}
                            strokeWidth="3"
                          />
                          <circle
                            cx={Number(r.rr) * 125}
                            cy="18"
                            r="5"
                            fill={color(r.style)}
                          />
                        </svg>
                        <span>
                          <b>{Number(r.rr).toFixed(2)}</b> ({r.rr_low}–
                          {r.rr_high})
                        </span>
                      </div>
                    ))}
                </div>
                <p className="analysis-muted">
                  Reference line = expected rate (RR 1). Whiskers: 95%
                  confidence intervals from club bootstrap samples.
                </p>
                <details>
                  <summary>Data and absolute excess</summary>
                  <Rows
                    rows={filtered('rr_ladder').filter(
                      (r) =>
                        r.adjustment === adjustment && r.exposure === exposure,
                    )}
                  />
                </details>
              </section>
              <section className="analysis-panel">
                <h2>Attacking × defensive styles</h2>
                <Rows
                  rows={data.grid.filter(
                    (r) => !style || r.attack === style || r.defence === style,
                  )}
                />
                <p className="analysis-muted">
                  Shrunk rate ratios reduce noise in smaller groups.
                </p>
              </section>
              <section className="analysis-panel">
                <h2>Where players get hurt</h2>
                <p className="analysis-muted">
                  “finding” marks results surviving permutation testing and
                  correction for multiple comparisons.
                </p>
                <Rows rows={filtered('body_areas')} />
              </section>
              <section className="analysis-panel">
                <h2>By age and position</h2>
                <Rows rows={filtered('breakdown')} />
              </section>
            </>
          )}
          {tab === 'Trends' && (
            <>
              <section className="analysis-panel">
                <h2>Injuries across seasons</h2>
                <p className="analysis-muted">
                  All styles and leagues · injuries per player-season, with a
                  three-season rolling line.
                </p>
                <LineChart
                  rows={data.season_trend.flatMap((r) => [
                    { ...r, series: 'Single season', rate: r.injuries_per_ps },
                    {
                      ...r,
                      series: '3-season rolling',
                      rate: r.injuries_rolling,
                    },
                  ])}
                  series="series"
                  value="rate"
                />
                <Rows rows={data.season_trend} />
                <p className="analysis-muted">
                  Calendar context: COVID restart and five substitutes (2020),
                  mid-season World Cup (2022), new Champions League format
                  (2024/25).
                </p>
              </section>
              <section className="analysis-panel">
                <h2>What changed between eras?</h2>
                <p>
                  Decomposition separates strength mix, style mix and change
                  within styles; it does not establish causation.
                </p>
                <Rows rows={data.decomposition} />
              </section>
            </>
          )}
          {tab === 'Leagues' && (
            <>
              {data.league_stories
                .filter((r) => league === 'All leagues' || r.league === league)
                .map((r) => (
                  <article className="analysis-panel" key={String(r.league)}>
                    <div className="analysis-kicker">LEAGUE STORY</div>
                    <h2>{String(r.league)}</h2>
                    <p>{String(r.story)}</p>
                    <Rows
                      rows={data.decomposition.filter(
                        (d) => d.scope === r.league,
                      )}
                    />
                  </article>
                ))}
            </>
          )}
          <p className="analysis-muted">
            Source: Phase 6 export ·{' '}
            <a href="/analysis/studio/phase-06/step-1">
              Inspect report checks →
            </a>
          </p>
        </>
      )}
    </>
  )
}
function LineChart({
  rows,
  series,
  value,
  color,
  percent,
}: {
  rows: Row[]
  series: string
  value: string
  color?: (name: unknown) => string
  percent?: boolean
}) {
  const seasons = [...new Set(rows.map((r) => String(r.season)))].sort()
  const groups = [...new Set(rows.map((r) => String(r[series])))]
  if (!rows.length) return <p>No matching data.</p>
  const values = rows.map((r) => Number(r[value]))
  const min = Math.min(0, ...values),
    max = Math.max(...values, 0.01)
  const x = (s: string) =>
    55 + (seasons.indexOf(s) / Math.max(1, seasons.length - 1)) * 780
  const y = (v: number) => 250 - ((v - min) / (max - min)) * 210
  const c = (g: string, i: number) => color?.(g) || palette[i % palette.length]
  return (
    <>
      <svg
        className="line-chart"
        viewBox="0 0 900 300"
        role="img"
        aria-label={`${value.replaceAll('_', ' ')} by season`}
      >
        <path d="M55 25V250H850" stroke="var(--muted)" fill="none" />
        <text x="5" y="40">
          {percent ? `${Math.round(max * 100)}%` : max.toFixed(2)}
        </text>
        <text x="5" y="250">
          {min.toFixed(2)}
        </text>
        {groups.map((g, i) => (
          <g key={g}>
            <polyline
              fill="none"
              stroke={c(g, i)}
              strokeWidth="2.5"
              points={rows
                .filter((r) => r[series] === g)
                .sort((a, b) =>
                  String(a.season).localeCompare(String(b.season)),
                )
                .map((r) => `${x(String(r.season))},${y(Number(r[value]))}`)
                .join(' ')}
            />
            {rows
              .filter((r) => r[series] === g)
              .map((r) => (
                <circle
                  key={String(r.season)}
                  cx={x(String(r.season))}
                  cy={y(Number(r[value]))}
                  r="4"
                  fill={c(g, i)}
                >
                  <title>{`${g} · ${r.season}: ${percent ? `${(Number(r[value]) * 100).toFixed(1)}%` : r[value]}`}</title>
                </circle>
              ))}
          </g>
        ))}
        {seasons
          .filter((_, i) => i % 2 === 0 || i === seasons.length - 1)
          .map((s) => (
            <text key={s} x={x(s)} y="280" textAnchor="middle">
              {s}
            </text>
          ))}
      </svg>
      <div className="chart-legend">
        {groups.map((g, i) => (
          <span key={g}>
            <i style={{ background: c(g, i) }} />
            {g}
          </span>
        ))}
      </div>
    </>
  )
}
