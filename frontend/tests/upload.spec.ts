import { expect, test } from '@playwright/test'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const fixtures = path.resolve(import.meta.dirname, 'fixtures')
const sampleWorkbook = path.resolve(import.meta.dirname, '../public/sample/Model A profile 1.xlsx')

test('uploads a workbook and shows its normalized performance summary', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel('Choose Excel workbooks').setInputFiles(sampleWorkbook)

  await expect(page.getByRole('heading', { name: 'Model A', exact: true })).toBeVisible()
  await expect(page.locator('.preview .profile-badge')).toHaveText('Profile 1')
  await expect(page.getByText('4 configurations')).toBeVisible()
  await expect(page.getByRole('table', { name: 'Normalized configurations' })).toBeVisible()
})

test('reports a specific workbook validation error and lets the user recover', async ({ page }) => {
  await page.goto('/')
  await page
    .getByLabel('Choose Excel workbooks')
    .setInputFiles(path.join(fixtures, 'invalid-columns.xlsx'))

  await expect(page.getByRole('alert')).toContainText('Batch Size')
  await expect(page.getByRole('heading', { name: 'No workbook loaded' })).toBeVisible()
  await page.getByRole('button', { name: 'Load sample workbook' }).click()
  await expect(page.getByRole('heading', { name: 'Model A', exact: true })).toBeVisible()
})

test('compares multiple uploads including an unseen model name', async ({ page }) => {
  await page.goto('/')
  const buffer = readFileSync(sampleWorkbook)
  await page.getByLabel('Choose Excel workbooks').setInputFiles([
    {
      name: 'Model A profile 1.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer,
    },
    {
      name: 'Model L profile 1.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer,
    },
  ])

  await expect(page.getByRole('heading', { name: 'Compare the same workload' })).toBeVisible()
  await expect(page.getByText('Direct comparison available')).toBeVisible()
  const table = page.getByRole('table', { name: 'Customer model comparison' })
  await expect(table.getByRole('rowheader', { name: 'Model A' })).toBeVisible()
  await expect(table.getByRole('rowheader', { name: 'Model L' })).toBeVisible()
  await page.getByLabel('Inspect one sweep and test customer targets').selectOption('1')
  await expect(page.getByRole('heading', { name: 'Model L', exact: true })).toBeVisible()
  await page.getByLabel('Projected workload').selectOption({ index: 1 })
  await page.getByLabel('Minimum total capacity').fill('1')
  await page.getByRole('button', { name: 'Check customer fit' }).click()
  const decisions = page.getByRole('table', { name: 'Customer decision comparison' })
  await expect(decisions.getByRole('row', { name: /Model A GO/ })).toBeVisible()
  await expect(decisions.getByRole('row', { name: /Model L GO/ })).toBeVisible()
})

test('sample flow works from the keyboard on a narrow screen', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByRole('button', { name: 'Load sample workbook' }).focus()
  await page.keyboard.press('Enter')

  await expect(page.getByRole('heading', { name: 'Model A', exact: true })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
})
