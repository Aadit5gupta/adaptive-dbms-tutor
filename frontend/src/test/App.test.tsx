import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { expect, it, vi } from 'vitest'

import { App } from '../app/App'

function renderApp() {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

it('checks readiness and keeps a signed-out user at the sign-in screen', async () => {
  const fetch = vi.fn((url: string) => Promise.resolve(url.endsWith('/health')
    ? Response.json({ status: 'ok', database: 'ready' })
    : Response.json({}, { status: 401 })))
  vi.stubGlobal('fetch', fetch)
  renderApp()

  expect(await screen.findByText('Backend ready')).toBeInTheDocument()
  expect(fetch).toHaveBeenCalledWith('/api/v1/health', { signal: expect.any(AbortSignal) })
  expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()

  const navigation = screen.getByRole('navigation', { name: 'Main navigation' })
  await userEvent.setup().click(within(navigation).getByRole('link', { name: 'SQL Lab' }))
  expect(within(navigation).getByRole('link', { name: 'SQL Lab' })).toHaveAttribute('aria-current', 'page')
  expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
})

it('can retry when the backend is unavailable', async () => {
  let first = true
  vi.stubGlobal('fetch', vi.fn((url: string) => {
    if (!url.endsWith('/health')) return Promise.resolve(Response.json({}, { status: 401 }))
    if (first) {
      first = false
      return Promise.resolve(Response.json({}, { status: 503 }))
    }
    return Promise.resolve(Response.json({ status: 'ok', database: 'ready' }))
  }))
  renderApp()

  expect(await screen.findByText('Backend unavailable')).toBeInTheDocument()
  await userEvent.setup().click(screen.getByRole('button', { name: 'Retry' }))
  expect(await screen.findByText('Backend ready')).toBeInTheDocument()
})
