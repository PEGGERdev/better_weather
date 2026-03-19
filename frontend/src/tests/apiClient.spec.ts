import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiClient } from '@/services/apiClient'
import { ApiError, createApiError, toUserErrorMessage } from '@/services/apiErrors'

class TestApiClient extends ApiClient {}

describe('ApiError', () => {
  it('formats error message correctly', () => {
    const error = new ApiError({
      status: 404,
      method: 'GET',
      path: '/test',
      data: { message: 'Not found' },
    })

    expect(error.status).toBe(404)
    expect(error.method).toBe('GET')
    expect(error.path).toBe('/test')
    expect(String(error)).toContain('HTTP 404')
    expect(String(error)).toContain('GET')
    expect(String(error)).toContain('/test')
  })

  it('provides user-friendly messages for common status codes', () => {
    const cases = [
      { status: 400, expected: 'Invalid request' },
      { status: 401, expected: 'Authentication failed' },
      { status: 403, expected: 'Access denied' },
      { status: 404, expected: 'Requested resource was not found' },
      { status: 422, expected: 'Submitted data is invalid' },
      { status: 500, expected: 'Server error' },
    ]

    for (const { status, expected } of cases) {
      const error = new ApiError({ status, method: 'GET', path: '/test', data: null })
      expect(error.userMessage().toLowerCase()).toContain(expected.toLowerCase())
    }
  })

  it('extracts message from error data', () => {
    const error = new ApiError({
      status: 400,
      method: 'POST',
      path: '/test',
      data: { detail: 'Field is required' },
    })

    expect(error.userMessage()).toBe('Field is required')
  })

  it('extracts message from validation errors', () => {
    const error = new ApiError({
      status: 422,
      method: 'POST',
      path: '/test',
      data: {
        detail: [
          { loc: ['body', 'temp'], msg: 'Field required' },
        ],
      },
    })

    expect(error.userMessage()).toContain('temp')
    expect(error.userMessage()).toContain('Field required')
  })
})

describe('createApiError', () => {
  it('creates ApiError with defaults', () => {
    const error = createApiError()

    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(0)
    expect(error.method).toBe('GET')
    expect(error.path).toBe('')
  })
})

describe('toUserErrorMessage', () => {
  it('returns fallback when error is null', () => {
    expect(toUserErrorMessage(null, 'Fallback')).toBe('Fallback')
  })

  it('extracts message from ApiError', () => {
    const error = new ApiError({
      status: 404,
      method: 'GET',
      path: '/test',
      data: { detail: 'Not found' },
    })

    expect(toUserErrorMessage(error, 'Fallback')).toBe('Not found')
  })

  it('extracts message from generic error', () => {
    const error = new Error('Something went wrong')
    expect(toUserErrorMessage(error, 'Fallback')).toBe('Something went wrong')
  })
})

describe('ApiClient', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('makes GET request with correct URL', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ data: 'test' }),
    }))
    vi.stubGlobal('fetch', fetchMock)

    const client = new TestApiClient('http://api.test')
    const result = await client.get('/endpoint')

    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/endpoint',
      expect.objectContaining({
        method: 'GET',
      })
    )
    expect(result).toEqual({ data: 'test' })
  })

  it('makes POST request with JSON body', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ id: 1 }),
    }))
    vi.stubGlobal('fetch', fetchMock)

    const client = new TestApiClient('http://api.test')
    const result = await client.post('/endpoint', { name: 'test' })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/endpoint',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ name: 'test' }),
      })
    )
    expect(result).toEqual({ id: 1 })
  })

  it('throws ApiError on non-ok response', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: false,
      status: 404,
      text: async () => JSON.stringify({ detail: 'Not found' }),
    }))
    vi.stubGlobal('fetch', fetchMock)

    const client = new TestApiClient('http://api.test')

    await expect(client.get('/endpoint')).rejects.toThrow(ApiError)
  })

  it('strips trailing slash from base URL', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({}),
    }))
    vi.stubGlobal('fetch', fetchMock)

    const client = new TestApiClient('http://api.test/')
    await client.get('/endpoint')

    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/endpoint',
      expect.any(Object)
    )
  })

  it('tries both with and without trailing slash on 404', async () => {
    let calls = 0
    const fetchMock = vi.fn(async () => {
      calls++
      if (calls === 1) {
        return {
          ok: false,
          status: 404,
          text: async () => JSON.stringify({}),
        }
      }
      return {
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ found: true }),
      }
    })
    vi.stubGlobal('fetch', fetchMock)

    const client = new TestApiClient('http://api.test')
    const result = await client.get('/endpoint')

    expect(calls).toBe(2)
    expect(result).toEqual({ found: true })
  })

  it('keeps query string valid when trying trailing-slash variants', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ ok: true }),
    }))
    vi.stubGlobal('fetch', fetchMock)

    const client = new TestApiClient('http://api.test')
    await client.get('/weather?limit=10')

    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/weather?limit=10',
      expect.objectContaining({ method: 'GET' })
    )
  })
})
