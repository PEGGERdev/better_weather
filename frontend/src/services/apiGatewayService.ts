import { getApiEndpointBinding, type ApiEndpointKey } from '@/api/registry'
import { BaseService } from './baseService'
import type { ApiClient } from './apiClient'

function asText(value: unknown): string {
  return String(value || '').trim()
}

function buildPath(pathTemplate: string, params: Record<string, unknown> = {}): string {
  const source = asText(pathTemplate)
  const path = source.replace(/\{([a-zA-Z0-9_]+)\}/g, (_full, name) => {
    const raw = params[name]
    const normalized = asText(raw)
    if (!normalized) {
      throw new Error(`Missing path parameter: ${name}`)
    }
    return encodeURIComponent(normalized)
  })

  if (/\{[a-zA-Z0-9_]+\}/.test(path)) {
    throw new Error(`Unresolved path template: ${source}`)
  }

  return path
}

function appendQuery(path: string, query: Record<string, unknown> = {}): string {
  const entries = Object.entries(query || {})
  if (!entries.length) return path

  const search = new URLSearchParams()
  for (const [key, value] of entries) {
    const queryKey = asText(key)
    if (!queryKey || value == null) continue

    const queryValue = String(value)
    if (!queryValue.trim()) continue
    search.append(queryKey, queryValue)
  }

  const qs = search.toString()
  if (!qs) return path
  return `${path}?${qs}`
}

export interface RequestOptions {
  params?: Record<string, unknown>
  query?: Record<string, unknown>
  body?: unknown
  token?: string
  formEncoded?: boolean
}

export class ApiGatewayService extends BaseService {
  private api: ApiClient

  constructor(api: ApiClient) {
    super({ serviceName: 'apiGateway' })
    this.api = api
  }

  private _resolveToken(options: { authenticated: boolean; token?: string }): string {
    const tokenOverride = asText(options.token)
    if (!options.authenticated) {
      return tokenOverride
    }

    const activeToken = tokenOverride
    if (!activeToken) {
      throw new Error('Authentication required')
    }
    return activeToken
  }

  private async _dispatchRequest(
    method: string,
    path: string,
    options: { body?: unknown; token?: string; formEncoded?: boolean }
  ): Promise<unknown> {
    const { body, token, formEncoded } = options

    if (method === 'GET') {
      return this.api.get(path, { token })
    }
    if (method === 'POST') {
      if (formEncoded) {
        return this.api.postForm(path, (body || {}) as Record<string, unknown>, { token })
      }
      return this.api.post(path, body || {}, { token })
    }
    if (method === 'PUT') {
      return this.api.put(path, body || {}, { token })
    }
    if (method === 'DELETE') {
      return this.api.delete(path, { token })
    }
    throw new Error(`Unsupported API method: ${method}`)
  }

  async request(endpointKey: ApiEndpointKey, options: RequestOptions = {}): Promise<unknown> {
    const { params = {}, query = {}, body, token = '', formEncoded } = options

    const binding = getApiEndpointBinding(endpointKey)
    const pathWithParams = buildPath(binding.path, params)
    const path = appendQuery(pathWithParams, query)
    const resolvedToken = this._resolveToken({
      authenticated: binding.authenticated,
      token,
    })

    const useFormEncoded = typeof formEncoded === 'boolean' ? formEncoded : binding.formEncoded

    try {
      const result = await this._dispatchRequest(binding.method, path, {
        body,
        token: resolvedToken,
        formEncoded: useFormEncoded,
      })
      this.clearError()
      return result
    } catch (error) {
      this.captureError(error, `API request failed: ${endpointKey}`)
      throw error
    }
  }

  async get(endpointKey: ApiEndpointKey, options: Omit<RequestOptions, 'body' | 'formEncoded'> = {}): Promise<unknown> {
    return this.request(endpointKey, { ...options, body: undefined, formEncoded: undefined })
  }

  async post(endpointKey: ApiEndpointKey, body: unknown, options: Omit<RequestOptions, 'body'> = {}): Promise<unknown> {
    return this.request(endpointKey, { ...options, body })
  }

  async put(endpointKey: ApiEndpointKey, body: unknown, options: Omit<RequestOptions, 'body'> = {}): Promise<unknown> {
    return this.request(endpointKey, { ...options, body })
  }

  async delete(endpointKey: ApiEndpointKey, options: Omit<RequestOptions, 'body' | 'formEncoded'> = {}): Promise<unknown> {
    return this.request(endpointKey, { ...options, body: undefined, formEncoded: undefined })
  }

  async postForm(endpointKey: ApiEndpointKey, body: Record<string, unknown>, options: Omit<RequestOptions, 'body' | 'formEncoded'> = {}): Promise<unknown> {
    return this.request(endpointKey, { ...options, body, formEncoded: true })
  }
}
