const nf = new Intl.NumberFormat('en-US')

export const fmt = (n: number) => nf.format(n)

/** Total with a leading ~ when it is still an estimate. */
export const fmtTotal = (n: number, estimate: boolean) => (estimate ? '~' : '') + fmt(n)

export const pct = (done: number, total: number) => (total > 0 ? Math.min(100, Math.floor((done / total) * 100)) : 0)

export function clock(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds))
  const pad = (v: number) => String(v).padStart(2, '0')
  return `${pad(Math.floor(s / 3600))}:${pad(Math.floor((s % 3600) / 60))}:${pad(s % 60)}`
}

/** "1 h 46 min", "12 min", "45 s" */
export function duration(seconds: number): string {
  const s = Math.max(0, Math.round(seconds))
  if (s < 60) return `${s} s`
  const h = Math.floor(s / 3600)
  const m = Math.round((s % 3600) / 60)
  return h ? `${h} h ${String(m).padStart(2, '0')} min` : `${m} min`
}

/** Shorten long hosts the way the design does (tmapi…/player/…). */
export function shortUrl(url: string): string {
  return url
    .replace('https://tmapi.transfermarkt.technology', 'tmapi…')
    .replace(/^https?:\/\/(www\.)?/, '')
}
