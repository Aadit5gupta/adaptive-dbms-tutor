import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { Link, useSearchParams } from 'react-router'

import { request } from '../api/client'
import type { Library, SearchHit, SourceKind } from '../api/library'

const card = 'rounded-2xl border border-stone-200 bg-white p-5 sm:p-6'
const link = 'text-green-900 underline decoration-green-500 underline-offset-4'

export function LibraryPage() {
  const [params, setParams] = useSearchParams()
  const query = (params.get('q') ?? '').trim().slice(0, 300)
  const source = params.get('kind')
  const kind: SourceKind | undefined = source === 'book' || source === 'lesson' ? source : undefined
  const filters = new URLSearchParams({ q: query })
  if (kind) filters.set('kind', kind)
  const catalog = useQuery({ queryKey: ['library'], queryFn: ({ signal }) => request<Library>('/library/books', { signal }), retry: false })
  const search = useQuery({
    queryKey: ['library', 'passages', query, kind],
    queryFn: ({ signal }) => request<SearchHit[]>(`/library/search?${filters}`, { signal }),
    enabled: query.length >= 2,
    retry: false,
  })
  return (
    <>
      <h1>Library</h1>
      <p className="mt-3 max-w-xl leading-7 text-stone-600">
        Search reviewed lessons and cleared book passages, or browse the original sources.
      </p>
      <form key={filters.toString()} className="mt-6 grid max-w-2xl gap-3 sm:grid-cols-[1fr_auto_auto] sm:items-end"
        onSubmit={(event) => {
          event.preventDefault()
          const values = new FormData(event.currentTarget)
          const nextQuery = String(values.get('q') ?? '').trim()
          const nextKind = values.get('kind')
          if (nextQuery.length < 2) return
          const next = new URLSearchParams({ q: nextQuery })
          if (nextKind === 'book' || nextKind === 'lesson') next.set('kind', nextKind)
          setParams(next)
        }}>
        <label className="block min-w-0 text-sm font-medium">
          Search passages
          <input name="q" type="search" defaultValue={query} required minLength={2} maxLength={300}
            className="mt-2 w-full rounded-lg border border-stone-300 bg-white px-3 py-2.5"
            placeholder="Try a concept or SQL term" />
        </label>
        <label className="block text-sm font-medium">
          Sources
          <select name="kind" defaultValue={kind ?? 'all'}
            className="mt-2 block w-full rounded-lg border border-stone-300 bg-white px-3 py-2.5">
            <option value="all">All sources</option>
            <option value="lesson">Original lessons</option>
            <option value="book">Textbooks</option>
          </select>
        </label>
        <button type="submit"
          className="flex w-fit items-center gap-2 rounded-lg bg-green-900 px-4 py-2.5 text-sm font-semibold text-white">
          <Search size={16} aria-hidden="true" />Search
        </button>
      </form>
      {query.length >= 2 && <section aria-label="Passage results" className="mt-6 grid gap-3">
        {search.isPending && <p role="status">Searching…</p>}
        {search.isError && <p role="alert" className="text-red-900">{search.error.message}</p>}
        {search.data?.length === 0 && <p className={card}>No matching reviewed passages.</p>}
        {search.data?.map(({ citation, excerpt, topic_id }) => (
          <article className={card} key={citation.id}>
            <p className="mb-1 text-sm text-stone-600">{citation.kind === 'book' ? 'Textbook excerpt' : 'Original lesson'}</p>
            <h2 className="text-lg font-semibold">
              {citation.lesson_ref
                ? <Link className={link} to={`/learn/${encodeURIComponent(citation.lesson_ref)}`}>{citation.title}</Link>
                : <a className={link} href={citation.url}>{citation.title}</a>}
            </h2>
            <p className="mt-3 break-words leading-7 text-stone-700">{excerpt}</p>
            <p className="mt-2 text-sm text-stone-600">{citation.attribution}</p>
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-sm">
              {citation.lesson_ref && <a className={link} href={citation.url}>Chapter reference</a>}
              {citation.license_url && <a className={link} href={citation.license_url}>License</a>}
              {citation.kind === 'book' && <Link className={link} to={`/tutor?${new URLSearchParams({ topic: topic_id })}`}
                state={{ question: query }}>Ask Tutor about this topic</Link>}
            </div>
          </article>
        ))}
      </section>}
      <section aria-labelledby="catalog-heading" className="mt-10">
        <h2 id="catalog-heading" className="text-xl font-semibold">Book catalog</h2>
        {catalog.isPending && <p className="mt-3" role="status">Loading catalog…</p>}
        {catalog.isError && <p className="mt-3 text-red-900" role="alert">{catalog.error.message}</p>}
        {catalog.data && <>
          <p className="mt-2 text-sm text-stone-600">{catalog.data.indexed_books} of {catalog.data.catalog_books} indexed</p>
          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            {catalog.data.books.map((book) => (
              <article className={card} key={book.id}>
                <h3 className="font-semibold"><a className={link} href={book.source_url}>{book.title}</a></h3>
                <p className="mt-2 text-sm text-stone-700">{book.authors.join(', ')}</p>
                <p className="mt-2 text-sm text-stone-700">
                  {book.indexed_sections ? `${book.indexed_sections} searchable section${book.indexed_sections === 1 ? '' : 's'}` : 'Link only'}
                  {book.cleared_sections > book.indexed_sections && ` · ${book.cleared_sections} cleared sections`}
                </p>
                <details className="mt-3 text-sm text-stone-600">
                  <summary className="cursor-pointer font-medium text-stone-800">Rights and exceptions</summary>
                  <p className="mt-2"><a className={link} href={book.license_evidence_url}>{book.license ?? 'Publisher license evidence'}</a></p>
                  <ul className="ml-4 mt-2 list-disc space-y-2">
                    {book.section_exceptions.map((item) => <li key={item.section_url + item.status}>{item.issue}</li>)}
                  </ul>
                </details>
              </article>
            ))}
          </div>
        </>}
      </section>
    </>
  )
}
