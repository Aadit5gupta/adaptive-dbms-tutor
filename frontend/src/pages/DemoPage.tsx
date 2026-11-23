import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRef, useState } from 'react'

import { ApiError } from '../api/client'
import { demoRequest } from '../api/demo'
import { TutorPanel } from '../components/TutorPanel'
import type { Activity, AnswerResult, DemoState, Item, Learner, Lesson, QueryResult } from '../api/demo'

export const demoButton = 'rounded-lg bg-green-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-green-800 disabled:cursor-default disabled:opacity-50'
const outlineButton = 'rounded-lg border border-stone-300 bg-white px-4 py-2.5 text-sm font-semibold text-stone-800 hover:border-green-700 disabled:opacity-50'
const card = 'rounded-2xl border border-stone-200 bg-white p-5 sm:p-7'
const labels: Record<Activity, string> = {
  diagnostic: 'Start diagnostic',
  practice: 'Start practice',
  checkpoint: 'Start checkpoints',
  sql: 'Open SQL exercise',
}
const topics: Record<string, string> = {
  'relational.keys': 'Relational keys',
  'sql.joins': 'SQL joins',
}

function ErrorMessage({ error }: { error: Error | null }) {
  return error && <p role="alert" className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-900">{error.message}</p>
}

function ResultGrid({ result }: { result: QueryResult }) {
  return (
    <div className="mt-4 overflow-auto">
      <table className="w-full border-collapse text-left text-sm">
        <caption className="pb-2 text-left font-medium">Preview result</caption>
        <thead className="bg-stone-100">
          <tr>{result.columns.map((column, index) => <th key={index} scope="col" className="p-2">{column}</th>)}</tr>
        </thead>
        <tbody>
          {result.rows.map((row, index) => <tr key={index} className="border-b border-stone-200">
            {row.map((cell, col) => <td className="p-2" key={col}>{cell ?? 'NULL'}</td>)}
          </tr>)}
        </tbody>
      </table>
      {result.rows.length === 0 && <p className="mt-2 text-sm text-stone-600">No rows returned.</p>}
    </div>
  )
}

function ActivityForm({ learner, sessionId, item, onAnswer }: {
  learner: Learner
  sessionId: string
  item: Item
  onAnswer: (result: AnswerResult) => Promise<void>
}) {
  const [choice, setChoice] = useState<number | null>(null)
  const [sql, setSql] = useState('')
  const key = useRef({ payload: '', id: '' })
  const isSql = item.options.length === 0
  const route = `/sessions/${sessionId}`
  const preview = useMutation({
    mutationFn: (query: string) => demoRequest<QueryResult>(learner, route + '/sql/run', { body: { item_id: item.item_id, query } }),
  })
  const submit = useMutation({
    mutationFn: () => {
      const body = isSql
        ? { item_id: item.item_id, query: sql }
        : { item_id: item.item_id, option_index: choice }
      const payload = JSON.stringify(body)
      if (key.current.payload !== payload) key.current = { payload, id: crypto.randomUUID() }
      return demoRequest<AnswerResult>(learner, route + (isSql ? '/sql/submit' : '/answer'), { body, key: key.current.id })
    },
    onSuccess: onAnswer,
  })
  const busy = submit.isPending || preview.isPending
  const filled = isSql ? Boolean(sql.trim()) : choice !== null

  return (
    <form className={card} onSubmit={(event) => { event.preventDefault(); if (filled && !busy) submit.mutate() }}>
      <h2 className="mb-4 text-xl font-semibold">{isSql ? 'SQL exercise' : 'Current question'}</h2>
      <p className="whitespace-pre-wrap leading-7 text-stone-700">{item.stem}</p>
      {isSql
        ? <div className="mt-4">
            <label htmlFor="sql-query" className="mb-2 block text-sm font-medium">Your SQLite query</label>
            <textarea id="sql-query" value={sql} maxLength={8192} rows={6}
              onChange={(event) => { setSql(event.target.value); preview.reset() }} spellCheck={false}
              className="w-full rounded-lg border border-stone-300 bg-stone-950 p-3 font-mono text-sm text-green-100"
            />
          </div>
        : <fieldset className="mt-4 grid gap-2">
            <legend className="mb-2 text-sm font-medium text-stone-700">Choose one answer</legend>
            {item.options.map((option, index) => (
              <label key={index} className="flex cursor-pointer items-start gap-3 rounded-lg border border-stone-200 p-3 has-checked:border-green-700 has-checked:bg-green-50">
                <input className="mt-1 accent-green-800" type="radio" name="answer" value={index}
                  checked={choice === index} onChange={() => setChoice(index)} />{option}
              </label>
            ))}
          </fieldset>}
      <div className="mt-5 flex flex-wrap gap-3">
        {isSql && <button type="button" className={outlineButton} disabled={!filled || busy} onClick={() => preview.mutate(sql)}>
          {preview.isPending ? 'Running…' : 'Run preview'}
        </button>}
        <button className={demoButton} disabled={!filled || busy}>{submit.isPending ? 'Submitting…' : 'Submit answer'}</button>
      </div>
      <ErrorMessage error={submit.error ?? preview.error} />
      {preview.data && <ResultGrid result={preview.data} />}
    </form>
  )
}

