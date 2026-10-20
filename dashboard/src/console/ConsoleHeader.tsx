import type { Status } from '../api/types'
import { Chalky } from '../components/chalky/Chalky'
import { PageHeader } from '../components/PageHeader'
import { clock, duration } from '../lib/format'
import { headerStatus } from './model'

interface Props {
  status: Status | null
  progress: number
  hurt: boolean
  fail: boolean
}

export function ConsoleHeader({ status, progress, hurt, fail }: Props) {
  const pill = headerStatus(status?.phase ?? 'idle', status)
  const running = status?.phase === 'running' || status?.phase === 'paused'
  return (
    <PageHeader
      variant="console"
      kicker="Raw collection · run_all.py · sheet 01"
      title="Big Five leagues — Playing style × Injuries, 2014/15–2025/26"
      stamp={status?.flags.dry_run && status.phase !== 'idle' ? <div aria-hidden="true" className="dry-stamp">DRY RUN</div> : null}
    >
      <Chalky progress={progress} hurt={hurt} fail={fail} />
      <div className="header-status">
        <div className="status-pill-lg">
          <span className={`dot ${pill.magnet ? '' : 'queued'}`} style={pill.magnet ? { background: pill.magnet } : undefined} />
          <span>{pill.text}</span>
        </div>
        <div className="clock">
          <span className="clock-time">{clock(status?.elapsed_s ?? 0)}</span>
          <span className="clock-target">target 1½–2 h</span>
          {running && status?.eta_s != null && <span className="clock-eta">· about {duration(status.eta_s)} left</span>}
        </div>
      </div>
    </PageHeader>
  )
}
