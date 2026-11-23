import { request } from './client'

export type Learner = 'a' | 'b'
export type Activity = 'diagnostic' | 'practice' | 'checkpoint' | 'sql'

export interface Item {
  item_id: string
  question_ref: string
  subtopic_id: string
  stem: string
  options: string[]
}

export interface DemoState {
  topic: string
  activities: Activity[]
  recommendation: { reason: string; lesson_ref: string | null } | null
  progress: { topic: string; score: number; confidence: string; attempts: number }[]
  hypotheses: { code: string; state: string; evidence_count: number }[]
  session: { session_id: string; items: Item[] } | null
  activity: Activity | null
}

export interface Lesson {
  title: string
  body: string
  source_url: string
  review_status: 'ai_verified' | 'author_verified' | 'independent_verified'
}

export interface AnswerResult {
  attempt_id: string
  correct: boolean
  explanation: string
  mastery: { before: number; after: number; confidence: string } | null
}

export interface QueryResult {
  columns: string[]
  rows: (string | number | null)[][]
}

export async function demoRequest<T>(
  learner: Learner,
  path = '',
  params?: { body: object; key?: string },
): Promise<T> {
  const headers = new Headers()
  if (params) headers.set('Content-Type', 'application/json')
  if (params?.key) headers.set('Idempotency-Key', params.key)

  return request<T>(`/demo/${learner}${path}`, {
    method: params ? 'POST' : 'GET',
    headers,
    body: params ? JSON.stringify(params.body) : undefined,
  })
}
