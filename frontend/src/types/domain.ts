export type LichtgitterNr = 1 | 2
export type OssdNr = 1 | 2

export interface WeatherRecord {
  _id?: string            // optionales MongoDB id-Feld
  auto_id: number
  temp: number
  preassure: number
  light: number
  winds: number
  winddir: number
  humidity: number
  rain: number
  time: string
}

export type OssdStatus = 'INT' | 'OK'

export interface InterruptRecord {
  _id?: string            // optionales MongoDB id-Feld
  auto_id: number
  fk_weather: number
  lichtgitterNr: LichtgitterNr
  ossdNr: OssdNr
  ossdStatus: OssdStatus
  time: string
}

export interface DashboardData {
  weather: WeatherRecord[]
  interrupts: InterruptRecord[]
}