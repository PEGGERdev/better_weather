import { describe, expect, it, vi } from 'vitest'
import { buildAppContext, createAppState } from '@/bootstrap/appBootstrap'
import { ApiClient } from '@/services/apiClient'
import { ApiGatewayService } from '@/services/apiGatewayService'
import { DashboardService } from '@/services/dashboardService'
import { DashboardController } from '@/controllers/dashboardController'

describe('createAppState', () => {
  it('creates default state with api base url', () => {
    const state = createAppState()

    expect(state.config.apiBaseUrl).toBeDefined()
    expect(state.dashboard.loading).toBe(false)
    expect(state.dashboard.error).toBe('')
  })
})

describe('buildAppContext', () => {
  it('creates context with all required services', () => {
    const ctx = buildAppContext()

    expect(ctx.service('apiClient')).toBeInstanceOf(ApiClient)
    expect(ctx.service('apiGateway')).toBeInstanceOf(ApiGatewayService)
    expect(ctx.service('dashboard')).toBeInstanceOf(DashboardService)
  })

  it('creates context with all required controllers', () => {
    const ctx = buildAppContext()

    expect(ctx.controller('dashboard')).toBeInstanceOf(DashboardController)
  })

  it('services are singletons', () => {
    const ctx = buildAppContext()

    const apiClient1 = ctx.service('apiClient')
    const apiClient2 = ctx.service('apiClient')

    expect(apiClient1).toBe(apiClient2)
  })

  it('controllers are singletons', () => {
    const ctx = buildAppContext()

    const controller1 = ctx.controller('dashboard')
    const controller2 = ctx.controller('dashboard')

    expect(controller1).toBe(controller2)
  })

  it('apiGateway uses apiClient from context', () => {
    const ctx = buildAppContext()

    const apiClient = ctx.service('apiClient') as ApiClient
    const apiGateway = ctx.service('apiGateway') as ApiGatewayService

    // The gateway should have the api client as its api property
    expect((apiGateway as any).api).toBe(apiClient)
  })

  it('dashboard service uses apiGateway from context', () => {
    const ctx = buildAppContext()

    const apiGateway = ctx.service('apiGateway') as ApiGatewayService
    const dashboardService = ctx.service('dashboard') as DashboardService

    // The dashboard service should have the gateway as its api property
    expect((dashboardService as any).api).toBe(apiGateway)
  })

  it('uses custom state when provided', () => {
    const customState = createAppState()
    customState.config.apiBaseUrl = 'http://custom:8000'
    customState.dashboard.loading = true

    const ctx = buildAppContext(customState)

    expect((ctx.state as any).config.apiBaseUrl).toBe('http://custom:8000')
    expect((ctx.state as any).dashboard.loading).toBe(true)
  })
})

describe('Full integration flow', () => {
  it('can load dashboard data through context', async () => {
    const ctx = buildAppContext()

    const apiClient = ctx.service('apiClient') as ApiClient
    const fetchSpy = vi.fn(async () => ({
      ok: true,
      status: 200,
      text: async () => JSON.stringify([]),
    }))
    
    // Mock fetch globally
    vi.stubGlobal('fetch', fetchSpy)

    const controller = ctx.controller('dashboard') as DashboardController
    const result = await controller.loadDashboardData()

    expect(result).toBeDefined()
    expect(result.weather).toEqual([])
    expect(result.interrupts).toEqual([])

    vi.unstubAllGlobals()
  })
})
