import { ref, watch, type Ref } from 'vue'

import type { ChartColorKey, ChartConfig } from '@/stores/uiStore'

const STORAGE_KEY = 'witterungs_chart_config_v1'

const defaultChartColors: Record<ChartColorKey, string> = {
  temp: '#e76f51',
  winds: '#e9c46a',
  humidity: '#2a9d8f',
  light: '#4cc9f0',
  pressure: '#ff6b6b',
  interrupts: '#d62828',
  offline: '#6d597a',
}

export const defaultChartConfig: ChartConfig = {
  timeUnit: 'hour',
  timeWindow: '24h',
  windowSpanPercent: 100,
  windowSpanMode: 'preset',
  autoY: true,
  yMax: undefined,
  tension: 0.4,
  visibleDatasets: {
    temp: true,
    winds: true,
    light: true,
    pressure: false,
    humidity: true,
    winddir: true,
    interrupts: true,
  },
  colors: defaultChartColors,
}

function cloneDefaultChartConfig(): ChartConfig {
  return {
    ...defaultChartConfig,
    visibleDatasets: { ...defaultChartConfig.visibleDatasets },
    colors: { ...defaultChartConfig.colors },
  }
}

function clampWindowSpanPercent(value: unknown): number {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) {
    return defaultChartConfig.windowSpanPercent
  }
  return Math.max(1, Math.min(100, Math.round(numeric)))
}

function mergeChartConfig(value: unknown): ChartConfig {
  const parsed = (value || {}) as Partial<ChartConfig> & {
    visibleDatasets?: Partial<ChartConfig['visibleDatasets']>
    colors?: Partial<ChartConfig['colors']>
  }

  return {
    timeUnit: parsed.timeUnit ?? defaultChartConfig.timeUnit,
    timeWindow: parsed.timeWindow ?? defaultChartConfig.timeWindow,
    windowSpanPercent: clampWindowSpanPercent(parsed.windowSpanPercent),
    windowSpanMode: parsed.windowSpanMode === 'manual' ? 'manual' : 'preset',
    autoY: parsed.autoY ?? defaultChartConfig.autoY,
    yMax: parsed.yMax ?? defaultChartConfig.yMax,
    tension: parsed.tension ?? defaultChartConfig.tension,
    visibleDatasets: {
      temp: parsed.visibleDatasets?.temp ?? defaultChartConfig.visibleDatasets.temp,
      winds: parsed.visibleDatasets?.winds ?? defaultChartConfig.visibleDatasets.winds,
      light: parsed.visibleDatasets?.light ?? defaultChartConfig.visibleDatasets.light,
      pressure: parsed.visibleDatasets?.pressure ?? defaultChartConfig.visibleDatasets.pressure,
      humidity: parsed.visibleDatasets?.humidity ?? defaultChartConfig.visibleDatasets.humidity,
      winddir: parsed.visibleDatasets?.winddir ?? defaultChartConfig.visibleDatasets.winddir,
      interrupts: parsed.visibleDatasets?.interrupts ?? defaultChartConfig.visibleDatasets.interrupts,
    },
    colors: {
      temp: parsed.colors?.temp ?? defaultChartColors.temp,
      winds: parsed.colors?.winds ?? defaultChartColors.winds,
      humidity: parsed.colors?.humidity ?? defaultChartColors.humidity,
      light: parsed.colors?.light ?? defaultChartColors.light,
      pressure: parsed.colors?.pressure ?? defaultChartColors.pressure,
      interrupts: parsed.colors?.interrupts ?? defaultChartColors.interrupts,
      offline: parsed.colors?.offline ?? defaultChartColors.offline,
    },
  }
}

function loadChartConfig(chartConfig: Ref<ChartConfig>): void {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    chartConfig.value = mergeChartConfig(JSON.parse(raw))
  } catch (error) {
    console.warn('ChartConfig: could not load config, using defaults', error)
    chartConfig.value = cloneDefaultChartConfig()
  }
}

function saveChartConfig(chartConfig: ChartConfig): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(chartConfig))
  } catch (error) {
    console.warn('ChartConfig: could not save config', error)
  }
}

export function useChartConfig(): { chartConfig: Ref<ChartConfig> } {
  const chartConfig = ref<ChartConfig>(cloneDefaultChartConfig())

  loadChartConfig(chartConfig)

  watch(
    chartConfig,
    (newValue) => {
      saveChartConfig(newValue)
    },
    { deep: true }
  )

  return { chartConfig }
}
