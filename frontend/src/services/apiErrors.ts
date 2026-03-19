function toText(value: unknown): string {
  if (value == null) return ''
  return String(value).trim()
}

function detailItemToText(item: unknown): string {
  if (item == null) return ''
  if (typeof item === 'string') return item.trim()
  if (typeof item !== 'object') return toText(item)

  const input = item as Record<string, unknown>
  const msg = toText(input.msg ?? input.message ?? input.error)
  const loc = Array.isArray(input.loc)
    ? input.loc.map((part) => toText(part)).filter(Boolean).join('.')
    : ''

  if (loc && msg) return `${loc}: ${msg}`
  return msg
}

function detailToText(detail: unknown): string {
  if (Array.isArray(detail)) {
    return detail.map((item) => detailItemToText(item)).filter(Boolean).join('; ')
  }
  return detailItemToText(detail)
}

function payloadToMessage(data: unknown): string {
  if (typeof data === 'string') return data.trim()
  if (!data || typeof data !== 'object') return ''

  const input = data as Record<string, unknown>
  const detail = detailToText(input.detail)
  if (detail) return detail

  return toText(input.message ?? input.error ?? input.raw)
}

function statusFallback(status: number): string {
  if (status === 400) return 'Invalid request.'
  if (status === 401) return 'Authentication failed.'
  if (status === 403) return 'Access denied.'
  if (status === 404) return 'Requested resource was not found.'
  if (status === 409) return 'A conflicting record already exists.'
  if (status === 422) return 'Submitted data is invalid.'
  if (status >= 500 && status <= 599) return 'Server error. Please try again later.'
  return ''
}

export class ApiError extends Error {
  status: number
  method: string
  path: string
  data: unknown

  constructor({ status = 0, method = 'GET', path = '', data = null }: { status?: number; method?: string; path?: string; data?: unknown } = {}) {
    const normalizedMethod = String(method || 'GET').toUpperCase()
    const normalizedPath = String(path || '')
    super(`HTTP ${status} ${normalizedMethod} ${normalizedPath}`.trim())

    this.name = 'ApiError'
    this.status = Number(status) || 0
    this.method = normalizedMethod
    this.path = normalizedPath
    this.data = data
  }

  userMessage(fallback = 'Request failed.'): string {
    const fromPayload = payloadToMessage(this.data)
    if (fromPayload) return fromPayload

    const fromStatus = statusFallback(this.status)
    if (fromStatus) return fromStatus

    const fromError = toText(this.message)
    if (fromError) return fromError

    return toText(fallback) || 'Request failed.'
  }
}

export function createApiError({ status = 0, method = 'GET', path = '', data = null }: { status?: number; method?: string; path?: string; data?: unknown } = {}): ApiError {
  return new ApiError({ status, method, path, data })
}

export function toUserErrorMessage(error: unknown, fallback = 'Request failed.'): string {
  if (!error) return toText(fallback) || 'Request failed.'
  if (error instanceof ApiError) return error.userMessage(fallback)

  const input = error as { data?: unknown; status?: unknown; message?: unknown }
  const fromPayload = payloadToMessage(input.data)
  if (fromPayload) return fromPayload

  const fromStatus = statusFallback(Number(input.status) || 0)
  if (fromStatus) return fromStatus

  const fromError = toText(input.message ?? error)
  if (fromError) return fromError

  return toText(fallback) || 'Request failed.'
}
