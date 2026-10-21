import { useState } from 'react'
import type { LogRow, SourceKey } from '../api/types'
import { Eyebrow } from '../components/Eyebrow'
import { SourceTile } from '../components/Sticker'
import { Tabs } from '../components/Tabs'
import { SITES } from '../data/leagues'
import { clock, fmt, shortUrl } from '../lib/format'

type Filter = 'all' | SourceKey
const TABS: [Filter, string][] = [['all', 'All'], ['fd', 'FD'], ['us', 'US'], ['tm', 'TM']]
const PAGE = 8

/** 06 Match log: newest manifest rows first, filterable by source. */
export function MatchLog({ rows }: { rows: LogRow[] }) {
  const [filter, setFilter] = useState<Filter>('all')
  const [expanded, setExpanded] = useState(false)
  const filtered = rows.filter((r) => filter === 'all' || r.source === filter)
  const shown = expanded ? filtered : filtered.slice(0, PAGE)
  return (
    <section aria-label="Manifest" className="log-panel panel-base">
      <div className="head-row">
        <div className="section-head">
          <Eyebrow number="06" label="Match log" icon="list" />
          <h2>manifest.csv — latest requests</h2>
        </div>
        <Tabs label="Filter log by source" items={TABS} value={filter} onChange={setFilter} small />
      </div>
      <div className="table-well">
        <table className="data-table log-table">
          <thead>
            <tr>
              <th>fetched_at</th>
              <th>Source</th>
              <th>url</th>
              <th>status</th>
              <th style={{ textAlign: 'right' }}>bytes</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((r, i) => (
              <tr key={`${r.fetched_at_elapsed_s}-${r.url}-${i}`}>
                <td>{clock(r.fetched_at_elapsed_s)}</td>
                <td className="log-src"><span><SourceTile source={r.source} />{SITES[r.source].short}</span></td>
                <td className="log-url" title={r.url}>{shortUrl(r.url)}</td>
                <td className="log-code" style={{ color: r.status === 200 ? 'var(--ok-text)' : 'var(--warn-text)' }}>{r.status ?? '—'}</td>
                <td style={{ textAlign: 'right' }}>{fmt(r.bytes)}</td>
                <td>{r.result}</td>
              </tr>
            ))}
            {shown.length === 0 && (
              <tr><td colSpan={6} style={{ padding: '14px 0', fontFamily: 'var(--font-ui)' }}>No requests yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
      {filtered.length > PAGE && (
        <button type="button" className="btn btn-outline btn-sm log-more" onClick={() => setExpanded((e) => !e)}>
          {expanded ? 'Show fewer' : `Show more (${filtered.length - PAGE})`}
        </button>
      )}
    </section>
  )
}
