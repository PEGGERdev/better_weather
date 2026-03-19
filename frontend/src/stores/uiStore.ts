export type ChartColorKey = 'temp' | 'winds' | 'humidity' | 'light' | 'pressure' | 'interrupts' | 'offline'

export type ChartConfig = {
  visibleDatasets: {
    temp: boolean
    winds: boolean
    light: boolean
    pressure: boolean
    humidity: boolean
    winddir: boolean
    interrupts: boolean
  }
  timeWindow: '6h' | '24h' | '7d' | 'all'
  timeUnit: 'minute' | 'hour' | 'day'
  windowSpanPercent: number
  windowSpanMode: 'preset' | 'manual'
  tension: number
  autoY: boolean
  yMax?: number | null
  colors: Record<ChartColorKey, string>
}
