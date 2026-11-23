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
}

export interface AnswerResult {
  correct: boolean
  explanation: string
  mastery: { before: number; after: number; confidence: string } | null
}

export interface QueryResult {
  columns: string[]
  rows: (string | number | null)[][]
}

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export async function demoRequest<T>(
  learner: Learner,
  path = '',
  params?: { body: object; key?: string },
): Promise<T> {
  const headers = new Headers()
  if (params) headers.set('Content-Type', 'application/json')
  if (params?.key) headers.set('Idempotency-Key', params.key)

  const response = await fetch(`/api/v1/demo/${learner}${path}`, {
    method: params ? 'POST' : 'GET',
    headers,
    body: params ? JSON.stringify(params.body) : undefined,
  })
  if (!response.ok) {
    let detail = 'The backend request failed. Retry in a moment.'
    try {
      const error: unknown = await response.json()
      if (typeof error === 'object' && error !== null && 'detail' in error
          && typeof error.detail === 'string' && response.status !== 404) {
        detail = error.detail
      }
    } catch {
      // Transport or framework errors can return a response without a JSON body.
    }
    throw new ApiError(detail, response.status)
  }
  return response.json() as Promise<T>
}
