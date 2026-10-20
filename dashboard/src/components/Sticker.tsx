import { useState } from 'react'
import type { CSSProperties } from 'react'
import type { SourceKey } from '../api/types'
import { LEAGUES, SITES } from '../data/leagues'

/** League logo on a paper tile with a bottom border in the league colour; falls back to the short code. */
export function LeagueSticker({ league, className = '', style }: { league: number; className?: string; style?: CSSProperties }) {
  const info = LEAGUES[league]
  const [broken, setBroken] = useState(false)
  return (
    <span aria-hidden="true" className={`sticker ${className}`} style={{ borderBottomColor: info.color, ...style }}>
      {broken ? <span className="sticker-short">{info.short}</span> : <img src={info.logo} alt="" onError={() => setBroken(true)} />}
    </span>
  )
}

/** Site tile for collector cards: real logo for Transfermarkt, typeset name tile for the other two. */
export function SiteSticker({ source }: { source: SourceKey }) {
  const site = SITES[source]
  if (site.logo) {
    return (
      <span aria-hidden="true" className="sticker site-tile mag" style={{ borderBottomColor: site.color }}>
        <img src={site.logo} alt="" />
      </span>
    )
  }
  return (
    <span aria-hidden="true" className="sticker sticker-word site-tile mag" style={{ borderBottomColor: site.color }}>
      <b>{site.word}</b>
      {site.wordSub && <small>{site.wordSub}</small>}
    </span>
  )
}

/** Small source tile for tables (match log, failures). */
export function SourceTile({ source, width = 40 }: { source: SourceKey; width?: number }) {
  const site = SITES[source]
  return site.logo ? (
    <span aria-hidden="true" className="src-tile" style={{ width }}><img src={site.logo} alt="" /></span>
  ) : (
    <span aria-hidden="true" className="src-tile word" style={{ minWidth: width }}>{site.word}</span>
  )
}
