import { expect, test, type Locator, type Page } from '@playwright/test'
import {
  installAgentFixture,
  installClosedMarketFixture,
  RUN_ID,
} from './agent-fixture.ts'

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

test('synthetic fixture event monitor and search stay inspectable', async ({ page }) => {
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

test('overview answers status, decision, risk, and next action in the first desktop viewport', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', '1280 by 800 desktop contract')
  await installAgentFixture(page)
  const errors = collectConsoleErrors(page)

  await page.goto('/agent')
  await expect(page).toHaveURL(/\/agent$/)
  await expect(page.getByRole('heading', { name: 'Today at a glance' })).toBeVisible()
  await expect(page.getByText('$100,250', { exact: true }).first()).toBeVisible()
  await expect(page.getByText('$580', { exact: true }).first()).toBeVisible()
  await expect(page.getByText('Evidence → Risk → Outcome', { exact: true })).toBeVisible()
  await expect(page.getByText('Last three runs', { exact: true })).toBeVisible()

  await expectInFirstViewport(page, page.getByRole('heading', { name: 'Today at a glance' }))
  await expectInFirstViewport(page, page.getByText('Account equity', { exact: true }))
  await expectInFirstViewport(page, page.getByText('Open risk', { exact: true }))
  await expectInFirstViewport(page, page.getByText('Evidence → Risk → Outcome', { exact: true }))
  await expectInFirstViewport(page, page.getByRole('link', { name: /Open Decision Workbench/ }))
  expect(await page.evaluate(() => window.scrollY)).toBe(0)
  expect(errors).toEqual([])
})

test('closed-market overview reports a past check and marks providers not sampled', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'state contract is covered once')
  await installClosedMarketFixture(page)

  await page.goto('/agent')
  await expect(page.getByRole('heading', { name: 'Market window was closed at the latest check' })).toBeVisible()
  await expect(page.getByText(/This is a past check result, not a claim about the market right now\./)).toBeVisible()
  await expect(page.getByText(/Return after the next eligible US-market scan/)).toBeVisible()
  await expect(page.getByText('Not sampled', { exact: true })).toHaveCount(4)
  await expect(page.getByText('Unavailable', { exact: true })).toHaveCount(0)
  await expect(page.getByText(/Evidence was not sampled → no candidate reached risk evaluation → the agent placed no order\./)).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Crowd Excess Matrix' })).toHaveCount(0)
})

test('judge path traces attention through risk and a clearly labelled shadow receipt', async ({ page }) => {
  await installAgentFixture(page)
  const errors = collectConsoleErrors(page)

  await page.goto('/decisions?symbol=AAPL')
  await expect(page).toHaveURL(/\/decisions\?symbol=AAPL/)
  await expect(page.getByRole('heading', { name: 'Decision Workbench' })).toBeVisible()
  await expect(page.getByText('Cross-border search')).toBeVisible()
  await expect(page.getByRole('cell', { name: 'AAPL INSPECTING' })).toBeVisible()
  await expect(page.getByText('Synthetic judge-path headlines do not explain the observed move.')).toBeVisible()
  await expect(page.getByText('SHADOW', { exact: true }).last()).toBeVisible()

  await page.getByRole('link', { name: /Open full audit trace/ }).click()
  await expect(page).toHaveURL(new RegExp(`/agent/runs/${RUN_ID}`))
  await expect(page.getByRole('heading', { name: RUN_ID })).toBeVisible()
  await expect(page.getByText('Approved by deterministic controls', { exact: true })).toBeVisible()
  await expect(page.getByText('OPEN · SHADOW', { exact: true })).toBeVisible()

  await page.getByRole('link', { name: 'Portfolio', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Paper Portfolio' })).toBeVisible()
  await expect(page.getByText('$100,250')).toBeVisible()

  await page.getByRole('link', { name: 'Strategy', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Strategy & Risk' })).toBeVisible()
  await expect(page.getByText('Live Alpaca endpoint does not exist in configuration.')).toBeVisible()
  expect(errors).toEqual([])
})

test('keyboard path connects overview, workbench, run detail, and portfolio', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'desktop keyboard assertion')
  await installAgentFixture(page)
  await page.goto('/agent')
  await expect(page.getByRole('heading', { name: 'Today at a glance' })).toBeVisible()

  await page.keyboard.press('Tab')
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page.locator('#main-content')).toBeFocused()

  const workbenchLink = page.getByRole('link', { name: /Open Decision Workbench/ })
  await workbenchLink.focus()
  await expect(workbenchLink).toBeFocused()
  expect(await workbenchLink.evaluate((element) => element.matches(':focus-visible'))).toBe(true)
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\/decisions$/)

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
  const search = page.locator('#global-search')
  await expect(search).toBeVisible()
  await page.keyboard.press('ControlOrMeta+K')
  await expect(search).toBeFocused()
  await search.fill('aapl')
  await search.press('Enter')
  await expect(page).toHaveURL(/\/decisions\?symbol=AAPL/)
  await expect(page.getByRole('heading', { name: 'Decision Workbench' })).toBeVisible()
})

