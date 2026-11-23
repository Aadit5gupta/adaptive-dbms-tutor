import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import { request } from '../api/client'
import type { Citation } from '../api/library'

type Mode = 'ask' | 'explain' | 'simpler' | 'example' | 'hint' | 'sql_feedback'

interface TutorReply {
  answer: string
  citations: Citation[]
  provider: 'curated' | 'ollama'
  status: 'ok' | 'ai_unavailable' | 'no_evidence'
}

export function TutorPanel({ topic, demo = false }: { topic?: string; demo?: boolean }) {
  const [question, setQuestion] = useState('')
  const [mode, setMode] = useState<Mode>('ask')
  const [level, setLevel] = useState(1)
  const tutor = useMutation({
    mutationFn: () => {
      const endpoint = mode === 'hint' ? '/hint' : mode === 'ask' ? '/ask' : '/explain'
      return request<TutorReply>(`${demo ? "/demo" : ""}/tutor${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: question.trim(), topic_id: topic, mode, hint_level: level }),
      })
    },
  })

  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-5 sm:p-7">
      <h2 className="text-xl font-semibold">Ask Tutor</h2>
      <form className="mt-4 grid gap-3" onSubmit={(event) => {
        event.preventDefault()
        if (question.trim().length >= 2 && !tutor.isPending) tutor.mutate()
      }}>
        <label className="grid gap-1 text-sm font-medium">
          Tutoring mode
          <select value={mode} onChange={(event) => setMode(event.target.value as Mode)} className="rounded-lg border border-stone-300 bg-white p-2">
            <option value="ask">Ask a question</option>
            <option value="explain">Explain a concept</option>
            <option value="simpler">Use simpler language</option>
            <option value="example">Work through an example</option>
            <option value="hint">Get a hint</option>
            <option value="sql_feedback">Explain a SQL mistake</option>
          </select>
        </label>
        {mode === 'hint' && <label className="grid gap-1 text-sm font-medium">
          Hint level
          <select value={level} onChange={(event) => setLevel(Number(event.target.value))} className="rounded-lg border border-stone-300 bg-white p-2">
            <option value={1}>1 · Starting point</option><option value={2}>2 · Concept clue</option><option value={3}>3 · Guided example</option>
          </select>
        </label>}
        <label className="grid gap-1 text-sm font-medium">
          Your question
          <textarea rows={3} value={question} maxLength={600} onChange={(event) => setQuestion(event.target.value)}
            className="rounded-lg border border-stone-300 p-3" />
        </label>
        <button type="submit" disabled={question.trim().length < 2 || tutor.isPending}
          className="w-fit rounded-lg bg-green-900 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
          {tutor.isPending ? 'Finding an explanation…' : 'Ask tutor'}
        </button>
      </form>
      {tutor.isError && <p className="mt-4 text-sm text-red-900" role="alert">{tutor.error.message}</p>}
      {tutor.data && <div className="mt-5 rounded-xl border border-green-200 bg-green-50 p-4" aria-live="polite">
        <p className="text-sm font-semibold text-green-900">
          {tutor.data.provider === 'ollama' ? 'Local AI' : tutor.data.status === 'ai_unavailable'
            ? 'Curated explanation · local AI unavailable' : 'Curated tutor'}
        </p>
        <p className="mt-2 whitespace-pre-wrap leading-7">{tutor.data.answer}</p>
        {tutor.data.citations.length > 0 && <ul className="mt-3 space-y-1 text-sm">
          {tutor.data.citations.map((citation) => (
            <li key={citation.id}>
              <a href={citation.url} className="font-medium text-green-900 underline">{citation.title}</a>
              <span className="text-stone-600"> · {citation.kind === 'lesson' ? 'Reviewed lesson reference' : citation.attribution}</span>
            </li>
          ))}
        </ul>}
      </div>}
    </section>
  )
}
