import type { AppContext } from './context'
import { GenericRegistry } from './registry'

export type ServiceFactory = (ctx: AppContext) => unknown
export type ControllerFactory = (ctx: AppContext) => unknown

const serviceRegistry = new GenericRegistry<ServiceFactory>()
const controllerRegistry = new GenericRegistry<ControllerFactory>()

export function registerServiceFactory(id: string, factory: ServiceFactory): void {
  serviceRegistry.register(String(id), factory)
}

export function registerControllerFactory(id: string, factory: ControllerFactory): void {
  controllerRegistry.register(String(id), factory)
}

export function getServiceFactories(): Record<string, ServiceFactory> {
  return serviceRegistry.snapshot()
}

export function getControllerFactories(): Record<string, ControllerFactory> {
  return controllerRegistry.snapshot()
}

export function validateRuntimeRegistry(options: {
  requiredServices: string[]
  requiredControllers: string[]
}): void {
  serviceRegistry.validate(options.requiredServices, 'service')
  controllerRegistry.validate(options.requiredControllers, 'controller')
}

export function resetRuntimeRegistry(): void {
  serviceRegistry.clear()
  controllerRegistry.clear()
}
