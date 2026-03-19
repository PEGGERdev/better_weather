import { inject, type InjectionKey } from 'vue'
import { AppContext } from './context'

export const APP_CTX_KEY: InjectionKey<AppContext> = Symbol('app-ctx')

export function useApp(): AppContext {
  const app = inject(APP_CTX_KEY)
  if (!app) {
    throw new Error('App context not provided')
  }
  return app
}

export function useService<T = unknown>(id: string): T {
  const app = useApp()
  return app.service(id) as T
}

export function useController<T = unknown>(id: string): T {
  const app = useApp()
  return app.controller(id) as T
}
