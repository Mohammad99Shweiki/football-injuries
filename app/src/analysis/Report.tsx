import { useEffect, useState } from 'react'
import { request, useResource } from './api'
import { Markdown } from './Markdown'

interface Finalise {
  items: { item: string; ok: boolean; detail: string }[]
  ready: boolean
  releases: string[]
}
const REPORTS = [
  ['summary.md', 'Course report (summary)'],
  ['00_data_audit.md', '00 Data audit'],
  ['01_entities.md', '01 Entity resolution'],
  ['02_injuries.md', '02 Injury cleaning'],
  ['03_features.md', '03 Features'],
  ['04_clustering.md', '04 Clustering'],
  ['05_injury_analysis.md', '05 Injury analysis'],
]

function useText(path: string) {
  const [state, setState] = useState<{ path: string; text?: string; error?: string }>({ path })
  useEffect(() => {
    let active = true
    fetch(`/api/analysis/${path}`, { cache: 'no-store' })
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error(`Could not load ${path} (${r.status})`))))
      .then((text) => active && setState({ path, text }), (e: Error) => active && setState({ path, error: e.message }))
    return () => { active = false }
  }, [path])
  return state.path === path ? state : { path }
}

/** Phase 7: the checklist before freezing a version, the reports, and every figure. */
export function Report({ file }: { file: string }) {
  const name = REPORTS.some(([f]) => f === file) ? file : 'summary.md'
  const status = useResource<Finalise>('finalise', 5000)
  const report = useText(`reports/${name}`)
  const figures = useResource<{ name: string; phase: string }[]>('figures')
  const [note, setNote] = useState('')
  const [message, setMessage] = useState('')
  const [pending, setPending] = useState(false)
  async function finalise() {
    setPending(true)
    setMessage('')
    try {
      const r = await request<{ release: string; path: string }>('finalise', { note })
      setMessage(`Release ${r.release} written to ${r.path}.`)
    } catch (e) {
      setMessage((e as Error).message)
    } finally {
      setPending(false)
    }
  }
  return (
    <>
      <section className="analysis-panel">
        <div className="analysis-toolbar">
          <div>
            <h2>Ready to finalise?</h2>
            <p className="analysis-muted">Finalising freezes this version: a manifest with every phase's run id and input hashes, the approvals, the git commit and the seed, in <code>reports/releases/</code>. It changes no result.</p>
          </div>
          <span className={`analysis-badge ${status.data?.ready ? 'passed' : 'review'}`}>{status.data?.ready ? 'ready' : 'not ready'}</span>
        </div>
        {status.error && <p role="alert">{status.error}</p>}
        {status.data?.items.map((i) => (
          <div className="check-row" key={i.item}>
            <span className={`analysis-badge ${i.ok ? 'passed' : 'failed'}`}>{i.ok ? 'done' : 'to do'}</span>
            <span>{i.item}</span>
            <small>{i.detail}</small>
          </div>
        ))}
        <div className="analysis-actions finalise-bar">
          <label>Note{' '}<input value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. version handed in" /></label>
          <button className="btn btn-primary" disabled={!status.data?.ready || pending} onClick={finalise}>Finalise this version</button>
          {!status.data?.ready && <a href="/analysis/reviews">Open reviews →</a>}
        </div>
        {message && <p role="status">{message}</p>}
        {!!status.data?.releases.length && <p className="analysis-muted">Earlier releases: {status.data.releases.join(', ')}</p>}
      </section>
      <section className="analysis-panel report-reader">
        <nav className="phase-picker" aria-label="Reports">
          {REPORTS.map(([f, label]) => (
            <a key={f} href={`/analysis/report/${f}`} aria-current={f === name ? 'page' : undefined}>{label}</a>
          ))}
        </nav>
        {report.error && <p role="alert">{report.error}</p>}
        {!report.text && !report.error && <p role="status">Loading {name}…</p>}
        {report.text && <Markdown text={report.text} className="report-text" />}
      </section>
      <section className="analysis-panel">
        <h2>All figures</h2>
        <div className="figure-grid">
          {figures.data?.map((f) => (
            <a key={f.name} href={`/api/analysis/figures/${f.name}`} target="_blank" rel="noreferrer">
              <img className="analysis-figure" src={`/api/analysis/figures/${f.name}`} alt={f.name.replace('.png', '').replaceAll('_', ' ')} loading="lazy" />
              <span>{f.name}</span>
            </a>
          ))}
        </div>
      </section>
    </>
  )
}
