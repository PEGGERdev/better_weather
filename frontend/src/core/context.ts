export class AppContext {
  state: Record<string, unknown>
  private _serviceFactories: Record<string, (ctx: AppContext) => unknown>
  private _controllerFactories: Record<string, (ctx: AppContext) => unknown>
  private _services: Map<string, unknown>
  private _controllers: Map<string, unknown>

  constructor({
    state,
    serviceFactories,
    controllerFactories,
  }: {
    state?: Record<string, unknown>
    serviceFactories: Record<string, (ctx: AppContext) => unknown>
    controllerFactories: Record<string, (ctx: AppContext) => unknown>
  }) {
    this.state = state || {}
    this._serviceFactories = serviceFactories
    this._controllerFactories = controllerFactories
    this._services = new Map()
    this._controllers = new Map()
  }

  service(id: string): unknown {
    if (this._services.has(id)) {
      return this._services.get(id)
    }
    const factory = this._serviceFactories[id]
    if (!factory) {
      throw new Error(`Unknown service_id: ${id}`)
    }
    const service = factory(this)
    this._services.set(id, service)
    return service
  }

  controller(id: string): unknown {
    if (this._controllers.has(id)) {
      return this._controllers.get(id)
    }
    const factory = this._controllerFactories[id]
    if (!factory) {
      throw new Error(`Unknown controller_id: ${id}`)
    }
    const controller = factory(this)
    this._controllers.set(id, controller)
    return controller
  }

  reset(): void {
    this._services.clear()
    this._controllers.clear()
  }
}
