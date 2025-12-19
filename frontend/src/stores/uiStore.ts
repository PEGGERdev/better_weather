// src/stores/uiStore.ts
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export type ChartConfig = {
  visibleDatasets: {
    temp: boolean
    light: boolean
    humidity: boolean
  }
  timeUnit: 'minute' | 'hour' | 'day'
  tension: number
  autoY: boolean
  yMax?: number | null
}

export const useUiStore = defineStore('ui', () => {
  const expandedChart = ref<boolean>(false)
  const expandedChartId = ref<string | null>(null) // e.g. 'weather'
  const chartConfig = reactive<ChartConfig>({
    visibleDatasets: { temp: true, light: true, humidity: true },
    timeUnit: 'minute',
    tension: 0.25,
    autoY: true,
    yMax: null
  })

  function expandChart(id: string) {
    expandedChart.value = true
    expandedChartId.value = id
    // scroll to top maybe handled by page when expanded
  }
  function collapseChart() {
    expandedChart.value = false
    expandedChartId.value = null
  }

  function setChartConfig(patch: Partial<ChartConfig>) {
    Object.assign(chartConfig, patch)
  }

  return {
    expandedChart,
    expandedChartId,
    chartConfig,
    expandChart,
    collapseChart,
    setChartConfig
  }
})
