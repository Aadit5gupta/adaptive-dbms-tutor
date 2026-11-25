import { useQuery } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router'

import { request } from '../api/client'
import type { LessonDetail, Topic } from '../api/learning'
import { card, Failure, PageHeading, Pending, primary, secondary, textLink } from '../components/layout'
import { LessonBody } from '../components/LessonBody'
import { TutorPanel } from '../components/TutorPanel'
import { topicDiagnosticPath, useCurriculum } from './DashboardPage'

function lessonPracticePath(topic: Topic, params?: URLSearchParams) {
  const query = new URLSearchParams({ topic: topic.id })
  const recommended = params?.get('difficulty')
  const fresh = recommended && params?.get('fresh') === '1'
  const difficulty = fresh ? recommended : topic.starting_practice_difficulty
  if (difficulty) query.set('difficulty', difficulty)
  if (fresh) query.set('fresh', '1')
  return `/practice?${query}`
}

export function LearnPage() {
  const curriculum = useCurriculum()
  const titles = new Map(curriculum.data?.flatMap((domain) => domain.topics.map((topic) => [topic.id, topic.title])))
  return (
    <>
      <PageHeading title="Learn">Browse the seven DBMS domains and open the reviewed lessons available for each topic.</PageHeading>
      {curriculum.isPending && <Pending>Loading curriculum…</Pending>}
      <Failure error={curriculum.error} retry={() => void curriculum.refetch()} />
      <div className="mt-7 grid gap-3">
        {curriculum.data?.map((domain) => <details className={card} key={domain.id}>
          <summary className="cursor-pointer text-lg font-semibold">{domain.title}</summary>
          <div className="mt-4 grid gap-5">
            {domain.topics.map((topic) => <section className="border-t border-stone-200 pt-4" key={topic.id}>
              <h2 className="font-semibold">{topic.title}</h2>
              {topic.prerequisites.length > 0 && <p className="mt-1 text-sm text-stone-600">Prerequisites · {topic.prerequisites.map((ref) => titles.get(ref) ?? ref).join(', ')}</p>}
              <div className="mt-3 flex flex-wrap gap-3">
                {topic.lessons.map((lesson) => <Link key={lesson.ref} className={textLink} to={`/learn/${lesson.ref}`}>{lesson.title}</Link>)}
                {topic.practice && <Link className={textLink} to={lessonPracticePath(topic)}>Practice</Link>}
                {topic.diagnostic && <Link className={textLink} to={topicDiagnosticPath(topic.id)}>Check understanding</Link>}
                {topic.lessons.length === 0 && !topic.practice && !topic.diagnostic && <p className="text-sm text-stone-600">Reviewed material pending.</p>}
              </div>
            </section>)}
          </div>
        </details>)}
      </div>
    </>
  )
}

export function LessonPage() {
  const { ref } = useParams()
  const [params] = useSearchParams()
  const checkpoint = params.get('checkpoints') === '1'
  const lesson = useQuery({
    queryKey: ['lesson', ref],
    queryFn: ({ signal }) => request<LessonDetail>(`/lessons/${encodeURIComponent(ref ?? '')}`, { signal }),
    retry: false,
  })
  const curriculum = useCurriculum()
  const topic = curriculum.data?.flatMap((domain) => domain.topics).find((entry) =>
    entry.id === lesson.data?.topic_id)
  if (lesson.isPending) return <Pending>Loading lesson…</Pending>
  if (lesson.isError) return <Failure error={lesson.error} retry={() => void lesson.refetch()} />
  return <>
    <Link className={textLink} to="/learn">Back to curriculum</Link>
    <div className="mt-4"><PageHeading title={lesson.data.title} /></div>
    <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(18rem,1fr)]">
      <article className={card}>
        {lesson.data.review_status === 'ai_verified' && <p className="mb-4 text-sm text-stone-600">AI-verified original lesson</p>}
        <LessonBody body={lesson.data.body} />
        <div className="mt-6 flex flex-wrap items-center gap-3">
          {checkpoint && <Link className={primary} to="/practice?mode=checkpoint">Open checkpoints</Link>}
          {!checkpoint && topic?.practice && <Link className={secondary} to={lessonPracticePath(topic, params)}>Practice this topic</Link>}
          <a className={textLink} href={lesson.data.source_url}>Lesson reference</a>
        </div>
      </article>
      <TutorPanel key={lesson.data.ref} topic={lesson.data.topic_id} />
    </div>
  </>
}
