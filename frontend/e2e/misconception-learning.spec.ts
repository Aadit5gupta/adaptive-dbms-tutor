import { expect, test, type Page } from '@playwright/test'

import type { Item } from '../src/api/demo'
import type { AssessmentResult, Progress, Session } from '../src/api/learning'

test.skip(process.env.DBMS_TEST_AUTHORED !== '1', 'Requires published learner content')

type Grade = AssessmentResult & {
  next_action: (NonNullable<AssessmentResult['next_action']> & { reason_code: string }) | null
}

const solutions: Record<string, number> = {
  q_topic_intro_relational_relations: 2,
  q_keys_detector_members: 2,
  q_lean_keys_candidate_count: 3,
  q_lean_keys_composite: 2,
  q_lean_keys_fk_target: 0,
  q_lean_keys_migrate_children: 1,
  q_practice_keys_missing: 1,
  q_lean_keys_alternate_parent: 2,
  q_lean_keys_cascaded_code: 0,
  q_lean_keys_superkey: 1,
  q_lean_keys_composite_fk_pair: 3,
  q_lean_keys_composite_null_rule: 2,
  q_lean_keys_composite_unique_scope: 1,
  q_keys_checkpoint_badges: 3,
  q_keys_checkpoint_rooms: 1,
  q_join_detector_orders: 2,
  q_join_practice_duplicate_matches: 2,
  q_join_practice_preservation_claim: 3,
  q_join_checkpoint_households: 0,
  q_join_checkpoint_teams: 3,
  q_lean_norm_detector_branch: 2,
  q_norm_practice_anomaly_update: 2,
  q_norm_practice_atomic_cell: 1,
  q_norm_practice_calibration_confusion: 2,
  q_lean_norm_checkpoint_depot: 3,
  q_lean_norm_checkpoint_order: 0,
  q_lean_select_null_filter: 2,
  q_progress_null_zero_or_missing: 2,
  q_progress_null_or_unknown: 2,
}

