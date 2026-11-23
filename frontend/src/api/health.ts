export interface Health {
  status: 'ok'
  database: 'ready'
}

function isHealth(value: unknown): value is Health {
  return typeof value === 'object' && value !== null
    && 'status' in value && value.status === 'ok'
    && 'database' in value && value.database === 'ready'
}

export async function fetchHealth(signal: AbortSignal): Promise<Health> {
  const response = await fetch('/api/v1/health', { signal })
  if (!response.ok) {
    throw new Error('Backend unavailable')
  }
  const body: unknown = await response.json()
  if (!isHealth(body)) {
    throw new Error('Unexpected backend response')
  }
  return body
}
