import type { ClubsRow } from '../api/types'
import { Eyebrow } from '../components/Eyebrow'
import { LeagueSticker } from '../components/Sticker'
import { LEAGUES } from '../data/leagues'
import { MAGNET } from '../data/magnets'

/** 03 Team sheets: clubs per league-season (T1), plus league fixtures per club-season (T5). */
export function TeamSheets({ clubs }: { clubs: ClubsRow[] }) {
  return (
    <section aria-label="Clubs per league-season" className="team-sheets panel panel-base">
      <div className="section-head">
        <Eyebrow number="03" label="Team sheets" icon="shield" />
        <h2>Clubs per league-season (T1)</h2>
      </div>
      {clubs.map((c) => {
        const ok = c.found_ok === c.of
        const fixturesOk = c.fixtures_of > 0 && c.fixtures_ok === c.fixtures_of
        return (
          <div key={c.league} className="team-row">
            <div className="team-row-left">
              <LeagueSticker league={c.league} className="mag" />
              <div className="team-row-text">
                <b>{LEAGUES[c.league].name}</b>
                <span>{c.expected}</span>
              </div>
            </div>
            <div className="team-found">
              <span style={{ color: ok ? 'var(--ok-text)' : 'var(--warn-text)' }}>
                <span aria-hidden="true" className="legend-dot" style={{ background: ok ? MAGNET.ok : MAGNET.fail }} />
                {c.found_ok} / {c.of}{!ok && ' !'}
              </span>
              <small title="Club-seasons with every league match found in the T5 fixtures">
                fixtures {c.fixtures_ok.toLocaleString('en-US')} / {c.fixtures_of.toLocaleString('en-US')}{c.fixtures_of > 0 && !fixturesOk && ' !'}
              </small>
            </div>
          </div>
        )
      })}
    </section>
  )
}
