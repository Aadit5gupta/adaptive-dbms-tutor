import { expect, test } from '@playwright/test'

test.skip(process.env.DBMS_TEST_PROGRESSION !== '1', 'Requires isolated synthetic difficulty coverage')

test('an improving learner uses actual recommendations from easy through hard and recovers after an error', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Create an account' }).click()
  await page.getByLabel('Email', { exact: true }).fill('tier-trajectory@example.com')
  await page.getByLabel('Password', { exact: true }).fill('synthetic tier trajectory passphrase')
  await page.getByRole('button', { name: 'Create account', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()

  async function submit(tier: string, index: number, correct: boolean) {
    const question = page.getByRole('heading', { name: `Synthetic progression ${tier} item ${index}`, exact: true })
    await expect(question).toBeVisible()
    await page.getByRole('radio', { name: correct ? 'A' : 'B', exact: true }).check()
    await page.getByRole('button', { name: 'Submit answer' }).click()
    await expect(question).toBeHidden()
    await expect(page.getByRole('heading', { name: correct ? 'Correct' : 'Review this idea', exact: true })).toBeVisible()
  }

  async function continueTo(tier: string) {
    await page.getByRole('link', { name: 'Dashboard', exact: true }).click()
    const recommendation = page.getByRole('link', { name: 'Open recommended activity' })
    await expect(recommendation).toHaveAttribute('href', new RegExp(`difficulty=${tier}&fresh=1$`))
    await recommendation.click()
    await page.getByRole('button', { name: 'Start or resume practice' }).click()
    await expect(page.getByText(`· ${tier}`)).toBeVisible()
  }

  await page.goto('/practice?topic=er.entities&difficulty=easy')
  await page.getByRole('button', { name: 'Start or resume practice' }).click()
  await submit('easy', 0, false)
  await submit('easy', 1, true)
  await submit('easy', 2, false)
  await submit('easy', 3, true)
  await continueTo('medium')
  await submit('medium', 0, true)
  await submit('medium', 1, true)
  await continueTo('hard')
  await page.reload()
  await submit('hard', 0, false)
  await continueTo('medium')
  await submit('medium', 2, true)
  await submit('medium', 3, true)
  await continueTo('hard')
  await submit('hard', 1, true)
  await submit('hard', 2, true)
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click()
  await expect(page.getByText(/Your independent work supports moving on to Relationships and cardinality/)).toBeVisible()
  await page.getByRole('link', { name: 'Open recommended activity' }).click()
  await expect(page.getByRole('heading', { name: 'Read relationship cardinality in both directions' })).toBeVisible()
})
