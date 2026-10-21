import type { SourceKey, Status, UsStep } from '../api/types'
import { Eyebrow } from '../components/Eyebrow'
import { MiniIcon } from '../components/Icons'
import { SiteSticker } from '../components/Sticker'
import { SITES, SOURCE_ORDER } from '../data/leagues'
import { BAR } from '../data/magnets'
import { fmt, fmtTotal, pct } from '../lib/format'
import { PILL } from './model'

/** 02 Collectors: one card per source. */
export function Collectors({ status }: { status: Status | null }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div className="section-row">
        <Eyebrow number="02" label="Collectors" icon="tray" />
        <div className="hand-note">three hosts, three rate limits, all at once</div>
      </div>
      <section aria-label="Collectors" className="collectors">
        {SOURCE_ORDER.map((key) => <CollectorCard key={key} source={key} status={status} />)}
      </section>
    </div>
  )
}

function CollectorCard({ source, status }: { source: SourceKey; status: Status | null }) {
  const site = SITES[source]
  const s = status?.sources[source]
  const idle = !s || s.state === 'queued'
  const pill = PILL[s?.state ?? 'queued']
  const dry = !!status?.flags.dry_run && status.phase !== 'idle'
  const width = s ? pct(s.done, s.total) : 0
  return (
    <article className="collector panel panel-base">
      <span aria-hidden="true" className={`pin ${pill.magnet ? '' : 'queued'}`} style={pill.magnet ? { background: pill.magnet } : undefined} />
      <div className="collector-top">
        <div className="collector-id">
          <SiteSticker source={source} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <h2>{site.name}</h2>
            <div className="collector-host">{site.host}</div>
          </div>
        </div>
        <span className={`pill ${pill.cls}`}>{pill.text}</span>
      </div>
      <div className="collector-count">
        <b>{idle ? '—' : fmt(s.done)}</b>
        <span>/ {idle ? '—' : fmtTotal(s.total, s.total_is_estimate)} {dry ? 'planned' : 'requests'}</span>
      </div>
      <div className="bar-track" role="progressbar" aria-label={`${site.short} progress`} aria-valuenow={width} aria-valuemin={0} aria-valuemax={100}>
        <div className="bar-fill" style={{ width: `${width}%`, background: s?.state === 'done' ? BAR.ok : s?.state === 'failed' || s?.state === 'paused' ? BAR.warn : BAR.run }} />
      </div>
      <dl className="stats">
        <div>
          <dt><MiniIcon><path d="M4 16a8 8 0 0 1 16 0" /><path d="M12 16l4.5-5" /></MiniIcon>Rate limit</dt>
          <dd>{s?.rate || (source === 'fd' ? '1 / 2 s' : source === 'us' ? '1 / s' : '4 conc · ~4/s')}</dd>
        </div>
        <div>
          <dt><MiniIcon><ellipse cx="12" cy="6" rx="7" ry="3" /><path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6" /><path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3" /></MiniIcon>Cache hits</dt>
          <dd>{fmt(s?.cache_hits ?? 0)}</dd>
        </div>
        <div>
          <dt><MiniIcon><path d="M12 3l9.5 17h-19z" /><path d="M12 10v4" /><path d="M12 17h.01" /></MiniIcon>Failed</dt>
          <dd>{fmt(s?.failed ?? 0)}</dd>
        </div>
      </dl>
      {source === 'us' && <SourceSteps steps={status?.us_steps} />}
      <div className="collector-note">{s?.note || site.defaultNote}</div>
    </article>
  )
}

const US_PLACEHOLDER: UsStep[] = [
  { id: 'U1', label: 'League data', call: 'getLeagueData(league, season)', done: 0, total: 0, total_is_estimate: true, sub: 'queued', state: 'queued' },
  { id: 'U2', label: 'Team statistics', call: 'getTeamData(team, season)', done: 0, total: 0, total_is_estimate: true, sub: 'queued', state: 'queued' },
]

/** Understat's two request kinds, each with its own count and bar. */
function SourceSteps({ steps }: { steps?: UsStep[] }) {
  return (
    <ul className="collector-steps" aria-label="Understat steps">
      {(steps ?? US_PLACEHOLDER).map((t) => (
        <li key={t.id}>
          <span className={`step-chip ${t.state}`}>{t.id}</span>
          <span className="collector-step-label" title={t.call}>{t.label}</span>
          <span className="collector-step-count">{t.total > 0 ? `${fmt(t.done)} / ${fmtTotal(t.total, t.total_is_estimate)}` : '—'}</span>
          <div className="bar-track" aria-hidden="true">
            <div className="bar-fill" style={{ width: `${pct(t.done, t.total)}%`, background: t.state === 'done' ? BAR.ok : BAR.run }} />
          </div>
        </li>
      ))}
    </ul>
  )
}
