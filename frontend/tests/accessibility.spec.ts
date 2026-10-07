import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'
import path from 'node:path'
import {
  checkGeneratedCustomerFit,
  generatedFixtures,
  modelL,
  uploadGeneratedModels,
} from './support/resilience'

for (const state of [
  'empty',
  'comparison',
  'customer-result',
  'engineering',
  'upload-error',
  'mixed-batch',
]) {
  test(`accessibility: ${state}`, async ({ page }) => {
    await page.goto('/')
    if (['comparison', 'customer-result', 'engineering'].includes(state))
      await uploadGeneratedModels(page)
    if (state === 'customer-result') await checkGeneratedCustomerFit(page)
    if (state === 'engineering') {
      await page.getByLabel('Engineering sweep').selectOption('1')
      await page
        .getByRole('table', { name: 'Engineering configurations' })
        .getByRole('button', { name: 'Row 2', exact: true })
        .click()
      await page.getByText('Analysis limits and assumptions', { exact: true }).click()
      await expect(page.locator('#engineering-detail')).toContainText('Model L')
    }
    if (state === 'upload-error' || state === 'mixed-batch') {
      const bad = path.join(generatedFixtures, 'missing-column.xlsx')
      await page
        .getByLabel('Choose Excel workbooks')
        .setInputFiles(state === 'upload-error' ? bad : [modelL, bad])
      if (state === 'upload-error') await expect(page.getByRole('alert')).toBeVisible()
      else {
        await expect(page.getByRole('region', { name: 'Upload diagnostics' })).toBeVisible()
        await expect(page.getByRole('heading', { name: 'Inspect the projection' })).toBeVisible()
      }
    }
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()
    expect(
      results.violations.map((violation) => ({
        rule: violation.id,
        failures: violation.nodes.map((node) => ({
          target: node.target,
          reason: node.failureSummary,
        })),
      })),
    ).toEqual([])
  })
}
