import { useQuery } from '@tanstack/react-query'
import { ArrowRight, BookOpen, CalendarClock, ChartNoAxesCombined } from 'lucide-react'
import { Link } from 'react-router'

import { request } from '../api/client'
import type { Account, Domain, Progress, Recommendation } from '../api/learning'
import { card, Failure, PageHeading, Pending, primary, secondary } from '../components/layout'

export function useCurriculum() {
  return useQuery({ queryKey: ['curriculum'], queryFn: ({ signal }) => request<Domain[]>('/curriculum', { signal }), retry: false })
}

export function useProgress() {
  return useQuery({ queryKey: ['progress'], queryFn: ({ signal }) => request<Progress>('/progress', { signal }), retry: false })
}

export function topicDiagnosticPath(topic: string) {
  return `/practice?${new URLSearchParams({ mode: 'diagnostic', topic })}`
}

export function actionLink(action: Recommendation) {
  const topic = encodeURIComponent(action.subtopic_id)
  if (action.lesson_ref) return `/learn/${action.lesson_ref}${action.action_type === 'MISCONCEPTION_REMEDIATION' ? '?checkpoints=1' : ''}`
  if (action.action_type === 'SQL_PRACTICE') return `/sql?topic=${topic}`
  if (action.action_type === 'DIAGNOSTIC') return topicDiagnosticPath(action.subtopic_id)
  if (action.action_type === 'MIXED_REVIEW') return `/practice?mode=review&topic=${topic}`
  if (action.action_type.startsWith('PRACTICE')) return `/practice?topic=${topic}&difficulty=${action.difficulty ?? 'easy'}`
  return '/learn'
}

export function DashboardPage({ account }: { account: Account }) {
  const catalog = useCurriculum()
  const progress = useProgress()
  const topics = catalog.data?.flatMap((domain) => domain.topics) ?? []
  const action = progress.data?.recommendation
  const assessed = progress.data?.topics.filter((topic) => topic.score !== null).length ?? 0
  const due = progress.data?.topics.filter((topic) => topic.review_due).length ?? 0

  return (
    <>
      <PageHeading title="Dashboard">Pick up with a diagnostic, a lesson, or your next recommended activity.</PageHeading>
      <Failure error={catalog.error ?? progress.error} retry={() => { void catalog.refetch(); void progress.refetch() }} />
      {progress.isPending || catalog.isPending ? <Pending /> : (
        <div className="mt-8 grid gap-4 lg:grid-cols-[minmax(0,1.55fr)_minmax(15rem,1fr)]">
          <section className="rounded-3xl bg-green-950 p-6 text-white sm:p-9">
            <h2 className="text-2xl font-semibold">Your next step</h2>
            <p className="mt-3 max-w-lg leading-7 text-green-100">
              {action?.reason ?? (topics.some((topic) => topic.diagnostic)
                ? 'Start with a short diagnostic on the domains with reviewed questions.'
                : 'The curriculum is available to browse. Reviewed activities will appear after content sign-off.')}
            </p>
            <Link className="mt-6 inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2.5 text-sm font-semibold text-green-950"
              to={action ? actionLink(action) : topics.some((topic) => topic.diagnostic) ? '/practice?mode=diagnostic' : '/learn'}>
              {action && action.action_type !== 'COMPLETE' ? 'Open recommended activity' : topics.some((topic) => topic.diagnostic) ? 'Start diagnostic' : 'Browse curriculum'}
              <ArrowRight size={16} aria-hidden="true" />
            </Link>
          </section>
          <section className={card}>
            <h2 className="text-lg font-semibold">Learning overview</h2>
            <div className="mt-5 grid gap-3 text-stone-700">
              <p className="flex items-center gap-2"><BookOpen size={17} aria-hidden="true" />{assessed} assessed topics</p>
              <p className="flex items-center gap-2"><CalendarClock size={17} aria-hidden="true" />{due} due for revision</p>
              <p className="flex items-center gap-2"><ChartNoAxesCombined size={17} aria-hidden="true" />{progress.data?.recent.length ?? 0} recent attempts</p>
            </div>
            <Link to="/progress" className={`mt-5 ${secondary}`}>View progress</Link>
          </section>
        </div>
      )}
      {!account.preferences.goal && <section className={`${card} mt-4 max-w-lg`}>
        <h2 className="text-lg font-semibold">Set your learning goal</h2>
        <p className="mt-2 text-sm leading-6 text-stone-600">Choose an objective and a daily time budget for your account.</p>
        <Link to="/settings" className={`mt-4 ${primary}`}>Set preferences</Link>
      </section>}
    </>
  )
}
