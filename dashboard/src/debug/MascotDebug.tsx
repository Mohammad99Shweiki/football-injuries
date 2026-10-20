import { useEffect, useRef, useState } from 'react'
import { Board } from '../components/Board'
import { Chalky } from '../components/chalky/Chalky'
import { MOODS, MOOD_ORDER } from '../components/chalky/rig'
import { Eyebrow } from '../components/Eyebrow'
import { PageHeader } from '../components/PageHeader'
import { CONSOLE_SCATTER } from '../data/scatter'

/** Design QA for Chalky (?debug=mascot): drive progress, knock and red card by hand, or play a demo match. */
export function MascotDebug() {
  const [p, setP] = useState(61)
  const [hurt, setHurt] = useState(false)
  const [fail, setFail] = useState(false)
  const [playing, setPlaying] = useState(false)
  const timer = useRef<number | null>(null)
  const knocked = useRef(false)

  const stop = () => {
    if (timer.current !== null) window.clearInterval(timer.current)
    timer.current = null
    setPlaying(false)
  }

  useEffect(() => () => stop(), [])

  const play = () => {
    if (playing) return stop()
    knocked.current = false
    setP(0); setHurt(false); setFail(false); setPlaying(true)
    timer.current = window.setInterval(() => {
      setP((v) => {
        if (v >= 100) { stop(); return v }
        if (v === 42 && !knocked.current) {
          knocked.current = true
          setHurt(true)
          window.setTimeout(() => setHurt(false), 2600)
          return v
        }
        return v + 1
      })
    }, 110)
  }

  return (
    <Board scatter={CONSOLE_SCATTER}>
      <PageHeader variant="console" kicker="Design QA · ?debug=mascot" title="Chalky — state machine and rig">
        <Chalky progress={p} hurt={hurt} fail={fail} />
      </PageHeader>
      <div className="page-body">
        <section className="panel-base debug-sheet" aria-label="Mascot controls">
          <Eyebrow label="Controls" icon="gauge" />
          <div className="debug-controls">
            <label className="mono">progress {p}%
              <input type="range" min={0} max={100} value={p} onChange={(e) => setP(Number(e.target.value))} />
            </label>
            <button type="button" className="btn btn-outline" onClick={() => { setHurt((h) => !h); setFail(false) }}>{hurt ? 'Heal' : 'Took a knock'}</button>
            <button type="button" className="btn btn-outline" onClick={() => { setFail((f) => !f); setHurt(false) }}>{fail ? 'Clear red card' : 'Red card'}</button>
            <button type="button" className="btn btn-primary" onClick={play}>{playing ? 'Stop' : 'Play a match'}</button>
            <button type="button" className="btn btn-outline" onClick={() => { stop(); setP(0); setHurt(false); setFail(false) }}>Reset</button>
          </div>
        </section>
        <section className="panel-base debug-sheet" aria-label="States">
          {MOOD_ORDER.map((k) => (
            <div key={k} className="finding" style={{ borderTop: 0 }}>
              <span className="pill idle" style={{ padding: '3px 8px', color: MOODS[k].color }}>{MOODS[k].name}</span>
              <div className="finding-text"><b>{MOODS[k].rule}</b><div>{MOODS[k].lines.join(' · ')}</div></div>
            </div>
          ))}
        </section>
      </div>
    </Board>
  )
}
