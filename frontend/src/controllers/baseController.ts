import type { AppContext } from '@/core/context'

export class BaseController {
  protected ctx: AppContext
  protected serviceId: string

  constructor(ctx: AppContext, serviceId: string) {
    this.ctx = ctx
    this.serviceId = serviceId
  }

  protected service(): unknown {
    return this.ctx.service(this.serviceId)
  }

  lastError(): string {
    const service = this.service() as { lastError?: () => string } | undefined
    if (!service || typeof service.lastError !== 'function') {
      return ''
    }
    return service.lastError()
  }

  clearError(): void {
    const service = this.service() as { clearError?: () => void } | undefined
    if (service && typeof service.clearError === 'function') {
      service.clearError()
    }
  }
}
