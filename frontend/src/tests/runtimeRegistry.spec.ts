import { describe, expect, it } from 'vitest'
import { registerRuntime, resetRuntimeRegistrationState } from '@/bootstrap/runtimeRegistrations'
import { getControllerFactories, getServiceFactories, resetRuntimeRegistry } from '@/core/runtimeRegistry'

describe('Runtime registry', () => {
  it('registers service and controller factories', () => {
    resetRuntimeRegistry()
    resetRuntimeRegistrationState()
    registerRuntime()

    const services = getServiceFactories()
    const controllers = getControllerFactories()

    expect(services.apiClient).toBeTypeOf('function')
    expect(services.apiGateway).toBeTypeOf('function')
    expect(services.dashboard).toBeTypeOf('function')
    expect(controllers.dashboard).toBeTypeOf('function')
  })
})
