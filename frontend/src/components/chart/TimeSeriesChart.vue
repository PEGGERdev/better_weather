<template>
  <div class="ts-chart-root">
    <canvas ref="canvasEl"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import { Chart, registerables } from 'chart.js'
import 'chartjs-adapter-date-fns'
import type { WeatherRecord, InterruptRecord } from '@/types/domain'
import type { ChartConfig } from '@/stores/uiStore'

Chart.register(...registerables)

const props = defineProps<{
  weather: WeatherRecord[]
  interrupts: InterruptRecord[]
  config: ChartConfig
  collapsed?: boolean
}>()

const canvasEl = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

const sortedWeather = computed(() =>
  [...props.weather].sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
)

function buildConfig() {
  const tempsPts = sortedWeather.value.map(w => ({ x: w.time, y: w.temp }))
  const lightsPts = sortedWeather.value.map(w => ({ x: w.time, y: w.light }))
  const humsPts = sortedWeather.value.map(w => ({ x: w.time, y: w.humidity }))

  const numericValues = [...tempsPts, ...lightsPts, ...humsPts]
    .map(p => (typeof p.y === 'number' ? p.y : NaN))
    .filter(v => !isNaN(v)) as number[]
  const maxY = numericValues.length ? Math.max(...numericValues) : 1

  const interruptPoints = props.interrupts
    .filter(i => i.ossdStatus === 'INT')
    .map(i => {
      const weatherForInterrupt = sortedWeather.value.find(w => w.auto_id === i.fk_weather)
      const time = weatherForInterrupt?.time ?? i.time
      return { x: time, y: (props.config.autoY ? maxY * 1.05 : (props.config.yMax ?? maxY * 1.05)) }
    })

  const datasets: any[] = []

  if (props.config.visibleDatasets.temp) {
    datasets.push({
      label: 'Temperatur (°C)',
      data: tempsPts,
      borderColor: '#f97316',
      backgroundColor: 'rgba(249,115,22,0.12)',
      tension: props.config.tension,
      parsing: false
    })
  }
  if (props.config.visibleDatasets.light) {
    datasets.push({
      label: 'Licht',
      data: lightsPts,
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59,130,246,0.12)',
      tension: props.config.tension,
      parsing: false
    })
  }
  if (props.config.visibleDatasets.humidity) {
    datasets.push({
      label: 'Luftfeuchte (%)',
      data: humsPts,
      borderColor: '#22c55e',
      backgroundColor: 'rgba(34,197,94,0.12)',
      tension: props.config.tension,
      parsing: false
    })
  }

  datasets.push({
    type: 'scatter',
    label: 'Lichtgitter-Interrupt',
    data: interruptPoints,
    showLine: false,
    pointBackgroundColor: 'red',
    pointBorderColor: 'red',
    pointRadius: 7,
    pointStyle: 'cross',
    parsing: false
  })

  const options: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      tooltip: { mode: 'nearest', intersect: false },
      legend: { display: true }
    },
    scales: {
      x: {
        type: 'time',
        time: { unit: props.config.timeUnit, tooltipFormat: 'yyyy-MM-dd HH:mm:ss' },
        ticks: { autoSkip: true, maxRotation: 0 },
        title: { display: true, text: 'Zeit' }
      },
      y: {
        title: { display: true, text: 'Messwerte' },
        min: 0,
        max: props.config.autoY ? undefined : props.config.yMax ?? undefined
      }
    }
  }

  return { data: { datasets }, options }
}

function renderChart() {
  if (!canvasEl.value) return
  if (chart) { chart.destroy(); chart = null }

  const ctx = canvasEl.value.getContext('2d')
  if (!ctx) return

  const { data, options } = buildConfig()
  chart = new Chart(ctx, { type: 'line', data, options })
}

onMounted(() => {
  renderChart()
})

watch(() => [props.weather, props.interrupts, props.config], () => {
  renderChart()
}, { deep: true })

onBeforeUnmount(() => {
  if (chart) {
    chart.destroy()
    chart = null
  }
})
</script>

<style scoped>
.ts-chart-root {
  width: 100%;
  height: 100%;
}
canvas {
  width: 100% !important;
  height: 100% !important;
  display: block;
}
</style>
