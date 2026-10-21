import type { SummaryTile } from '../api/types'
import { MAGNET } from '../data/magnets'

const ICONS = [
  'M6 3h9l4 4v14H6z M14 3v5h5 M9 13h7 M9 17h7',
  'M8 4c-2 0-3 1-3 3v2c0 1-1 2-2 3 1 1 2 2 2 3v2c0 2 1 3 3 3 M16 4c2 0 3 1 3 3v2c0 1 1 2 2 3-1 1-2 2-2 3v2c0 2-1 3-3 3',
  'M12 3l9.5 17h-19z M12 10v4 M12 17h.01',
  'M3 5h18v14H3z M3 10h18 M9 10v9',
]

export function Summary({ tiles }: { tiles: SummaryTile[] }) {
  return (
    <section aria-label="Summary" className="summary">
      {tiles.map((m, i) => {
        const pass = m.state === 'pass'
        return (
          <div key={m.label} className="tile panel panel-base">
            <span aria-hidden="true" className="pin" style={{ background: pass ? MAGNET.ok : MAGNET.fail }} />
            <div className="tile-top">
              <span className="tile-label">
                <svg aria-hidden="true" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--annotation)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d={ICONS[i % ICONS.length]} /></svg>
                {m.label}
              </span>
              <span className={`pill ${pass ? 'ok' : 'warn'}`}>{pass ? 'Pass' : 'Attention'}</span>
            </div>
            <div className="tile-value">{m.value}</div>
            <div className="tile-sub">{m.sub}</div>
          </div>
        )
      })}
    </section>
  )
}
