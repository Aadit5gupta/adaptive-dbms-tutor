import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
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

it('loads readiness from the API and navigates to a clearly labeled placeholder', async () => {
  const fetch = vi.fn().mockResolvedValue(Response.json({ status: 'ok', database: 'ready' }))
  vi.stubGlobal('fetch', fetch)
  renderApp()

  expect(screen.getByRole('status')).toHaveTextContent('Checking backend')
  expect(await screen.findByText('Backend ready')).toBeInTheDocument()
  expect(fetch).toHaveBeenCalledWith('/api/v1/health', { signal: expect.any(AbortSignal) })

  await userEvent.setup().click(screen.getByRole('link', { name: 'SQL Lab' }))
  expect(screen.getByRole('heading', { level: 1, name: 'SQL Lab' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'SQL Lab' })).toHaveAttribute('aria-current', 'page')
  expect(screen.getByRole('heading', { name: 'Not available yet' })).toBeInTheDocument()
})

it('can retry when the backend is unavailable', async () => {
  vi.stubGlobal('fetch', vi.fn()
    .mockResolvedValueOnce(Response.json({}, { status: 503 }))
    .mockResolvedValueOnce(Response.json({ status: 'ok', database: 'ready' })))
  renderApp()

  expect(await screen.findByText('Backend unavailable')).toBeInTheDocument()
  await userEvent.setup().click(screen.getByRole('button', { name: 'Retry' }))
  expect(await screen.findByText('Backend ready')).toBeInTheDocument()
})
