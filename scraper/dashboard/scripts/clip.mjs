// Screenshot a vertical slice of a page with fake data: node scripts/clip.mjs <path> <width> <y> <height> <out.png>
import { chromium } from 'playwright-core'
import { status, validation } from './fixtures.mjs'
const [, , path, width, y, h, out] = process.argv
const b = await chromium.launch({ channel: 'chrome' })
const p = await b.newPage({ viewport: { width: +width, height: 900 } })
await p.route('**/api/status', (r) => r.fulfill({ json: status() }))
await p.route('**/api/validation', (r) => r.fulfill({ json: validation() }))
await p.goto('http://localhost:4173' + path); await p.waitForTimeout(1200)
await p.screenshot({ path: out, fullPage: true, clip: { x: 0, y: +y, width: +width, height: +h } })
await b.close()
