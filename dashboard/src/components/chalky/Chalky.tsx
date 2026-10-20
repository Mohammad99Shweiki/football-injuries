import { useEffect, useRef, useState } from 'react'
import { CONFETTI, EMBERS, MOODS, RING_LENGTH, auraFor, moodFor } from './rig'

interface Props {
  /** Overall progress, 0-100 (already floored and monotonic). */
  progress: number
  hurt: boolean
  fail: boolean
}

const STAR = 'M0 -13 L3.8 -4.2 13 -4 5.8 1.9 8.3 11 0 5.9 -8.3 11 -5.8 1.9 -13 -4 -3.8 -4.2 Z'
const AURA = 'M110 -44 L126 14 L156 -22 L152 36 L192 12 L174 66 L206 76 L182 110 L200 156 L154 168 L110 196 L66 168 L20 156 L38 110 L14 76 L46 66 L28 12 L68 36 L64 -22 L94 14 Z'

/** Eyes follow the cursor: pupil offset from the widget's centre, clamped to ±3.5 x and ±3 y. */
function useLook(target: React.RefObject<HTMLElement | null>) {
  const [look, setLook] = useState({ x: 0, y: 0 })
  useEffect(() => {
    let frame: number | null = null
    let last: MouseEvent | null = null
    const update = () => {
      frame = null
      const el = target.current
      if (!el || !last) return
      const r = el.getBoundingClientRect()
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2
      setLook({
        x: Math.max(-3.5, Math.min(3.5, (last.clientX - cx) / 60)),
        y: Math.max(-3, Math.min(3, (last.clientY - cy) / 60)),
      })
    }
    const onMove = (e: MouseEvent) => {
      last = e
      if (frame === null) frame = requestAnimationFrame(update)
    }
    const onLeave = () => setLook({ x: 0, y: 0 })
    window.addEventListener('mousemove', onMove)
    document.addEventListener('mouseleave', onLeave)
    return () => {
      window.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseleave', onLeave)
      if (frame !== null) cancelAnimationFrame(frame)
    }
  }, [target])
  return look
}

