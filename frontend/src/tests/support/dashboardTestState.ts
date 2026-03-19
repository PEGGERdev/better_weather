import type { WidgetState } from '@/core/widgetRegistry'

export function createDashboardTestState(overrides: Partial<WidgetState> = {}): WidgetState {
  const weather = [
    {
      _id: 'weather-1',
      temp: 21.4,
      pressure: 1009.3,
      light: 420,
      winds: 2.1,
      winddir: 'NE',
      rain: 0,
      humidity: 55,
      time: '2026-03-11T14:00:00+00:00',
    },
  ]

  const interrupts = [
    {
      _id: 'ossd-1',
      time: '2026-03-11T14:01:00+00:00',
      lichtgitterNr: 1,
      ossdNr: 1,
      ossdStatus: 'E',
    },
    {
      _id: 'ossd-2',
      time: '2026-03-11T14:02:00+00:00',
      lichtgitterNr: 1,
      ossdNr: 2,
      ossdStatus: 'O',
    },
  ]

  const appStates = [
    {
      _id: 'state-1',
      time: '2026-03-11T12:30:00+00:00',
      state: 'stop',
    },
    {
      _id: 'state-2',
      time: '2026-03-11T13:10:00+00:00',
      state: 'start',
    },
  ]

  return {
    weather,
    interrupts,
    appStates,
    loading: false,
    error: null,
    latestWeather: weather[0],
    chartConfig: {
      visibleDatasets: {
        temp: true,
        winds: true,
        light: true,
        pressure: false,
        humidity: true,
        winddir: true,
        interrupts: true,
      },
      timeWindow: '24h',
      timeUnit: 'hour',
      windowSpanPercent: 100,
      windowSpanMode: 'preset',
      tension: 0.4,
      autoY: true,
      yMax: null,
      colors: {
        temp: '#e76f51',
        winds: '#e9c46a',
        humidity: '#2a9d8f',
        light: '#4cc9f0',
        pressure: '#ff6b6b',
        interrupts: '#d62828',
        offline: '#6d597a',
      },
    },
    ...overrides,
  }
}
