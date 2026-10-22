import { useEffect, useState } from 'react'
import { Board } from '../components/Board'
import { CreditsFooter } from '../components/CreditsFooter'
import { REPORT_SCATTER } from '../data/scatter'
import { request, useResource } from './api'
import type { Job, Mapping, Phase, Row, Step } from './api'
import { DataTable, Rows } from './DataTable'
import { Results } from './Results'

export function Badge({ status }: { status: string }) {
  return (
    <span className={`analysis-badge ${status}`}>
      {status.replaceAll('_', ' ')}
    </span>
  )
}
export function AnalysisPage({ path }: { path: string }) {
  const view = path.split('/')[2] || 'progress'
  const phases = useResource<Phase[]>('phases', 4000)
  const job = useResource<Job>('run', 2000)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => {
    document.title = `${view[0].toUpperCase() + view.slice(1)} · The football study`
  }, [view])
  async function run(phase: string, until?: number) {
    setPending(true)
    setError('')
    try {
      await request('run', { phase, until })
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setPending(false)
    }
  }
  const busy =
    pending || !!job.data?.running || !!job.data?.scrape_busy || !job.data
  return (
    <Board scatter={REPORT_SCATTER}>
      <nav className="workspace-tabs" aria-label="Analysis pages">
        {['progress', 'studio', 'results', 'reviews', 'logs'].map((v) => (
          <a
            key={v}
            href={`/analysis/${v === 'progress' ? '' : v}`}
            aria-current={view === v ? 'page' : undefined}
          >
            {v[0].toUpperCase() + v.slice(1)}
          </a>
        ))}
      </nav>
      <div className="analysis-shell">
        <header className="analysis-heading">
          <div>
            <div className="analysis-kicker">
              STEP 02 · FROM TABLES TO FINDINGS
            </div>
            <h1>
              {(
                {
                  progress: 'The study, at a glance',
                  studio: 'Analysis Studio',
                  results: 'Style or schedule?',
                  reviews: 'Review the evidence',
                  logs: 'The research notebook',
                } as Record<string, string>
              )[view] || 'Analysis'}
            </h1>
            <p>
              Playing style × injuries · Europe’s Big Five · 2014/15–2025/26
            </p>
          </div>
          <a className="btn btn-outline" href="/scraping/validation">
            ← Scraping report
          </a>
        </header>
        {(error || phases.error || job.error) && (
          <div className="analysis-alert" role="alert">
            {error || phases.error || job.error}
          </div>
        )}
        {job.data?.running && (
          <div className="analysis-notice" role="status">
            Analysis is running
            {job.data.current_phase ? ` · phase ${job.data.current_phase}` : ''}
            . Results refresh as steps finish.
          </div>
        )}
        {job.data?.scrape_busy && (
          <div className="analysis-notice" role="status">
            Scraping is active. Analysis run controls become available when it
            finishes.
          </div>
        )}
        {job.data && (job.data.running || job.data.returncode != null) && (
          <details className="analysis-panel">
            <summary>
              Run console{' '}
              {job.data.returncode != null
                ? `· exit ${job.data.returncode}`
                : ''}
            </summary>
            <pre>{job.data.output.join('\n') || 'Starting…'}</pre>
          </details>
        )}
        {view === 'progress' &&
          (phases.data ? (
            <Progress phases={phases.data} busy={busy} run={run} />
          ) : (
            !phases.error && <p role="status">Reading phase records…</p>
          ))}
        {view === 'studio' && phases.data && (
          <Studio path={path} phases={phases.data} busy={busy} run={run} />
        )}
        {view === 'results' && <Results />}
        {view === 'reviews' && <Reviews />}
        {view === 'logs' && <Logs />}
        {!['progress', 'studio', 'results', 'reviews', 'logs'].includes(
          view,
        ) && (
          <p>
            Page not found. <a href="/analysis">Open project progress.</a>
          </p>
        )}
        <CreditsFooter />
      </div>
    </Board>
  )
}
function Progress({
  phases,
  busy,
  run,
}: {
  phases: Phase[]
  busy: boolean
  run: (phase: string) => Promise<void>
}) {
  const styles = useResource<Row[]>('results/styles')
  const ladder = useResource<Row[]>('results/rr_ladder')
  const rr = useResource<Row[]>('results/injury_rr')
  const teamSeasons = styles.data
    ?.filter((s) => s.phase === 'attack')
    .reduce((n, s) => n + Number(s.team_seasons), 0)
  const players = rr.data
    ?.filter((s) => s.grouping === 'attack')
    .reduce((n, s) => n + Number(s.player_seasons), 0)
  const stale = phases.filter((p) => p.stale)
  return (
    <>
      <section className="analysis-hero analysis-panel">
        <div>
          <div className="analysis-kicker">THE RESEARCH QUESTION</div>
          <h2>
            Does the way a team plays relate to how its players get injured?
          </h2>
          <p>
            Cluster clubs by how they attack and defend. Compare injury
            frequency, severity and body areas across styles, seasons and
            leagues.
          </p>
          <a className="text-link" href="/analysis/results">
            Explore the findings ↗
          </a>
        </div>
        <div className="study-stamp">
          <strong>
            {phases.filter((p) => p.status === 'passed' && !p.stale).length}
            <span>/ {phases.length}</span>
          </strong>
          <span>phases up to date</span>
        </div>
      </section>
      <div className="analysis-kpis">
        <div>
          <strong>{teamSeasons?.toLocaleString() ?? '—'}</strong>
          <span>team-seasons</span>
        </div>
        <div>
          <strong>{players?.toLocaleString() ?? '—'}</strong>
          <span>player-club-seasons</span>
        </div>
        <div>
          <strong>
            {styles.data
              ? `${styles.data.filter((s) => s.phase === 'attack').length} × ${styles.data.filter((s) => s.phase === 'defence').length}`
              : '—'}
          </strong>
          <span>attacking × defensive styles</span>
        </div>
      </div>
      <section className="analysis-panel">
        <div className="analysis-toolbar">
          <div>
            <h2>The analysis pipeline</h2>
            <p className="analysis-muted">
              Run all reruns stale phases in order and stops on failure.
            </p>
          </div>
          <button
            className="btn btn-primary"
            disabled={busy}
            onClick={() => run('all')}
          >
            {busy ? 'Run in progress…' : 'Run all stale phases →'}
          </button>
        </div>
        {stale.length > 0 && (
          <div className="analysis-notice">
            {stale.length} phases need attention:{' '}
            {stale
              .map((p) => `${p.id}: ${p.stale_reasons.join(', ')}`)
              .join(' · ')}
          </div>
        )}
        <div className="phase-grid">
          {phases.map((p) => (
            <a
              className="phase-card"
              key={p.id}
              href={`/analysis/studio/phase-${p.id}/step-${p.steps[0]?.index ?? 0}`}
            >
              <div className="analysis-toolbar">
                <span className="phase-number">{p.id}</span>
                <Badge status={p.stale ? 'stale' : p.status} />
              </div>
              <h3>{p.title}</h3>
              <p>
                {p.steps.filter((s) => s.status === 'passed').length} /{' '}
                {p.steps.length} steps passed
              </p>
              <div className="phase-track">
                <i
                  style={{
                    width: `${(100 * p.steps.filter((s) => s.status === 'passed').length) / Math.max(1, p.steps.length)}%`,
                  }}
                />
              </div>
              <small>
                {p.finished
                  ? `Last run ${new Date(p.finished).toLocaleString()}`
                  : 'Ready for its first run'}
              </small>
            </a>
          ))}
        </div>
      </section>
      <section className="analysis-panel">
        <div className="analysis-toolbar">
          <h2>Possession: follow the adjustments</h2>
          <a href="/analysis/results">Open results →</a>
        </div>
        <p>
          Most of the initial excess shrinks after team strength and match load
          are taken into account.
        </p>
        {ladder.data && (
          <Rows
            rows={ladder.data.filter(
              (r) => r.style === 'Positional possession',
            )}
          />
        )}
        <p className="analysis-muted">
          Association, not cause. Transfermarkt under-reports injuries, with
          uneven coverage across leagues and seasons.
        </p>
      </section>
    </>
  )
}
function Studio({
  path,
  phases,
  busy,
  run,
}: {
  path: string
  phases: Phase[]
  busy: boolean
  run: (p: string, until?: number) => Promise<void>
}) {
  const id = path.match(/phase-(\d+)/)?.[1]?.padStart(2, '0') || '00'
  const phase = phases.find((p) => p.id === id)
  const index = Number(
    path.match(/step-(\d+)/)?.[1] ?? phase?.steps[0]?.index ?? 0,
  )
  const step = useResource<Step>(`phases/${id}/steps/${index}`, 4000)
  const [table, setTable] = useState('')
  if (!phase) return <p>Phase not found.</p>
  const position = phase.steps.findIndex((s) => s.index === index)
  const url = (n: number) => `/analysis/studio/phase-${id}/step-${n}`
  return (
    <>
      <div className="phase-picker">
        {phases.map((p) => (
          <a
            key={p.id}
            href={`/analysis/studio/phase-${p.id}/step-${p.steps[0]?.index ?? 0}`}
            aria-current={p.id === id ? 'page' : undefined}
          >
            {p.id} {p.title}
          </a>
        ))}
      </div>
      <div className="studio-layout">
        <aside className="analysis-panel step-sidebar" aria-label="Phase steps">
          <div className="analysis-kicker">PHASE {id}</div>
          <h2>{phase.title}</h2>
          {phase.steps.map((s) => (
            <a
              key={s.index}
              href={url(s.index)}
              aria-current={s.index === index ? 'step' : undefined}
            >
              <span>{s.index}</span>
              <div>
                {s.title}
                <small>
                  {s.status.replaceAll('_', ' ')} · {s.checks} checks
                </small>
              </div>
            </a>
          ))}
        </aside>
        <section
          className="analysis-panel step-inspector"
          key={`${id}-${index}`}
        >
          <div className="analysis-toolbar">
            <div>
              <div className="analysis-kicker">
                STEP {id}.{index}
              </div>
              <h2>{step.data?.title || 'Loading step…'}</h2>
            </div>
            <Badge
              status={phase.stale ? 'stale' : step.data?.status || 'not_run'}
            />
          </div>
          {phase.stale && (
            <p className="analysis-notice">
              Inputs changed: {phase.stale_reasons.join('; ')}
            </p>
          )}
          <div className="analysis-actions">
            <button
              className="btn btn-primary"
              disabled={busy}
              onClick={() => run(id)}
            >
              Run phase
            </button>
            <button
              className="btn btn-outline"
              disabled={busy}
              onClick={() => run(id, index)}
            >
              Run through this step
            </button>
          </div>
          <p className="analysis-muted">
            Steps share state, so running through a step executes its
            prerequisites in this phase.
          </p>
          {step.error && <p role="alert">{step.error}</p>}
          {step.data && (
            <>
              <p className="step-note-text">{step.data.note}</p>
              {!step.data.run && (
                <p className="analysis-notice">
                  This step has not run yet. Run the phase to see its outputs.
                </p>
              )}
              {step.data.run && (
                <>
                  <h3>
                    Checks <small>· {step.data.run.duration_s}s</small>
                  </h3>
                  {!step.data.run.checks.length && (
                    <p className="analysis-muted">
                      No assertions recorded for this step.
                    </p>
                  )}
                  {step.data.run.checks.map((c, i) => (
                    <div className="check-row" key={i}>
                      <Badge status={c.failed ? 'failed' : 'passed'} />
                      <code>{c.statement}</code>
                      <small>
                        {c.passed} passed · {c.failed} failed
                      </small>
                    </div>
                  ))}
                  {!!step.data.run.log.length && (
                    <>
                      <h3>What changed</h3>
                      <Rows rows={step.data.run.log} />
                    </>
                  )}
                  {!!step.data.run.outputs.length && (
                    <>
                      <h3>Outputs</h3>
                      {step.data.run.outputs.map((o) => (
                        <div key={o.path} className="output-item">
                          {o.kind === 'table' ? (
                            <button
                              className="text-link"
                              onClick={() => setTable(o.path)}
                            >
                              {o.path} · {o.rows?.toLocaleString()} rows ↗
                            </button>
                          ) : o.kind === 'figure' ? (
                            <a
                              href={`/api/analysis/figures/${o.path.split('/').pop()}`}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <img
                                className="analysis-figure"
                                src={`/api/analysis/figures/${o.path.split('/').pop()}`}
                                alt={o.path
                                  .split('/')
                                  .pop()
                                  ?.replaceAll('_', ' ')}
                                loading="lazy"
                              />
                            </a>
                          ) : (
                            <span>{o.path}</span>
                          )}
                        </div>
                      ))}
                    </>
                  )}
                  {table && (
                    <details open key={table}>
                      <summary>{table}</summary>
                      <DataTable key={table} path={table} />
                    </details>
                  )}
                  {step.data.run.previews
                    .filter((p) => p.kind === 'table' && p.rows && p.columns)
                    .map((p, i) => (
                      <details key={i}>
                        <summary>Table preview {i + 1}</summary>
                        <Rows
                          rows={p.rows!.map((r, n) =>
                            Object.fromEntries([
                              ...(p.index ? [['row', String(p.index[n])]] : []),
                              ...p.columns!.map((c, j) => [
                                c,
                                r[j] as string | number | null,
                              ]),
                            ]),
                          )}
                        />
                      </details>
                    ))}
                  {step.data.run.error && (
                    <details open>
                      <summary>Step failed</summary>
                      <pre>{step.data.run.error.traceback}</pre>
                    </details>
                  )}
                  {step.data.run.stdout && (
                    <details>
                      <summary>Execution log</summary>
                      <pre>{step.data.run.stdout}</pre>
                    </details>
                  )}
                </>
              )}
              <details>
                <summary>Source code</summary>
                <pre>{step.data.code.join('\n\n')}</pre>
              </details>
            </>
          )}
          <div className="analysis-toolbar step-pagination">
            {position > 0 ? (
              <a
                className="btn btn-outline"
                href={url(phase.steps[position - 1].index)}
              >
                ← Previous step
              </a>
            ) : (
              <span />
            )}
            {position >= 0 && position < phase.steps.length - 1 && (
              <a
                className="btn btn-outline"
                href={url(phase.steps[position + 1].index)}
              >
                Next step →
              </a>
            )}
          </div>
        </section>
      </div>
    </>
  )
}
function Reviews() {
  const mappings = useResource<Mapping[]>('mappings', 3000)
  const [selected, setSelected] = useState('')
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  async function approve(m: Mapping) {
    setPending(true)
    setError('')
    try {
      await request(`mappings/${encodeURIComponent(m.file)}/approve`, {
        hash: m.hash,
        note: 'Reviewed in the unified analysis app.',
      })
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setPending(false)
    }
  }
  return (
    <section className="analysis-panel">
      <h2>Hand-reviewed inputs</h2>
      <p>
        Inspect the team and injury label mappings before approving the current
        file version. Approval records your review; it does not change the
        analysis results.
      </p>
      {(error || mappings.error) && (
        <p role="alert">{error || mappings.error}</p>
      )}
      {!mappings.data && !mappings.error && (
        <p role="status">Loading review points…</p>
      )}
      {mappings.data?.map((m) => (
        <div className="mapping-row" key={m.file}>
          <div>
            <button className="text-link" onClick={() => setSelected(m.path)}>
              {m.file} ↗
            </button>
            <small>
              {m.rows} rows · version {m.hash}
              {m.approval ? ` · last approved ${m.approval.date}` : ''}
            </small>
          </div>
          <Badge status={m.approved_current ? 'passed' : 'review'} />
          <button
            className="btn btn-outline review-action"
            disabled={pending || m.approved_current || selected !== m.path}
            onClick={() => approve(m)}
          >
            Approve current version
          </button>
        </div>
      ))}
      {selected && <DataTable key={selected} path={selected} />}
      <p className="analysis-muted">
        Mapping edits are made in the tracked CSV files; rerun affected phases
        after changing them. Review approvals are read-only on small screens.
      </p>
    </section>
  )
}
function Logs() {
  const [kind, setKind] = useState('decisions')
  const [query, setQuery] = useState('')
  const { data, error } = useResource<Row[]>(`logs/${kind}`)
  return (
    <section className="analysis-panel">
      <div className="analysis-toolbar">
        <div className="analysis-actions">
          {['decisions', 'preprocessing'].map((k) => (
            <button
              key={k}
              className="btn btn-outline"
              aria-pressed={kind === k}
              onClick={() => setKind(k)}
            >
              {k === 'decisions' ? 'Decisions' : 'Preprocessing'}
            </button>
          ))}
        </div>
        <label>
          Search log{' '}
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Find a decision or operation…"
          />
        </label>
      </div>
      {error && <p role="alert">{error}</p>}
      {data ? (
        <Rows
          rows={data.filter((r) =>
            Object.values(r)
              .join(' ')
              .toLowerCase()
              .includes(query.toLowerCase()),
          )}
        />
      ) : (
        !error && <p role="status">Loading research log…</p>
      )}
    </section>
  )
}
