import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import type { DashboardController } from '@/controllers/dashboardController'
import type { AppStateRecord, InterruptRecord, WeatherRecord } from '@/types/domain'

const REFRESH_INTERVAL_MS = 5_000

export function useDashboardRuntime(controller: DashboardController) {
  const weather = ref<WeatherRecord[]>([])
  const interrupts = ref<InterruptRecord[]>([])
  const appStates = ref<AppStateRecord[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  let refreshIntervalId: number | null = null

  async function refresh(): Promise<void> {
    loading.value = true
    try {
      const data = await controller.refresh()
      weather.value = data.weather
      interrupts.value = data.interrupts
      appStates.value = data.appStates
      error.value = null
    } catch (err: any) {
      console.error(err)
      error.value = controller.lastError() || err?.message || 'Unknown error'
    } finally {
      loading.value = false
    }
  }

  const latestWeather = computed((): WeatherRecord | null => {
    const items = [...weather.value].sort(
      (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()
    )

    if (items.length === 0) {
      return null
    }

    return items[items.length - 1] ?? null
  })

  onMounted(async () => {
    await refresh()
    refreshIntervalId = window.setInterval(refresh, REFRESH_INTERVAL_MS)
  })

  onBeforeUnmount(() => {
    if (refreshIntervalId !== null) {
      window.clearInterval(refreshIntervalId)
    }
  })

  return {
    weather,
    interrupts,
    appStates,
    loading,
    error,
    latestWeather,
    refresh,
  }
}
