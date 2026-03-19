import { describe, expect, it, vi } from 'vitest'
import { API_ENDPOINTS, getApiEndpointBinding, type ApiEndpointKey } from '@/api/registry'
import { ApiGatewayService } from '@/services/apiGatewayService'
import type { ApiClient } from '@/services/apiClient'

class TestApiGatewayService extends ApiGatewayService {}

function createApiClientMock(): ApiClient {
  return {
    get: vi.fn(async (path: string) => ({ method: 'GET', path })),
    post: vi.fn(async (path: string, body: unknown) => ({ method: 'POST', path, body })),
    postForm: vi.fn(async (path: string, body: unknown) => ({ method: 'POST_FORM', path, body })),
    put: vi.fn(async (path: string, body: unknown) => ({ method: 'PUT', path, body })),
    delete: vi.fn(async (path: string) => ({ method: 'DELETE', path })),
  } as unknown as ApiClient
}

describe('API Registry', () => {
  it('defines all expected endpoints', () => {
    const expectedKeys: readonly string[] = ['WEATHER_LIST', 'WEATHER_CREATE', 'OSSD_LIST', 'OSSD_CREATE', 'WITTERUNGSSTATION_PY_STATE_LIST', 'WITTERUNGSSTATION_PY_STATE_CREATE']
    
    for (const key of expectedKeys) {
      expect(API_ENDPOINTS).toHaveProperty(key)
    }
  })

  it('returns valid binding for each registered endpoint', () => {
    const endpointKeys = Object.values(API_ENDPOINTS) as ApiEndpointKey[]
    
    for (const key of endpointKeys) {
      const binding = getApiEndpointBinding(key)
      expect(binding).toBeDefined()
      expect(binding.method).toMatch(/^(GET|POST|PUT|DELETE)$/)
      expect(binding.path).toBeTruthy()
      expect(binding.path.startsWith('/')).toBe(true)
    }
  })
})

describe('ApiGatewayService', () => {
  it('dispatches GET requests to weather endpoint', async () => {
    const apiClient = createApiClientMock()
    const gateway = new TestApiGatewayService(apiClient)

    await gateway.get(API_ENDPOINTS.WEATHER_LIST)

    expect(apiClient.get).toHaveBeenCalledWith('/weather/', expect.any(Object))
  })

  it('dispatches GET requests to ossd endpoint', async () => {
    const apiClient = createApiClientMock()
    const gateway = new TestApiGatewayService(apiClient)

    await gateway.get(API_ENDPOINTS.OSSD_LIST)

    expect(apiClient.get).toHaveBeenCalledWith('/ossd/', expect.any(Object))
  })

  it('dispatches GET requests to python state endpoint', async () => {
    const apiClient = createApiClientMock()
    const gateway = new TestApiGatewayService(apiClient)

    await gateway.get(API_ENDPOINTS.WITTERUNGSSTATION_PY_STATE_LIST)

    expect(apiClient.get).toHaveBeenCalledWith('/witterungsstation_py_state/', expect.any(Object))
  })

  it('appends limit query parameter when provided', async () => {
    const apiClient = createApiClientMock()
    const gateway = new TestApiGatewayService(apiClient)

    await gateway.get(API_ENDPOINTS.WEATHER_LIST, { query: { limit: 10 } })

    expect(apiClient.get).toHaveBeenCalledWith(
      expect.stringContaining('limit=10'),
      expect.any(Object)
    )
  })

  it('dispatches POST requests with body', async () => {
    const apiClient = createApiClientMock()
    const gateway = new TestApiGatewayService(apiClient)

    await gateway.post(API_ENDPOINTS.WEATHER_CREATE, { temp: 20.0 })

    expect(apiClient.post).toHaveBeenCalledWith(
      '/weather/',
      { temp: 20.0 },
      expect.any(Object)
    )
  })

  it('dispatches form-encoded POST requests', async () => {
    const apiClient = createApiClientMock()
    const gateway = new TestApiGatewayService(apiClient)

    await gateway.postForm(API_ENDPOINTS.OSSD_CREATE, { ossdStatus: 'E' })

    expect(apiClient.postForm).toHaveBeenCalledWith(
      '/ossd/',
      { ossdStatus: 'E' },
      expect.any(Object)
    )
  })

  it('throws for unknown endpoint key', async () => {
    const apiClient = createApiClientMock()
    const gateway = new TestApiGatewayService(apiClient)

    await expect(gateway.request('UNKNOWN_ENDPOINT' as any)).rejects.toThrow('Unknown API endpoint key')
  })

  it('captures errors and provides lastError', async () => {
    const apiClient = createApiClientMock()
    vi.mocked(apiClient.get!).mockRejectedValue(new Error('Network error'))
    const gateway = new TestApiGatewayService(apiClient)

    await expect(gateway.get(API_ENDPOINTS.WEATHER_LIST)).rejects.toThrow('Network error')
    expect(gateway.lastError()).toContain('Network error')
  })

  it('clears error on successful request', async () => {
    const apiClient = createApiClientMock()
    vi.mocked(apiClient.get!)
      .mockRejectedValueOnce(new Error('First error'))
      .mockResolvedValueOnce([])
    const gateway = new TestApiGatewayService(apiClient)

    await expect(gateway.get(API_ENDPOINTS.WEATHER_LIST)).rejects.toThrow()
    expect(gateway.lastError()).toBeTruthy()

    await gateway.get(API_ENDPOINTS.WEATHER_LIST)
    expect(gateway.lastError()).toBe('')
  })
})
