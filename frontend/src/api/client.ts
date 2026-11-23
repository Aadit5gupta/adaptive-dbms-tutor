export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, options)
  if (!response.ok) {
    let detail = 'The backend request failed. Retry in a moment.'
    try {
      const error: unknown = await response.json()
      if (typeof error === 'object' && error !== null && 'detail' in error
          && typeof error.detail === 'string') {
        detail = error.detail
      }
    } catch {
      // Framework errors may have a non-JSON body.
    }
    throw new ApiError(detail, response.status)
  }
  return response.json() as Promise<T>
}
