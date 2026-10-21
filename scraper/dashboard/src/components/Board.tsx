import type { CSSProperties, ReactNode } from 'react'
import type { ScatterConfig } from '../data/scatter'
import { usePointer } from '../hooks/usePointer'
import { Prints } from './Prints'

/**
 * Page shell. Stacking order, back to front: dot grid, grain, cursor spotlight, prints, then the page (header +
 * panels, which are semi-transparent so prints show faintly through).
 */
export function Board({ scatter, children }: { scatter: ScatterConfig; children: ReactNode }) {
  const { pointer, onMouseMove, onMouseLeave } = usePointer()
  const spot = { '--mx': `${pointer.x}px`, '--my': `${pointer.y}px`, opacity: pointer.hot ? 1 : 0 } as CSSProperties
  return (
    <div className="board" onMouseMove={onMouseMove} onMouseLeave={onMouseLeave}>
      <svg aria-hidden="true" width="0" height="0" className="board-defs">
        <defs>
          <filter id="chalk" x="-5%" y="-5%" width="110%" height="110%">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" result="n" />
            <feDisplacementMap in="SourceGraphic" in2="n" scale="2.4" />
          </filter>
          <filter id="grain">
            <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch" />
            <feColorMatrix type="saturate" values="0" />
          </filter>
        </defs>
      </svg>
      <svg aria-hidden="true" className="board-grain"><rect width="100%" height="100%" filter="url(#grain)" /></svg>
      <div aria-hidden="true" className="spot-glow" style={spot} />
      <div aria-hidden="true" className="spot-dots" style={spot} />
      <Prints config={scatter} pointer={pointer} />
      {children}
    </div>
  )
}
