import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import { mutate } from '../api/learning'
import { Failure, field, secondary, textLink } from './layout'

interface HintRequest {
  level: number
  question?: string
}

interface HintReply {
  answer: string
  conversation_id: string
}

const labels = ['Starting point', 'Concept clue', 'Guided example']

export function AssessmentHints({ itemId, busy }: { itemId: string; busy: boolean }) {
  const [prepared, setPrepared] = useState<string[]>([])
  const [specific, setSpecific] = useState<string>()
  const [showQuestion, setShowQuestion] = useState(false)
  const [question, setQuestion] = useState('')
  const [conversation, setConversation] = useState<string>()
  const hint = useMutation({
    mutationFn: ({ level, question }: HintRequest) => mutate<HintReply>('/tutor/hint', {
      item_id: itemId, hint_level: level, query: question, conversation_id: conversation,
    }),
    onSuccess: (reply, { question }) => {
      setConversation(reply.conversation_id)
      if (question === undefined) {
        setPrepared((previous) => [...previous, reply.answer])
      } else {
        setSpecific(reply.answer)
        setQuestion('')
      }
    },
  })
  const unavailable = busy || hint.isPending
  const next = prepared.length + 1

  return <div className="mt-4">
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
      {next <= labels.length && <button type="button" className={secondary} disabled={unavailable}
        onClick={() => hint.mutate({ level: next })}>
        {hint.isPending && hint.variables.question === undefined ? 'Getting hint…'
          : next === 1 ? 'Get a hint' : 'Get the next hint'}
      </button>}
      <button type="button" className={`${textLink} text-sm`} aria-expanded={showQuestion}
        onClick={() => setShowQuestion(!showQuestion)}>
        {showQuestion ? 'Close specific clue' : 'Ask for a specific clue'}
      </button>
    </div>
    {prepared.length > 0 && <ol className="mt-3 grid gap-2" aria-live="polite">
      {prepared.map((answer, index) => <li key={labels[index]} className="rounded-lg border border-green-200 bg-green-50 p-3">
        <p className="text-sm font-semibold text-green-950">{index + 1} · {labels[index]}</p>
        <p className="mt-1 text-sm leading-6">{answer}</p>
      </li>)}
    </ol>}
    {showQuestion && <form className="mt-4 grid gap-2" onSubmit={(event) => {
      event.preventDefault()
      if (!unavailable && question.trim().length >= 2) hint.mutate({ level: 1, question: question.trim() })
    }}>
      <label className="grid gap-1 text-sm font-medium">
        What are you stuck on?
        <textarea className={field} value={question} rows={2} maxLength={600} disabled={unavailable}
          placeholder="e.g. Why does this value repeat?" onChange={(event) => setQuestion(event.target.value)} />
      </label>
      <button type="submit" className={secondary} disabled={unavailable || question.trim().length < 2}>
        {hint.isPending && hint.variables.question !== undefined ? 'Getting clue…' : 'Get a clue'}
      </button>
      {specific && <p className="rounded-lg border border-green-200 bg-green-50 p-3 text-sm leading-6"
        aria-live="polite">{specific}</p>}
    </form>}
    <Failure error={hint.error} />
  </div>
}
