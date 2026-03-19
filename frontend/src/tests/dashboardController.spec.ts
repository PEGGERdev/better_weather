import { describe, expect, it, vi } from 'vitest'
import { AppContext } from '@/core/context'
import { DashboardController } from '@/controllers/dashboardController'
import { DashboardService } from '@/services/dashboardService'
import type { ApiGatewayService } from '@/services/apiGatewayService'

class TestDashboardController extends DashboardController {}
class TestDashboardService extends DashboardService {}

function createApiGatewayMock(): ApiGatewayService {
  return {
    request: vi.fn(),
  } as unknown as ApiGatewayService
}

function createContext() {
  const apiGateway = createApiGatewayMock()
  const dashboardService = new TestDashboardService(apiGateway)

  const ctx = new AppContext({
    state: {
      config: { apiBaseUrl: 'http://test' },
      dashboard: { loading: false, error: '' },
    },
    serviceFactories: {
      apiGateway: () => apiGateway,
      dashboard: () => dashboardService,
    },
    controllerFactories: {
      dashboard: (ctx) => new TestDashboardController(ctx),
    },
  })

  return { ctx, apiGateway, dashboardService }
}

describe('DashboardController', () => {
  it('loads dashboard data through service', async () => {
    const { ctx, apiGateway } = createContext()

    const weatherData = [{ temp: 20, pressure: 1000, humidity: 50, light: 0, winds: 0, winddir: 'N', rain: 0 }]
    const ossdData = [{ lichtgitterNr: 1, ossdNr: 1, ossdStatus: 'E' }]

    vi.mocked(apiGateway.request!)
      .mockResolvedValueOnce(weatherData)
      .mockResolvedValueOnce(ossdData)

    const controller = ctx.controller('dashboard') as DashboardController
    const result = await controller.loadDashboardData()

    expect(result.weather).toHaveLength(1)
    expect(result.interrupts).toHaveLength(1)
  })

  it('exposes service errors', async () => {
    const { ctx, apiGateway } = createContext()

    vi.mocked(apiGateway.request!).mockRejectedValue(new Error('Network error'))

    const controller = ctx.controller('dashboard') as DashboardController

    await expect(controller.loadDashboardData()).rejects.toThrow()
    expect(controller.lastError()).toBeTruthy()
  })

  it('clears error on refresh', async () => {
    const { ctx, apiGateway } = createContext()

    vi.mocked(apiGateway.request!)
      .mockRejectedValueOnce(new Error('Error'))
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])

    const controller = ctx.controller('dashboard') as DashboardController

    await expect(controller.loadDashboardData()).rejects.toThrow()
    expect(controller.lastError()).toBeTruthy()

    await controller.refresh()
    expect(controller.lastError()).toBe('')
  })
})

describe('AppContext integration with DashboardController', () => {
  it('wires controller to service through context', async () => {
    const apiGateway = createApiGatewayMock()
    const dashboardService = new TestDashboardService(apiGateway)

    vi.mocked(apiGateway.request!)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])

    const ctx = new AppContext({
      serviceFactories: {
        apiGateway: () => apiGateway,
        dashboard: () => dashboardService,
      },
      controllerFactories: {
        dashboard: (ctx) => new DashboardController(ctx),
      },
    })

    const controller = ctx.controller('dashboard') as DashboardController
    const result = await controller.loadDashboardData()

    expect(result).toBeDefined()
    expect(result.weather).toEqual([])
    expect(result.interrupts).toEqual([])
  })

  it('controller and service are singletons within context', () => {
    const apiGateway = createApiGatewayMock()
    const dashboardService = new TestDashboardService(apiGateway)

    const ctx = new AppContext({
      serviceFactories: {
        apiGateway: () => apiGateway,
        dashboard: () => dashboardService,
      },
      controllerFactories: {
        dashboard: (ctx) => new DashboardController(ctx),
      },
    })

    const service1 = ctx.service('dashboard')
    const service2 = ctx.service('dashboard')
    const controller1 = ctx.controller('dashboard')
    const controller2 = ctx.controller('dashboard')

    expect(service1).toBe(service2)
    expect(controller1).toBe(controller2)
  })
})
