import { expect, test } from '@playwright/test'

test('synthetic fixture event monitor and search stay inspectable', async ({ page }) => {
  const errors: string[] = []
  page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })
  await page.goto('/')
  await expect(page).toHaveURL(/\/events/)
  await expect(page.getByRole('heading', { name: 'Event Monitor' })).toBeVisible()
  await expect(page.getByText('1 event')).toBeVisible()

  await page.getByRole('textbox', { name: 'Search securities', exact: true }).fill('123456')
  await expect(page).toHaveURL(/q=123456/)
  await expect(page.getByText('1 matching observation')).toBeVisible()
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

test('mobile event monitor does not overflow the viewport', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile-chromium', 'mobile-only assertion')
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Event Monitor' })).toBeVisible()
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)
  expect(overflow).toBe(false)
})
