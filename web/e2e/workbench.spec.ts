import { expect, test, type Locator, type Page } from '@playwright/test'
import {
  CLOSED_RUN_ID,
  installAccountUnavailableFixture,
  installAgentFixture,
  installAuditUnavailableFixture,
  installClosedMarketFixture,
  installEvidenceUnavailableFixture,
  installNoRunsFixture,
  installNewerFailureAfterSampleFixture,
  installOneRunFixture,
  installPartialSignalFixture,
  installPostSampleFailureFixture,
  installQuoteWidthFixture,
  QUOTE_RUN_ID,
  RUN_ID,
} from './agent-fixture.ts'

const CORE_PROJECTS = new Set(['desktop-chromium', 'mobile-chromium'])

function collectConsoleErrors(page: Page) {
  const errors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  return errors
}

async function expectInFirstViewport(page: Page, locator: Locator) {
  await expect(locator).toBeVisible()
  const box = await locator.boundingBox()
  const viewport = page.viewportSize()
  expect(box, 'expected a rendered bounding box').not.toBeNull()
  expect(viewport, 'expected an explicit Playwright viewport').not.toBeNull()
  expect(box!.y).toBeGreaterThanOrEqual(0)
  expect(box!.y + box!.height).toBeLessThanOrEqual(viewport!.height)
}

async function expectNoHorizontalOverflow(page: Page) {
  await page.evaluate(async () => {
    await document.fonts.ready
    await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
  })
  const measurement = await page.evaluate(() => ({
    body: Math.max(0, document.body.scrollWidth - window.innerWidth),
    document: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
    offenders: Array.from(document.querySelectorAll<HTMLElement>('body *'))
      .map((element) => ({
        className: element.className.toString(),
        right: Math.round(element.getBoundingClientRect().right),
        tag: element.tagName,
      }))
      .filter((element) => element.right > document.documentElement.clientWidth + 1)
      .slice(0, 8),
  }))
  expect(
    { body: measurement.body, document: measurement.document },
    `overflowing elements: ${JSON.stringify(measurement.offenders)}`,
  ).toEqual({ body: 0, document: 0 })
}

async function expectTouchTarget(locator: Locator) {
  await expect(locator).toBeVisible()
  const box = await locator.boundingBox()
  expect(box, 'expected a rendered touch target').not.toBeNull()
  expect(box!.width).toBeGreaterThanOrEqual(44)
  expect(box!.height).toBeGreaterThanOrEqual(44)
}

test('synthetic fixture event monitor and search stay inspectable', async ({ page }, testInfo) => {
  test.skip(!CORE_PROJECTS.has(testInfo.project.name), 'covered by the bounded core matrix')
  const errors = collectConsoleErrors(page)
  await page.goto('/events')
  await expect(page).toHaveURL(/\/events/)
  await expect(page.getByRole('heading', { name: 'Event Monitor' })).toBeVisible()
  await expect(page.getByText('1 event')).toBeVisible()

  await page.getByRole('textbox', { name: 'Search securities', exact: true }).fill('123456')
  await expect(page).toHaveURL(/q=123456/)
  await expect(page.getByText('1 matching observation')).toBeVisible()
  expect(errors).toEqual([])
})

