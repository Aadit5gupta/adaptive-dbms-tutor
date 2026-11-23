import { useQuery } from '@tanstack/react-query'
import {
  BookOpen, ChartNoAxesCombined, Database, House, LibraryBig, MessageCircle, PenLine, Settings, Terminal, Users,
} from 'lucide-react'
import { lazy, Suspense } from 'react'
import { NavLink, Route, Routes } from 'react-router'

import { fetchHealth } from '../api/health'
import { RequireAccount } from '../components/account'
import { PageHeading, Pending } from '../components/layout'
import { TutorPanel } from '../components/TutorPanel'
import { DashboardPage } from '../pages/DashboardPage'
import { DemoPage } from '../pages/DemoPage'
import { LibraryPage } from '../pages/LibraryPage'
import { PracticePage } from '../pages/PracticePage'
import { ProgressPage } from '../pages/ProgressPage'
import { SettingsPage } from '../pages/SettingsPage'

const LearnPage = lazy(async () => ({ default: (await import('../pages/LearnPage')).LearnPage }))
const LessonPage = lazy(async () => ({ default: (await import('../pages/LearnPage')).LessonPage }))
const SqlPage = lazy(async () => ({ default: (await import('../pages/SqlPage')).SqlPage }))

const pages = [
  { path: '/', title: 'Dashboard', icon: House },
  { path: '/learn', title: 'Learn', icon: BookOpen },
  { path: '/practice', title: 'Practice', icon: PenLine },
  { path: '/sql', title: 'SQL Lab', icon: Terminal },
  { path: '/library', title: 'Library', icon: LibraryBig },
  { path: '/progress', title: 'Progress', icon: ChartNoAxesCombined },
  { path: '/tutor', title: 'Ask Tutor', icon: MessageCircle },
  { path: '/settings', title: 'Settings', icon: Settings },
  { path: '/demo', title: 'Learner demo', icon: Users },
] as const

function BackendStatus() {
  const health = useQuery({
    queryKey: ['health'],
    queryFn: ({ signal }) => fetchHealth(signal),
    retry: false,
    refetchOnWindowFocus: false,
  })
  const label = health.isPending ? 'Checking backend…' : health.isError ? 'Backend unavailable' : 'Backend ready'
  return (
    <div className="flex items-center gap-3 text-sm text-stone-600">
      <span role="status" className="flex items-center gap-2.5">
        <span aria-hidden="true" className={`size-2 rounded-full ${health.isSuccess ? 'bg-green-700' : 'bg-amber-600'}`} />
        {label}
      </span>
      {health.isError && (
        <button className="font-semibold text-green-800 underline" onClick={() => void health.refetch()}>
          Retry
        </button>
      )}
    </div>
  )
}

export function App() {
  return (
    <div className="min-h-screen md:grid md:grid-cols-[15rem_1fr]">
      <a href="#main" className="absolute left-4 top-3 z-10 -translate-y-40 rounded bg-white p-3 focus:translate-y-0">
        Skip to content
      </a>
      <aside className="border-b border-stone-200 bg-white/80 px-5 py-5 md:border-b-0 md:border-r md:px-5 md:py-8">
        <NavLink to="/" className="flex w-fit items-center gap-3 rounded-md text-sm font-bold tracking-tight">
          <span className="rounded-xl bg-green-900 p-2.5 text-white"><Database size={19} aria-hidden="true" /></span>
          Adaptive DBMS Tutor
        </NavLink>
        <nav aria-label="Main navigation" className="mt-5 grid grid-cols-2 gap-1 sm:grid-cols-3 md:mt-12 md:grid-cols-1">
          {pages.map(({ path, title, icon: Icon }) => (
            <NavLink key={path} to={path} end={path === '/'} className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium ${isActive ? 'bg-green-100 text-green-950' : 'text-stone-600 hover:bg-stone-100'}`
            }>
              <Icon size={18} aria-hidden="true" />{title}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div>
        <header className="flex min-h-16 items-center justify-end border-b border-stone-200 px-6 md:px-10">
          <BackendStatus />
        </header>
        <main id="main" tabIndex={-1} className="mx-auto max-w-6xl px-6 py-12 md:px-10 md:py-20">
          <Routes>
            <Route path="/" element={<RequireAccount>{(account) => <DashboardPage account={account} />}</RequireAccount>} />
            <Route path="/learn" element={<RequireAccount>{() => <Suspense fallback={<Pending />}><LearnPage /></Suspense>}</RequireAccount>} />
            <Route path="/learn/:ref" element={<RequireAccount>{() => <Suspense fallback={<Pending />}><LessonPage /></Suspense>}</RequireAccount>} />
            <Route path="/practice" element={<RequireAccount>{() => <PracticePage />}</RequireAccount>} />
            <Route path="/sql" element={<RequireAccount>{() => <Suspense fallback={<Pending />}><SqlPage /></Suspense>}</RequireAccount>} />
            <Route path="/progress" element={<RequireAccount>{() => <ProgressPage />}</RequireAccount>} />
            <Route path="/tutor" element={<RequireAccount>{() => <>
              <PageHeading title="DBMS tutor">Ask about a concept, work through an example, or request a hint.</PageHeading>
              <div className="mt-6 max-w-2xl"><TutorPanel /></div>
            </>}</RequireAccount>} />
            <Route path="/settings" element={<RequireAccount>{(account) => <SettingsPage account={account} />}</RequireAccount>} />
            <Route path="/library" element={<LibraryPage />} />
            <Route path="/demo" element={<DemoPage />} />
            <Route path="*" element={<><h1>Page missing</h1><NavLink className="mt-6 inline-block underline" to="/">Return to dashboard</NavLink></>} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
