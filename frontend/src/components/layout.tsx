import type { ReactNode } from 'react'
import { Link } from 'react-router'

export const card = 'rounded-2xl border border-stone-200 bg-white p-5 sm:p-7'
export const primary = 'inline-flex w-fit items-center justify-center gap-2 rounded-lg bg-green-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-green-800 disabled:cursor-default disabled:opacity-50'
export const secondary = 'inline-flex w-fit items-center justify-center gap-2 rounded-lg border border-stone-300 bg-white px-4 py-2.5 text-sm font-semibold text-stone-800 hover:border-green-700 disabled:opacity-50'
export const field = 'w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-stone-900'
export const textLink = 'font-medium text-green-900 underline decoration-green-500 underline-offset-4'

export function PageHeading({ title, children }: { title: string; children?: ReactNode }) {
  return <><h1>{title}</h1>{children && <p className="mt-3 max-w-2xl leading-7 text-stone-600">{children}</p>}</>
}

export function Pending({ children = 'Loading…' }: { children?: ReactNode }) {
  return <p className="my-5 text-stone-600" role="status">{children}</p>
}

export function Failure({ error, retry }: { error: Error | null; retry?: () => void }) {
  if (!error) return null
  return <div role="alert" className="mt-4 flex flex-wrap items-center gap-3 rounded-lg bg-red-50 p-3 text-sm text-red-900">
    {error.message}
    {retry && <button className="font-semibold underline" type="button" onClick={retry}>Retry</button>}
  </div>
}

export function Empty({ children, action }: { children: ReactNode; action?: { label: string; to: string } }) {
  return <section className={`${card} my-5 max-w-2xl`}><p className="leading-7 text-stone-600">{children}</p>
    {action && <Link className={`mt-4 ${secondary}`} to={action.to}>{action.label}</Link>}
  </section>
}
