import { useState } from 'react'
import type { Validation } from '../api/types'
import { Eyebrow } from '../components/Eyebrow'
import { LeagueSticker } from '../components/Sticker'
import { Tabs } from '../components/Tabs'
import { LEAGUES, SEASON_LABELS } from '../data/leagues'

type Source = 'fd' | 'us'
const TABS: [Source, string][] = [['fd', 'Football-Data'], ['us', 'Understat']]
const TABLE: Record<Source, string> = { fd: 'fd_matches', us: 'us_matches (played)' }

/** 01 Results sheet: league matches per season vs expected, per source. */
export function ResultsSheet({ matches }: { matches: Validation['matches'] }) {
  const [source, setSource] = useState<Source>('fd')
  const known = new Map(matches.known_exceptions.map((k) => [`${k.league}-${k.season}`, k.note]))
  return (
    <section aria-label="League matches per season" className="results panel panel-base">
      <div className="results-head">
        <div className="section-head">
          <Eyebrow number="01" label="Results sheet" icon="sheet" />
          <h2>League matches per season</h2>
          <div className="section-sub">Found in {TABLE[source]} vs. expected. Known exceptions are marked, not fixed.</div>
        </div>
        <Tabs label="Source" items={TABS} value={source} onChange={setSource} />
      </div>
      <div className="table-well" style={{ padding: '6px 14px' }}>
        <table className="data-table results-table">
          <thead>
            <tr>
              <th>League</th>
              {SEASON_LABELS.map((s) => <th key={s}>{s}</th>)}
            </tr>
          </thead>
          <tbody>
            {LEAGUES.map((league, li) => (
              <tr key={league.name}>
                <th scope="row"><span><LeagueSticker league={li} className="mag" />{league.name}</span></th>
                {SEASON_LABELS.map((season, si) => {
                  const n = matches.found[source][li][si]
                  const e = matches.expected[li][si]
                  const note = known.get(`${li}-${si}`)
                  const kind = n == null ? 'missing' : n !== e ? 'bad' : note ? 'known' : 'normal'
                  const title = n == null
                    ? `${league.name} ${season}: not collected yet, ${e} expected`
                    : `${league.name} ${season}: ${n} found, ${e} expected${note ? ` (${note}, known exception)` : ''}`
                  return (
                    <td key={season}>
                      <div className={`result-cell mag ${kind}`} title={title}>
                        {n ?? '—'}{kind === 'bad' && <small>!</small>}
                      </div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="legend report">
        <span><span className="legend-sq normal" />Matches expected</span>
        <span><span className="legend-sq known" />Known exception (~279)</span>
        <span><span className="legend-sq bad" />Mismatch (!)</span>
        <span>Expected: 380 · Bundesliga 306 · Ligue 1 306 from 2023/24</span>
        <span className="hand-note">Ligue 1 19/20 stopped early (COVID) — that's fine</span>
      </div>
    </section>
  )
}
