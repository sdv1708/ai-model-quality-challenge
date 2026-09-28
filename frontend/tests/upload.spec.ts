import { expect, test } from '@playwright/test'
import path from 'node:path'

const fixtures = path.resolve(import.meta.dirname, 'fixtures')
const sampleWorkbook = path.resolve(import.meta.dirname, '../public/sample/Model A profile 1.xlsx')

test('uploads a workbook and shows its normalized performance summary', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel('Choose an Excel workbook').setInputFiles(sampleWorkbook)

  await expect(page.getByRole('heading', { name: 'Model A' })).toBeVisible()
  await expect(page.getByText('Profile 1', { exact: true })).toBeVisible()
  await expect(page.getByText('4 configurations')).toBeVisible()
  await expect(page.getByRole('table', { name: 'Normalized configurations' })).toBeVisible()
})

test('reports a specific workbook validation error and lets the user recover', async ({ page }) => {
  await page.goto('/')
  await page
    .getByLabel('Choose an Excel workbook')
    .setInputFiles(path.join(fixtures, 'invalid-columns.xlsx'))

  await expect(page.getByRole('alert')).toContainText('Batch Size')
  await expect(page.getByRole('heading', { name: 'No workbook loaded' })).toBeVisible()
  await page.getByRole('button', { name: 'Load sample workbook' }).click()
  await expect(page.getByRole('heading', { name: 'Model A' })).toBeVisible()
})

test('sample flow works from the keyboard on a narrow screen', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByRole('button', { name: 'Load sample workbook' }).focus()
  await page.keyboard.press('Enter')

  await expect(page.getByRole('heading', { name: 'Model A' })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
})
