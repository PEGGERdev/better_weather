import type { AppContext } from '@/core/context'
import { BaseController } from './baseController'
import type { DashboardData } from '@/types/domain'
import type { DashboardService } from '@/services/dashboardService'

export class DashboardController extends BaseController {
  constructor(ctx: AppContext) {
    super(ctx, 'dashboard')
  }

  private dashboardService(): DashboardService {
    return this.service() as DashboardService
  }

  async loadDashboardData(): Promise<DashboardData> {
    return this.dashboardService().loadDashboardData()
  }

  async refresh(): Promise<DashboardData> {
    this.clearError()
    try {
      return await this.loadDashboardData()
    } catch (error) {
      this.dashboardService().captureError(error, 'Failed to refresh dashboard')
      throw error
    }
  }
}
