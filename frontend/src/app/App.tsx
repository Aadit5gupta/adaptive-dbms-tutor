import { useQuery } from '@tanstack/react-query'
import {
  BookOpen, ChartNoAxesCombined, Database, House, LibraryBig, PenLine, Terminal, Users,
} from 'lucide-react'
import { NavLink, Route, Routes } from 'react-router'

import { fetchHealth } from '../api/health'
import { DemoPage } from '../pages/DemoPage'
import { FoundationPage } from '../pages/FoundationPage'

const pages = [
  { path: '/', title: 'Dashboard', icon: House, description: 'See your next learning step and recent progress.' },
  { path: '/learn', title: 'Learn', icon: BookOpen, description: 'Explore DBMS lessons and worked examples.' },
  { path: '/practice', title: 'Practice', icon: PenLine, description: 'Check your understanding and get feedback on your answers.' },
  { path: '/sql', title: 'SQL Lab', icon: Terminal, description: 'Write queries against exercise datasets.' },
  { path: '/library', title: 'Library', icon: LibraryBig, description: 'Find attributed source material for DBMS and SQL.' },
  { path: '/progress', title: 'Progress', icon: ChartNoAxesCombined, description: 'Review your practice history and topics due for revision.' },
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
          <NavLink to="/demo" className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium ${isActive ? 'bg-green-100 text-green-950' : 'text-stone-600 hover:bg-stone-100'}`
          }>
            <Users size={18} aria-hidden="true" />Learner demo
          </NavLink>
        </nav>
      </aside>
      <div>
        <header className="flex min-h-16 items-center justify-end border-b border-stone-200 px-6 md:px-10">
          <BackendStatus />
        </header>
        <main id="main" tabIndex={-1} className="mx-auto max-w-6xl px-6 py-12 md:px-10 md:py-20">
          <Routes>
            {pages.map(({ path, title, description }) => (
              <Route key={path} path={path} element={<FoundationPage title={title} description={description} />} />
            ))}
            <Route path="/demo" element={<DemoPage />} />
            <Route path="*" element={<><h1>Page missing</h1><NavLink className="mt-6 inline-block underline" to="/">Return to dashboard</NavLink></>} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
