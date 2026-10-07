import path from 'node:path'
import { expect, type Page } from '@playwright/test'

// Playwright global setup generates independent browser fixtures automatically.
export const generatedFixtures = path.resolve(import.meta.dirname, '../fixtures/browser-generated')
export const modelA = path.join(generatedFixtures, 'Model A profile 1.xlsx')
export const modelL = path.join(generatedFixtures, 'Model L profile 1.xlsx')

export async function uploadGeneratedModels(page: Page) {
  await page.goto('/')
  await page.getByLabel('Choose Excel workbooks').setInputFiles([modelA, modelL])
  await expect(page.getByRole('table', { name: 'Customer model comparison' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Inspect the projection' })).toBeVisible()
}

export async function checkGeneratedCustomerFit(page: Page) {
  await page.getByLabel('Inspect one sweep and test customer targets').selectOption('1')
  await page.getByLabel('Projected workload').selectOption({ index: 1 })
  await page.getByLabel('Minimum total capacity').fill('450')
  await page.getByRole('button', { name: 'Check customer fit' }).click()
  const decisions = page.getByRole('table', { name: 'Customer decision comparison' })
  await expect(decisions.getByRole('row', { name: /Model A NO GO/ })).toBeVisible()
  await expect(decisions.getByRole('row', { name: /Model L GO/ })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Go for this projected workload' })).toBeVisible()
}