test('product definition, sampled verdict, and primary CTA lead the first viewport', async ({ page }, testInfo) => {
  test.skip(!CORE_PROJECTS.has(testInfo.project.name), '1280 desktop and 390 mobile contract')
  await installAgentFixture(page)
  const errors = collectConsoleErrors(page)

  await page.goto('/agent')
  await expect(page).toHaveURL(/\/agent$/)
  await expect(page.getByText('MARKET REACTION FILTER / PAPER OPTIONS', { exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Find When Market Attention Outruns the Evidence' })).toBeVisible()
  await expect(page.getByText('CROWD EXCESS = (PRICE MOVE × ATTENTION) − NEWS EVIDENCE', { exact: true })).toBeVisible()
  for (const step of ['Measure the Reaction', 'Test the Explanation', 'Decide or Abstain']) {
    await expect(page.getByText(step, { exact: true })).toBeVisible()
  }
  await expect(page.getByRole('heading', { name: 'No Tradable Crowd Excess Found' })).toBeVisible()
  await expect(
    page.getByRole('region', { name: 'No Tradable Crowd Excess Found' })
      .getByText('No symbol passed attention, move, evidence, and market gates.', { exact: true }),
  ).toBeVisible()
  const scanLink = page.getByRole('link', { name: 'Review Latest Market Scan' })
  await expect(scanLink).toHaveAttribute('href', `/decisions?run=${RUN_ID}`)

  await expectInFirstViewport(page, page.getByRole('heading', { name: 'Find When Market Attention Outruns the Evidence' }))
  await expectInFirstViewport(page, page.getByRole('heading', { name: 'No Tradable Crowd Excess Found' }))
  await expectInFirstViewport(page, scanLink)
  if (testInfo.project.name === 'mobile-chromium') {
    await expectInFirstViewport(page, page.locator('.overview-observed'))
  }
  if (testInfo.project.name === 'desktop-chromium') {
    await expect(page.getByRole('heading', { name: 'Paper Account & Risk' })).toBeVisible()
    await expectInFirstViewport(page, page.getByText('Account Equity', { exact: true }))
    await expectInFirstViewport(page, page.getByText('Open Risk', { exact: true }))
  }
  const overviewType = await page.evaluate(() => ({
    body: Number.parseFloat(getComputedStyle(document.querySelector('.overview-definition')!).fontSize),
    metadata: Number.parseFloat(getComputedStyle(document.querySelector('.agent-overview .eyebrow')!).fontSize),
  }))
  expect(overviewType.body).toBeGreaterThanOrEqual(12)
  expect(overviewType.metadata).toBeGreaterThanOrEqual(10)
  expect(await page.evaluate(() => window.scrollY)).toBe(0)
  expect(errors).toEqual([])
})

test('closed automation context keeps the prior sampled scan as the primary verdict', async ({ page }, testInfo) => {
  test.skip(!CORE_PROJECTS.has(testInfo.project.name), 'production-like closed context is covered on desktop and mobile')
  await installClosedMarketFixture(page)

  await page.goto('/agent')
  await expect(page.getByRole('heading', { name: 'No Tradable Crowd Excess Found' })).toBeVisible()
  await expect(page.getByText('Market closed at the latest automation check. Showing the most recent completed market scan.', { exact: true })).toBeVisible()
  const sampledLink = page.getByRole('link', { name: 'Review Latest Market Scan' })
  await expect(sampledLink).toHaveAttribute('href', `/decisions?run=${RUN_ID}`)
  await expectInFirstViewport(page, sampledLink)
  await sampledLink.click()
  await expect(page).toHaveURL(new RegExp(`/decisions\\?run=${RUN_ID}$`))
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Crowd Excess Market Scan' })).toBeVisible()
  await expect(page.getByRole('cell', { name: 'AAPL INSPECTING' })).toBeVisible()
})

test('overview gives an honest no-runs verdict and status CTA', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'empty-state contract is covered once')
  await installNoRunsFixture(page)

  await page.goto('/agent')
  await expect(page.getByRole('heading', { name: 'Waiting for the First Market Scan' })).toBeVisible()
  const statusLink = page.getByRole('link', { name: 'View Market Scan Status' })
  await expect(statusLink).toHaveAttribute('href', '/decisions')
  await expect(page.getByText('No market scans recorded', { exact: true })).toBeVisible()
  await expect(page.getByText('Not observed', { exact: true }).first()).toBeVisible()
})

test('overview keeps the product definition and safe first action when the audit is unavailable', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'audit outage contract is covered once')
  await installAuditUnavailableFixture(page)

  await page.goto('/agent')
  await expect(page.getByRole('heading', { name: 'Find When Market Attention Outruns the Evidence' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Market Scan Status Unavailable' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'View Market Scan Status' })).toHaveAttribute('href', '/decisions')
  await expect(page.getByRole('link', { name: 'See How It Works' })).toHaveAttribute('href', '/strategy')
  await expect(page.getByRole('heading', { name: 'Paper Account & Risk' })).toHaveCount(0)
})

test('overview keeps a complete scan readable when only paper account metrics are unavailable', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'ancillary outage contract is covered once')
  await installAccountUnavailableFixture(page)

  await page.goto('/agent')
  await expect(page.getByRole('heading', { name: 'No Tradable Crowd Excess Found' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Review Latest Market Scan' })).toHaveAttribute('href', `/decisions?run=${RUN_ID}`)
  await expect(page.getByRole('alert')).toContainText('Paper account metrics are temporarily unavailable. The market scan remains readable.')
  await expect(page.getByRole('heading', { name: 'Market Scan Status Unavailable' })).toHaveCount(0)
})

test('overview treats incomplete fixed-universe coverage as a safely stopped scan', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'coverage completeness is covered once')
  await installPartialSignalFixture(page)

  await page.goto('/agent')
  await expect(page.getByRole('heading', { name: 'Scan Stopped Safely' })).toBeVisible()
  await expect(
    page.getByRole('region', { name: 'Scan Stopped Safely' })
      .getByText('Only four symbol observations were recorded; the scan stopped safely.', { exact: true }),
  ).toBeVisible()
})

test('overview discloses a newer unsampled automation failure without replacing the sampled verdict', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'newer automation context is covered once')
  await installNewerFailureAfterSampleFixture(page)

  await page.goto('/agent')
  await expect(page.getByRole('heading', { name: 'No Tradable Crowd Excess Found' })).toBeVisible()
  await expect(page.getByText(/A newer failed automation check is recorded: A newer automation check failed before provider sampling\./)).toBeVisible()
  await expect(page.locator('.overview-account-risk').getByText('FAILED', { exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Review Latest Market Scan' })).toHaveAttribute('href', `/decisions?run=${RUN_ID}`)
})

test('judge path traces five sampled symbols through risk to an honest abstention', async ({ page }, testInfo) => {
  test.skip(!CORE_PROJECTS.has(testInfo.project.name), 'covered by the bounded core matrix')
  await installQuoteWidthFixture(page)
  const errors = collectConsoleErrors(page)

  await page.goto('/decisions?symbol=AAPL')
  await expect(page).toHaveURL(/\/decisions\?symbol=AAPL/)
  await expect(page.getByRole('heading', { name: 'Crowd Excess Market Scan' })).toBeVisible()
  await expect(page.getByText('Cross-border search')).toBeVisible()
  await expect(page.getByRole('cell', { name: 'AAPL INSPECTING' })).toBeVisible()
  await expect(page.getByRole('row')).toHaveCount(6)
  await expect(page.getByText('Synthetic five-symbol fixture: supplied headlines do not explain the observed AAPL move.')).toBeVisible()
  await expect(page.getByText('abstain', { exact: true })).toHaveCount(4)
  await expect(page.getByText(/quote width/, { exact: false }).first()).toBeVisible()
  const workbenchType = await page.evaluate(() => ({
    body: Number.parseFloat(getComputedStyle(document.querySelector('.agent-console-head > div:first-child > p:last-child')!).fontSize),
    metadata: Number.parseFloat(getComputedStyle(document.querySelector('.block-head small')!).fontSize),
  }))
  expect(workbenchType.body).toBeGreaterThanOrEqual(12)
  expect(workbenchType.metadata).toBeGreaterThanOrEqual(10)

  await page.getByRole('link', { name: /Open full audit trace/ }).click()
  await expect(page).toHaveURL(new RegExp(`/agent/runs/${QUOTE_RUN_ID}`))
  await expect(page.getByRole('heading', { name: QUOTE_RUN_ID })).toBeVisible()
  await expect(page.getByText(/Abstained — quote_width: synthetic spread exceeded the declared liquidity limit/)).toBeVisible()
  await expect(page.getByText('FAILURE STAGE', { exact: true })).toBeVisible()
  await expect(page.getByText('risk evaluation', { exact: true })).toBeVisible()
  await expect(page.getByText('risk_gate_rejected', { exact: true })).toBeVisible()
  await expect(page.getByText('No order submitted', { exact: true })).toBeVisible()
  await expect(page.getByText(/OPEN ·/)).toBeVisible()

  await page.getByRole('link', { name: 'Portfolio', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Paper Portfolio' })).toBeVisible()
  await expect(page.getByText('$100,025')).toBeVisible()
  await expect(page.getByText('No open risk', { exact: true })).toBeVisible()

  await page.getByRole('link', { name: 'How It Works', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Strategy & Risk' })).toBeVisible()
  await expect(page.getByText('Live Alpaca endpoint does not exist in configuration.')).toBeVisible()
  expect(errors).toEqual([])
})

test('keyboard path connects overview, workbench, run detail, and portfolio', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'desktop keyboard assertion')
  await installAgentFixture(page)
  await page.goto('/agent')
  await expect(page.getByRole('heading', { name: 'Find When Market Attention Outruns the Evidence' })).toBeVisible()

  await page.keyboard.press('Tab')
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page.locator('#main-content')).toBeFocused()

  const workbenchLink = page.getByRole('link', { name: 'Review Latest Market Scan' })
  await workbenchLink.focus()
  await expect(workbenchLink).toBeFocused()
  expect(await workbenchLink.evaluate((element) => element.matches(':focus-visible'))).toBe(true)
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(new RegExp(`/decisions\\?run=${RUN_ID}$`))

  const traceLink = page.getByRole('link', { name: /Open full audit trace/ })
  await traceLink.focus()
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(new RegExp(`/agent/runs/${RUN_ID}`))

  const portfolioLink = page.getByRole('link', { name: 'Portfolio', exact: true })
  await portfolioLink.focus()
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\/portfolio$/)
  await expect(page.getByRole('heading', { name: 'Paper Portfolio' })).toBeVisible()
})

test('global search focuses from the shortcut and opens the decision workbench', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'desktop keyboard assertion')
  await installAgentFixture(page)
  await page.goto('/agent')
  const search = page.getByRole('textbox', { name: 'Inspect a Symbol in Market Scan' })
  await expect(search).toBeVisible()
  await expect(search).toHaveAttribute('placeholder', 'Inspect AAPL, MSFT, NVDA, TSLA, or QQQ…')
  await page.keyboard.press('ControlOrMeta+K')
  await expect(search).toBeFocused()
  await search.fill('aapl')
  await search.press('Enter')
  await expect(page).toHaveURL(new RegExp(`/decisions\\?run=${RUN_ID}&symbol=AAPL$`))
  await expect(page.getByRole('heading', { name: 'Crowd Excess Market Scan' })).toBeVisible()
})

