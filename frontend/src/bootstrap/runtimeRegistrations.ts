import { DashboardController } from '@/controllers/dashboardController'
import {
  registerControllerFactory,
  registerServiceFactory,
  resetRuntimeRegistry,
  validateRuntimeRegistry,
} from '@/core/runtimeRegistry'
import type { AppContext } from '@/core/context'
import { ApiClient } from '@/services/apiClient'
import { ApiGatewayService } from '@/services/apiGatewayService'
import { DashboardService } from '@/services/dashboardService'

export function resetRuntimeRegistrationState(): void {
  resetRuntimeRegistry()
}

export function registerRuntime(): void {
  resetRuntimeRegistry()

  registerServiceFactory('apiClient', (ctx: AppContext) => {
    const config = ctx.state.config as { apiBaseUrl: string }
    return new ApiClient(config.apiBaseUrl)
  })

  registerServiceFactory('apiGateway', (ctx: AppContext) => {
    return new ApiGatewayService(ctx.service('apiClient') as ApiClient)
  })

  registerServiceFactory('dashboard', (ctx: AppContext) => {
    return new DashboardService(ctx.service('apiGateway') as ApiGatewayService)
  })

  registerControllerFactory('dashboard', (ctx: AppContext) => {
    return new DashboardController(ctx)
  })

  validateRuntimeRegistry({
    requiredServices: ['apiClient', 'apiGateway', 'dashboard'],
    requiredControllers: ['dashboard'],
  })
}
