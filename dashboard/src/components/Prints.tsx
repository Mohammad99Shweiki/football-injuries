import { useMemo, useState } from 'react'
import type { CSSProperties } from 'react'
import type { Pointer } from '../hooks/usePointer'
import { LEAGUES } from '../data/leagues'
import { scatter, type PlacedPrint, type ScatterConfig } from '../data/scatter'

const REVEAL_RADIUS = 190
const MOBILE_PRINTS = 6

/** Disposable-camera prints of notable injuries: ghosted at rest, revealed near the cursor or on tap. */
export function Prints({ config, pointer }: { config: ScatterConfig; pointer: Pointer }) {
  const prints = useMemo(() => scatter(config), [config])
  const [tapped, setTapped] = useState<Set<number>>(new Set())

  const toggle = (index: number) =>
    setTapped((s) => {
      const next = new Set(s)
      if (next.has(index)) next.delete(index)
      else next.add(index)
      return next
    })

  return (
    <div role="group" aria-label="Notable injuries from the 2014/15–2025/26 seasons" className="prints">
      {prints.map((p) => {
        const cx = (p.xPct / 100) * pointer.width - 40 + 88
        const cy = p.y + 110
        const near = pointer.hot && Math.hypot(pointer.x - cx, pointer.y - cy) < REVEAL_RADIUS
        return <Print key={p.player} print={p} visible={near || tapped.has(p.index)} onTap={() => toggle(p.index)} />
      })}
    </div>
  )
}

function Print({ print: p, visible, onTap }: { print: PlacedPrint; visible: boolean; onTap: () => void }) {
  const [broken, setBroken] = useState(false)
  const [logoBroken, setLogoBroken] = useState(false)
  const league = LEAGUES[p.lg]
  const style = {
    '--r': p.rot, '--s': p.scale, opacity: visible ? 1 : 0.05,
    left: `calc(${p.xPct.toFixed(1)}% - 40px)`, top: `${p.y}px`,
  } as CSSProperties
  return (
    <figure className={`print ${p.index >= MOBILE_PRINTS ? 'extra' : ''}`} style={style} onClick={onTap}>
      <span aria-hidden="true" className="print-tape" style={{ transform: `rotate(${p.tape})` }} />
      <div className="print-photo">
        {broken ? (
          <div className="print-fallback">{p.player}</div>
        ) : (
          <img src={p.img} alt={`Photo of ${p.player}`} loading="lazy" onError={() => setBroken(true)} />
        )}
        <div aria-hidden="true" className="print-flash" style={{ background: `radial-gradient(circle at ${p.flash} 18%, rgba(255,244,214,0.38), transparent 46%)` }} />
        <div aria-hidden="true" className="print-vignette" />
        <svg aria-hidden="true" className="print-grain"><rect width="100%" height="100%" filter="url(#grain)" /></svg>
        <span className="print-stamp">{p.stamp}</span>
        <span aria-hidden="true" className="print-logo">
          {logoBroken ? <span>{league.short}</span> : <img src={league.logo} alt="" onError={() => setLogoBroken(true)} />}
        </span>
        <span className="print-area">{p.area}</span>
        {p.recur && <span className="print-again">again!</span>}
      </div>
      <figcaption>
        <span className="print-caption">{p.player} — {p.what}</span>
        <span className="print-match">{p.match} · {p.date}</span>
        <a href={p.page} className="print-credit" title={`Photo: ${p.artist}, ${p.license}, via Wikimedia Commons`}>
          Photo: {p.artist} · {p.license}
        </a>
      </figcaption>
    </figure>
  )
}
