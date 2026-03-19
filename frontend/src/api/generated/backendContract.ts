// AUTO-GENERATED FILE. DO NOT EDIT.
// Source: backend/data/models.py

export type BackendOssdStatus = 'O' | 'E'

export interface BackendWeatherRecord {
  _id?: string
  temp: number
  pressure: number
  light: number
  winds: number
  winddir: string
  rain: number
  humidity: number
  time: string
}

export interface BackendInterruptRecord {
  _id?: string
  time: string
  lichtgitterNr: number
  ossdNr: number
  ossdStatus: 'O' | 'E'
}

export interface BackendWitterungsstationPyStateRecord {
  _id?: string
  time: string
  state: 'start' | 'stop'
}

export const BACKEND_ROUTES = {
  OSSD: '/ossd/',
  WEATHER: '/weather/',
  WITTERUNGSSTATION_PY_STATE: '/witterungsstation_py_state/',
} as const
