import { AppContext } from '@/core/context'
import { getControllerFactories, getServiceFactories } from '@/core/runtimeRegistry'
import { createAppState, type AppState } from '@/app/appState'
import { registerRuntime } from './runtimeRegistrations'

export { createAppState }
export type { AppState }

export function buildAppContext(state?: AppState): AppContext {
  const appState = state || createAppState()

  registerRuntime()
  const serviceFactories = getServiceFactories()
  const controllerFactories = getControllerFactories()

  return new AppContext({
    state: appState,
    serviceFactories,
    controllerFactories,
  })
}
