import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'

import { request } from '../api/client'
import type { Hypothesis } from '../api/learning'
import { card, Failure, PageHeading, Pending, textLink } from '../components/layout'
import { MisconceptionStatus } from '../components/MisconceptionStatus'
import { actionLink, topicDiagnosticPath, useCurriculum, useProgress } from './DashboardPage'

export function ProgressPage() {
  const progress = useProgress()
  const course = useCurriculum()
  const hypotheses = useQuery({ queryKey: ['hypotheses'], queryFn: ({ signal }) => request<Hypothesis[]>('/misconceptions', { signal }) })
  const titles = new Map(course.data?.map((domain) => [domain.id, domain.title]))
  const next = progress.data?.recommendation
  const diagnosticTopics = new Set(course.data?.flatMap((domain) => domain.topics).filter((topic) => topic.diagnostic).map((topic) => topic.id))
  const topicTitles = new Map(progress.data?.topics.map((topic) => [topic.topic, topic.title]))
  return <>
    <PageHeading title="Progress">See which topics have evidence, when revision is due, and how your latest attempts changed your score.</PageHeading>
    <Failure error={progress.error ?? hypotheses.error} />
    {progress.isPending && <Pending>Loading your progress…</Pending>}
    {progress.data && <>
      <div className="mt-7 grid gap-4 xl:grid-cols-2">
        <section className={card}>
          <h2 className="text-lg font-semibold">Domain coverage</h2>
          <div className="mt-4 grid gap-3">{progress.data.domains.map((row) => (
            <div key={row.domain} className="flex items-center justify-between gap-3 border-b border-stone-100 pb-2 text-sm">
              <span className="font-medium">{titles.get(row.domain) ?? row.domain}</span>
              <span className="text-right text-stone-600">{row.assessed_topics} of {row.listed_topics} assessed</span>
            </div>
          ))}</div>
          {progress.data.domains.length === 0 && <p className="mt-3 text-sm text-stone-600">The curriculum has no installed content yet.</p>}
        </section>
        <section className={card}>
          <h2 className="text-lg font-semibold">Revision and misconceptions</h2>
          {progress.data.topics.filter((row) => row.review_due).map((row) => (
            <Link key={row.topic} className={`mt-3 block text-sm ${textLink}`} to={`/practice?mode=review&topic=${row.topic}`}>Review {row.title}</Link>
          ))}
          {!progress.data.topics.some((row) => row.review_due) && <p className="mt-3 text-sm text-stone-600">No topics are due for revision.</p>}
          <div id="misconceptions" className="mt-5 border-t border-stone-200 pt-4">
            <h3 className="font-semibold">Misconceptions</h3>
            {hypotheses.isPending && <Pending>Checking misconception progress…</Pending>}
            {hypotheses.data?.length === 0 &&
              <p className="mt-2 text-sm text-stone-600">No misconception patterns detected yet.</p>}
            {hypotheses.data?.map((row) => <article key={row.code} className="mt-3">
              <MisconceptionStatus hypothesis={row} />
              {row.state === 'possible' && diagnosticTopics.has(row.topic_id) &&
                <Link to={topicDiagnosticPath(row.topic_id)} className={`mt-2 inline-block text-sm ${textLink}`}>
                  Check this topic in Diagnostic
                </Link>}
              {next?.action_type === 'MISCONCEPTION_REMEDIATION' && next.misconception_code === row.code &&
                <Link to={actionLink(next)} className={`mt-2 inline-block text-sm ${textLink}`}>Open remediation lesson</Link>}
            </article>)}
          </div>
        </section>
        <section className={card}>
          <h2 className="text-lg font-semibold">Topic scores</h2>
          {progress.data.topics.filter((row) => row.score !== null).map((row) => <div className="mt-4" key={row.topic}>
            <label htmlFor={row.topic} className="text-sm font-medium">{row.title}</label>
            <meter className="mt-1 block w-full" id={row.topic} min={0} max={1} value={row.score ?? 0} />
            <p className="text-sm text-stone-600">{Math.round((row.score ?? 0) * 100)}% score · {row.confidence} confidence · {row.distinct} distinct responses</p>
          </div>)}
          {!progress.data.topics.some((row) => row.score !== null) && <p className="mt-2 text-sm text-stone-600">Scores appear after your first graded activity.</p>}
        </section>
        <section className={card}>
          <h2 className="text-lg font-semibold">Recent attempts</h2>
          {progress.data.recent.length ? <ol className="mt-4 grid gap-3">
            {progress.data.recent.map((row, index) => <li key={row.created_at + ':' + index} className="border-b border-stone-100 pb-2 text-sm">
              <span className="font-medium">{topicTitles.get(row.topic) ?? row.topic}</span>
              <span className="ml-2 text-stone-600">{row.context} · {row.correct ? 'correct' : 'incorrect'}</span>
              <time className="block text-stone-600" dateTime={new Date(row.created_at * 1000).toISOString()}>{new Date(row.created_at * 1000).toLocaleString()}</time>
            </li>)}
          </ol> : <p className="mt-2 text-sm text-stone-600">No attempts yet.</p>}
        </section>
      </div>
    </>}
  </>
}