test('redirects and legacy research deep links remain compatible', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'route compatibility is covered once')
  await installAgentFixture(page)

  await page.goto('/dashboard')
  await expect(page).toHaveURL(/\/agent$/)
  await expect(page.getByRole('heading', { name: 'Find When Market Attention Outruns the Evidence' })).toBeVisible()

  await page.goto('/settings')
  await expect(page).toHaveURL(/\/strategy$/)
  await expect(page.getByRole('heading', { name: 'Strategy & Risk' })).toBeVisible()

  await page.goto(`/agent/runs/${RUN_ID}`)
  await expect(page.getByRole('heading', { name: RUN_ID })).toBeVisible()

  await page.goto('/events')
  await expect(page.getByRole('heading', { name: 'Event Monitor' })).toBeVisible()

  await page.goto('/lineage')
  await expect(page.getByRole('heading', { name: 'Source Lineage' })).toBeVisible()
})

test('a direct comparison URL reconstructs aligned A and B traces with neutral deltas', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'comparison contract is covered at 1280 by 800')
  await installAgentFixture(page)
  const errors = collectConsoleErrors(page)
  const path = `/decisions?run=${RUN_ID}&compare=${CLOSED_RUN_ID}&symbol=AAPL`

  await page.goto(path)
  await expect(page).toHaveURL(new RegExp(`${path.replaceAll('?', '\\?')}$`))
  await expect(page.getByRole('heading', { name: 'RUN COMPARISON' })).toBeVisible()
  const table = page.getByRole('table', { name: 'Side-by-side comparison of selected agent runs A and B' })
  await expect(table).toBeVisible()
  await expect(table.getByRole('columnheader', { name: 'Run A' })).toBeVisible()
  await expect(table.getByRole('columnheader', { name: 'Run B' })).toBeVisible()
  await expect(table.getByRole('columnheader', { name: 'B − A' })).toBeVisible()

  const statusRow = table.locator('tbody tr').filter({ hasText: /^Status/ })
  await expect(statusRow).toContainText('ABSTAINED')
  await expect(statusRow).toContainText('Same state')
  const symbolRow = table.locator('tbody tr').filter({ hasText: /^Top symbol/ })
  await expect(symbolRow).toContainText('AAPL')
  await expect(symbolRow).toContainText('Not sampled')
  await expect(page.getByText('Direction only — no quality or profitability ranking is implied.')).toBeVisible()
  await expect(page.getByRole('button', { name: `Use ${RUN_ID} as run A` })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('button', { name: `Use ${CLOSED_RUN_ID} as run B` })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('cell', { name: 'AAPL INSPECTING' })).toBeVisible()

  await page.reload()
  await expect(table).toBeVisible()
  const params = await page.evaluate(() => Object.fromEntries(new URL(window.location.href).searchParams))
  expect(params).toEqual({ run: RUN_ID, compare: CLOSED_RUN_ID, symbol: 'AAPL' })
  expect(errors).toEqual([])
})

