import { expect, test } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Load sample workbook' }).click()
  await expect(
    page.getByRole('heading', { name: 'Will it work for your customers?' }),
  ).toBeVisible()
})

test('shows an API backed go decision with evidence and assumptions', async ({ page }) => {
  await page.getByLabel('Projected workload').selectOption({ index: 1 })
  await page.getByLabel('Minimum total capacity').fill('1')
  await page.getByRole('button', { name: 'Check customer fit' }).click()

  await expect(page.getByRole('heading', { name: 'Go for this projected workload' })).toBeVisible()
  await expect(page.getByText('Meets target', { exact: true }).first()).toBeVisible()
  await expect(
    page.getByRole('complementary', { name: 'Assumptions and limitations' }),
  ).toContainText('do not guarantee production service levels')
  await page.getByText(/Review all .* matching configurations/).click()
  await expect(page.getByRole('heading', { name: /Batch size/ }).first()).toBeVisible()
})

test('explains a no go decision when every matching configuration fails', async ({ page }) => {
  await page.getByLabel('Minimum total capacity').fill('999999999')
  await page.getByRole('button', { name: 'Check customer fit' }).click()

  await expect(
    page.getByRole('heading', { name: 'No go for this projected workload' }),
  ).toBeVisible()
  await expect(page.getByText('Misses target', { exact: true }).first()).toBeVisible()
  await expect(
    page.getByText('Every matching configuration misses at least one requested limit.'),
  ).toBeVisible()
})

test('keeps missing cost assumptions visible on a narrow screen', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByLabel('Maximum hardware cost').fill('2.50')
  await page.getByRole('button', { name: 'Check customer fit' }).click()

  await expect(page.getByRole('heading', { name: 'More information needed' })).toBeVisible()
  await expect(page.getByText('Unknown', { exact: true }).first()).toBeVisible()
  await expect(
    page.getByText(
      'No hardware price per box-hour was supplied, so the cost check remains unknown.',
    ),
  ).toBeVisible()
  await expect(page.getByText('hardware_cost_usd_per_box_hour')).toHaveCount(0)
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
})

test('distinguishes a calculated context requirement from the customer minimum', async ({
  page,
}) => {
  await page.getByLabel('Projected workload').selectOption({ index: 1 })
  await page.getByLabel('Minimum context window').fill('100')
  await page.getByLabel('Supported context window').fill('1000')
  await page.getByRole('button', { name: 'Check customer fit' }).click()

  await expect(
    page.getByRole('heading', { name: 'No go for this projected workload' }),
  ).toBeVisible()
  await expect(page.getByText(/Required window: .* tokens/).first()).toBeVisible()
  await expect(page.getByText(/Your limit: .* tokens/)).toHaveCount(0)
})
