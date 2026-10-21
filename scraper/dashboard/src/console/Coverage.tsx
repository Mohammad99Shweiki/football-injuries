import { useState } from 'react'
import type { SourceKey, Status } from '../api/types'
import { Eyebrow } from '../components/Eyebrow'
import { LeagueSticker } from '../components/Sticker'
import { Tabs } from '../components/Tabs'
import { LEAGUES, SEASON_LABELS } from '../data/leagues'
import { MAGNET } from '../data/magnets'
import { CELL_NAMES, cellStyle, countCells } from './model'

const TABS: [SourceKey, string][] = [['fd', 'Football-Data'], ['us', 'Understat'], ['tm', 'Transfermarkt']]

function note(status: Status | null, source: SourceKey): string {
  if (!status || status.phase === 'idle') return 'magnets go up as league-seasons land'
  const done = countCells(status, source, 'done')
  const failed = countCells(status, source, 'failed')
  if (failed) return `${failed} league-season${failed > 1 ? 's' : ''} dropped some — retry queued`
  if (source === 'fd') return done === 60 ? 'all 60 CSVs in — bytes as received' : `${done} of 60 CSVs in`
  if (source === 'us') return done === 60 ? 'all 60 league-seasons in' : `${done} of 60 league-seasons in`
  return done === 60 ? 'every player of every league-season stored' : `${done} of 60 league-seasons fully collected`
}

/** 05 The board: league x season magnets per source. */
export function Coverage({ status }: { status: Status | null }) {
  const [source, setSource] = useState<SourceKey>('tm')
  return (
    <section aria-label="Coverage" className="coverage panel panel-base">
      <div className="head-row">
        <div className="section-head">
          <Eyebrow number="05" label="The board" icon="pitch" />
          <h2>Coverage by league-season</h2>
        </div>
        <Tabs label="Source" items={TABS} value={source} onChange={setSource} />
      </div>
      <div className="scroll-x">
        <div className="cov-grid">
          <div className="cov-row head">
            <div />
            {SEASON_LABELS.map((s) => <div key={s}>{s}</div>)}
          </div>
          {LEAGUES.map((league, li) => (
            <div key={league.name} className="cov-row body">
              <div className="cov-league"><LeagueSticker league={li} /><span>{league.name}</span></div>
              {SEASON_LABELS.map((season, si) => {
                const state = status?.coverage[source][li][si] ?? 'queued'
                const detail = status?.coverage_detail[source][li][si]
                const { magnet, mark } = cellStyle(state)
                return (
                  <div key={season} className="cov-cell">
                    <div
                      className={`cov-magnet mag ${magnet ? '' : 'queued'}`}
                      style={magnet ? { background: magnet } : undefined}
                      title={`${league.name} ${season}: ${CELL_NAMES[state]}${detail ? ` — ${detail}` : ''}`}
                    >
                      {mark}
                    </div>
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>
      <div className="legend">
        <span><span className="legend-dot" style={{ background: MAGNET.ok }} />Saved raw</span>
        <span><span className="legend-dot" style={{ background: MAGNET.run }} />In progress</span>
        <span><span className="legend-dot queued" />Queued</span>
        <span><span className="legend-dot" style={{ background: MAGNET.fail }} />Failed — retry queued (!)</span>
        <span className="hand-note sm">{note(status, source)}</span>
      </div>
    </section>
  )
}