test('mobile comparison switches between the A and B trace columns', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile-chromium', 'mobile A/B disclosure contract')
  await installAgentFixture(page)
  await page.goto(`/decisions?run=${RUN_ID}&compare=${CLOSED_RUN_ID}&symbol=AAPL`)

  const table = page.getByRole('table', { name: 'Side-by-side comparison of selected agent runs A and B' })
  const switcher = page.getByRole('group', { name: 'Visible comparison run on mobile' })
  const runA = switcher.getByRole('button', { name: 'Run A' })
  const runB = switcher.getByRole('button', { name: 'Run B' })
  await expect(runA).toHaveAttribute('aria-pressed', 'true')
  await expectTouchTarget(runA)
  await expectTouchTarget(runB)
  await expect(table.getByRole('columnheader', { name: 'Run A' })).toBeVisible()
  await expect(table.getByRole('columnheader', { name: 'Run B' })).toBeHidden()

  await runB.click()
  await expect(runB).toHaveAttribute('aria-pressed', 'true')
  await expect(table.getByRole('columnheader', { name: 'Run B' })).toBeVisible()
  await expect(table.getByRole('columnheader', { name: 'Run A' })).toBeHidden()
  await expect(table.getByRole('columnheader', { name: 'B − A' })).toBeVisible()
  await expectNoHorizontalOverflow(page)
})

