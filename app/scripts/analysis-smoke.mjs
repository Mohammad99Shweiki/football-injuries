import { chromium } from 'playwright-core'
import assert from 'node:assert/strict'
const base = process.env.DASHBOARD_URL || 'http://127.0.0.1:8766'
const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || chromium.executablePath(),
  headless: true,
})
const page = await browser.newPage()
const errors = []
page.on('pageerror', (error) => errors.push(error.message))
page.on('response', (response) => {
  if (response.url().includes('/api/analysis/') && response.status() >= 400)
    errors.push(`${response.status()} ${response.url()}`)
})
try {
  for (const width of [1440, 768, 375]) {
    await page.setViewportSize({ width, height: 1000 })
    for (const [path, ready] of [
      ['/analysis', '.phase-card'],
      ['/analysis/studio/phase-02/step-1', '.check-row'],
      ['/analysis/reviews', '.mapping-row'],
      ['/analysis/logs', '.analysis-table tbody tr'],
      ['/analysis/results', '.cluster-chart circle'],
      ['/analysis/clustering', '.metric-card'],
      ['/analysis/report', '.check-row'],
    ]) {
      await page.goto(base + path)
      await page.locator(ready).first().waitFor()
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
        `${path} overflows at ${width}`,
      )
      if (path === '/analysis/results') {
        for (const tab of ['Evolution', 'Injuries', 'Same club', 'Trends', 'Leagues']) {
          await page.getByRole('tab', { name: tab, exact: true }).click()
          if (width === 1440) await page.screenshot({ path: `/tmp/football-results-${tab.replace(' ', '-')}.png`, fullPage: true })
          await page.waitForTimeout(100)
          assert.equal(
            await page.evaluate(
              () => document.documentElement.scrollWidth > innerWidth,
            ),
            false,
            `${tab} overflows at ${width}`,
          )
        }
      }
      if (width === 1440)
        await page.screenshot({
          path: `/tmp/football-${path.split('/')[2] || 'progress'}.png`,
          fullPage: true,
        })
    }
  }
  await page.goto(base + '/analysis/reviews')
  await page
    .getByRole('button', { name: /team.*csv/ })
    .first()
    .click()
  await page.locator('.table-view tbody tr').first().waitFor()
  await page.getByPlaceholder('Search this table…').fill('Arsenal')
  await page.waitForTimeout(500)
  assert.match(await page.locator('.table-view').innerText(), /Arsenal/)
  await page.goto(base + '/scraping')
  await page.getByRole('navigation', { name: 'Project navigation' }).waitFor()
  await page.goto(base + '/validation')
  assert.equal(
    await page.getByRole('navigation', { name: 'Scraping pages' }).count(),
    1,
  )
  // Exercise the busy state without launching any analysis or scraping process.
  await page.route('**/api/analysis/run', (route) =>
    route.fulfill({ json: { running: false, scrape_busy: true, output: [] } }),
  )
  await page.goto(base + '/analysis')
  await page.getByRole('button', { name: 'Run in progress…' }).waitFor()
  assert.equal(
    await page.getByRole('button', { name: 'Run in progress…' }).isDisabled(),
    true,
  )
  assert.match(
    await page.locator('.analysis-shell').innerText(),
    /Scraping is active/,
  )
  await page.unroute('**/api/analysis/run')
  assert.deepEqual(errors, [])
  console.log(
    'PASS: 3 widths, 7 analysis routes, all results tabs, table filtering, and legacy scraping navigation; no browser or analysis API errors.',
  )
} finally {
  await browser.close()
}
