import { API_ENDPOINTS } from '@/api/registry'
import { normalizeDashboardData } from '@/models/dashboardMapper'

import { BaseService } from './baseService'
import type { ApiGatewayService } from './apiGatewayService'

export class DashboardService extends BaseService {
  api: ApiGatewayService
  static readonly WEATHER_LIMIT = 1000
  static readonly OSSD_LIMIT = 1000
  static readonly STATE_LIMIT = 1000

  constructor(api: ApiGatewayService) {
    super({ serviceName: 'dashboard' })
    this.api = api
  }

  async loadDashboardData() {
    try {
      const [weatherRows, interruptRows, appStateRows] = await Promise.all([
        this.api.request(API_ENDPOINTS.WEATHER_LIST, { query: { limit: DashboardService.WEATHER_LIMIT } }),
        this.api.request(API_ENDPOINTS.OSSD_LIST, { query: { limit: DashboardService.OSSD_LIMIT } }),
        this.api.request(API_ENDPOINTS.WITTERUNGSSTATION_PY_STATE_LIST, { query: { limit: DashboardService.STATE_LIMIT } }),
      ])
      this.clearError()
      return normalizeDashboardData(weatherRows, interruptRows, appStateRows)
    } catch (error) {
      this.captureError(error, 'Could not load dashboard data')
      throw error
    }
  }
}