test('one recorded run disables comparison with an explicit explanation', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'single-run state is covered once')
  await installOneRunFixture(page)
  await page.goto(`/decisions?run=${RUN_ID}&symbol=AAPL`)

  const state = page.getByRole('status').filter({ hasText: 'Comparison needs two recorded runs' })
  await expect(state).toBeVisible()
  await expect(state).toContainText('Only one run is available.')
  await expect(state).toContainText('A/B controls will unlock after the next autonomous check is stored.')
  await expect(page.getByRole('button', { name: `Use ${RUN_ID} as run B` })).toBeDisabled()
})

test('comparison preserves both run IDs while a secondary trace loads and then fails', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'comparison failure state is covered once')
  await installAgentFixture(page)
  await page.route(`**/api/v1/agent/runs/${CLOSED_RUN_ID}`, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 450))
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Synthetic secondary trace is temporarily unavailable.' }),
    })
  })
  const path = `/decisions?run=${RUN_ID}&compare=${CLOSED_RUN_ID}&symbol=AAPL`
  await page.goto(path)

  await expect(page.getByRole('status', { name: '' }).filter({ hasText: 'Loading both immutable run traces…' })).toBeVisible()
  const alert = page.getByRole('alert').filter({ hasText: 'One comparison trace could not be loaded' })
  await expect(alert).toBeVisible({ timeout: 5_000 })
  await expect(alert).toContainText('The selected run IDs remain in the URL.')
  await expect(page).toHaveURL(new RegExp(`${path.replaceAll('?', '\\?')}$`))
})

