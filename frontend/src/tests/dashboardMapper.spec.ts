import { describe, expect, it } from 'vitest'
import {
  normalizeAppStateRecord,
  normalizeWeatherRecord,
  normalizeInterruptRecord,
  normalizeDashboardData,
} from '@/models/dashboardMapper'

describe('normalizeWeatherRecord', () => {
  it('normalizes raw weather data', () => {
    const raw = {
      temp: 20.5,
      pressure: 1010.2,
      humidity: 50,
      light: 100,
      winds: 2.5,
      winddir: 'ne',
      rain: 0,
      time: '2026-01-01T12:00:00Z',
    }

    const result = normalizeWeatherRecord(raw)

    expect(result.temp).toBe(20.5)
    expect(result.pressure).toBe(1010.2)
    expect(result.humidity).toBe(50)
    expect(result.winddir).toBe('NE')
    expect(result.time).toBe('2026-01-01T12:00:00.000Z')
  })

  it('handles missing optional fields', () => {
    const raw = {
      temp: 20,
      pressure: 1000,
      humidity: 50,
      light: 100,
      winds: 0,
      winddir: '',
      rain: 0,
    }

    const result = normalizeWeatherRecord(raw)

    expect(result.temp).toBe(20)
    expect(result._id).toBeUndefined()
    expect(result.winddir).toBe('')
  })

  it('preserves _id when present', () => {
    const raw = {
      _id: 'abc123',
      temp: 20,
      pressure: 1000,
      humidity: 50,
      light: 0,
      winds: 0,
      winddir: 'N',
      rain: 0,
    }

    const result = normalizeWeatherRecord(raw)

    expect(result._id).toBe('abc123')
  })

  it('extracts Mongo-style _id and $date values', () => {
    const raw = {
      _id: { $oid: '699d4708acdf1fa57732595b' },
      temp: 20,
      pressure: 1000,
      humidity: 50,
      light: 0,
      winds: 0,
      winddir: 'N',
      rain: 0,
      time: { $date: '2026-02-24T06:36:56.715Z' },
    }

    const result = normalizeWeatherRecord(raw)

    expect(result._id).toBe('699d4708acdf1fa57732595b')
    expect(result.time).toBe('2026-02-24T06:36:56.715Z')
  })

  it('handles non-object input gracefully', () => {
    const result = normalizeWeatherRecord(null)

    expect(result.temp).toBe(0)
    expect(result.pressure).toBe(0)
  })

  it('defaults pressure to 0 when missing', () => {
    const raw = {
      temp: 20,
      humidity: 50,
      light: 0,
      winds: 0,
      winddir: 'N',
      rain: 0,
    }

    const result = normalizeWeatherRecord(raw)

    expect(result.pressure).toBe(0)
  })
})

describe('normalizeInterruptRecord', () => {
  it('normalizes raw interrupt data', () => {
    const raw = {
      lichtgitterNr: 1,
      ossdNr: 2,
      ossdStatus: 'E',
      time: '2026-01-01T12:00:00Z',
    }

    const result = normalizeInterruptRecord(raw)

    expect(result.lichtgitterNr).toBe(1)
    expect(result.ossdNr).toBe(2)
    expect(result.ossdStatus).toBe('E')
  })

  it('keeps canonical statuses E and O', () => {
    expect(normalizeInterruptRecord({ ossdStatus: 'E' }).ossdStatus).toBe('E')
    expect(normalizeInterruptRecord({ ossdStatus: 'O' }).ossdStatus).toBe('O')
  })

  it('defaults unknown status to O', () => {
    const raw = {
      ossdStatus: 'UNKNOWN',
    }

    const result = normalizeInterruptRecord(raw)

    expect(result.ossdStatus).toBe('O')
  })

  it('constrains lichtgitterNr to 1 or 2', () => {
    expect(normalizeInterruptRecord({ lichtgitterNr: 1 }).lichtgitterNr).toBe(1)
    expect(normalizeInterruptRecord({ lichtgitterNr: 2 }).lichtgitterNr).toBe(2)
    expect(normalizeInterruptRecord({ lichtgitterNr: 0 }).lichtgitterNr).toBe(1)
    expect(normalizeInterruptRecord({ lichtgitterNr: 3 }).lichtgitterNr).toBe(1)
  })

  it('constrains ossdNr to 1 or 2', () => {
    expect(normalizeInterruptRecord({ ossdNr: 1 }).ossdNr).toBe(1)
    expect(normalizeInterruptRecord({ ossdNr: 2 }).ossdNr).toBe(2)
    expect(normalizeInterruptRecord({ ossdNr: 0 }).ossdNr).toBe(1)
    expect(normalizeInterruptRecord({ ossdNr: 3 }).ossdNr).toBe(1)
  })

  it('preserves _id when present', () => {
    const raw = {
      _id: 'xyz789',
      lichtgitterNr: 1,
      ossdNr: 1,
      ossdStatus: 'O',
    }

    const result = normalizeInterruptRecord(raw)

    expect(result._id).toBe('xyz789')
  })

  it('extracts Mongo-style interrupt _id and $date', () => {
    const raw = {
      _id: { $oid: '699d4708acdf1fa57732595a' },
      lichtgitterNr: 1,
      ossdNr: 2,
      ossdStatus: 'E',
      time: { $date: '2026-02-24T06:36:56.715Z' },
    }

    const result = normalizeInterruptRecord(raw)

    expect(result._id).toBe('699d4708acdf1fa57732595a')
    expect(result.time).toBe('2026-02-24T06:36:56.715Z')
  })

  it('handles non-object input gracefully', () => {
    const result = normalizeInterruptRecord(null)

    expect(result.lichtgitterNr).toBe(1)
    expect(result.ossdNr).toBe(1)
    expect(result.ossdStatus).toBe('O')
  })
})

