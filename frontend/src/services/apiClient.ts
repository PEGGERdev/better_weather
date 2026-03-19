import { createApiError } from './apiErrors'
import { getPathVariants } from './apiPath'

export interface RequestOptions {
  body?: unknown
  token?: string
  form?: boolean
}

export class ApiClient {
  baseUrl: string
  onUnauthorized: ((payload: { status: number; method: string; path: string; data: unknown }) => void) | null

  constructor(baseUrl: string, { onUnauthorized }: { onUnauthorized?: (payload: { status: number; method: string; path: string; data: unknown }) => void } = {}) {
    this.baseUrl = baseUrl
    this.onUnauthorized = typeof onUnauthorized === 'function' ? onUnauthorized : null
  }

  async request(method: string, path: string, options: RequestOptions = {}): Promise<unknown> {
    const { body, token, form = false } = options
    const headers: Record<string, string> = {}
    let payload: string | undefined
    const hasAuthToken = Boolean(String(token || '').trim())

    if (body !== undefined) {
      if (form) {
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        payload = new URLSearchParams(body as Record<string, string>).toString()
      } else {
        headers['Content-Type'] = 'application/json'
        payload = JSON.stringify(body)
      }
    }

    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    const tryPaths = getPathVariants(path)

    let lastError: unknown = null
    for (const p of tryPaths) {
      const url = new URL(p, this.baseUrl).toString()
      try {
        const res = await fetch(url, { method, headers, body: payload })
        const text = await res.text()
        let data: unknown = {}
        if (text) {
          try {
            data = JSON.parse(text)
          } catch {
            data = { raw: text }
          }
        }

        if (!res.ok) {
          if (res.status === 401 && hasAuthToken && this.onUnauthorized) {
            try {
              this.onUnauthorized({ status: res.status, method, path: p, data })
            } catch {
              // Ignore unauthorized callback failures.
            }
          }

          throw createApiError({
            status: res.status,
            method,
            path: p,
            data,
          })
        }

        return data
      } catch (error) {
        lastError = error
        const status = Number((error as { status?: number })?.status) || 0
        if (status !== 404) {
          break
        }
      }
    }

    throw lastError || new Error('Unknown API error')
  }

  get(path: string, options: Omit<RequestOptions, 'body' | 'form'> = {}): Promise<unknown> {
    return this.request('GET', path, { ...options, body: undefined, form: undefined })
  }

  post(path: string, body: unknown, options: Omit<RequestOptions, 'body'> = {}): Promise<unknown> {
    return this.request('POST', path, { ...options, body })
  }

  postForm(path: string, body: Record<string, unknown>, options: Omit<RequestOptions, 'body' | 'form'> = {}): Promise<unknown> {
    return this.request('POST', path, { ...options, body, form: true })
  }

  put(path: string, body: unknown, options: Omit<RequestOptions, 'body'> = {}): Promise<unknown> {
    return this.request('PUT', path, { ...options, body })
  }

  delete(path: string, options: Omit<RequestOptions, 'body' | 'form'> = {}): Promise<unknown> {
    return this.request('DELETE', path, { ...options, body: undefined, form: undefined })
  }
}
