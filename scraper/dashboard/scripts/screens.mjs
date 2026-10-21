// Screenshot checks against fake API payloads: node scripts/screens.mjs [outDir]
// Needs `npm run build` and `npx vite preview --port 4173` running; uses the installed Google Chrome.
import { chromium } from 'playwright-core'
import { status, validation } from './fixtures.mjs'

const out = process.argv[2] ?? 'screens'
const base = 'http://localhost:4173'
const browser = await chromium.launch({ channel: 'chrome' })

async function shot(name, path, { width = 1440, height = 900, statusArgs = {}, full = true, hover } = {}) {
  const page = await browser.newPage({ viewport: { width, height } })
  await page.route('**/api/status', (r) => r.fulfill({ json: status(statusArgs) }))
  await page.route('**/api/validation', (r) => r.fulfill({ json: validation() }))
  await page.goto(base + path)
  await page.waitForTimeout(1500)
  if (hover) await page.mouse.move(hover.x, hover.y)
  await page.waitForTimeout(500)
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: full })
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
  const chalky = await page.$eval('[aria-label^="Chalky:"]', (el) => el.getAttribute('aria-label')).catch(() => '-')
  console.log(`${name}: horizontal overflow ${overflow}px · ${chalky}`)
  await page.close()
}

await shot('console-1440', '/')
await shot('console-hover', '/', { full: false, hover: { x: 700, y: 520 } })
await shot('report-1440', '/validation')
for (const w of [375, 768, 1280]) {
  await shot(`console-${w}`, '/', { width: w })
  await shot(`report-${w}`, '/validation', { width: w })
}
// Chalky state machine at the documented thresholds.
for (const [name, args] of [
  ['warm', { progress: 5 }], ['jog', { progress: 30 }], ['sprint', { progress: 62 }], ['charge', { progress: 80 }],
  ['ignited', { progress: 95 }], ['fulltime', { progress: 100, phase: 'finished' }], ['knock', { phase: 'paused' }],
  ['backoff', { backoff: true }], ['redcard', { progress: 100, phase: 'finished', failed: 3 }],
]) {
  await shot(`chalky-${name}`, '/', { full: false, statusArgs: args, height: 260 })
}
await browser.close()