test('redirects and legacy research deep links remain compatible', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'route compatibility is covered once')
  await installAgentFixture(page)

  await page.goto('/dashboard')
  await expect(page).toHaveURL(/\/agent$/)
  await expect(page.getByRole('heading', { name: 'Today at a glance' })).toBeVisible()

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

test('mobile bottom navigation and More sheet meet focus and touch contracts', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile-chromium', '390 by 844 mobile contract')
  await installAgentFixture(page)
  const errors = collectConsoleErrors(page)
  await page.goto('/agent')

  const mobileNavigation = page.getByRole('navigation', { name: 'Mobile navigation' })
  await expect(mobileNavigation).toBeVisible()
  for (const name of ['Overview', 'Decisions', 'Portfolio', 'Strategy']) {
    await expectTouchTarget(mobileNavigation.getByRole('link', { name, exact: true }))
  }
  const more = mobileNavigation.getByRole('button', { name: 'More', exact: true })
  await expectTouchTarget(more)

  await more.click()
  const sheet = page.getByRole('dialog', { name: 'Research Archive' })
  await expect(sheet).toBeVisible()
  const close = sheet.getByRole('button', { name: 'Close More menu' })
  await expect(close).toBeFocused()
  await page.keyboard.press('Shift+Tab')
  await expect(sheet.getByRole('link', { name: 'Research Lineage' })).toBeFocused()
  await page.keyboard.press('Tab')
  await expect(close).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(sheet).toBeHidden()
  await expect(more).toBeFocused()

  await more.click()
  await sheet.getByRole('link', { name: 'Korea Events' }).click()
  await expect(page).toHaveURL(/\/events$/)
  await expect(page.getByRole('heading', { name: 'Event Monitor' })).toBeVisible()

  await mobileNavigation.getByRole('button', { name: 'More', exact: true }).click()
  await page.getByRole('dialog', { name: 'Research Archive' }).getByRole('link', { name: 'Research Lineage' }).click()
  await expect(page).toHaveURL(/\/lineage$/)
  await expect(page.getByRole('heading', { name: 'Source Lineage' })).toBeVisible()
  expect(errors).toEqual([])
})

test('mobile primary and legacy pages have no body-level horizontal overflow', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile-chromium', '390 by 844 mobile contract')
  await installAgentFixture(page)
  const routes = [
    { path: '/agent', heading: 'Today at a glance' },
    { path: '/decisions?symbol=AAPL', heading: 'Decision Workbench' },
    { path: `/agent/runs/${RUN_ID}`, heading: RUN_ID },
    { path: '/portfolio', heading: 'Paper Portfolio' },
    { path: '/strategy', heading: 'Strategy & Risk' },
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
