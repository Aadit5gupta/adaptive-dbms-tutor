import { expect, test, type Page } from '@playwright/test'

test.skip(process.env.DBMS_TEST_AUTHORED !== '1', 'Requires the original reviewed lesson and question bank')

async function answer(page: Page, choice: string | RegExp) {
  await page.getByRole('radio', { name: choice }).check()
  await page.getByRole('button', { name: 'Submit answer' }).click()
}

test('original questions, lessons and SQL take both demo learners through remediation', async ({ page }) => {
  await page.goto('/demo')
  await page.getByRole('button', { name: 'Start diagnostic' }).click()
  await answer(page, /Only one ticket can reference account 9/)
  await expect(page.getByText('KEYS-02 · possible · 1 distinct signals')).toBeVisible()
  await page.getByRole('button', { name: 'Start practice' }).click()
  await answer(page, /violate the foreign key because club 22 appears twice/)
  await expect(page.getByText('KEYS-02 · active · 2 distinct signals')).toBeVisible()
  await page.reload()
  await expect(page.getByText('KEYS-02 · active · 2 distinct signals')).toBeVisible()
  await page.getByRole('button', { name: 'Open lesson' }).click()
  await expect(page.getByRole('heading', { name: 'One parent, many child rows' })).toBeVisible()
  await expect(page.getByRole('table')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Lesson reference' })).toHaveAttribute('href', /07-constraints\/constraints\.html$/)
  await page.getByLabel('Your question').fill('Why can two tickets reference one account with a foreign key?')
  await page.getByRole('button', { name: 'Ask tutor', exact: true }).click()
  await expect(page.getByText(/AI-verified original lesson by/)).toHaveCount(1)
  await page.getByLabel('Follow-up question').fill('What changes when the child column is unique?')
  await page.getByRole('button', { name: 'Send follow-up' }).click()
  await expect(page.getByText('Curated tutor', { exact: true })).toHaveCount(2)
  await page.getByRole('button', { name: 'Start checkpoints' }).click()
  await answer(page, 'The badges with NULL and office 2 are accepted.')
  await expect(page.getByText('KEYS-02 · improving · 2 distinct signals')).toBeVisible()
  await answer(page, 'UNIQUE on Bookings.room_id.')
  await expect(page.getByText('KEYS-02 · resolved · 2 distinct signals')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Start checkpoints' })).toHaveCount(0)

  await page.getByRole('button', { name: 'Learner B' }).click()
  await expect(page.getByText('No answers submitted yet.')).toBeVisible()
  await page.getByRole('button', { name: 'Start diagnostic' }).click()
  await answer(page, 'INNER JOIN Departures on the route ID.')
  await expect(page.getByText('SQL-JOIN-01 · possible · 1 distinct signals')).toBeVisible()
  await page.getByRole('button', { name: 'Start practice' }).click()
  await answer(page, 'One row with null order columns.')
  await expect(page.getByText('SQL-JOIN-01 · active · 2 distinct signals')).toBeVisible()
  await page.getByRole('button', { name: 'Open lesson' }).click()
  await expect(page.getByRole('heading', { name: 'Keep unmatched rows with LEFT JOIN' })).toBeVisible()
  await page.getByRole('button', { name: 'Start checkpoints' }).click()
  await answer(page, 'One household row with NULL meter columns.')
  await expect(page.getByText('SQL-JOIN-01 · improving · 2 distinct signals')).toBeVisible()
  await answer(page, 'Cedar 2, Maple 0.')
  await expect(page.getByText('SQL-JOIN-01 · resolved · 2 distinct signals')).toBeVisible()
  if (process.platform === 'darwin' && process.arch === 'arm64') {
    await page.getByRole('button', { name: 'Open SQL exercise' }).click()
    await page.getByLabel('Your SQLite query').fill(
      'SELECT c.id, c.name, (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id) FROM customers c',
    )
    await page.getByRole('button', { name: 'Run preview' }).click()
    await expect(page.getByRole('table', { name: 'Preview result' })).toBeVisible()
    await page.getByRole('button', { name: 'Submit answer' }).click()
    await expect(page.getByText('The query returned the required results on all grading fixtures.')).toBeVisible()
  }
  await page.goto('/library')
  await expect(page.getByText('0 of 5 indexed')).toBeVisible()
})


test('a narrow lesson scrolls its example table inside the page', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 })
  await page.goto('/')
  await page.getByRole('button', { name: 'Create an account' }).click()
  await page.getByLabel('Email', { exact: true }).fill('mobile-audit@example.com')
  await page.getByLabel('Password', { exact: true }).fill('synthetic lesson passphrase')
  await page.getByRole('button', { name: 'Create account', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
  await page.goto('/learn/lesson_candidate_keys@1')
  await expect(page.getByRole('table', { name: '' })).toBeVisible()
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBe(390)
})
