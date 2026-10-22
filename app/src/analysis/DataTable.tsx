import { useState } from 'react'
import { useResource } from './api'
import type { Row, Table } from './api'

export function Rows({ rows }: { rows: Row[] }) {
  if (!rows.length)
    return <p className="analysis-muted">No matching records.</p>
  const columns = [...new Set(rows.flatMap(Object.keys))]
  return (
    <div
      className="table-scroll"
      tabIndex={0}
      role="region"
      aria-label="Data table"
    >
      <table className="analysis-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c}>{c.replaceAll('_', ' ')}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td key={c}>{String(row[c] ?? '—')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function DataTable({ path }: { path: string }) {
  const [query, setQuery] = useState('')
  const [offset, setOffset] = useState(0)
  const [sort, setSort] = useState('')
  const [desc, setDesc] = useState(false)
  const params = new URLSearchParams({
    path,
    q: query,
    offset: String(offset),
    limit: '50',
    sort,
    desc: desc ? '1' : '0',
  })
  const { data, error } = useResource<Table>(`table?${params}`)
  return (
    <section className="table-view">
      <div className="analysis-toolbar">
        <label>
          Filter rows{' '}
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setOffset(0)
            }}
            placeholder="Search this table…"
          />
        </label>
        <a
          className="btn btn-outline btn-sm"
          href={`/api/analysis/download?path=${encodeURIComponent(path)}`}
        >
          Download CSV
        </a>
      </div>
      {error && <p role="alert">{error}</p>}
      {!data && !error && <p role="status">Loading table…</p>}
      {data && (
        <>
          <div
            className="table-scroll"
            role="region"
            aria-label={path}
            tabIndex={0}
          >
            <table className="analysis-table">
              <thead>
                <tr>
                  {data.columns.map((c) => (
                    <th
                      key={c.name}
                      aria-sort={
                        sort === c.name
                          ? desc
                            ? 'descending'
                            : 'ascending'
                          : 'none'
                      }
                    >
                      <button
                        onClick={() => {
                          setSort(c.name)
                          setDesc(sort === c.name ? !desc : false)
                          setOffset(0)
                        }}
                      >
                        {c.name} {sort === c.name ? (desc ? '↓' : '↑') : ''}
                        <small>{c.type}</small>
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row, i) => (
                  <tr key={i}>
                    {row.map((v, j) => (
                      <td key={j}>{v == null ? '—' : String(v)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="analysis-toolbar">
            <span>
              {data.total ? offset + 1 : 0}–{Math.min(offset + 50, data.total)}{' '}
              of {data.total.toLocaleString()} rows
            </span>
            <div>
              <button
                className="btn btn-outline btn-sm"
                disabled={!offset}
                onClick={() => setOffset(Math.max(0, offset - 50))}
              >
                Previous
              </button>{' '}
              <button
                className="btn btn-outline btn-sm"
                disabled={offset + 50 >= data.total}
                onClick={() => setOffset(offset + 50)}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </section>
  )
}
