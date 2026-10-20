import type { Failure } from '../api/types'
import { Eyebrow } from '../components/Eyebrow'
import { RetryIcon } from '../components/Icons'
import { SourceTile } from '../components/Sticker'
import { SITES } from '../data/leagues'
import { shortUrl } from '../lib/format'

interface Props {
  failures: Failure[]
  requeued: Set<string>
  onRequeue: (id: string) => void
}

/** 02 Fouls & stoppages: failed and suspicious responses, each with Re-queue. */
export function Fouls({ failures, requeued, onRequeue }: Props) {
  return (
    <section aria-label="Failed and suspicious responses" className="fouls panel panel-base">
      <div className="section-head">
        <Eyebrow number="02" label="Fouls & stoppages" icon="warning" />
        <h2>Failed and suspicious responses</h2>
        <div className="section-sub">Failed after 5 attempts, or small, empty or WAF-challenge bodies. Re-queue deletes the stored file and puts the request back in the queue.</div>
      </div>
      <div className="table-well">
        <table className="data-table fouls-table">
          <thead>
            <tr>
              <th>Source</th>
              <th>url</th>
              <th>Problem</th>
              <th>Attempts</th>
              <th><span className="sr-only">Action</span></th>
            </tr>
          </thead>
          <tbody>
            {failures.map((f) => (
              <tr key={f.id}>
                <td><SourceTile source={f.source} width={44} /><span className="sr-only">{SITES[f.source].short}</span></td>
                <td className="mono log-url" title={f.url}>{shortUrl(f.url)}</td>
                <td><span className="fouls-code">{f.code ?? '—'}</span> <span className="muted">{f.why}</span></td>
                <td className="mono">{f.attempts}</td>
                <td>
                  {requeued.has(f.id) ? (
                    <span className="pill run" style={{ padding: '4px 10px' }}>Re-queued</span>
                  ) : (
                    <button type="button" className="btn btn-outline btn-sm" onClick={() => onRequeue(f.id)}>
                      <RetryIcon size={14} />Re-queue
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {failures.length === 0 && (
              <tr className="fouls-empty"><td colSpan={5}>Clean sheet: no failed or suspicious responses.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
