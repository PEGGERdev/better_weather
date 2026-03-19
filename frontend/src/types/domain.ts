import type {
  BackendInterruptRecord,
  BackendOssdStatus,
  BackendWeatherRecord,
  BackendWitterungsstationPyStateRecord,
} from '@/api/generated/backendContract'

export type LichtgitterNr = 1 | 2
export type OssdNr = 1 | 2

export type WeatherRecord = BackendWeatherRecord

export type OssdStatus = BackendOssdStatus

export interface InterruptRecord extends Omit<BackendInterruptRecord, 'lichtgitterNr' | 'ossdNr' | 'ossdStatus'> {
  lichtgitterNr: LichtgitterNr
  ossdNr: OssdNr
  ossdStatus: OssdStatus
}

export type AppStateRecord = BackendWitterungsstationPyStateRecord

export interface DashboardData {
  weather: WeatherRecord[]
  interrupts: InterruptRecord[]
  appStates: AppStateRecord[]
}
