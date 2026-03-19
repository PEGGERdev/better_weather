import type { AppStateRecord, DashboardData, InterruptRecord, OssdStatus, WeatherRecord } from '@/types/domain'

function asNumber(value: unknown, fallback = 0): number {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function asMongoDate(value: unknown): unknown {
  if (!value || typeof value !== 'object') {
    return value
  }

  const candidate = value as { $date?: unknown }
  if (candidate.$date !== undefined) {
    return candidate.$date
  }
  return value
}

function asMongoId(value: unknown): string | undefined {
  if (typeof value === 'string') {
    return value
  }
  if (!value || typeof value !== 'object') {
    return undefined
  }
  const candidate = value as { $oid?: unknown }
  if (typeof candidate.$oid === 'string') {
    return candidate.$oid
  }
  return undefined
}

function asIsoTime(value: unknown): string {
  const normalized = asMongoDate(value)
  const ts = new Date((normalized as string | number | Date) || Date.now())
  if (Number.isNaN(ts.getTime())) {
    return new Date().toISOString()
  }
  return ts.toISOString()
}

function normalizeStatus(value: unknown): OssdStatus {
  const status = String(value || '').trim().toUpperCase()
  return status === 'E' ? 'E' : 'O'
}

export function normalizeWeatherRecord(item: unknown): WeatherRecord {
  const input = (item && typeof item === 'object') ? item as Record<string, unknown> : {}
  const pressure = asNumber(input.pressure)

  return {
    _id: asMongoId(input._id),
    temp: asNumber(input.temp),
    pressure,
    light: asNumber(input.light),
    winds: asNumber(input.winds),
    winddir: String(input.winddir || '').toUpperCase(),
    humidity: asNumber(input.humidity),
    rain: asNumber(input.rain),
    time: asIsoTime(input.time),
  }
}

export function normalizeInterruptRecord(item: unknown): InterruptRecord {
  const input = (item && typeof item === 'object') ? item as Record<string, unknown> : {}

  return {
    _id: asMongoId(input._id),
    lichtgitterNr: input.lichtgitterNr === 2 ? 2 : 1,
    ossdNr: input.ossdNr === 2 ? 2 : 1,
    ossdStatus: normalizeStatus(input.ossdStatus),
    time: asIsoTime(input.time),
  }
}

export function normalizeAppStateRecord(item: unknown): AppStateRecord {
  const input = (item && typeof item === 'object') ? item as Record<string, unknown> : {}
  const state = String(input.state || '').trim().toLowerCase()

  return {
    _id: asMongoId(input._id),
    state: state === 'stop' ? 'stop' : 'start',
    time: asIsoTime(input.time),
  }
}

export function normalizeDashboardData(weatherRows: unknown, interruptRows: unknown, appStateRows: unknown): DashboardData {
  const weather = Array.isArray(weatherRows) ? weatherRows.map((item) => normalizeWeatherRecord(item)) : []
  const interrupts = Array.isArray(interruptRows)
    ? interruptRows.map((item) => normalizeInterruptRecord(item))
    : []
  const appStates = Array.isArray(appStateRows)
    ? appStateRows.map((item) => normalizeAppStateRecord(item))
    : []

  return {
    weather,
    interrupts,
    appStates,
  }
}