async function register(page: Page, id: string) {
  await page.goto('/')
  await page.getByRole('button', { name: 'Create an account' }).click()
  await page.getByLabel('Email', { exact: true }).fill(`misconception-${id}@example.com`)
  await page.getByLabel('Password', { exact: true }).fill(`learner test passphrase ${id}`)
  await page.getByRole('button', { name: 'Create account', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
}

function studio(page: Page, journey: string) {
  const log: object[] = []
  let current: Session | undefined
  function safeItem(item: Item) {
    expect(Object.keys(item).sort()).toEqual(['difficulty', 'item_id', 'options', 'question_ref', 'stem', 'subtopic_id'])
    expect(item.options).toHaveLength(4)
    expect(item.options.every((option) => typeof option === 'string')).toBeTruthy()
  }
  return {
    item: () => current?.items[0],
    async start(checkpoint = false) {
      const endpoint = checkpoint ? '/api/v1/practice/checkpoints' : '/api/v1/practice/sessions'
      const started = page.waitForResponse((response) =>
        new URL(response.url()).pathname === endpoint && response.request().method() === 'POST')
      await page.getByRole('button', { name: checkpoint ? 'Start checkpoints' : 'Start or resume practice' }).click()
      const response = await started
      expect(response.ok()).toBeTruthy()
      current = await response.json() as Session
      expect(current.items).toHaveLength(1)
      safeItem(current.items[0])
      log.push({ activity: checkpoint ? 'checkpoint' : 'practice', total: current.total,
        remaining: current.remaining, first: current.items[0].question_ref })
      return current
    },
    async answer(item: Item, choice = solutions[item.question_ref.split('@')[0]], correct = true) {
      expect(choice).toBeDefined()
      const question = page.getByRole('heading', { name: item.stem, exact: true })
      await expect(question).toBeVisible()
      await expect(page.getByText(`· ${item.difficulty}`, { exact: true })).toBeVisible()
      const path = `/api/v1/practice/sessions/${current?.session_id}`
      const graded = page.waitForResponse((response) => new URL(response.url()).pathname === path + '/answer')
      const advanced = page.waitForResponse(async (response) =>
        new URL(response.url()).pathname === path && response.request().method() === 'GET' &&
        response.ok() && (await response.json() as Session).items[0]?.item_id !== item.item_id)
      await page.getByRole('radio', { name: item.options[choice], exact: true }).check()
      await page.getByRole('button', { name: 'Submit answer' }).click()
      const response = await graded
      expect(response.ok()).toBeTruthy()
      const result: Grade = await response.json()
      expect(result.correct).toBe(correct)
      current = await (await advanced).json() as Session
      if (current.items[0]) safeItem(current.items[0])
      await expect(question).toBeHidden()
      await expect(page.getByRole('heading', { name: correct ? 'Correct' : 'Review this idea', exact: true })).toBeVisible()
      log.push({ ref: item.question_ref, tier: item.difficulty, choice, selected: item.options[choice], correct,
        mastery: result.mastery, misconception: result.misconception, next: result.next_action,
        next_item: current.items[0]?.question_ref })
      return result
    },
    async follow(expected?: RegExp) {
      await page.getByRole('link', { name: 'Dashboard', exact: true }).click()
      const next = page.getByRole('link', { name: 'Open recommended activity' })
      if (expected) await expect(next).toHaveAttribute('href', expected)
      const href = await next.getAttribute('href')
      expect(href).toBeTruthy()
      await next.click()
      log.push({ followed: href })
      return href
    },
    async progress(topic: string) {
      const response = page.waitForResponse((result) => new URL(result.url()).pathname === '/api/v1/progress')
      await page.getByRole('link', { name: 'Progress', exact: true }).click()
      const observed: Progress = await (await response).json()
      log.push({ progress: observed.topics.find((entry) => entry.topic === topic) })
      return observed
    },
    async evidence() {
      const body = JSON.stringify({ journey, log })
      await test.info().attach(`${journey}.json`, { body, contentType: 'application/json' })
      console.log(`LEARNER_EVIDENCE ${body}`)
    },
  }
}

async function fromLesson(page: Page, domain: string, lesson: string) {
  await page.getByRole('link', { name: 'Learn', exact: true }).click()
  await page.getByText(domain, { exact: true }).click()
  await page.getByRole('link', { name: lesson, exact: true }).click()
  await expect(page.getByRole('heading', { name: lesson, exact: true })).toBeVisible()
  await page.getByRole('link', { name: 'Practice this topic' }).click()
  await expect(page.getByRole('combobox', { name: 'Difficulty' })).toHaveValue('easy')
}

const patterns = [
  {
    learner: 'keys', code: 'KEYS-02', topic: 'relational.keys', domain: 'Relational model',
    lesson: 'Test whether a key is minimal', remediation: 'One parent, many child rows', lessonRef: 'lesson_fk_multiplicity',
    detectors: { 'q_keys_detector_members@1': 3, 'q_lean_keys_migrate_children@1': 0 },
    checkpoints: ['q_keys_checkpoint_badges@1', 'q_keys_checkpoint_rooms@1'],
  },
  {
    learner: 'joins', code: 'SQL-JOIN-01', topic: 'sql.joins', domain: 'SQL',
    lesson: 'Keep unmatched rows with LEFT JOIN', remediation: 'Keep unmatched rows with LEFT JOIN', lessonRef: 'lesson_join_unmatched',
    detectors: { 'q_join_detector_orders@1': 0, 'q_join_practice_preservation_claim@1': 0 },
    checkpoints: ['q_join_checkpoint_households@1', 'q_join_checkpoint_teams@1'],
  },
  {
    learner: 'normal-forms', code: 'NORM-03', topic: 'normalization.normal_forms', domain: 'Functional dependencies and normalization',
    lesson: 'Separate partial dependencies from dependency chains', remediation: 'Separate partial dependencies from dependency chains',
    lessonRef: 'lesson_dependency_chain',
    detectors: { 'q_lean_norm_detector_branch@1': 0, 'q_norm_practice_calibration_confusion@1': 0 },
    checkpoints: ['q_lean_norm_checkpoint_depot@1', 'q_lean_norm_checkpoint_order@1'],
  },
] satisfies {
  learner: string; code: string; topic: string; domain: string; lesson: string; remediation: string
  lessonRef: string; detectors: Partial<Record<string, number>>; checkpoints: string[]
}[]

for (const pattern of patterns) {
  test(`${pattern.learner} misconception activates and resolves from ordinary lesson practice`, async ({ page }) => {
    await register(page, pattern.learner)
    const learner = studio(page, pattern.learner)
    await fromLesson(page, pattern.domain, pattern.lesson)
    await learner.start()
    let signals = 0
    for (let item = learner.item(); item; item = learner.item()) {
      expect(item.subtopic_id).toBe(pattern.topic)
      expect(item.difficulty).toBe('easy')
      expect(pattern.checkpoints).not.toContain(item.question_ref)
      const miss = (pattern.detectors as Partial<Record<string, number>>)[item.question_ref]
      const result = await learner.answer(item, miss, miss === undefined)
      if (miss === undefined) {
        expect(result.misconception).toBeNull()
        continue
      }
      signals += 1
      const state = signals === 1 ? 'possible' : 'active'
      expect(result.misconception).toMatchObject({ code: pattern.code, state, evidence_count: signals })
      await expect(page.getByText(signals === 1 ? 'Possible misconception' : 'Active misconception', { exact: true })).toBeVisible()
      if (signals === 1) {
        await expect(page.getByRole('link', { name: 'Open remediation lesson' })).toHaveCount(0)
      } else {
        expect(result.next_action).toMatchObject({ action_type: 'MISCONCEPTION_REMEDIATION' })
        break
      }
    }
    expect(signals).toBe(2)
    expect(await learner.follow()).toContain(`/learn/${pattern.lessonRef}@1?checkpoints=1`)
    await expect(page.getByRole('heading', { name: pattern.remediation, exact: true })).toBeVisible()
    await page.getByRole('link', { name: 'Open checkpoints' }).click()
    const checkpoints = await learner.start(true)
    expect(checkpoints.total).toBe(2)
    expect(learner.item()?.question_ref).toBe(pattern.checkpoints[0])
    const first = await learner.answer(learner.item()!)
    expect(first.misconception).toMatchObject({ state: 'improving', evidence_count: 2 })
    await page.reload()
    expect(learner.item()?.question_ref).toBe(pattern.checkpoints[1])
    const last = await learner.answer(learner.item()!)
    expect(last.misconception).toMatchObject({ code: pattern.code, state: 'resolved', evidence_count: 2 })
    expect(last.next_action?.action_type).not.toBe('MISCONCEPTION_REMEDIATION')
    await learner.progress(pattern.topic)
    await expect(page.getByText('Misconception resolved', { exact: true })).toBeVisible()
    expect(await learner.follow()).toBeTruthy()
    await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible()
    await learner.evidence()
  })
}

test('published keys progress through easy, medium, hard, recovery and advancement', async ({ page }) => {
  await register(page, 'advancing')
  const learner = studio(page, 'advancing')
  await fromLesson(page, 'Relational model', 'Read a relation and its constraints')
  const prerequisite = (await learner.start()).items[0]
  expect(prerequisite.question_ref).toBe('q_topic_intro_relational_relations@1')
  await learner.answer(prerequisite)

  await fromLesson(page, 'Relational model', 'Test whether a key is minimal')
  await learner.start()
  for (let i = 0; i < 4; i++) {
    const result = await learner.answer(learner.item()!)
    expect(result.misconception).toBeNull()
  }
  expect(await learner.follow(/difficulty=medium&fresh=1$/)).toMatch(/difficulty=medium&fresh=1$/)
  const medium = await learner.start()
  for (let i = 0; i < 2; i++) {
    await learner.answer(learner.item()!)
  }
  const remainingMedium = learner.item()?.question_ref
  expect(await learner.follow(/difficulty=hard&fresh=1$/)).toMatch(/difficulty=hard&fresh=1$/)
  const hard = await learner.start()
  expect(hard.total).toBe(3)
  const miss = await learner.answer(learner.item()!, 0, false)
  const remainingHard = learner.item()?.question_ref
  expect(miss.mastery?.confidence).toBe('supported')
  expect(miss.misconception).toBeNull()
  expect(await learner.follow(/difficulty=medium&fresh=1$/)).toMatch(/difficulty=medium&fresh=1$/)
  expect((await learner.start()).session_id).toBe(medium.session_id)
  expect(learner.item()?.question_ref).toBe(remainingMedium)
  await learner.answer(learner.item()!)
  expect(await learner.follow(/difficulty=hard&fresh=1$/)).toMatch(/difficulty=hard&fresh=1$/)
  const remaining = await learner.start()
  expect(remaining.session_id).toBe(hard.session_id)
  expect(remaining.remaining).toBe(2)
  expect(learner.item()?.question_ref).toBe(remainingHard)
  await learner.answer(learner.item()!)
  const last = await learner.answer(learner.item()!)
  expect(last.next_action).toMatchObject({ action_type: 'LEARN', reason_code: 'ADVANCE_TOPIC' })
  await expect(page.getByRole('heading', { name: 'Session complete' })).toBeVisible()
  expect(await learner.follow(/^\/learn\//)).toMatch(/^\/learn\//)
  await expect(page.getByRole('heading', { name: 'Identify entities and their attributes' })).toBeVisible()
  await learner.progress('relational.keys')
  await expect(page.getByText('No misconception patterns detected yet.')).toBeVisible()
  await learner.evidence()
})

test('unrelated wrong answers and a late mapped replay do not diagnose', async ({ page }) => {
  await register(page, 'unrelated')
  const learner = studio(page, 'unrelated')
  await fromLesson(page, 'Relational model', 'Test whether a key is minimal')
  const practice = await learner.start()
  const expected = [
    'q_keys_detector_members@1', 'q_lean_keys_candidate_count@1', 'q_lean_keys_composite@1',
    'q_lean_keys_fk_target@1', 'q_lean_keys_migrate_children@1',
  ]
  expect(practice.total).toBe(expected.length)
  const unrelated = [0, 2, 1, 2, 2]
  for (const [i, ref] of expected.entries()) {
    expect(learner.item()?.question_ref).toBe(ref)
    const result = await learner.answer(learner.item()!, unrelated[i], false)
    expect(result.misconception).toBeNull()
  }
  await page.getByRole('button', { name: 'Choose another activity' }).click()
  await learner.start()
  expect(learner.item()?.question_ref).toBe('q_practice_keys_missing@1')
  await learner.answer(learner.item()!)
  expect(learner.item()?.question_ref).toBe('q_keys_detector_members@1')
  const replay = await learner.answer(learner.item()!, 3, false)
  expect(replay.misconception).toBeNull()
  expect(replay.mastery?.after).toBe(replay.mastery?.before)
  await learner.progress('relational.keys')
  await expect(page.getByText('No misconception patterns detected yet.')).toBeVisible()
  await learner.evidence()
})

test('NULL practice exhaustion opens an eligible alternate activity', async ({ page }) => {
  await register(page, 'exhaustion')
  const learner = studio(page, 'exhaustion')
  await page.getByRole('link', { name: 'Learn', exact: true }).click()
  await page.getByText('SQL', { exact: true }).click()
  const nulls = page.locator('section').filter({ has: page.getByRole('heading', { name: 'NULL and three-valued logic', exact: true }) })
  await nulls.getByRole('link', { name: 'Practice', exact: true }).click()
  await page.getByRole('combobox', { name: 'Difficulty' }).selectOption({ label: 'Any difficulty' })
  const practice = await learner.start()
  expect(practice.total).toBe(3)
  await expect(page.getByText('This session has 3 eligible questions for your selection.')).toBeVisible()
  for (let item = learner.item(); item; item = learner.item()) {
    expect(item.subtopic_id).toBe('sql.null')
    await learner.answer(item)
  }
  await expect(page.getByRole('heading', { name: 'Session complete' })).toBeVisible()
  expect(await learner.follow()).toMatch(/^\/sql\?exercise=sql_unassigned_orders$|^\/learn\//)
  await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible()
  await learner.progress('sql.null')
  await learner.evidence()
})
