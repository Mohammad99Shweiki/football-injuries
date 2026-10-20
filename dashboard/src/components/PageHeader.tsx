import type { ReactNode } from 'react'

const PLAYS = {
  console: (
    <>
      <path className="play" d="M110 92 C 150 40, 200 38, 236 58" />
      <path className="play" d="M228 50 L 238 59 L 226 63" />
      <path d="M330 40 l10 10 M340 40 l-10 10" />
      <path d="M372 96 l10 10 M382 96 l-10 10" />
      <circle cx="150" cy="44" r="6" />
      <circle cx="190" cy="100" r="6" />
    </>
  ),
  report: (
    <>
      <path className="play" d="M300 96 C 340 40, 400 40, 440 66" />
      <path className="play" d="M430 58 L 441 67 L 428 71" />
      <path d="M120 40 l10 10 M130 40 l-10 10" />
      <path d="M160 92 l10 10 M170 92 l-10 10" />
      <circle cx="330" cy="46" r="6" />
    </>
  ),
}

interface Props {
  variant: keyof typeof PLAYS
  kicker: string
  title: string
  children: ReactNode
  stamp?: ReactNode
}

/** Header strip with the chalk pitch sketch (brightens and redraws the tactic arrow on hover). */
export function PageHeader({ variant, kicker, title, children, stamp }: Props) {
  return (
    <header className="page-header">
      <svg className="pitch" aria-hidden="true" viewBox="0 0 520 140" preserveAspectRatio="xMaxYMid meet">
        <g fill="none" stroke="#E4E7DE" strokeWidth="1.6" filter="url(#chalk)">
          <rect x="10" y="12" width="500" height="116" />
          <line x1="260" y1="12" x2="260" y2="128" />
          <circle cx="260" cy="70" r="26" />
          <rect x="10" y="38" width="62" height="64" />
          <rect x="448" y="38" width="62" height="64" />
          {PLAYS[variant]}
        </g>
      </svg>
      {stamp}
      <div className="header-inner">
        <div className="header-title">
          <div className="header-kicker">{kicker}</div>
          <h1>{title}</h1>
        </div>
        {children}
      </div>
    </header>
  )
}
