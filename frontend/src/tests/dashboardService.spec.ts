import { describe, expect, it, vi } from 'vitest'
import { DashboardService } from '@/services/dashboardService'
import { API_ENDPOINTS } from '@/api/registry'
import type { ApiGatewayService } from '@/services/apiGatewayService'

class TestDashboardService extends DashboardService {}

function createApiGatewayMock() {
  return {
    request: vi.fn(),
  } as unknown as ApiGatewayService
}

describe('DashboardService', () => {
  it('fetches weather and ossd data from api gateway', async () => {
    const apiGateway = createApiGatewayMock()
    const weatherData = [
      { temp: 20.5, pressure: 1010, humidity: 50 },
    ]
    const ossdData = [
      { lichtgitterNr: 1, ossdNr: 1, ossdStatus: 'E' },
    ]

    apiGateway.request = vi.fn()
      .mockResolvedValueOnce(weatherData)
      .mockResolvedValueOnce(ossdData)
      .mockResolvedValueOnce([{ state: 'stop', time: '2026-01-01T13:00:00Z' }])

    const service = new TestDashboardService(apiGateway)
    const result = await service.loadDashboardData()
    const data = result!

    expect(apiGateway.request).toHaveBeenCalledTimes(3)
    expect(apiGateway.request).toHaveBeenNthCalledWith(1, API_ENDPOINTS.WEATHER_LIST, { query: { limit: 1000 } })
    expect(apiGateway.request).toHaveBeenNthCalledWith(2, API_ENDPOINTS.OSSD_LIST, { query: { limit: 1000 } })
    expect(apiGateway.request).toHaveBeenNthCalledWith(3, API_ENDPOINTS.WITTERUNGSSTATION_PY_STATE_LIST, { query: { limit: 1000 } })
    expect(data.weather).toHaveLength(1)
    expect(data.interrupts).toHaveLength(1)
    expect(data.appStates).toHaveLength(1)
  })

  it('normalizes weather data', async () => {
    const apiGateway = createApiGatewayMock()
    const weatherData = [
      {
        temp: 20.5,
        pressure: 1010.2,
        humidity: 50,
        light: 100,
        winds: 2.5,
        winddir: 'ne',
        rain: 0,
        time: '2026-01-01T12:00:00Z',
      },
    ]

    apiGateway.request = vi.fn()
      .mockResolvedValueOnce(weatherData)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])

    const service = new TestDashboardService(apiGateway)
    const result = await service.loadDashboardData()
    const data = result!

    expect(data.weather[0]!.temp).toBe(20.5)
    expect(data.weather[0]!.pressure).toBe(1010.2)
    expect(data.weather[0]!.winddir).toBe('NE')
  })

  it('normalizes ossd status to E or O', async () => {
    const apiGateway = createApiGatewayMock()

    apiGateway.request = vi.fn()
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        { lichtgitterNr: 1, ossdNr: 1, ossdStatus: 'E', time: '2026-01-01T12:00:00Z' },
        { lichtgitterNr: 1, ossdNr: 2, ossdStatus: 'O', time: '2026-01-01T12:00:00Z' },
        { lichtgitterNr: 2, ossdNr: 1, ossdStatus: 'E', time: '2026-01-01T12:00:00Z' },
        { lichtgitterNr: 2, ossdNr: 2, ossdStatus: 'O', time: '2026-01-01T12:00:00Z' },
      ])
      .mockResolvedValueOnce([])

    const service = new TestDashboardService(apiGateway)
    const result = await service.loadDashboardData()
    const data = result!

    expect(data.interrupts[0]!.ossdStatus).toBe('E')
    expect(data.interrupts[1]!.ossdStatus).toBe('O')
    expect(data.interrupts[2]!.ossdStatus).toBe('E')
    expect(data.interrupts[3]!.ossdStatus).toBe('O')
  })

  it('handles empty responses', async () => {
    const apiGateway = createApiGatewayMock()

    apiGateway.request = vi.fn()
      .mockResolvedValueOnce(null)
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce(undefined)

    const service = new TestDashboardService(apiGateway)
    const result = await service.loadDashboardData()

    const data = result!
    expect(data.weather).toEqual([])
    expect(data.interrupts).toEqual([])
    expect(data.appStates).toEqual([])
  })

  it('captures and exposes errors', async () => {
    const apiGateway = createApiGatewayMock()

    apiGateway.request = vi.fn().mockRejectedValue(new Error('Network error'))

    const service = new TestDashboardService(apiGateway)

    await expect(service.loadDashboardData()).rejects.toThrow()
    expect(service.lastError().toLowerCase()).toContain('network error')
  })

  it('clears error on successful request', async () => {
    const apiGateway = createApiGatewayMock()

    apiGateway.request = vi.fn()
      .mockRejectedValueOnce(new Error('First error'))
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])

    const service = new TestDashboardService(apiGateway)

    await expect(service.loadDashboardData()).rejects.toThrow()
    expect(service.lastError()).toBeTruthy()

    await service.loadDashboardData()
    expect(service.lastError()).toBe('')
  })
})
