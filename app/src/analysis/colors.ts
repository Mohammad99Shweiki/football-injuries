/** Fixed slots for the four styles of a phase (board tokens, distinct in lightness as well as hue). */
export const STYLE_COLORS = ['var(--site-fd)', 'var(--lg-pl)', 'var(--annotation)', 'var(--warn)']
const BELOW = '76, 141, 219' // --run: fewer than expected
const ABOVE = '224, 123, 57' // --warn: more than expected

/** Background for a rate ratio (log scale, full colour at a factor of about 1.4) or a z-score (full at ±1.5). */
export function shade(value: number, mode: 'ratio' | 'z' = 'ratio'): string {
  const strength = mode === 'ratio' ? Math.abs(Math.log2(value)) / 0.5 : Math.abs(value) / 1.5
  const below = mode === 'ratio' ? value < 1 : value < 0
  return `rgba(${below ? BELOW : ABOVE}, ${(0.08 + 0.62 * Math.min(1, strength)).toFixed(2)})`
}
