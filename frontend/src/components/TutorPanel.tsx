import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import { request } from '../api/client'
import type { Learner } from '../api/demo'
import type { Citation } from '../api/library'

type Mode = 'ask' | 'explain' | 'simpler' | 'example' | 'hint' | 'sql_feedback'

interface TutorReply {
  answer: string
  citations: Citation[]
  conversation_id: string
  provider: 'curated' | 'ollama'
  status: 'ok' | 'ai_unavailable' | 'no_evidence'
}

interface TutorPanelProps {
  topic?: string
  demoLearner?: Learner
  itemId?: string
  sqlAttempt?: string
}

export function TutorPanel({ topic, demoLearner, itemId, sqlAttempt }: TutorPanelProps) {
  const fixedMode = itemId ? 'hint' : sqlAttempt ? 'sql_feedback' : null
  const [question, setQuestion] = useState('')
  const [mode, setMode] = useState<Mode>(fixedMode ?? 'ask')
  const [level, setLevel] = useState(1)
  const [maxLevel, setMaxLevel] = useState(itemId ? 1 : 3)
  const [conversation, setConversation] = useState<string>()
  const [turns, setTurns] = useState<{ question: string; reply: TutorReply }[]>([])
  const tutor = useMutation({
    mutationFn: (query: string) => {
      const endpoint = mode === 'hint' ? '/hint' : mode === 'ask' ? '/ask' : '/explain'
      const path = demoLearner ? `/demo/tutor/${demoLearner}` : '/tutor'
      return request<TutorReply>(path + endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query, topic_id: topic, mode, hint_level: level,
          conversation_id: conversation, item_id: itemId, attempt_id: sqlAttempt,
        }),
      })
    },
    onSuccess: (reply, query) => {
      setConversation(reply.conversation_id)
      setTurns((recent) => [...recent.slice(-2), { question: query, reply }])
      setQuestion('')
      if (itemId && reply.status !== 'no_evidence') setMaxLevel((available) => Math.min(3, Math.max(available, level + 1)))
    },
  })

  function reset() {
    tutor.reset()
    setConversation(undefined)
    setTurns([])
    setQuestion('')
  }

  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-5 sm:p-7">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-xl font-semibold">{itemId ? 'Progressive hints' : sqlAttempt ? 'SQL mistake explanation' : 'Ask Tutor'}</h2>
        {turns.length > 0 && <button type="button" className="text-sm font-medium text-green-900 underline"
          onClick={reset} disabled={tutor.isPending}>New conversation</button>}
      </div>
      {turns.length > 0 && <div className="mt-4 grid gap-3" aria-live="polite">
        {turns.map(({ question, reply }, index) => (
          <article key={index} className="grid gap-2">
            <p className="w-fit rounded-lg bg-stone-100 px-3 py-2 text-sm">{question}</p>
            <div className="rounded-xl border border-green-200 bg-green-50 p-4">
              <p className="text-sm font-semibold text-green-900">
                {reply.provider === 'ollama' ? 'Local AI' : reply.status === 'ai_unavailable'
                  ? 'Curated explanation · local AI unavailable' : 'Curated tutor'}
              </p>
              <p className="mt-2 whitespace-pre-wrap leading-7">{reply.answer}</p>
              {reply.citations.length > 0 && <ul className="mt-3 space-y-1 text-sm">
                {reply.citations.map((citation) => (
                  <li key={citation.id}>
                    <a href={citation.url} className="font-medium text-green-900 underline">{citation.title}</a>
                    <span className="text-stone-600"> · {citation.attribution}</span>
                    {citation.license_url && <> · <a href={citation.license_url} className="text-green-900 underline">License</a></>}
                  </li>
                ))}
              </ul>}
            </div>
          </article>
        ))}
      </div>}
      <form className="mt-4 grid gap-3" onSubmit={(event) => {
        event.preventDefault()
        if (question.trim().length >= 2 && !tutor.isPending) tutor.mutate(question.trim())
      }}>
        {!fixedMode && <label className="grid gap-1 text-sm font-medium">
          Tutoring mode
          <select value={mode} disabled={tutor.isPending} onChange={(event) => setMode(event.target.value as Mode)} className="rounded-lg border border-stone-300 bg-white p-2">
            <option value="ask">Ask a question</option>
            <option value="explain">Explain a concept</option>
            <option value="simpler">Use simpler language</option>
            <option value="example">Work through an example</option>
            <option value="hint">Get a hint</option>
            <option value="sql_feedback">Explain a SQL mistake</option>
          </select>
        </label>}
        {mode === 'hint' && <label className="grid gap-1 text-sm font-medium">
          Hint level
          <select value={level} disabled={tutor.isPending} onChange={(event) => setLevel(Number(event.target.value))} className="rounded-lg border border-stone-300 bg-white p-2">
            <option value={1}>1 · Starting point</option>
            <option value={2} disabled={maxLevel < 2}>2 · Concept clue</option>
            <option value={3} disabled={maxLevel < 3}>3 · Guided example</option>
          </select>
        </label>}
        <label className="grid gap-1 text-sm font-medium">
          {turns.length ? 'Follow-up question' : 'Your question'}
          <textarea rows={3} value={question} maxLength={600} disabled={tutor.isPending}
            onChange={(event) => setQuestion(event.target.value)}
            className="rounded-lg border border-stone-300 p-3" />
        </label>
        <button type="submit" disabled={question.trim().length < 2 || tutor.isPending}
          className="w-fit rounded-lg bg-green-900 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
          {tutor.isPending ? 'Finding an explanation…' : turns.length ? 'Send follow-up' : 'Ask tutor'}
        </button>
      </form>
      {tutor.isError && <p className="mt-4 text-sm text-red-900" role="alert">{tutor.error.message}</p>}
    </section>
  )
}
