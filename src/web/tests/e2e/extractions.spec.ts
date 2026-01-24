import { expect, test } from '@playwright/test'

test.describe('Extraction preview', () => {
  test('renders recent extractions and opens document', async ({ page }) => {
    await page.goto('/e2e/extractions')

    await expect(page.getByRole('heading', { name: 'Recent extractions' })).toBeVisible()
    await expect(page.getByText('completed')).toBeVisible()
    await expect(page.getByText('title abstract')).toBeVisible()

    const [popup] = await Promise.all([
      page.waitForEvent('popup'),
      page.getByRole('button', { name: 'Open' }).click(),
    ])

    await expect(popup).toHaveURL(/example\.com\/extractions\/e2e-doc\.txt/)
  })
})