function LearnerPanel({ learner }: { learner: Learner }) {
  const client = useQueryClient()
  const [feedback, setFeedback] = useState<AnswerResult | null>(null)
  const [lessonOpen, setLessonOpen] = useState(false)
  const stateKey = ['demo', learner]
  const query = useQuery({ queryKey: stateKey, queryFn: () => demoRequest<DemoState>(learner), retry: false })
  const ref = query.data?.recommendation?.lesson_ref
  const lesson = useQuery({
    queryKey: ['demo-lesson', learner, ref],
    queryFn: () => demoRequest<Lesson>(learner, '/lesson'),
    enabled: Boolean(lessonOpen && ref),
    retry: false,
  })
  const start = useMutation({
    mutationFn: (activity: Activity) => demoRequest(learner, '/sessions', { body: { activity } }),
    onSuccess: async () => {
      setFeedback(null)
      await client.invalidateQueries({ queryKey: stateKey })
    },
  })

  if (query.isPending) return <p className="mt-6" role="status">Loading learner…</p>
  if (query.error instanceof ApiError && query.error.status === 404) {
    return <p className={`${card} mt-6`}>The local demo is disabled. See the README for setup.</p>
  }
  if (query.isError) return <ErrorMessage error={query.error} />

  const state = query.data
  const item = state.session?.items[0]
  return (
    <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(16rem,0.65fr)]">
      <div className="grid content-start gap-4">
        {feedback && <section className={card} aria-live="polite">
          <h2 className="text-lg font-semibold">{feedback.correct ? 'Correct' : 'Keep practicing'}</h2>
          <p className="mt-2 leading-7">{feedback.explanation}</p>
        </section>}
        {state.session && item ? (
          <ActivityForm key={item.item_id} learner={learner} sessionId={state.session.session_id} item={item}
            onAnswer={async (result) => {
              setFeedback(result)
              await client.invalidateQueries({ queryKey: stateKey })
            }} />
        ) : (
          <section className={card}>
            <h2 className="text-xl font-semibold">{topics[state.topic] ?? state.topic}</h2>
            {state.activities.length === 0 ? (
              <p className="mt-3 text-stone-600">No reviewed activities are available yet.</p>
            ) : (
              <div className="mt-4 flex flex-wrap gap-2">
                {state.activities.map((activity) => (
                  <button key={activity} disabled={start.isPending} className={outlineButton} onClick={() => start.mutate(activity)}>
                    {labels[activity]}
                  </button>
                ))}
              </div>
            )}
            <ErrorMessage error={start.error} />
          </section>
        )}
        {lessonOpen && ref && (
          <section className={card}>
            {lesson.isPending && <p role="status">Loading lesson…</p>}
            <ErrorMessage error={lesson.error} />
            {lesson.data && <>
              <h2 className="text-xl font-semibold">{lesson.data.title}</h2>
              <p className="mt-4 whitespace-pre-wrap leading-7 text-stone-700">{lesson.data.body}</p>
              <a href={lesson.data.source_url} className="mt-4 inline-block text-sm text-green-800 underline">Lesson reference</a>
            </>}
          </section>
        )}
        {lessonOpen && ref && <TutorPanel topic={state.topic} />}
      </div>
      <aside className="grid content-start gap-4">
        <section className={card}>
          <h2 className="text-lg font-semibold">Next step</h2>
          <p className="mt-2 leading-7 text-stone-600">{state.recommendation?.reason ?? 'Complete an activity to get a recommendation.'}</p>
          {ref && <button className={`mt-4 ${demoButton}`} onClick={() => setLessonOpen(!lessonOpen)}>
            {lessonOpen ? 'Close lesson' : 'Open lesson'}
          </button>}
        </section>
        <section className={card}>
          <h2 className="text-lg font-semibold">Learning progress</h2>
          {state.progress.length === 0 && <p className="mt-2 text-stone-600">No answers submitted yet.</p>}
          {state.progress.map((row) => (
            <div key={row.topic} className="mt-3">
              <p className="text-sm font-medium">{topics[row.topic] ?? row.topic}</p>
              <p className="text-sm text-stone-600">Mastery score {Math.round(row.score * 100)}% · {row.confidence} confidence · {row.attempts} attempts</p>
            </div>
          ))}
          {state.hypotheses.map((row) => (
            <p key={row.code} className="mt-3 border-t border-stone-200 pt-3 text-sm text-stone-700">
              {row.code} · {row.state} · {row.evidence_count} distinct signals
            </p>
          ))}
        </section>
      </aside>
    </div>
  )
}

export function DemoPage() {
  const [learner, setLearner] = useState<Learner>('a')
  return (
    <>
      <h1>Learner demo</h1>
      <p className="mt-3 text-stone-600">Compare two synthetic learners in the dedicated demo database.</p>
      <div aria-label="Choose learner" className="mt-5 flex gap-3" role="group">
        {(['a', 'b'] as const).map((id) => (
          <button key={id} aria-pressed={learner === id} className={learner === id ? demoButton : outlineButton} onClick={() => setLearner(id)}>
            Learner {id.toUpperCase()}
          </button>
        ))}
      </div>
      <LearnerPanel key={learner} learner={learner} />
    </>
  )
}
