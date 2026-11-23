import { SQLite, sql } from '@codemirror/lang-sql'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import CodeMirror, { EditorView } from '@uiw/react-codemirror'
import { useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router'

import { request } from '../api/client'
import type { AnswerResult, QueryResult } from '../api/demo'
import { mutate, type FixtureTable, type Session, type SQLExercise } from '../api/learning'
import { card, Empty, Failure, PageHeading, Pending, primary, secondary } from '../components/layout'
import { TutorPanel } from '../components/TutorPanel'

const extensions = [
  sql({ dialect: SQLite }),
  EditorView.lineWrapping,
  EditorView.contentAttributes.of({ 'aria-label': 'Your SQLite query' }),
]

function ResultTable({ result, label }: { result: QueryResult; label: string }) {
  return <div className="overflow-x-auto">
    <table className="w-full border-collapse text-left text-sm">
      <caption className="pb-2 text-left font-semibold">{label}</caption>
      <thead className="bg-stone-100"><tr>
        {result.columns.map((column, index) => <th key={index} className="p-2" scope="col">{column}</th>)}
      </tr></thead>
      <tbody>{result.rows.map((row, index) => <tr key={index} className="border-b border-stone-100">
        {row.map((cell, col) => <td className="p-2" key={col}>{cell === null ? <em>NULL</em> : cell}</td>)}
      </tr>)}</tbody>
    </table>
    {!result.rows.length && <p className="mt-2 text-sm text-stone-600">No rows returned.</p>}
  </div>
}

function Workbench({ exercise }: { exercise: SQLExercise }) {
  const client = useQueryClient()
  const [query, setQuery] = useState('')
  const [asking, setAsking] = useState(false)
  const route = `/sql/exercises/${encodeURIComponent(exercise.id)}`
  const schema = useQuery({
    queryKey: ['sql-schema', exercise.ref], queryFn: ({ signal }) => request<FixtureTable[]>(route + '/schema', { signal }),
    enabled: exercise.enabled, retry: false,
  })
  const start = useMutation({ mutationFn: () => mutate<Session>(route + '/sessions') })
  const item = start.data?.items[0]
  const key = useRef({ query: '', item: '', key: '' })
  const preview = useMutation({
    mutationFn: () => mutate<QueryResult>(route + '/run', {
      item_id: item?.item_id, session_id: start.data?.session_id, query,
    }),
  })
  const submit = useMutation({
    mutationFn: () => {
      if (key.current.query !== query || key.current.item !== item?.item_id)
        key.current = { query, item: item?.item_id ?? '', key: crypto.randomUUID() }
      return mutate<AnswerResult>(route + '/submit', {
        item_id: item?.item_id, session_id: start.data?.session_id, query,
      }, { key: key.current.key })
    },
    onSuccess: () => void client.invalidateQueries({ queryKey: ['progress'] }),
  })
  const tooLong = new TextEncoder().encode(query).length > 8192
  const busy = preview.isPending || submit.isPending
  return <div className="mt-5 grid gap-4 xl:grid-cols-[minmax(0,1.55fr)_minmax(16rem,1fr)]">
    <section className={card}>
      <p className="text-sm font-medium text-stone-600">SQLite {exercise.minimum_sqlite_version}+ · {exercise.difficulty}</p>
      <p className="mt-2 whitespace-pre-wrap leading-7">{exercise.prompt}</p>
      {!exercise.enabled ? <Empty>SQL execution is unavailable on this platform.</Empty> : !item ? (
        <button className={`mt-4 ${primary}`} disabled={start.isPending} onClick={() => start.mutate()}>
          {start.isPending ? 'Opening…' : 'Start or resume exercise'}
        </button>
      ) : <>
        <div className="mt-5 overflow-hidden rounded-xl border border-stone-300">
          <CodeMirror value={query} height="185px" theme="dark" extensions={extensions}
            indentWithTab={false} editable={!busy && !submit.isSuccess}
            onChange={(value) => { setQuery(value); preview.reset() }} />
        </div>
        {tooLong && <p role="alert" className="mt-2 text-sm text-red-900">Use a query of at most 8,192 UTF-8 bytes.</p>}
        {submit.isSuccess ? <button className={`mt-4 ${secondary}`} onClick={() => {
          submit.reset()
          preview.reset()
          setAsking(false)
          start.mutate()
        }}>Try another attempt</button> : <div className="mt-4 flex flex-wrap gap-3">
          <button className={secondary} disabled={!query.trim() || busy || tooLong} onClick={() => preview.mutate()}>
            {preview.isPending ? 'Running…' : 'Run preview'}
          </button>
          <button className={primary} disabled={!query.trim() || busy || tooLong} onClick={() => submit.mutate()}>
            {submit.isPending ? 'Grading…' : 'Submit for grading'}
          </button>
        </div>}
      </>}
      <Failure error={start.error ?? preview.error ?? submit.error} />
      {preview.data && <div className="mt-5"><ResultTable result={preview.data} label="Preview result" /></div>}
      {submit.data && <div aria-live="polite" className="mt-5 rounded-lg bg-green-50 p-4">
        <h2 className="font-semibold">{submit.data.correct ? 'Correct' : 'Review your query'}</h2>
        <p className="mt-2">{submit.data.explanation}</p>
        {!submit.data.correct && <button className={`mt-3 ${secondary}`} onClick={() => setAsking(!asking)}>
          {asking ? 'Close tutor' : 'Ask about this mistake'}
        </button>}
      </div>}
    </section>
    <section className={card}>
      <h2 className="text-lg font-semibold">Visible fixture</h2>
      {exercise.enabled && schema.isPending && <Pending>Loading example rows…</Pending>}
      {schema.data?.map((table) => <div className="mt-4" key={table.name}><ResultTable result={table.data} label={table.name} /></div>)}
      <Failure error={schema.error} retry={() => void schema.refetch()} />
    </section>
    {asking && submit.data && <TutorPanel topic={exercise.topic_id} sqlAttempt={submit.data.attempt_id} />}
  </div>
}

export function SqlPage() {
  const [params, setParams] = useSearchParams()
  const exercises = useQuery({ queryKey: ['sql-exercises'], queryFn: ({ signal }) => request<SQLExercise[]>('/sql/exercises', { signal }), retry: false })
  const selected = exercises.data?.find((exercise) => exercise.id === params.get('exercise'))
    ?? exercises.data?.find((exercise) => exercise.topic_id === params.get('topic')) ?? exercises.data?.[0]
  return <>
    <PageHeading title="SQL Lab">Run a preview on the visible fixture. Submit to grade against additional datasets and update your progress.</PageHeading>
    {exercises.isPending && <Pending>Loading reviewed exercises…</Pending>}
    <Failure error={exercises.error} retry={() => void exercises.refetch()} />
    {exercises.data && !selected && <Empty action={{ label: 'Browse curriculum', to: '/learn' }}>No reviewed SQL exercises are available yet.</Empty>}
    {selected && <>
      <nav aria-label="Choose SQL exercise" className="mt-6 flex flex-wrap gap-2">
        {exercises.data?.map((exercise, index) => <button className={exercise.id === selected.id ? primary : secondary}
          aria-pressed={exercise.id === selected.id} key={exercise.id}
          onClick={() => setParams({ exercise: exercise.id })}>Exercise {index + 1}</button>)}
        <Link className={secondary} to="/progress">View SQL progress</Link>
      </nav>
      <Workbench key={selected.ref} exercise={selected} />
    </>}
  </>
}
