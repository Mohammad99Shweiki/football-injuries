// Seeded, jittered 4-column placement of the injury prints (stable between reloads). Ported from the designs.
import { MOMENTS, photoOf, type Moment, type Photo } from './moments'

export interface ScatterConfig {
  seed: number
  rowHeight: number
  top: number // prints start below the header (console 240px, report 200px)
  yJitter: number
  orderStep: number
  offsetOddRows: boolean // console shifts odd rows by 12%, the report shifts even rows
}

export const CONSOLE_SCATTER: ScatterConfig = { seed: 7, rowHeight: 450, top: 240, yJitter: 140, orderStep: 7, offsetOddRows: true }
export const REPORT_SCATTER: ScatterConfig = { seed: 31, rowHeight: 420, top: 200, yJitter: 160, orderStep: 5, offsetOddRows: false }

export interface PlacedPrint extends Moment, Photo {
  index: number
  xPct: number
  y: number
  rot: string
  tape: string
  scale: string
  flash: string
}

const COLS = 4

export function scatter(config: ScatterConfig): PlacedPrint[] {
  let seed = config.seed
  const rnd = () => {
    seed = (seed * 9301 + 49297) % 233280
    return seed / 233280
  }
  const n = MOMENTS.length
  const order = MOMENTS.map((_, i) => i).sort((a, b) => ((a * config.orderStep) % n) - ((b * config.orderStep) % n))
  return order.map((idx, k) => {
    const m = MOMENTS[idx]
    const col = k % COLS, row = Math.floor(k / COLS)
    const offset = (row % 2 === 1) === config.offsetOddRows ? 12 : 0
    const xPct = Math.min(92, Math.max(-3, col * 25 + offset + rnd() * 14 - 4))
    const y = config.top + row * config.rowHeight + Math.round(rnd() * config.yJitter)
    return {
      ...m,
      ...photoOf(m.player),
      index: k,
      xPct,
      y,
      rot: (rnd() * 26 - 13).toFixed(1) + 'deg',
      tape: (rnd() * 10 - 5).toFixed(1) + 'deg',
      scale: (0.86 + rnd() * 0.24).toFixed(2),
      flash: Math.round(20 + rnd() * 60) + '%',
    }
  })
}