describe('normalizeAppStateRecord', () => {
  it('normalizes runtime state records', () => {
    const result = normalizeAppStateRecord({ _id: { $oid: 'state-1' }, state: 'STOP', time: '2026-01-01T12:00:00Z' })

    expect(result._id).toBe('state-1')
    expect(result.state).toBe('stop')
    expect(result.time).toBe('2026-01-01T12:00:00.000Z')
  })

  it('defaults unknown state to start', () => {
    expect(normalizeAppStateRecord({ state: 'unknown' }).state).toBe('start')
  })
})

describe('normalizeDashboardData', () => {
  it('combines weather and interrupt normalization', () => {
    const weatherRows = [
      { temp: 20, pressure: 1000, humidity: 50, light: 0, winds: 0, winddir: 'N', rain: 0 },
    ]
    const interruptRows = [
      { lichtgitterNr: 1, ossdNr: 1, ossdStatus: 'E' },
    ]
    const appStateRows = [
      { state: 'stop' },
    ]

    const result = normalizeDashboardData(weatherRows, interruptRows, appStateRows)

    expect(result.weather).toHaveLength(1)
    expect(result.interrupts).toHaveLength(1)
    expect(result.weather[0]!.temp).toBe(20)
    expect(result.interrupts[0]!.ossdStatus).toBe('E')
    expect(result.appStates[0]!.state).toBe('stop')
  })

  it('handles null/undefined inputs', () => {
    const result1 = normalizeDashboardData(null as any, undefined as any, null as any)
    const result2 = normalizeDashboardData({ temp: 20 } as any, undefined as any, undefined as any)
    const result3 = normalizeDashboardData(null as any, { ossdStatus: 'E' } as any, { state: 'stop' } as any)

    expect(result1.weather).toEqual([])
    expect(result1.interrupts).toEqual([])
    expect(result1.appStates).toEqual([])
    expect(result2!.weather).toEqual([])
    expect(result2!.interrupts).toEqual([])
    expect(result2!.appStates).toEqual([])
    expect(result3!.weather).toEqual([])
    expect(result3!.interrupts).toEqual([])
    expect(result3!.appStates).toEqual([])
  })

  it('processes multiple records', () => {
    const weatherRows = [
      { temp: 20, pressure: 1000, humidity: 50, light: 0, winds: 0, winddir: 'N', rain: 0 },
      { temp: 21, pressure: 1001, humidity: 51, light: 1, winds: 1, winddir: 'S', rain: 1 },
    ]
    const interruptRows = [
      { lichtgitterNr: 1, ossdNr: 1, ossdStatus: 'E' },
      { lichtgitterNr: 2, ossdNr: 2, ossdStatus: 'O' },
    ]
    const appStateRows = [
      { state: 'start' },
      { state: 'stop' },
    ]

    const result = normalizeDashboardData(weatherRows, interruptRows, appStateRows)

    expect(result.weather).toHaveLength(2)
    expect(result.interrupts).toHaveLength(2)
    expect(result.appStates).toHaveLength(2)
  })
})
