import { useCallback, useEffect, useState } from 'react'
import { control, fetchValidation } from '../api/client'
import type { Validation } from '../api/types'
import { Board } from '../components/Board'
import { Chalky } from '../components/chalky/Chalky'
import { CreditsFooter } from '../components/CreditsFooter'
import { RetryIcon } from '../components/Icons'
import { PageHeader } from '../components/PageHeader'
import { REPORT_SCATTER } from '../data/scatter'
import { duration } from '../lib/format'
import { FullTime } from './FullTime'
import { Fouls } from './Fouls'
import { ResultsSheet } from './ResultsSheet'
import { Summary } from './Summary'
import { TeamSheets } from './TeamSheets'
import { TreatmentRoom } from './TreatmentRoom'

function title(v: Validation | null): string {
  if (!v) return 'Validation report'
  const tail = v.attention ? `${v.attention} check${v.attention > 1 ? 's' : ''} need${v.attention > 1 ? '' : 's'} attention` : 'all checks pass'
  return v.run_time_s != null ? `Run finished in ${duration(v.run_time_s)} — ${tail}` : `Validation report — ${tail}`
}

export function ReportPage() {
  const [report, setReport] = useState<Validation | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [requeued, setRequeued] = useState<Set<string>>(new Set())

  useEffect(() => {
    document.title = 'Validation report'
    fetchValidation().then(setReport, (e: Error) => setError(e.message))
  }, [])

  const requeue = useCallback(async (ids: string[]) => {
    setError(null)
    try {
      await control('requeue', { ids })
      setRequeued((s) => new Set([...s, ...ids]))
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }, [])

  const failures = report?.failures ?? []
  const open = failures.filter((f) => !requeued.has(f.id))
  const clean = !!report && report.attention === 0 && failures.length === 0

  return (
    <Board scatter={REPORT_SCATTER}>
      <PageHeader variant="report" kicker="Validation report · printed after each run · sheet 02" title={title(report)}>
        <Chalky progress={report ? 100 : 0} hurt={false} fail={!!report && !clean} />
        <div className="header-actions">
          <span className="hand-note">post-match analysis</span>
          <a href="/scraping" className="btn btn-outline">
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 6l-6 6 6 6" /></svg>
            Back to run console
          </a>
          <button
            type="button" className="btn btn-primary" disabled={!open.length} aria-disabled={!open.length}
            onClick={() => requeue(open.map((f) => f.id))}
          >
            <RetryIcon />Retry failed ({open.length})
          </button>
        </div>
      </PageHeader>
      {error && <div className="stale-banner" role="alert"><div>Couldn't load or update the report: {error}</div></div>}
      <div className="page-body">
        {!report ? (
          <>
            <div className="summary">{[0, 1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 132 }} />)}</div>
            <div className="skeleton" style={{ height: 420 }} />
          </>
        ) : (
          <>
            <Summary tiles={report.summary} />
            <ResultsSheet matches={report.matches} />
            <div className="row-pair">
              <Fouls failures={failures} requeued={requeued} onRequeue={(id) => requeue([id])} />
              <TeamSheets clubs={report.clubs} />
            </div>
            <div className="row-pair">
              <TreatmentRoom perSeason={report.injuries_per_season} zero={report.zero_injury_players} players={report.players_total} />
              <FullTime dod={report.dod} quirks={report.documented_quirks} />
            </div>
          </>
        )}
        <CreditsFooter />
      </div>
    </Board>
  )
}
