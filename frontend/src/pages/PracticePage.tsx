import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router'

import { request } from '../api/client'
import type { AnswerResult, Item } from '../api/demo'
import { mutate, type Session } from '../api/learning'
import { card, Empty, Failure, field, PageHeading, Pending, primary, secondary, textLink } from '../components/layout'
import { TutorPanel } from '../components/TutorPanel'
import { useCurriculum } from './DashboardPage'

type Mode = 'practice' | 'diagnostic' | 'checkpoint' | 'review'
const modeNames: Record<Mode, string> = {
  practice: 'Practice', diagnostic: 'Diagnostic', checkpoint: 'Checkpoints', review: 'Revision',
}

function QuestionForm({ item, submit, busy }: { item: Item; submit: (choice: number) => void; busy: boolean }) {
  const [choice, setChoice] = useState<number | null>(null)
  return (
    <form onSubmit={(event) => { event.preventDefault(); if (choice !== null && !busy) submit(choice) }}>
      <h2 className="text-lg font-semibold">{item.stem}</h2>
      <fieldset className="mt-4 grid gap-2">
        <legend className="mb-2 text-sm text-stone-600">Choose one answer</legend>
        {item.options.map((option, index) => <label key={index} className="flex cursor-pointer gap-3 rounded-lg border border-stone-200 p-3 has-checked:border-green-800 has-checked:bg-green-50">
          <input className="accent-green-800" type="radio" name="option" checked={choice === index} onChange={() => setChoice(index)} />
          <span>{option}</span>
        </label>)}
      </fieldset>
      <button className={`mt-5 ${primary}`} disabled={choice === null || busy}>{busy ? 'Checking…' : 'Submit answer'}</button>
    </form>
  )
}

export function PracticePage() {
  const [params, setParams] = useSearchParams()
  const [hintFor, setHintFor] = useState<string>()
  const client = useQueryClient()
  const modeParameter = params.get('mode')
  const mode: Mode = modeParameter === 'diagnostic' || modeParameter === 'checkpoint' || modeParameter === 'review' ? modeParameter : 'practice'
  const sessionId = params.get('session')
  const selectedTopic = params.get('topic') ?? ''
  const curriculum = useCurriculum()
  const topics = curriculum.data?.flatMap((domain) => domain.topics).filter((topic) =>
    mode === 'diagnostic' ? topic.diagnostic : topic.practice) ?? []
  const session = useQuery({
    queryKey: ['practice', sessionId],
    queryFn: ({ signal }) => request<Session>(`/practice/sessions/${encodeURIComponent(sessionId ?? '')}`, { signal }),
    enabled: Boolean(sessionId), retry: false,
  })
  const start = useMutation({
    mutationFn: () => {
      const topic = selectedTopic || undefined
      const difficulty = params.get('difficulty') || undefined
      if (mode === 'checkpoint') return mutate<Session>('/practice/checkpoints')
      if (mode === 'diagnostic') return mutate<Session>('/assessments/start', { topic })
      return mutate<Session>('/practice/sessions', { topic, difficulty, mode })
    },
    onSuccess: (view) => {
      client.setQueryData(['practice', view.session_id], view)
      setParams((query) => { query.set('session', view.session_id); return query })
    },
  })
  const idem = useRef({ item: '', choice: -1, key: '' })
  const answer = useMutation({
    mutationFn: ({ item, choice }: { item: Item; choice: number }) => {
      if (idem.current.item !== item.item_id || idem.current.choice !== choice) {
        idem.current = { item: item.item_id, choice, key: crypto.randomUUID() }
      }
      const route = mode === 'diagnostic' ? `/assessments/${sessionId}/submit` : `/practice/sessions/${sessionId}/answer`
      return mutate<AnswerResult>(route, { item_id: item.item_id, option_index: choice }, { key: idem.current.key })
    },
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ['practice', sessionId] }),
        client.invalidateQueries({ queryKey: ['progress'] }),
        client.invalidateQueries({ queryKey: ['hypotheses'] }),
      ])
    },
  })

  const item = session.data?.items[0]
  return <>
    <PageHeading title={modeNames[mode]}>
      {mode === 'diagnostic' ? 'Check your understanding with reviewed questions. Topics without evidence stay unassessed.'
        : mode === 'checkpoint' ? 'Answer a fresh question to check whether the concept is clearer.'
          : 'Work through a short session with feedback after each answer.'}
    </PageHeading>
    {answer.data && <section className={`${card} mt-5 max-w-2xl`} aria-live="polite">
      <h2 className="font-semibold text-green-950">{answer.data.correct ? 'Correct' : 'Review this idea'}</h2>
      <p className="mt-2 leading-7 text-stone-700">{answer.data.explanation}</p>
    </section>}
    <Failure error={start.error ?? session.error ?? answer.error}
      retry={session.isError ? () => void session.refetch() : undefined} />
    {sessionId && session.isPending && <Pending>Loading your question…</Pending>}
    {session.data && item && <section className={`${card} mt-5 max-w-2xl`}>
      <p className="mb-3 text-sm font-medium text-stone-600">Question {session.data.total - session.data.remaining + 1} of {session.data.total}</p>
      <QuestionForm key={item.item_id} item={item} busy={answer.isPending} submit={(choice) => answer.mutate({ item, choice })} />
      {mode === 'practice' && <button type="button" className={`mt-4 ${secondary}`} onClick={() => {
        setHintFor(hintFor === item.item_id ? undefined : item.item_id)
      }}>{hintFor === item.item_id ? 'Close hints' : 'Get a hint'}</button>}
      {mode === 'practice' && hintFor === item.item_id && <div className="mt-4">
        <TutorPanel key={item.item_id} topic={item.subtopic_id} itemId={item.item_id} />
      </div>}
    </section>}
    {session.data && !item && <section className={`${card} mt-5 max-w-2xl`}>
      <h2 className="font-semibold">Session complete</h2>
      <div className="mt-4 flex flex-wrap gap-2">
        <Link to="/" className={primary}>See your next step</Link>
        <button className={secondary} type="button" onClick={() => {
          answer.reset()
          setParams((query) => { query.delete('session'); return query })
        }}>Choose another activity</button>
      </div>
    </section>}
    {!sessionId && <section className={`${card} mt-6 max-w-xl`}>
      <div className="mb-4 flex flex-wrap gap-3">
        {mode !== 'diagnostic' && <Link className={textLink} to="/practice?mode=diagnostic">Diagnostic</Link>}
        {mode !== 'practice' && <Link className={textLink} to="/practice">Practice</Link>}
      </div>
      {mode !== 'checkpoint' && curriculum.isPending ? <Pending>Checking available questions…</Pending>
        : mode !== 'checkpoint' && topics.length === 0 ? <Empty>There are no reviewed questions for this activity yet.</Empty>
          : <>
            {mode !== 'checkpoint' && <label className="mb-4 grid gap-2 text-sm font-medium">Topic
              <select className={field} value={selectedTopic} onChange={(event) => setParams((query) => {
                if (event.target.value) query.set('topic', event.target.value)
                else query.delete('topic')
                return query
              })}>
                <option value="">Available topics</option>
                {topics.map((topic) => <option key={topic.id} value={topic.id}>{topic.title}</option>)}
              </select>
            </label>}
            <button className={primary} disabled={start.isPending} onClick={() => start.mutate()}>
              {start.isPending ? 'Starting…' : mode === 'checkpoint' ? 'Start checkpoints' : `Start or resume ${modeNames[mode].toLowerCase()}`}
            </button>
          </>}
    </section>}
  </>
}