test('a selected primary trace failure is explicit and never rendered as an empty scan', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'primary audit failure is covered once')
  await installAgentFixture(page)
  await page.route(`**/api/v1/agent/runs/${RUN_ID}`, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 200))
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Synthetic primary trace is temporarily unavailable.' }),
    })
  })
  await page.goto(`/decisions?run=${RUN_ID}&symbol=AAPL`)

  await expect(page.getByRole('status').filter({ hasText: 'Loading the agent audit' })).toBeVisible()
  const alert = page.getByRole('alert')
  await expect(alert.getByRole('heading', { name: 'Research data could not be loaded' })).toBeVisible()
  await expect(alert).toContainText('Synthetic primary trace is temporarily unavailable.')
  await expect(page.getByText('No completed scan recorded', { exact: true })).toHaveCount(0)
})

test('run detail links to its previous immutable run and accepts a legacy clockless row', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'run-detail compatibility is covered once')
  await installAgentFixture(page)

  await page.goto(`/agent/runs/${RUN_ID}`)
  await expect(page.getByText(/OPEN ·/)).toBeVisible()
  await expect(page.getByRole('link', { name: 'Back to Market Scan' })).toHaveAttribute('href', `/decisions?run=${RUN_ID}&symbol=AAPL`)
  const compare = page.getByRole('link', { name: 'Compare with previous' })
  await expect(compare).toHaveAttribute('href', `/decisions?run=${RUN_ID}&compare=${CLOSED_RUN_ID}&symbol=AAPL`)
  await compare.click()
  await expect(page.getByRole('table', { name: 'Side-by-side comparison of selected agent runs A and B' })).toBeVisible()

  await page.goto(`/agent/runs/${CLOSED_RUN_ID}`)
  await expect(page.getByRole('heading', { name: CLOSED_RUN_ID })).toBeVisible()
  await expect(page.getByText('MARKET AT CHECK', { exact: true })).toHaveCount(0)
  await page.locator('summary').filter({ hasText: 'Signal snapshots' }).click()
  await expect(page.getByText('No market inputs were sampled for this run.', { exact: false })).toBeVisible()
})

test('portfolio renders chronological history, zero-risk summary, and declared utilization', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'portfolio contract is covered once')
  await installAgentFixture(page)
  const errors = collectConsoleErrors(page)
  await page.goto('/portfolio')

  await expect(page.getByRole('heading', { name: 'Paper Portfolio' })).toBeVisible()
  await expect(page.getByText('3 snapshots', { exact: true })).toBeVisible()
  await expect(page.getByRole('img', { name: /Paper account history across 3 snapshots\. Latest equity \$100,025/ })).toBeVisible()
  await expect(page.getByText('Snapshots are displayed in recorded time order.')).toBeVisible()
  await expect(page.getByText('No open risk', { exact: true })).toBeVisible()
  await expect(page.getByRole('progressbar', { name: 'Position risk: 0% of declared limit' })).toHaveAttribute('value', '0')
  await expect(page.getByRole('progressbar', { name: 'Total premium risk: 0% of declared limit' })).toHaveAttribute('value', '0')
  await expect(page.getByRole('progressbar', { name: 'Daily-loss proximity: 0% of declared limit' })).toHaveAttribute('value', '0')
  expect(errors).toEqual([])
})

