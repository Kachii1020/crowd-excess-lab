import { expect, test } from '@playwright/test'
import { installAgentFixture, RUN_ID } from './agent-fixture.ts'

test('synthetic fixture event monitor and search stay inspectable', async ({ page }) => {
  const errors: string[] = []
  page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })
  await page.goto('/events')
  await expect(page).toHaveURL(/\/events/)
  await expect(page.getByRole('heading', { name: 'Event Monitor' })).toBeVisible()
  await expect(page.getByText('1 event')).toBeVisible()

  await page.getByRole('textbox', { name: 'Search securities', exact: true }).fill('123456')
  await expect(page).toHaveURL(/q=123456/)
  await expect(page.getByText('1 matching observation')).toBeVisible()
  expect(errors).toEqual([])
})

test('judge path traces attention through risk and a clearly labelled shadow receipt', async ({ page }, testInfo) => {
  await installAgentFixture(page)
  const errors: string[] = []
  page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })

  await page.goto('/')
  await expect(page).toHaveURL(/\/agent/)
  await expect(page.getByRole('heading', { name: 'Agent Console' })).toBeVisible()
  await expect(page.getByText('NAVER heat')).toBeVisible()
  await expect(page.getByRole('cell', { name: 'AAPL INSPECTING' })).toBeVisible()
  await expect(page.getByText('Synthetic judge-path headlines do not explain the observed move.')).toBeVisible()
  await expect(page.getByText('SHADOW', { exact: true }).last()).toBeVisible()

  await page.getByRole('link', { name: /Open full audit trace/ }).click()
  await expect(page).toHaveURL(new RegExp(`/agent/runs/${RUN_ID}`))
  await expect(page.getByRole('heading', { name: RUN_ID })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Approved by deterministic controls' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'SHADOW' })).toBeVisible()

  if (testInfo.project.name === 'mobile-chromium') {
    await page.getByRole('button', { name: 'Open navigation' }).click()
  }
  await page.getByRole('link', { name: 'Paper Portfolio' }).click()
  await expect(page.getByRole('heading', { name: 'Paper Portfolio' })).toBeVisible()
  await expect(page.getByText('$100,250')).toBeVisible()

  if (testInfo.project.name === 'mobile-chromium') {
    await page.getByRole('button', { name: 'Open navigation' }).click()
  }
  await page.getByRole('link', { name: 'Strategy & Risk' }).click()
  await expect(page.getByRole('heading', { name: 'Strategy & Risk' })).toBeVisible()
  await expect(page.getByText('Live Alpaca endpoint does not exist in configuration.')).toBeVisible()
  expect(errors).toEqual([])
})

test('keyboard shortcut focuses global search', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop-chromium', 'desktop keyboard assertion')
  await page.goto('/')
  const search = page.locator('#global-search')
  await expect(search).toBeVisible()
  await page.keyboard.press('ControlOrMeta+K')
  await expect(search).toBeFocused()
})

test('mobile agent console does not overflow the viewport', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile-chromium', 'mobile-only assertion')
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Agent Console' })).toBeVisible()
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)
  expect(overflow).toBe(false)
})
