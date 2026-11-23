import { request } from './client'
import type { Item, QueryResult } from './demo'

export type Goal = 'exam' | 'placements' | 'understanding'
export type Level = 'beginner' | 'some_experience' | 'advanced'

export interface Preferences {
  goal: Goal | null
  level: Level | null
  daily_minutes: number | null
}

export interface Account {
  email: string
  created_at: number
  preferences: Preferences
}

export interface Domain {
  id: string
  title: string
  topics: Topic[]
}

export interface Topic {
  id: string
  title: string
  prerequisites: string[]
  lessons: { ref: string; title: string }[]
  diagnostic: boolean
  practice: boolean
}

export interface LessonDetail {
  ref: string
  title: string
  body: string
  source_url: string
  topic_id: string
}

export interface Recommendation {
  action_type: string
  subtopic_id: string
  reason: string
  lesson_ref: string | null
  difficulty: string | null
}

export interface Progress {
  domains: { domain: string; assessed_topics: number; listed_topics: number; score: number | null }[]
  topics: {
    topic: string
    title: string
    score: number | null
    confidence: string
    distinct: number
    attempts: number
    review_due: boolean
  }[]
  recent: { topic: string; context: string; correct: boolean; created_at: number; mastery_after: number | null }[]
  recommendation: Recommendation | null
}

export interface Hypothesis {
  code: string
  title: string
  state: string
  evidence_count: number
}

export interface Session {
  session_id: string
  items: Item[]
  total: number
  remaining: number
}

export interface SQLExercise {
  id: string
  ref: string
  topic_id: string
  prompt: string
  difficulty: string
  dialect: string
  minimum_sqlite_version: string
  enabled: boolean
}

export interface FixtureTable {
  name: string
  data: QueryResult
}

export function mutate<T>(path: string, body?: object, options?: { method?: 'PATCH' | 'DELETE' | 'POST'; key?: string }) {
  const headers = new Headers()
  if (body !== undefined) headers.set('Content-Type', 'application/json')
  if (options?.key) headers.set('Idempotency-Key', options.key)
  return request<T>(path, { method: options?.method ?? 'POST', headers, body: body === undefined ? undefined : JSON.stringify(body) })
}
