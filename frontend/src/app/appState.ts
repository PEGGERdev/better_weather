const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ||
  'http://127.0.0.1:8000'

export interface AppState {
  config: {
    apiBaseUrl: string
  }
  dashboard: {
    loading: boolean
    error: string
  }
  [key: string]: unknown
}

export function createAppState(): AppState {
  return {
    config: {
      apiBaseUrl: API_BASE,
    },
    dashboard: {
      loading: false,
      error: '',
    },
  }
}
