import { expect, test, type Page } from '@playwright/test'

async function answer(page: Page, choice: 'A' | 'B') {
  await page.getByRole('radio', { name: choice, exact: true }).check()
  await page.getByRole('button', { name: 'Submit answer' }).click()
}

async function activate(page: Page, code: string) {
  await page.getByRole('button', { name: 'Start diagnostic' }).click()
  await answer(page, 'B')
  await expect(page.getByText(`${code} · possible · 1 distinct signals`)).toBeVisible()
  await page.getByRole('button', { name: 'Start practice' }).click()
  await answer(page, 'B')
  await expect(page.getByText(`${code} · active · 2 distinct signals`)).toBeVisible()
}

test('learners diverge, progress survives a refresh, and checkpoints change the next action', async ({ page }) => {
  await page.goto('/demo')
  await activate(page, 'KEYS-02')
  await page.reload()
  await expect(page.getByText('KEYS-02 · active · 2 distinct signals')).toBeVisible()
  await page.getByRole('button', { name: 'Open lesson' }).click()
  await expect(page.getByRole('heading', { name: 'keys', exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Start checkpoints' }).click()
  await answer(page, 'A')
  await expect(page.getByText('KEYS-02 · improving · 2 distinct signals')).toBeVisible()
  await answer(page, 'A')
  await expect(page.getByText('KEYS-02 · resolved · 2 distinct signals')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Start checkpoints' })).toHaveCount(0)

  await page.getByRole('button', { name: 'Learner B' }).click()
  await expect(page.getByText('No answers submitted yet.')).toBeVisible()
  await activate(page, 'SQL-JOIN-01')
  await page.getByRole('button', { name: 'Open lesson' }).click()
  await expect(page.getByRole('heading', { name: 'joins', exact: true })).toBeVisible()

  if (process.platform === 'darwin' && process.arch === 'arm64') {
    await page.getByRole('button', { name: 'Open SQL exercise' }).click()
    await page.getByLabel('Your SQLite query').fill('SELECT n FROM t')
    await page.getByRole('button', { name: 'Run preview' }).click()
    await expect(page.getByRole('table', { name: 'Preview result' })).toBeVisible()
    await page.getByRole('button', { name: 'Submit answer' }).click()
    await expect(page.getByText('The query returned the required results on all grading fixtures.')).toBeVisible()
  }
})

test('demo rejects cross-origin mutations', async ({ request }) => {
  const response = await request.post('/api/v1/demo/a/sessions', {
    data: { activity: 'practice' },
    headers: { Origin: 'https://example.invalid' },
  })
  expect(response.status()).toBe(403)
})

test('library reports searchable sources and an honest empty search', async ({ page }) => {
  await page.goto('/library')
  await expect(page.getByText('0 of 5 indexed')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Database Fundamentals' })).toBeVisible()
  await page.getByRole('searchbox', { name: 'Search passages' }).fill('foreign key')
  await page.getByRole('button', { name: 'Search', exact: true }).click()
  await expect(page.getByText('No matching reviewed passages.')).toBeVisible()
})
