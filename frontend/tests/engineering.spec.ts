import { expect, test } from '@playwright/test'
import path from 'node:path'
import type { EngineeringAnalysisResponse } from '../src/engineering'

const sampleWorkbook = path.resolve(import.meta.dirname, '../public/sample/Model A profile 1.xlsx')

test('uses the engineering API to inspect sourced rows and controlled trends', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByLabel('Choose Excel workbooks').setInputFiles(sampleWorkbook)

  await page.getByRole('link', { name: 'Engineering inspection' }).click()
  await expect(page.getByRole('heading', { name: 'Inspect the projection' })).toBeVisible()
  const table = page.getByRole('table', { name: 'Engineering configurations' })
  await expect(table.getByRole('row')).toHaveCount(5)
  await table.getByRole('button', { name: 'Row 2' }).click()
  await expect(page.locator('#engineering-detail')).toContainText('normalized row 2')
  await expect(page.locator('#engineering-detail')).toContainText('Per-box throughput')
  await expect(page.getByLabel('Engineering trends')).toContainText('Batch size 10 to 20')
  await page.getByLabel('Change to inspect').selectOption('cache_percentage')
  await expect(
    page.getByText('No controlled cache-setting pair exists in this sweep.'),
  ).toBeVisible()
  await page.getByText('Analysis limits and assumptions').click()
  await expect(page.getByText(/not production measurements/).last()).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
})

test('review flag links to the rows and metrics that support it', async ({ page }) => {
  await page.route('**/api/v1/engineering/analyze', async (route) => {
    const response = await route.fetch()
    const data = (await response.json()) as EngineeringAnalysisResponse
    const source = data.configurations[1].source
    data.anomalies = [
      {
        code: 'ANOMALY_NONPOSITIVE_METRIC',
        rule: 'Flag reported throughput, TTFT, or generation speed at or below zero',
        explanation: 'Review a projected zero TTFT in normalized row 2.',
        sources: [source],
      },
    ]
    await route.fulfill({ response, json: data })
  })

  await page.goto('/')
  await page.getByLabel('Choose Excel workbooks').setInputFiles(sampleWorkbook)
  await expect(page.getByText('1 review flag across all sweeps')).toBeVisible()
  await page.getByRole('link', { name: 'Inspect Model A · Profile 1 · normalized row 2' }).click()
  await expect(page.locator('#engineering-detail')).toContainText('normalized row 2')
  await expect(
    page.getByRole('table', { name: 'Engineering configurations' }).getByRole('row').nth(2),
  ).toContainText('1')
})

test('an engineering API error leaves the customer flow available', async ({ page }) => {
  await page.route('**/api/v1/engineering/analyze', (route) =>
    route.fulfill({ status: 503, body: 'Unavailable' }),
  )
  await page.goto('/')
  await page.getByLabel('Choose Excel workbooks').setInputFiles(sampleWorkbook)

  await expect(page.getByRole('alert')).toContainText('Engineering analysis unavailable')
  await expect(
    page.getByRole('heading', { name: 'Will it work for your customers?' }),
  ).toBeVisible()
  await expect(page.getByRole('table', { name: 'Customer model comparison' })).toBeVisible()
})
