import { useEffect, useState } from 'react'
import { control } from '../api/client'
import type { ControlAction, Flags, Status } from '../api/types'
import { Board } from '../components/Board'
import { CreditsFooter } from '../components/CreditsFooter'
import { CONSOLE_SCATTER } from '../data/scatter'
import { useStatus } from '../hooks/useStatus'
import { Collectors } from './Collectors'
import { ConsoleHeader } from './ConsoleHeader'
import { Controls } from './Controls'
import { Coverage } from './Coverage'
import { MatchLog } from './MatchLog'
import { Play } from './Play'
import { Scouting } from './Scouting'
import { Tempo } from './Tempo'
import { failuresRemain, isBackingOff, overallProgress } from './model'

/** Progress never goes backwards within a run: when totals grow, hold the shown value until it catches up. */
function useMonotonicProgress(status: Status | null): number {
  const [best, setBest] = useState({ run: '', value: 0 })
  const run = status?.started_at ?? 'idle'
  const value = status ? overallProgress(status) : 0
  const shown = best.run === run ? Math.max(best.value, value) : value
  if (best.run !== run || shown !== best.value) setBest({ run, value: shown }) // derived state, updated during render
  return shown
}

function Skeleton() {
  return (
    <>
      <div className="skeleton" style={{ height: 104 }} />
      <div className="collectors">{[0, 1, 2].map((i) => <div key={i} className="skeleton" style={{ height: 268 }} />)}</div>
      <div className="row-pair">
        <div className="skeleton" style={{ flex: '999 1 560px', height: 420 }} />
        <div className="skeleton" style={{ flex: '1 1 360px', height: 420 }} />
      </div>
    </>
  )
}

export function ConsolePage() {
  const { status, stale, refresh } = useStatus()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const progress = useMonotonicProgress(status)
  const finished = status?.phase === 'finished'
  const hurt = !!status && (status.phase === 'paused' || isBackingOff(status))
  const fail = !!status && failuresRemain(status)

  useEffect(() => {
    const phase = status?.phase
    document.title = phase === 'running' || phase === 'paused'
      ? `${progress}% · Run console`
      : finished ? `Full time · Run console` : 'Run console'
  }, [status?.phase, progress, finished])

  const act = async (action: ControlAction, flags?: Flags) => {
    setBusy(true)
    setError(null)
    try {
      await control(action, flags ? { flags } : {})
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Board scatter={CONSOLE_SCATTER}>
      <ConsoleHeader status={status} progress={progress} hurt={hurt} fail={fail} />
      {stale && <div className="stale-banner" role="alert"><div>Lost contact with the collectors, retrying…</div></div>}
      {error && <div className="stale-banner" role="alert"><div>Couldn't do that: {error}</div></div>}
      <div className="page-body">
        {!status ? <Skeleton /> : (
          <>
            <Controls
              phase={status.phase}
              activeFlags={status.flags}
              busy={busy}
              onStart={(flags) => act('start', flags)}
              onSmoke={(flags) => act('smoke_test', flags)}
              onPause={() => act('pause')}
              onResume={() => act('resume')}
            />
            {finished && !status.flags.dry_run && (
              <div className="callout ok" style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                <b style={{ fontSize: 14 }}>Run finished. The validation report is ready.</b>
                <a className="btn btn-primary" href="/validation">Open validation report</a>
              </div>
            )}
            <Collectors status={status} />
            <div className="row-pair">
              <Play status={status} />
              <Tempo limiter={status.limiter} />
            </div>
            <Coverage status={status} />
            <div className="row-pair">
              <MatchLog rows={status.manifest_tail} />
              <Scouting findings={status.smoke_test} />
            </div>
          </>
        )}
        <CreditsFooter />
      </div>
    </Board>
  )
}
