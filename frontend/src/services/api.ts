// src/services/api.ts
import type { DashboardData } from '../types/domain'

const USE_MOCK: boolean = true

const mockData: DashboardData = {
  weather: [
    {
      auto_id: 1,
      temp: 21.4,
      preassure: 1018,
      light: 300,
      winds: 2.5,
      winddir: 180,
      humidity: 45,
      rain: 0,
      time: '2025-01-01 10:00:00'
    },
    {
      auto_id: 2,
      temp: 22.1,
      preassure: 1017,
      light: 450,
      winds: 3.1,
      winddir: 200,
      humidity: 40,
      rain: 0,
      time: '2025-01-01 10:05:00'
    },
    {
      auto_id: 3,
      temp: 22.0,
      preassure: 1016,
      light: 460,
      winds: 4.0,
      winddir: 210,
      humidity: 42,
      rain: 0,
      time: '2025-01-01 10:10:00'
    }
  ],
  interrupts: [
    {
      auto_id: 10,
      fk_weather: 2,
      lichtgitterNr: 1,
      ossdNr: 1,
      ossdStatus: 'INT',
      time: '2025-01-01 10:05:02'
    },
    {
      auto_id: 11,
      fk_weather: 3,
      lichtgitterNr: 2,
      ossdNr: 2,
      ossdStatus: 'INT',
      time: '2025-01-01 10:10:01'
    }
  ]
}

export async function fetchDashboardData(): Promise<DashboardData> {
  if (USE_MOCK) {
    return Promise.resolve(mockData)
  }

  const res = await fetch('/api/dashboard-data.php')
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }
  const data = (await res.json()) as DashboardData
  return data
}
