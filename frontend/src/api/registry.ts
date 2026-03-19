import { BACKEND_ROUTES } from './generated/backendContract'

export const API_ENDPOINTS = {
  WEATHER_LIST: 'WEATHER_LIST',
  WEATHER_CREATE: 'WEATHER_CREATE',
  OSSD_LIST: 'OSSD_LIST',
  OSSD_CREATE: 'OSSD_CREATE',
  WITTERUNGSSTATION_PY_STATE_LIST: 'WITTERUNGSSTATION_PY_STATE_LIST',
  WITTERUNGSSTATION_PY_STATE_CREATE: 'WITTERUNGSSTATION_PY_STATE_CREATE',
} as const

export type ApiEndpointKey = typeof API_ENDPOINTS[keyof typeof API_ENDPOINTS]

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

export type ApiEndpointBinding = {
  method: HttpMethod
  path: string
  authenticated: boolean
  formEncoded?: boolean
}

const REGISTRY: Record<ApiEndpointKey, ApiEndpointBinding> = {
  [API_ENDPOINTS.WEATHER_LIST]: {
    method: 'GET',
    path: BACKEND_ROUTES.WEATHER,
    authenticated: false,
  },
  [API_ENDPOINTS.WEATHER_CREATE]: {
    method: 'POST',
    path: BACKEND_ROUTES.WEATHER,
    authenticated: false,
  },
  [API_ENDPOINTS.OSSD_LIST]: {
    method: 'GET',
    path: BACKEND_ROUTES.OSSD,
    authenticated: false,
  },
  [API_ENDPOINTS.OSSD_CREATE]: {
    method: 'POST',
    path: BACKEND_ROUTES.OSSD,
    authenticated: false,
  },
  [API_ENDPOINTS.WITTERUNGSSTATION_PY_STATE_LIST]: {
    method: 'GET',
    path: BACKEND_ROUTES.WITTERUNGSSTATION_PY_STATE,
    authenticated: false,
  },
  [API_ENDPOINTS.WITTERUNGSSTATION_PY_STATE_CREATE]: {
    method: 'POST',
    path: BACKEND_ROUTES.WITTERUNGSSTATION_PY_STATE,
    authenticated: false,
  },
}

export function getApiEndpointBinding(key: ApiEndpointKey): ApiEndpointBinding {
  const binding = REGISTRY[key]
  if (!binding) {
    throw new Error(`Unknown API endpoint key: ${String(key)}`)
  }
  return binding
}

export function getApiEndpointBindings(): Array<{ key: ApiEndpointKey; binding: ApiEndpointBinding }> {
  return Object.entries(REGISTRY).map(([key, binding]) => ({
    key: key as ApiEndpointKey,
    binding,
  }))
}
