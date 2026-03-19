import { describe, expect, it } from 'vitest'
import { AppContext } from '@/core/context'

describe('AppContext', () => {
  it('creates services lazily and caches them', () => {
    const calls: string[] = []

    class TestService {
      constructor() {
        calls.push('created')
      }
    }

    const ctx = new AppContext({
      serviceFactories: {
        test: () => new TestService(),
      },
      controllerFactories: {},
    })

    expect(calls).toHaveLength(0)

    const service1 = ctx.service('test')
    const service2 = ctx.service('test')

    expect(service1).toBeInstanceOf(TestService)
    expect(service1).toBe(service2)
    expect(calls).toHaveLength(1)
  })

  it('creates controllers lazily and caches them', () => {
    const calls: string[] = []

    class TestController {
      constructor() {
        calls.push('controller')
      }
    }

    const ctx = new AppContext({
      serviceFactories: {},
      controllerFactories: {
        test: () => new TestController(),
      },
    })

    expect(calls).toHaveLength(0)

    const controller1 = ctx.controller('test')
    const controller2 = ctx.controller('test')

    expect(controller1).toBeInstanceOf(TestController)
    expect(controller1).toBe(controller2)
    expect(calls).toHaveLength(1)
  })

  it('throws for unknown service', () => {
    const ctx = new AppContext({
      serviceFactories: {},
      controllerFactories: {},
    })

    expect(() => ctx.service('unknown')).toThrow('Unknown service_id: unknown')
  })

  it('throws for unknown controller', () => {
    const ctx = new AppContext({
      serviceFactories: {},
      controllerFactories: {},
    })

    expect(() => ctx.controller('unknown')).toThrow('Unknown controller_id: unknown')
  })

  it('allows services to access context state', () => {
    class ConfigService {
      constructor(private ctx: AppContext) {}
      getApiUrl() {
        return (this.ctx.state as { apiUrl: string }).apiUrl
      }
    }

    const ctx = new AppContext({
      state: { apiUrl: 'http://test:8000' },
      serviceFactories: {
        config: (ctx) => new ConfigService(ctx),
      },
      controllerFactories: {},
    })

    const config = ctx.service('config') as ConfigService
    expect(config.getApiUrl()).toBe('http://test:8000')
  })

  it('allows services to depend on other services', () => {
    class LoggerService {
      logs: string[] = []
      log(msg: string) {
        this.logs.push(msg)
      }
    }

    class ApiService {
      constructor(private ctx: AppContext) {}
      request(url: string) {
        const logger = this.ctx.service('logger') as LoggerService
        logger.log(`Request to ${url}`)
        return { data: 'ok' }
      }
    }

    const ctx = new AppContext({
      serviceFactories: {
        logger: () => new LoggerService(),
        api: (ctx) => new ApiService(ctx),
      },
      controllerFactories: {},
    })

    const api = ctx.service('api') as ApiService
    api.request('/test')

    const logger = ctx.service('logger') as LoggerService
    expect(logger.logs).toContain('Request to /test')
  })

  it('reset clears cached services and controllers', () => {
    const serviceCalls: string[] = []
    const controllerCalls: string[] = []

    const ctx = new AppContext({
      serviceFactories: {
        test: () => {
          serviceCalls.push('service')
          return {}
        },
      },
      controllerFactories: {
        test: () => {
          controllerCalls.push('controller')
          return {}
        },
      },
    })

    ctx.service('test')
    ctx.controller('test')
    expect(serviceCalls).toHaveLength(1)
    expect(controllerCalls).toHaveLength(1)

    ctx.reset()

    ctx.service('test')
    ctx.controller('test')
    expect(serviceCalls).toHaveLength(2)
    expect(controllerCalls).toHaveLength(2)
  })
})
