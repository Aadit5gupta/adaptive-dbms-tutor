import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { useState } from 'react'

import { request } from '../api/client'
import type { Library, SearchHit } from '../api/library'

const card = 'rounded-2xl border border-stone-200 bg-white p-5 sm:p-6'
const link = 'text-green-900 underline decoration-green-500 underline-offset-4'

export function LibraryPage() {
  const [input, setInput] = useState('')
  const [query, setQuery] = useState('')
  const catalog = useQuery({ queryKey: ['library'], queryFn: ({ signal }) => request<Library>('/library/books', { signal }), retry: false })
  const search = useQuery({
    queryKey: ['library', query],
    queryFn: ({ signal }) => request<SearchHit[]>(`/library/search?${new URLSearchParams({ q: query })}`, { signal }),
    enabled: query.length >= 2,
    retry: false,
  })
  return (
    <>
      <h1>Library</h1>
      <p className="mt-3 max-w-xl leading-7 text-stone-600">
        Search reviewed lessons and cleared book passages, or browse the original sources.
      </p>
      <form className="mt-6 max-w-xl" onSubmit={(event) => { event.preventDefault(); setQuery(input.trim()) }}>
        <label htmlFor="library-query" className="mb-2 block text-sm font-medium">Search passages</label>
        <div className="flex gap-2">
          <input id="library-query" type="search" value={input} maxLength={300}
            className="w-full rounded-lg border border-stone-300 bg-white px-3 py-2.5"
            placeholder="Search for a DBMS concept" onChange={(event) => setInput(event.target.value)} />
          <button type="submit" disabled={input.trim().length < 2}
            className="flex items-center gap-2 rounded-lg bg-green-900 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
            <Search size={16} aria-hidden="true" />Search
          </button>
        </div>
      </form>
      {query && <section aria-label="Passage results" className="mt-6 grid gap-3">
        {search.isPending && <p role="status">Searching…</p>}
        {search.isError && <p role="alert" className="text-red-900">{search.error.message}</p>}
        {search.data?.length === 0 && <p className={card}>No matching reviewed passages.</p>}
        {search.data?.map(({ citation, excerpt }) => (
          <article className={card} key={citation.id}>
            <a className={`${link} font-semibold`} href={citation.url}>{citation.title}</a>
            <p className="mt-3 leading-7 text-stone-700">{excerpt}</p>
            <p className="mt-2 text-sm text-stone-600">{citation.attribution}</p>
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
                  {book.indexed_sections ? `${book.indexed_sections} searchable sections` : 'Link only'}
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