test('Data Health maps the kickoff five-signal evidence abstention without claiming readiness', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'provider-state contract is covered once')
  await installEvidenceUnavailableFixture(page)

  await page.goto('/agent')
  await expect(page.getByRole('heading', { name: 'Scan Stopped Safely' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Review Latest Market Scan' })).toHaveAttribute('href', `/decisions?run=${RUN_ID}`)
  await page.goto('/data')

  await expect(page.getByRole('heading', { name: 'Data Health' })).toBeVisible()
  await expect(page.getByLabel('Data health summary')).toContainText('3 Ready')
  await expect(page.getByLabel('Data health summary')).toContainText('2 Not sampled')
  await expect(page.getByLabel('Data health summary')).toContainText('1 Error')
  for (const provider of ['NAVER Attention', 'Alpaca Market', 'Audit Store']) {
    const article = page.locator('article.health-detail').filter({ has: page.getByRole('heading', { name: provider }) })
    await expect(article.getByText('Ready', { exact: true })).toBeVisible()
  }
  for (const provider of ['Alpaca Options', 'Risk Engine']) {
    const article = page.locator('article.health-detail').filter({ has: page.getByRole('heading', { name: provider }) })
    await expect(article.getByText('Not sampled', { exact: true })).toBeVisible()
  }
  const openai = page.locator('article.health-detail').filter({ has: page.getByRole('heading', { name: 'OpenAI Evidence' }) })
  await expect(openai.getByText('Error', { exact: true })).toBeVisible()
  await expect(page.getByText('5 symbol observations are attached to the latest trace.')).toBeVisible()
  await expect(page.getByText('No signal reached option-chain construction in the latest run.')).toBeVisible()
  await expect(page.getByText('Structured evidence assessment was unavailable; the affected signal abstained.')).toBeVisible()
  await expect(page.getByText('No candidate reached option-structure risk evaluation in this run.')).toBeVisible()
})

test('Data Health treats a legacy closed run as Not sampled', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'provider-state contract is covered once')
  await installClosedMarketFixture(page)
  await page.goto('/data')

  await expect(page.getByLabel('Data health summary')).toContainText('5 Not sampled')
  await expect(page.getByLabel('Data health summary')).toContainText('1 Ready')
  for (const provider of ['NAVER Attention', 'Alpaca Market', 'Alpaca Options', 'OpenAI Evidence', 'Risk Engine']) {
    const article = page.locator('article.health-detail').filter({ has: page.getByRole('heading', { name: provider }) })
    await expect(article.getByText('Not sampled', { exact: true })).toBeVisible()
  }
  await expect(page.getByText('The latest run ended before provider sampling.')).toBeVisible()
})

test('Data Health preserves sampled provider facts when the run fails later', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'post-sampling attribution is covered once')
  await installPostSampleFailureFixture(page)
  await page.goto('/data')

  await expect(page.getByLabel('Data health summary')).toContainText('6 Ready')
  await expect(page.getByLabel('Data health summary')).toContainText('0 Error')
  for (const provider of ['NAVER Attention', 'Alpaca Market', 'Alpaca Options', 'OpenAI Evidence', 'Risk Engine', 'Audit Store']) {
    const article = page.locator('article.health-detail').filter({ has: page.getByRole('heading', { name: provider }) })
    await expect(article.getByText('Ready', { exact: true })).toBeVisible()
  }
  await expect(page.getByRole('status').filter({ hasText: 'Latest boundary outcome' })).toContainText(
    'Stage execution · code alpaca_execution_unavailable',
  )
})