/** Chalky, the run mascot: 140x132 widget + speech bubble + match clock (HANDOFF section 5). */
export function Chalky({ progress, hurt, fail }: Props) {
  const p = Math.max(0, Math.min(100, Math.floor(progress)))
  const key = moodFor(p, hurt, fail)
  const m = MOODS[key]
  const aura = auraFor(p, hurt, fail)
  const [line, setLine] = useState(0)
  const [kick, setKick] = useState(false)
  const kickTimer = useRef<number | null>(null)
  const button = useRef<HTMLButtonElement>(null)
  const look = useLook(button)

  // A new state starts on its first line.
  const [lastKey, setLastKey] = useState(key)
  if (lastKey !== key) {
    setLastKey(key)
    setLine(0)
  }

  useEffect(() => () => {
    if (kickTimer.current !== null) window.clearTimeout(kickTimer.current)
  }, [])

  const poke = () => {
    if (kickTimer.current !== null) window.clearTimeout(kickTimer.current)
    setKick(true)
    setLine((l) => l + 1)
    kickTimer.current = window.setTimeout(() => setKick(false), 700)
  }

  const auraOn = aura !== 'none'
  const ignite = aura === 'ignite'
  const auraOpacity = aura === 'charge' ? (0.25 + ((p - 75) / 15) * 0.45).toFixed(2) : aura === 'glow' ? '0.55' : '1'
  const embers = ignite ? EMBERS : EMBERS.slice(0, aura === 'charge' ? 5 : 7)
  const minute = p >= 100 ? 'FT' : `${Math.round(p * 0.9)}′`
  const pupilLX = (88 + look.x).toFixed(1), pupilRX = (128 + look.x).toFixed(1), pupilY = (95 + look.y).toFixed(1)
  const spd = { '--spd': m.spd } as React.CSSProperties

  return (
    <div role="group" aria-label="Chalky, the run mascot" className="chalky">
      <button
        ref={button}
        type="button"
        onClick={poke}
        aria-label={`Chalky: ${m.name}, ${p}% collected. Poke him.`}
        className={`chalky-btn ${ignite ? 'quake' : ''}`}
        style={{ background: `radial-gradient(circle at 50% 48%, ${m.glow}, rgba(0,0,0,0) 66%)` }}
      >
        <svg aria-hidden="true" viewBox="0 0 140 132" width="140" height="132" style={{ inset: 0 }}>
          <circle cx="70" cy="64" r="58" fill="none" stroke="rgba(228,231,222,0.10)" strokeWidth="6" />
          <circle
            className={`ring ${m.pulse ? 'pulse' : ''}`} cx="70" cy="64" r="58" fill="none" stroke={m.color} strokeWidth="6"
            strokeLinecap="round" strokeDasharray={RING_LENGTH} strokeDashoffset={(RING_LENGTH * (1 - p / 100)).toFixed(1)}
            transform="rotate(-90 70 64)"
          />
        </svg>
        <svg aria-hidden="true" viewBox="0 0 220 240" width="92" height="100" style={{ left: 24, top: 14, overflow: 'visible', ...spd }}>
          <defs>
            <linearGradient id="chAuraOuter" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stopColor="#FF9E1B" stopOpacity="0.95" /><stop offset="0.55" stopColor="#FFD54A" stopOpacity="0.7" /><stop offset="1" stopColor="#FFF6C8" stopOpacity="0" /></linearGradient>
            <linearGradient id="chAuraInner" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stopColor="#FFF3B0" stopOpacity="1" /><stop offset="0.7" stopColor="#FFFFFF" stopOpacity="0.55" /><stop offset="1" stopColor="#FFFFFF" stopOpacity="0" /></linearGradient>
            <filter id="chAuraBlur" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3.5" /></filter>
          </defs>
          {auraOn && <ellipse cx="110" cy="226" rx={ignite ? 70 : 52} ry="10" fill="#FFD54A" opacity="0.35" filter="url(#chAuraBlur)" />}
          <ellipse className={`fb sh-${m.anim}`} cx="110" cy="228" rx="48" ry="7" fill="rgba(0,0,0,0.5)" />
          <g className={`vb ch-${m.anim}`} style={{ transformOrigin: '110px 226px' }}>
            {auraOn && (
              <g style={{ opacity: auraOpacity }}>
                <g className="vb flick1" style={{ transformOrigin: '110px 200px' }}><path filter="url(#chAuraBlur)" d={AURA} fill="url(#chAuraOuter)" /></g>
                <g transform="translate(110 196) scale(0.8) translate(-110 -196)"><g className="vb flick2" style={{ transformOrigin: '110px 196px' }}><path d={AURA} fill="url(#chAuraInner)" opacity="0.85" /></g></g>
                {ignite && (
                  <>
                    <g className="vb flick3" style={{ transformOrigin: '110px 190px' }}><path d="M110 -70 L120 -10 L140 -40 L136 10 M110 -70 L100 -10 L80 -40 L84 10" stroke="#FFF6C8" strokeWidth="3" fill="none" strokeLinecap="round" opacity="0.8" /></g>
                    <g stroke="#FFFBE0" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round">
                      <polyline className="zap" points="36,52 50,74 40,78 56,104" />
                      <polyline className="zap" style={{ animationDelay: '.3s' }} points="184,44 170,68 182,72 164,98" />
                      <polyline className="zap" style={{ animationDelay: '.55s' }} points="22,128 40,140 30,146 50,164" />
                      <polyline className="zap" style={{ animationDelay: '.15s' }} points="198,122 182,136 194,142 176,162" />
                    </g>
                  </>
                )}
              </g>
            )}
            {m.speed && (
              <g className="speed" stroke="#E4E7DE" strokeWidth="3" strokeLinecap="round"><line x1="4" y1="78" x2="36" y2="78" /><line x1="-6" y1="104" x2="30" y2="104" style={{ animationDelay: '.15s' }} /><line x1="8" y1="130" x2="36" y2="130" style={{ animationDelay: '.3s' }} /></g>
            )}
            <g className={m.legs} stroke="#E4E7DE" strokeWidth="6" strokeLinecap="round">
              <g className="vb leg-l" style={{ transformOrigin: '96px 152px' }}><line x1="96" y1="152" x2="90" y2="198" /><rect x="76" y="194" width="24" height="11" rx="5" fill={m.color} stroke="none" /></g>
              <g className="vb leg-r" style={{ transformOrigin: '124px 152px' }}><line x1="124" y1="152" x2="130" y2="198" /><rect x="120" y="194" width="24" height="11" rx="5" fill={m.color} stroke="none" /></g>
            </g>
            <g fill="none" stroke="#E4E7DE" strokeWidth="6" strokeLinecap="round">
              <g className={`vb ${m.swingL}`}><path d={m.armL} />{m.fists && <circle cx={m.fxL} cy={m.fyL} r="7" fill="#E4E7DE" stroke="none" />}</g>
              <g className={`vb ${m.swingR}`}><path d={m.armR} />{m.fists && <circle cx={m.fxR} cy={m.fyR} r="7" fill="#E4E7DE" stroke="none" />}</g>
            </g>
            {m.card && <rect x="176" y="96" width="18" height="26" rx="2" fill="#E5636B" stroke="#1E2A24" strokeWidth="2" transform="rotate(12 185 109)" />}
            <g className={`vb ${kick ? 'kick' : ''}`} style={{ transformOrigin: '110px 100px' }}>
              <circle cx="110" cy="100" r="58" fill="#F1ECDF" stroke={m.color} strokeWidth="5" />
              <g fill="#26332C"><path d="M110 47 L122.4 56 L117.6 70.5 L102.4 70.5 L97.6 56 Z" /><path d="M53 96 L66 92 L72 106 L64 118 L55 116 Z" /><path d="M167 96 L154 92 L148 106 L156 118 L165 116 Z" /><path d="M98 156 L104 143 L116 143 L122 156 Z" /></g>
              <g stroke="#26332C" strokeWidth="2" fill="none" opacity="0.55"><path d="M97.6 56 L66 92" /><path d="M122.4 56 L154 92" /><path d="M64 118 L104 143" /><path d="M156 118 L116 143" /></g>
              {m.headband && (
                <>
                  <path d="M56 74 Q 110 58 164 74 L 165 84 Q 110 68 55 84 Z" fill={m.color} />
                  <path d="M164 78 L180 70 M164 80 L182 86" stroke={m.color} strokeWidth="5" strokeLinecap="round" />
                </>
              )}
              {m.eyesOpen && (
                <g className={`fb ${m.eyepop ? 'eyepop' : ''}`}>
                  <ellipse cx="90" cy="98" rx={m.eyeRx} ry={m.eyeRy} fill="#1E2A24" />
                  <ellipse cx="130" cy="98" rx={m.eyeRx} ry={m.eyeRy} fill="#1E2A24" />
                  <circle cx={pupilLX} cy={pupilY} r={m.shine} fill="#FFFFFF" />
                  <circle cx={pupilRX} cy={pupilY} r={m.shine} fill="#FFFFFF" />
                  {m.sparkle && <><circle cx="94" cy="103" r="1.8" fill="#FFFFFF" /><circle cx="134" cy="103" r="1.8" fill="#FFFFFF" /></>}
                </g>
              )}
              {m.starEyes && (
                <>
                  <g transform="translate(90 98)"><path className="fb starspin" d={STAR} fill="#F2C14E" stroke="#1E2A24" strokeWidth="2.5" strokeLinejoin="round" /></g>
                  <g transform="translate(130 98)"><path className="fb starspin" d={STAR} fill="#F2C14E" stroke="#1E2A24" strokeWidth="2.5" strokeLinejoin="round" /></g>
                </>
              )}
              {m.eyesHappy && <path d="M80 101 Q 90 88 100 101 M120 101 Q 130 88 140 101" stroke="#1E2A24" strokeWidth="4.5" fill="none" strokeLinecap="round" />}
              {m.eyesX && <path d="M83 91 L97 105 M97 91 L83 105 M123 91 L137 105 M137 91 L123 105" stroke="#1E2A24" strokeWidth="4" strokeLinecap="round" />}
              <path d={m.brows} stroke="#1E2A24" strokeWidth="4" fill="none" strokeLinecap="round" />
              <path d={m.mouth} fill={m.mouthFill} stroke="#1E2A24" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
              {m.teeth && (
                <>
                  <ellipse cx="110" cy={m.tongueCy} rx={m.tongueRx} ry="4.5" fill="#E5636B" />
                  <path d={m.teethD} fill="#FFFFFF" />
                </>
              )}
              {m.blush && <><circle cx="74" cy="116" r="7" fill={m.color} opacity="0.45" /><circle cx="146" cy="116" r="7" fill={m.color} opacity="0.45" /></>}
              {m.tear && <path className="sweat" d="M84 110 C 86 116, 88 119, 85 122 C 82 124, 79 121, 81 116 Z" fill="#A6C8F2" />}
              {m.plaster && <g transform="rotate(-25 142 120)"><rect x="128" y="114" width="28" height="11" rx="4" fill="#F3C9A0" stroke="#B5835A" strokeWidth="1.5" /><rect x="137" y="114" width="10" height="11" fill="#E8B486" /></g>}
            </g>
            {m.sweat && <path className="sweat" d="M170 60 C 174 68, 176 72, 172 76 C 168 78, 164 74, 166 68 Z" fill="#A6C8F2" />}
            {m.bandage && (
              <>
                <g className="ice"><rect x="88" y="30" width="44" height="22" rx="9" fill="#9CC4F2" stroke="#2F68AD" strokeWidth="2" /><path d="M96 36 h6 M106 36 h6 M116 36 h6" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" /></g>
                <g transform="rotate(28 140 66)"><rect x="124" y="60" width="34" height="12" rx="4" fill="#F1ECDF" stroke="#E07B39" strokeWidth="2" /></g>
                <g transform="rotate(-28 140 66)"><rect x="124" y="60" width="34" height="12" rx="4" fill="#F1ECDF" stroke="#E07B39" strokeWidth="2" /></g>
              </>
            )}
            {m.stars && (
              <g className="vb orbit" fill="#E9D98B"><path d="M80 34 l3 6 6 1 -4.5 4 1 6 -5.5 -3 -5.5 3 1 -6 -4.5 -4 6 -1z" /><path d="M140 26 l2.5 5 5 .8 -3.6 3.4 .8 5 -4.7 -2.4 -4.6 2.4 .9 -5 -3.7 -3.4 5.1 -.8z" /><path d="M112 8 l2 4 4 .6 -3 2.8 .7 4 -3.7 -2 -3.7 2 .7 -4 -3 -2.8 4 -.6z" /></g>
            )}
            {m.zz && (
              <g fontFamily="Caveat, cursive" fontWeight="700" fill="#E4E7DE"><text className="zz" x="150" y="44" fontSize="22">z</text><text className="zz" x="164" y="30" fontSize="16" style={{ animationDelay: '1s' }}>z</text></g>
            )}
          </g>
          {auraOn && embers.map((e, i) => (
            <circle key={i} className="fb rise" cx={e.x} cy={e.y} r={e.r} fill={e.fill} style={{ animationDelay: e.d }} />
          ))}
          {ignite && (
            <g fill="#5A4A3A" stroke="#2A2214" strokeWidth="1.5">
              <path className="fb floaty" d="M58 222 l8 -5 7 3 -2 7 -9 1z" />
              <path className="fb floaty" style={{ animationDelay: '.7s' }} d="M150 224 l6 -6 8 2 0 6 -8 2z" />
              <path className="fb floaty" style={{ animationDelay: '1.3s' }} d="M92 226 l5 -4 6 2 -1 5 -7 1z" />
              <path className="fb floaty" style={{ animationDelay: '1.8s' }} d="M172 220 l4 -4 5 1 0 4 -5 2z" />
            </g>
          )}
          {m.sparkles && (
            <>
              <g transform="translate(26 40)"><path className="fb twinkle" d="M0 -10 Q 1.8 -1.8 10 0 Q 1.8 1.8 0 10 Q -1.8 1.8 -10 0 Q -1.8 -1.8 0 -10 Z" fill={m.color} /></g>
              <g transform="translate(198 48)"><path className="fb twinkle" style={{ animationDelay: '.35s' }} d="M0 -8 Q 1.5 -1.5 8 0 Q 1.5 1.5 0 8 Q -1.5 1.5 -8 0 Q -1.5 -1.5 0 -8 Z" fill="#F1ECDF" /></g>
              <g transform="translate(14 150)"><path className="fb twinkle" style={{ animationDelay: '.6s' }} d="M0 -7 Q 1.4 -1.4 7 0 Q 1.4 1.4 0 7 Q -1.4 1.4 -7 0 Q -1.4 -1.4 0 -7 Z" fill="#F1ECDF" /></g>
              <g transform="translate(206 160)"><path className="fb twinkle" style={{ animationDelay: '.2s' }} d="M0 -10 Q 1.8 -1.8 10 0 Q 1.8 1.8 0 10 Q -1.8 1.8 -10 0 Q -1.8 -1.8 0 -10 Z" fill={m.color} /></g>
              <g transform="translate(110 -6)"><path className="fb twinkle" style={{ animationDelay: '.8s' }} d="M0 -7 Q 1.4 -1.4 7 0 Q 1.4 1.4 0 7 Q -1.4 1.4 -7 0 Q -1.4 -1.4 0 -7 Z" fill="#F2C14E" /></g>
            </>
          )}
          {m.confetti && CONFETTI.map((c, i) => (
            <rect key={i} className="fb confetti" x={c.x} y={c.y} width={c.w} height={c.h} rx="1.5" fill={c.fill} style={{ animationDelay: c.d }} />
          ))}
        </svg>
      </button>
      <div className="chalky-side">
        {/* Announced on state changes and pokes only, since the text changes only then. */}
        <div className={`chalky-bubble ${m.bob ? 'bob' : ''}`} role="status" aria-live="polite" style={{ borderColor: m.color }}>
          {m.lines[line % m.lines.length]}
        </div>
        <div className="chalky-meta">
          <span className="chalky-minute" style={{ color: m.color }}>{minute}</span>
          <span className="chalky-mood">{m.name} · {p}% collected</span>
        </div>
      </div>
    </div>
  )
}
