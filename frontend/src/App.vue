<template>
  <TwoColumnLayout>
    <template #left>
      <WebcamPanel />

      <OSSDStatusPanel
        :interrupts="interrupts"
        :loading="loading"
      />
    </template>

    <template #right>
      <TimeSeriesChart
        v-if="weather.length"
        :weather="weather"
        :interrupts="interrupts"
        :config="chartConfig"
      />

      <WeatherDetailsPanel
        :weather="latestWeather"
      />

      <BaseCard v-if="error">
        <p>Fehler beim Laden der Daten: {{ error }}</p>
      </BaseCard>
    </template>
  </TwoColumnLayout>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, computed, watch } from 'vue'
import TwoColumnLayout from './components/layout/TwoColumnLayout.vue'
import WebcamPanel from './components/webcam/WebcamPanel.vue'
import OSSDStatusPanel from './components/ossd/OSSDStatusPanel.vue'
import TimeSeriesChart from './components/chart/TimeSeriesChart.vue'
import WeatherDetailsPanel from './components/weather/WeatherDetailsPanel.vue'
import BaseCard from './components/base/BaseCard.vue'
import type { WeatherRecord, InterruptRecord } from './types/domain'
import { fetchDashboardData } from './services/api'
import type { ChartConfig } from '@/stores/uiStore' // Pfad wie im Projekt benutzen

const weather = ref<WeatherRecord[]>([])
const interrupts = ref<InterruptRecord[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

let refreshIntervalId: number | null = null

async function loadData() {
  loading.value = true
  try {
    const data = await fetchDashboardData()
    weather.value = data.weather
    interrupts.value = data.interrupts
    error.value = null
  } catch (err: any) {
    console.error(err)
    error.value = err?.message ?? 'Unbekannter Fehler'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadData()
  // entspricht dem Meta-Refresh der PHP-Seite (alle 60 Sekunden)
  refreshIntervalId = window.setInterval(loadData, 60_000)

  // lade chart config beim Start
  loadChartConfigFromStorage()
})

onBeforeUnmount(() => {
  if (refreshIntervalId !== null) {
    window.clearInterval(refreshIntervalId)
  }
})

// Latest Weather
const latestWeather = computed((): WeatherRecord | null => {
  const items = [...weather.value].sort(
    (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()
  )

  if (items.length === 0) {
    return null
  }

  return items[items.length - 1]!
})

// ----------------------
// ChartConfig: reactive + persistence (LocalStorage placeholder)
// ----------------------
const STORAGE_KEY = 'witterungs_chart_config_v1'

const defaultChartConfig: ChartConfig = {
  timeUnit: 'hour',
  autoY: true,
  yMax: undefined,
  tension: 0.4,
  visibleDatasets: {
    temp: true,
    light: true,
    humidity: true
  }
}

const chartConfig = ref<ChartConfig>({ ...defaultChartConfig })

function loadChartConfigFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw)
    // minimaler Validierungs-/Merge Schritt, damit fehlende Felder Default bekommen
    chartConfig.value = {
      timeUnit: parsed.timeUnit ?? defaultChartConfig.timeUnit,
      autoY: parsed.autoY ?? defaultChartConfig.autoY,
      yMax: parsed.yMax ?? defaultChartConfig.yMax,
      tension: parsed.tension ?? defaultChartConfig.tension,
      visibleDatasets: {
        temp: parsed.visibleDatasets?.temp ?? defaultChartConfig.visibleDatasets.temp,
        light: parsed.visibleDatasets?.light ?? defaultChartConfig.visibleDatasets.light,
        humidity: parsed.visibleDatasets?.humidity ?? defaultChartConfig.visibleDatasets.humidity
      }
    }
  } catch (e) {
    console.warn('ChartConfig: konnte nicht geladen werden, benutze Default', e)
    chartConfig.value = { ...defaultChartConfig }
  }
}

function saveChartConfigToStorage(cfg: ChartConfig) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg))
  } catch (e) {
    console.warn('ChartConfig: konnte nicht gespeichert werden', e)
  }
}

// speichere Änderungen automatisch (debounce erwägens, aber minimaler Implementierung)
watch(chartConfig, (newVal) => {
  saveChartConfigToStorage(newVal)
}, { deep: true })

// Optional: Funktion, die später die config in deiner DB/Tabelle speichert.
// exportiere oder rufe eine API auf, die /user-configs schreibt (nicht implementiert hier).
async function persistChartConfigToServer() {
  // Platzhalter: implementiere später POST /api/user/chart-config
  // await api.saveUserChartConfig(chartConfig.value)
}

</script>

<style>
:root {
  color-scheme: dark;
  --bg: #020617;
  --bg-elevated: #0f172a;
  --border-subtle: #1f2937;
  --accent: #38bdf8;
  --text: #e5e7eb;
  --text-muted: #9ca3af;
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background-color: var(--bg);
  color: var(--text);
}
</style>