test('wide and tablet viewports keep new audit pages readable without overflow', async ({ page }, testInfo) => {
  test.skip(!['wide-chromium', 'tablet-chromium'].includes(testInfo.project.name), 'auxiliary responsive projects only')
  await installAgentFixture(page)
  const errors = collectConsoleErrors(page)
  const expectedViewport = testInfo.project.name === 'wide-chromium'
    ? { width: 1440, height: 900 }
    : { width: 900, height: 1024 }
  expect(page.viewportSize()).toEqual(expectedViewport)
  const routes = [
    { path: '/agent', heading: 'Find When Market Attention Outruns the Evidence' },
    { path: `/decisions?run=${RUN_ID}&compare=${CLOSED_RUN_ID}&symbol=AAPL`, heading: 'Crowd Excess Market Scan' },
    { path: '/portfolio', heading: 'Paper Portfolio' },
    { path: '/data', heading: 'Data Health' },
  ]
  for (const route of routes) {
    await page.goto(route.path)
    await expect(page.getByRole('heading', { name: route.heading })).toBeVisible()
    await expectNoHorizontalOverflow(page)
  }
  expect(errors).toEqual([])
})

test('mobile bottom navigation and More sheet meet focus and touch contracts', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile-chromium', '390 by 844 mobile contract')
  await installAgentFixture(page)
  const errors = collectConsoleErrors(page)
  await page.goto('/agent')

  const mobileNavigation = page.getByRole('navigation', { name: 'Mobile navigation' })
  await expect(mobileNavigation).toBeVisible()
  for (const name of ['Overview', 'Market Scan', 'Portfolio', 'How It Works']) {
    await expectTouchTarget(mobileNavigation.getByRole('link', { name, exact: true }))
  }
  const more = mobileNavigation.getByRole('button', { name: 'More', exact: true })
  await expectTouchTarget(more)

  await more.click()
  const sheet = page.getByRole('dialog', { name: 'Data & Research' })
  await expect(sheet).toBeVisible()
  expect(await page.evaluate(() => getComputedStyle(document.body).overflow)).toBe('hidden')
  const close = sheet.getByRole('button', { name: 'Close More menu' })
  await expect(close).toBeFocused()
  await page.keyboard.press('Shift+Tab')
  await expect(sheet.getByRole('link', { name: 'Research Lineage' })).toBeFocused()
  await page.keyboard.press('Tab')
  await expect(close).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(sheet).toBeHidden()
  await expect(more).toBeFocused()
  expect(await page.evaluate(() => getComputedStyle(document.body).overflow)).not.toBe('hidden')

  await more.click()
  await expect(sheet.getByRole('link', { name: 'Data Health' })).toBeVisible()
  await sheet.getByRole('link', { name: 'Korea Events' }).click()
  await expect(page).toHaveURL(/\/events$/)
  await expect(page.getByRole('heading', { name: 'Event Monitor' })).toBeVisible()

  await mobileNavigation.getByRole('button', { name: 'More', exact: true }).click()
  await page.getByRole('dialog', { name: 'Data & Research' }).getByRole('link', { name: 'Research Lineage' }).click()
  await expect(page).toHaveURL(/\/lineage$/)
  await expect(page.getByRole('heading', { name: 'Source Lineage' })).toBeVisible()
  expect(errors).toEqual([])
})

test('mobile primary and legacy pages have no body-level horizontal overflow', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile-chromium', '390 by 844 mobile contract')
  await installAgentFixture(page)
  const routes = [
    { path: '/agent', heading: 'Find When Market Attention Outruns the Evidence' },
    { path: '/decisions?symbol=AAPL', heading: 'Crowd Excess Market Scan' },
    { path: `/agent/runs/${RUN_ID}`, heading: RUN_ID },
    { path: '/portfolio', heading: 'Paper Portfolio' },
    { path: '/strategy', heading: 'Strategy & Risk' },
    { path: '/data', heading: 'Data Health' },
    { path: '/events', heading: 'Event Monitor' },
    { path: '/lineage', heading: 'Source Lineage' },
  ]

  for (const route of routes) {
    await test.step(route.path, async () => {
      await page.goto(route.path)
      await expect(page.getByRole('heading', { name: route.heading })).toBeVisible()
      await expectNoHorizontalOverflow(page)
    })
  }
})
