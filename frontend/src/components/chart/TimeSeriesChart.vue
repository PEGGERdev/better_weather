<template>
  <BaseCard data-testid="widget-time-series-card">
      <BaseSectionTitle title="Zeitverlauf" subtitle="Wetterwerte, OSSD-Interrupts und Offline-Zeiten" />

    <div v-if="!weatherPoints.length" class="ts-chart-empty" data-testid="widget-time-series-empty">
      Keine Wetterdaten fuer den Zeitverlauf vorhanden.
    </div>

    <div v-else class="ts-chart-shell" :class="{ 'ts-chart-shell--expanded': !!expanded }" data-testid="widget-time-series">
      <ChartControlsPanel
        :dataset-controls="datasetControls"
        :color-controls="colorControls"
        :time-window="draftConfig.timeWindow"
        :has-pending-changes="hasPendingConfigChanges"
        :time-window-options="timeWindowOptions"
        :summary="windowSummary"
        :slider-value="sliderValue"
        :window-span-percent="draftConfig.windowSpanPercent"
        :window-span-label="draftWindowSpanLabel"
        :can-pan-window="canPanWindow"
        :can-reset="canResetView"
        @toggle-dataset="toggleDataset"
        @apply-palette="applyPalette"
        @update-color="updateColor"
        @update-time-window="onTimeWindowChange"
        @update-window-span="onWindowSpanInput"
        @update-slider="onSliderInput"
        @shift-window="shiftWindow"
        @apply-settings="applySettings"
        @reset-draft="resetDraftSettings"
        @reset="resetToLatest"
      />

      <p class="ts-chart-summary" data-testid="widget-time-series-window-label">
        {{ windowSummary }}
      </p>

      <div v-if="props.config.visibleDatasets.winddir" class="ts-chart-wind-legend" data-testid="widget-time-series-wind-legend">
        <span class="ts-chart-wind-legend__label">Windfarben</span>
        <span class="ts-chart-wind-legend__bar" aria-hidden="true"></span>
        <span class="ts-chart-wind-legend__item">N schwarz</span>
        <span class="ts-chart-wind-legend__item">E blau</span>
        <span class="ts-chart-wind-legend__item">S weiss</span>
        <span class="ts-chart-wind-legend__item">W gelb</span>
      </div>

      <div v-if="!visibleWeatherPoints.length && !visibleInterruptRows.length && !offlineBands.length" class="ts-chart-empty ts-chart-empty--window" data-testid="widget-time-series-window-empty">
        Keine Wetterdaten im gewaehlten Zeitraum.
      </div>

      <div v-else class="ts-chart-canvas-frame">
        <svg
          ref="chartSvg"
          class="ts-chart-svg"
          data-testid="widget-time-series-canvas"
          viewBox="0 0 960 360"
          preserveAspectRatio="none"
          @pointerdown="startZoomSelection"
          @pointermove="updateZoomSelection"
          @pointerup="finishZoomSelection"
          @pointerleave="cancelZoomSelection"
          @pointercancel="cancelZoomSelection"
        >
          <rect x="0" y="0" width="960" height="360" rx="18" class="ts-chart-bg" />

          <line
            v-for="tick in yTicks"
            :key="`grid-${tick.value}`"
            :x1="PLOT.left"
            :x2="PLOT.right"
            :y1="tick.y"
            :y2="tick.y"
            class="ts-chart-grid"
          />

          <line
            v-for="(tick, index) in xTicks"
            :key="`x-grid-${index}-${tick.x}`"
            :x1="tick.x"
            :x2="tick.x"
            :y1="PLOT.top"
            :y2="PLOT.bottom"
            class="ts-chart-grid ts-chart-grid--vertical"
          />

          <line :x1="PLOT.left" :x2="PLOT.left" :y1="PLOT.top" :y2="PLOT.bottom" class="ts-chart-axis" />
          <line :x1="PLOT.left" :x2="PLOT.right" :y1="PLOT.bottom" :y2="PLOT.bottom" class="ts-chart-axis" />
          <line v-if="showAuxiliaryAxis" :x1="AUXILIARY_AXIS_X" :x2="AUXILIARY_AXIS_X" :y1="PLOT.top" :y2="PLOT.bottom" class="ts-chart-axis ts-chart-axis--auxiliary" />

          <rect
            v-for="band in offlineBands"
            :key="band.id"
            :x="band.x"
            :y="PLOT.top"
            :width="band.width"
            :height="PLOT.bottom - PLOT.top"
            class="ts-chart-offline-band"
            :style="offlineBandStyle"
            @pointerenter="showTooltip(band.hover, $event)"
            @pointermove="moveTooltip($event)"
            @pointerleave="hideTooltip"
          >
            <title>{{ band.hover.description }}</title>
          </rect>

          <rect
            v-for="band in windDirectionBands"
            :key="band.id"
            :x="band.x"
            :y="PLOT.top"
            :width="band.width"
            :height="PLOT.bottom - PLOT.top"
            :fill="band.color"
            class="ts-chart-wind-band"
            @pointerenter="showTooltip(band.hover, $event)"
            @pointermove="moveTooltip($event)"
            @pointerleave="hideTooltip"
          >
            <title>{{ band.hover.description }}</title>
          </rect>

          <polyline
            v-if="tempPolyline"
            :points="tempPolyline"
            class="ts-chart-line ts-chart-line--temp"
            :style="lineStyle('temp')"
          />
          <polyline
            v-if="windsPolyline"
            :points="windsPolyline"
            class="ts-chart-line ts-chart-line--winds"
            :style="lineStyle('winds')"
          />
          <polyline
            v-if="humidityPolyline"
            :points="humidityPolyline"
            class="ts-chart-line ts-chart-line--humidity"
            :style="lineStyle('humidity')"
          />
          <polyline
            v-if="lightPolyline"
            :points="lightPolyline"
            class="ts-chart-line ts-chart-line--light"
            :style="lineStyle('light')"
          />
          <polyline
            v-if="pressurePolyline"
            :points="pressurePolyline"
            class="ts-chart-line ts-chart-line--pressure"
            :style="lineStyle('pressure')"
          />

          <g v-for="marker in interruptMarkers" :key="`interrupt-${marker.id}`" class="ts-chart-interrupt" :style="interruptStyle">
            <line :x1="marker.x - 6" :x2="marker.x + 6" :y1="marker.y - 6" :y2="marker.y + 6" />
            <line :x1="marker.x - 6" :x2="marker.x + 6" :y1="marker.y + 6" :y2="marker.y - 6" />
            <line :x1="marker.x" :x2="marker.x" :y1="PLOT.top" :y2="PLOT.bottom" class="ts-chart-interrupt__stem" :style="interruptStemStyle" />
          </g>

          <rect
            v-if="selectionRect"
            :x="selectionRect.x"
            :y="PLOT.top"
            :width="selectionRect.width"
            :height="PLOT.bottom - PLOT.top"
            class="ts-chart-selection"
          />

          <text v-for="tick in yTicks" :key="`y-label-${tick.value}`" :x="PLOT.left - 12" :y="tick.y + 4" class="ts-chart-label ts-chart-label--left">
            {{ tick.label }}
          </text>
          <text v-for="tick in auxiliaryTicks" :key="`aux-label-${tick.value}`" :x="AUXILIARY_AXIS_X + 12" :y="tick.y + 4" class="ts-chart-label ts-chart-label--right ts-chart-label--auxiliary">
            {{ tick.label }}
          </text>
          <text v-for="(tick, index) in xTicks" :key="`x-label-${index}-${tick.x}`" :x="tick.x" :y="PLOT.bottom + 24" class="ts-chart-label ts-chart-label--bottom">
            {{ tick.label }}
          </text>

          <text :x="PLOT.left" :y="24" class="ts-chart-caption">Temp / Luftfeuchte / Wind</text>
          <text v-if="props.config.visibleDatasets.winddir" :x="PLOT.left" :y="PLOT.top + 18" class="ts-chart-caption ts-chart-caption--wind">Windrichtung als Hintergrundfarbe</text>
          <text v-if="showAuxiliaryAxis" :x="AUXILIARY_AXIS_X" :y="24" class="ts-chart-caption ts-chart-caption--right ts-chart-caption--auxiliary">Licht (x1000) / Druck</text>

          <g v-for="target in hoverTargets" :key="target.id">
            <circle
              :cx="target.x"
              :cy="target.y"
              r="11"
              class="ts-chart-hover-target"
              @pointerenter="showTooltip(target, $event)"
              @pointermove="moveTooltip($event)"
              @pointerleave="hideTooltip"
            >
              <title>{{ target.description }}</title>
            </circle>
          </g>
        </svg>

        <div
          v-if="tooltip"
          class="ts-chart-tooltip"
          :style="{ left: `${tooltip.left}px`, top: `${tooltip.top}px` }"
        >
          <p class="ts-chart-tooltip__title">{{ tooltip.title }}</p>
          <p class="ts-chart-tooltip__body">{{ tooltip.body }}</p>
        </div>
      </div>
    </div>
  </BaseCard>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseCard from '@/components/base/BaseCard.vue'
import BaseSectionTitle from '@/components/base/BaseSectionTitle.vue'
import ChartControlsPanel from '@/components/chart/ChartControlsPanel.vue'
import type { AppStateRecord, InterruptRecord, WeatherRecord } from '@/types/domain'
import type { ChartColorKey, ChartConfig } from '@/stores/uiStore'

type ChartPoint = {
  id: string
  x: number
  y: number
}

type SeriesPoint = ChartPoint & {
  value: number
}

type Tick = {
  value: number
  y: number
  label: string
}

type TimeWindowOption = {
  value: ChartConfig['timeWindow']
  label: string
}

type DatasetControl = {
  key: keyof ChartConfig['visibleDatasets']
  label: string
  active: boolean
  swatch: string
}

type ColorControl = {
  key: ChartColorKey
  label: string
  value: string
}

type HoverTarget = {
  id: string
  x: number
  y: number
  title: string
  body: string
  description: string
}

type TooltipState = {
  title: string
  body: string
  left: number
  top: number
}

const props = defineProps<{
  weather: WeatherRecord[]
  interrupts: InterruptRecord[]
  appStates: AppStateRecord[]
  config: ChartConfig
  collapsed?: boolean
  expanded?: boolean
}>()

const WIDTH = 960
const HEIGHT = 360
const AUXILIARY_AXIS_X = WIDTH - 72
const PLOT = {
  left: 76,
  right: WIDTH - 104,
  top: 34,
  bottom: HEIGHT - 40,
}

const timeWindowOptions: TimeWindowOption[] = [
  { value: '6h', label: 'Letzte 6 Stunden' },
  { value: '24h', label: 'Letzte 24 Stunden' },
  { value: '7d', label: 'Letzte 7 Tage' },
  { value: 'all', label: 'Komplette Historie' },
]

const COLOR_PALETTES: Record<'default' | 'colorblind' | 'highContrast', Record<ChartColorKey, string>> = {
  default: {
    temp: '#e76f51',
    winds: '#e9c46a',
    humidity: '#2a9d8f',
    light: '#4cc9f0',
    pressure: '#ff6b6b',
    interrupts: '#d62828',
    offline: '#6d597a',
  },
  colorblind: {
    temp: '#d55e00',
    winds: '#e69f00',
    humidity: '#009e73',
    light: '#56b4e9',
    pressure: '#cc79a7',
    interrupts: '#000000',
    offline: '#7f7f7f',
  },
  highContrast: {
    temp: '#ff7f11',
    winds: '#ffd000',
    humidity: '#00d1b2',
    light: '#00bbf9',
    pressure: '#ff006e',
    interrupts: '#ffffff',
    offline: '#9b5de5',
  },
}

const PAN_STEP_PERCENT = 10

function cloneChartConfig(config: ChartConfig): ChartConfig {
  return {
    ...config,
    visibleDatasets: { ...config.visibleDatasets },
    colors: { ...config.colors },
  }
}

function configsEqual(left: ChartConfig, right: ChartConfig): boolean {
  return JSON.stringify(left) === JSON.stringify(right)
}

const sliderValue = ref(100)
const chartSvg = ref<SVGSVGElement | null>(null)
const zoomSelection = ref<{ startX: number; currentX: number } | null>(null)
const zoomRange = ref<{ min: number; max: number } | null>(null)
const tooltip = ref<TooltipState | null>(null)
const draftConfig = ref<ChartConfig>(cloneChartConfig(props.config))

watch(
  () => props.config,
  (value) => {
    draftConfig.value = cloneChartConfig(value)
  },
  { deep: true }
)

const weatherPoints = computed(() =>
  [...props.weather]
    .map((entry, index) => ({
      ...entry,
      timeMs: new Date(entry.time).getTime(),
      id: entry._id ?? `weather-${index}`,
      tempValue: Number(entry.temp),
      windsValue: Number(entry.winds),
      humidityValue: Number(entry.humidity),
      pressureValue: Number(entry.pressure),
      lightValue: Number(entry.light),
      lightDisplayValue: Number(entry.light) / 1000,
      windDirectionAngle: parseWindDirection(entry.winddir),
    }))
    .filter((entry) => Number.isFinite(entry.timeMs))
    .sort((a, b) => a.timeMs - b.timeMs),
)

const interruptRows = computed(() =>
  [...props.interrupts]
    .map((entry, index) => ({
      ...entry,
      timeMs: new Date(entry.time).getTime(),
      id: entry._id ?? `interrupt-${index}`,
    }))
    .filter((entry) => Number.isFinite(entry.timeMs) && entry.ossdStatus === 'E')
    .sort((a, b) => a.timeMs - b.timeMs),
)

const appStateRows = computed(() =>
  [...props.appStates]
    .map((entry, index) => ({
      ...entry,
      timeMs: new Date(entry.time).getTime(),
      id: entry._id ?? `app-state-${index}`,
      state: entry.state === 'stop' ? 'stop' : 'start',
    }))
    .filter((entry) => Number.isFinite(entry.timeMs))
    .sort((a, b) => a.timeMs - b.timeMs),
)

const fullTimeRange = computed(() => {
  const times = [
    ...weatherPoints.value.map((entry) => entry.timeMs),
    ...interruptRows.value.map((entry) => entry.timeMs),
    ...appStateRows.value.map((entry) => entry.timeMs),
  ]

  if (!times.length) {
    return { min: 0, max: 1 }
  }
  const min = Math.min(...times)
  const max = Math.max(...times)
  return { min, max: max === min ? min + 60_000 : max }
})

const fullSpan = computed(() => fullTimeRange.value.max - fullTimeRange.value.min)

function presetDurationFor(config: ChartConfig, span: number): number {
  switch (config.timeWindow) {
    case '6h':
      return Math.min(span, 6 * 60 * 60 * 1000)
    case '24h':
      return Math.min(span, 24 * 60 * 60 * 1000)
    case '7d':
      return Math.min(span, 7 * 24 * 60 * 60 * 1000)
    case 'all':
    default:
      return span
  }
}

function clampWindowSpan(span: number, value: number): number {
  if (span <= 0) {
    return 100
  }
  return Math.max(1, Math.min(100, Math.round(value)))
}

function durationToPercent(durationMs: number, spanMs: number): number {
  if (spanMs <= 0) {
    return 100
  }
  return clampWindowSpan(spanMs, (durationMs / spanMs) * 100)
}

const activeWindowDuration = computed(() => {
  const span = fullSpan.value
  const presetDuration = presetDurationFor(props.config, span)

  if (props.config.windowSpanMode !== 'manual') {
    return Math.max(60_000, presetDuration)
  }

  const manualDuration = span * (props.config.windowSpanPercent / 100)
  return Math.min(span, Math.max(60_000, manualDuration || presetDuration))
})

const windowSpanLabel = computed(() => formatDuration(activeWindowDuration.value))
const draftWindowSpanLabel = computed(() => {
  const span = fullSpan.value
  const presetDuration = presetDurationFor(draftConfig.value, span)
  if (draftConfig.value.windowSpanMode !== 'manual') {
    return formatDuration(Math.max(60_000, presetDuration))
  }
  return formatDuration(Math.min(span, Math.max(60_000, span * (draftConfig.value.windowSpanPercent / 100) || presetDuration)))
})
const hasPendingConfigChanges = computed(() => !configsEqual(draftConfig.value, props.config))

watch(fullSpan, (span) => {
  if (span <= 0) {
    sliderValue.value = 100
    props.config.windowSpanPercent = 100
    props.config.windowSpanMode = 'preset'
    return
  }

  if (props.config.windowSpanMode === 'manual') {
    props.config.windowSpanPercent = clampWindowSpan(span, props.config.windowSpanPercent)
  }
})

const canPanWindow = computed(() => activeWindowDuration.value < fullSpan.value)

const windowStartMs = computed(() => {
  if (!canPanWindow.value) {
    return fullTimeRange.value.min
  }
  const maxStart = fullTimeRange.value.max - activeWindowDuration.value
  return fullTimeRange.value.min + (maxStart - fullTimeRange.value.min) * (sliderValue.value / 100)
})

const windowEndMs = computed(() => windowStartMs.value + activeWindowDuration.value)

const baseTimeRange = computed(() => ({
  min: windowStartMs.value,
  max: Math.max(windowEndMs.value, windowStartMs.value + 60_000),
}))

watch(
  () => props.config.timeWindow,
  () => {
    sliderValue.value = 50
    zoomRange.value = null
  },
)

const timeRange = computed(() => {
  if (!zoomRange.value) {
    return baseTimeRange.value
  }
  return {
    min: Math.max(baseTimeRange.value.min, zoomRange.value.min),
    max: Math.min(baseTimeRange.value.max, zoomRange.value.max),
  }
})

const visibleWeatherPoints = computed(() =>
  weatherPoints.value.filter((entry) => entry.timeMs >= timeRange.value.min && entry.timeMs <= timeRange.value.max),
)

const visibleInterruptRows = computed(() =>
  interruptRows.value.filter((entry) => entry.timeMs >= timeRange.value.min && entry.timeMs <= timeRange.value.max),
)

const datasetControls = computed<DatasetControl[]>(() => [
  {
    key: 'temp',
    label: 'Temperatur',
    active: draftConfig.value.visibleDatasets.temp,
    swatch: draftConfig.value.colors.temp,
  },
  {
    key: 'winds',
    label: 'Windtempo',
    active: draftConfig.value.visibleDatasets.winds,
    swatch: draftConfig.value.colors.winds,
  },
  {
    key: 'humidity',
    label: 'Luftfeuchte',
    active: draftConfig.value.visibleDatasets.humidity,
    swatch: draftConfig.value.colors.humidity,
  },
  {
    key: 'light',
    label: 'Licht',
    active: draftConfig.value.visibleDatasets.light,
    swatch: draftConfig.value.colors.light,
  },
  {
    key: 'pressure',
    label: 'Druck',
    active: draftConfig.value.visibleDatasets.pressure,
    swatch: draftConfig.value.colors.pressure,
  },
  {
    key: 'winddir',
    label: 'Windrichtung',
    active: draftConfig.value.visibleDatasets.winddir,
    swatch: 'linear-gradient(90deg, #101010 0%, #2563eb 33%, #f5f5f5 66%, #facc15 100%)',
  },
  {
    key: 'interrupts',
    label: 'OSSD Fehler',
    active: draftConfig.value.visibleDatasets.interrupts,
    swatch: draftConfig.value.colors.interrupts,
  },
])

const colorControls = computed<ColorControl[]>(() => [
  { key: 'temp', label: 'Temperatur', value: draftConfig.value.colors.temp },
  { key: 'winds', label: 'Windtempo', value: draftConfig.value.colors.winds },
  { key: 'humidity', label: 'Luftfeuchte', value: draftConfig.value.colors.humidity },
  { key: 'light', label: 'Licht', value: draftConfig.value.colors.light },
  { key: 'pressure', label: 'Druck', value: draftConfig.value.colors.pressure },
  { key: 'interrupts', label: 'OSSD Fehler', value: draftConfig.value.colors.interrupts },
  { key: 'offline', label: 'Offline-Zeit', value: draftConfig.value.colors.offline },
])

const canResetView = computed(() => sliderValue.value !== 100 || zoomRange.value !== null || props.config.windowSpanMode === 'manual')

function expandRange(min: number, max: number): { min: number; max: number } {
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return { min: 0, max: 1 }
  }
  if (min === max) {
    return { min: min - 1, max: max + 1 }
  }
  const padding = (max - min) * 0.12
  return { min: Math.max(0, min - padding), max: max + padding }
}

const climateRange = computed(() => {
  const values: number[] = []
  if (props.config.visibleDatasets.temp) {
    values.push(...visibleWeatherPoints.value.map((entry) => entry.tempValue))
  }
  if (props.config.visibleDatasets.winds) {
    values.push(...visibleWeatherPoints.value.map((entry) => entry.windsValue))
  }
  if (props.config.visibleDatasets.humidity) {
    values.push(...visibleWeatherPoints.value.map((entry) => entry.humidityValue))
  }
  const valid = values.filter((value) => Number.isFinite(value))
  if (!valid.length) {
    return { min: 0, max: 100 }
  }
  const baseRange = props.config.autoY
    ? expandRange(Math.min(...valid), Math.max(...valid))
    : { min: 0, max: props.config.yMax ?? Math.max(...valid, 100) }
  return baseRange.max <= baseRange.min ? { min: 0, max: 100 } : baseRange
})

const auxiliaryRange = computed(() => {
  const values: number[] = []
  if (props.config.visibleDatasets.light) {
    values.push(...visibleWeatherPoints.value.map((entry) => entry.lightDisplayValue))
  }
  if (props.config.visibleDatasets.pressure) {
    values.push(...visibleWeatherPoints.value.map((entry) => entry.pressureValue))
  }
  const valid = values.filter((value) => Number.isFinite(value))
  if (!valid.length) {
    return { min: 0, max: 100 }
  }
  const range = expandRange(Math.min(...valid), Math.max(...valid))
  return range.max <= range.min ? { min: 0, max: 100 } : range
})

const showAuxiliaryAxis = computed(() => lightPoints.value.length > 0 || pressurePoints.value.length > 0)

function scaleX(timeMs: number): number {
  const span = timeRange.value.max - timeRange.value.min
  return PLOT.left + ((timeMs - timeRange.value.min) / span) * (PLOT.right - PLOT.left)
}

function scaleY(value: number, range: { min: number; max: number }): number {
  const span = range.max - range.min
  if (!Number.isFinite(value) || span <= 0) {
    return PLOT.bottom
  }
  const ratio = (value - range.min) / span
  return PLOT.bottom - ratio * (PLOT.bottom - PLOT.top)
}

function buildSeries(getValue: (entry: (typeof weatherPoints.value)[number]) => number, range: { min: number; max: number }): SeriesPoint[] {
  return visibleWeatherPoints.value
    .map((entry) => ({
      id: entry.id,
      x: scaleX(entry.timeMs),
      y: scaleY(getValue(entry), range),
      value: getValue(entry),
    }))
    .filter((point) => Number.isFinite(point.y))
}

const tempPoints = computed(() => props.config.visibleDatasets.temp ? buildSeries((entry) => entry.tempValue, climateRange.value) : [])
const windsPoints = computed(() => props.config.visibleDatasets.winds ? buildSeries((entry) => entry.windsValue, climateRange.value) : [])
const humidityPoints = computed(() => props.config.visibleDatasets.humidity ? buildSeries((entry) => entry.humidityValue, climateRange.value) : [])
const lightPoints = computed(() => props.config.visibleDatasets.light ? buildSeries((entry) => entry.lightDisplayValue, auxiliaryRange.value) : [])
const pressurePoints = computed(() => props.config.visibleDatasets.pressure ? buildSeries((entry) => entry.pressureValue, auxiliaryRange.value) : [])

function toPolyline(points: ChartPoint[]): string {
  return points.map((point) => `${point.x},${point.y}`).join(' ')
}

const tempPolyline = computed(() => tempPoints.value.length > 1 ? toPolyline(tempPoints.value) : '')
const windsPolyline = computed(() => windsPoints.value.length > 1 ? toPolyline(windsPoints.value) : '')
const humidityPolyline = computed(() => humidityPoints.value.length > 1 ? toPolyline(humidityPoints.value) : '')
const lightPolyline = computed(() => lightPoints.value.length > 1 ? toPolyline(lightPoints.value) : '')
const pressurePolyline = computed(() => pressurePoints.value.length > 1 ? toPolyline(pressurePoints.value) : '')

const interruptMarkers = computed(() =>
  props.config.visibleDatasets.interrupts
    ? visibleInterruptRows.value.map((entry) => ({
        id: entry.id,
        x: scaleX(entry.timeMs),
        y: PLOT.top + 18,
      }))
    : [],
)

const offlineBands = computed(() => {
  const bands: Array<{ id: string; x: number; width: number; hover: HoverTarget }> = []
  let offlineStart: { id: string; timeMs: number } | null = null

  for (const entry of appStateRows.value) {
    if (entry.state === 'stop') {
      offlineStart = offlineStart ?? { id: entry.id, timeMs: entry.timeMs }
      continue
    }

    if (!offlineStart || entry.timeMs <= offlineStart.timeMs) {
      offlineStart = null
      continue
    }

    const startMs = Math.max(offlineStart.timeMs, timeRange.value.min)
    const endMs = Math.min(entry.timeMs, timeRange.value.max)
    if (endMs > startMs) {
      bands.push({
        id: `offline-${offlineStart.id}-${entry.id}`,
        x: scaleX(startMs),
        width: Math.max(2, scaleX(endMs) - scaleX(startMs)),
        hover: {
          id: `hover-offline-${offlineStart.id}-${entry.id}`,
          x: scaleX((startMs + endMs) / 2),
          y: PLOT.top + 16,
          title: `Offline · ${formatDateTime(offlineStart.timeMs)}`,
          body: `Keine Python-App Aktivitaet bis ${formatDateTime(entry.timeMs)}`,
          description: `Python-App offline von ${formatDateTime(offlineStart.timeMs)} bis ${formatDateTime(entry.timeMs)}`,
        },
      })
    }
    offlineStart = null
  }

  if (offlineStart) {
    const startMs = Math.max(offlineStart.timeMs, timeRange.value.min)
    const endMs = timeRange.value.max
    if (endMs > startMs) {
      bands.push({
        id: `offline-open-${offlineStart.id}`,
        x: scaleX(startMs),
        width: Math.max(2, scaleX(endMs) - scaleX(startMs)),
        hover: {
          id: `hover-offline-open-${offlineStart.id}`,
          x: scaleX((startMs + endMs) / 2),
          y: PLOT.top + 16,
          title: `Offline seit ${formatDateTime(offlineStart.timeMs)}`,
          body: 'Python-App hat noch kein neues Startsignal gesendet.',
          description: `Python-App offline seit ${formatDateTime(offlineStart.timeMs)}`,
        },
      })
    }
  }

  return bands
})

function lineStyle(key: Extract<ChartColorKey, 'temp' | 'winds' | 'humidity' | 'light' | 'pressure'>): { stroke: string } {
  return { stroke: props.config.colors[key] }
}

const interruptStyle = computed(() => ({
  stroke: props.config.colors.interrupts,
}))

const interruptStemStyle = computed(() => ({
  stroke: withAlpha(props.config.colors.interrupts, 0.3),
}))

const offlineBandStyle = computed(() => ({
  fill: withAlpha(props.config.colors.offline, 0.16),
  stroke: withAlpha(props.config.colors.offline, 0.34),
}))

function formatShortTime(timeMs: number): string {
  return new Intl.DateTimeFormat('de-DE', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(timeMs))
}

function formatTick(value: number): string {
  return value.toFixed(2)
}

function formatValue(value: number): string {
  return Number.isFinite(value) ? value.toFixed(2) : '--'
}

function formatLightValue(value: number): string {
  return `${formatValue(value)} lx`
}

function formatLightDisplayValue(value: number): string {
  return `${formatValue(value)} x1000 lx`
}

function buildVerticalTicks(range: { min: number; max: number }): Tick[] {
  const steps = 4
  return Array.from({ length: steps + 1 }, (_, index) => {
    const value = range.min + ((range.max - range.min) / steps) * index
    return {
      value,
      y: scaleY(value, range),
      label: formatTick(value),
    }
  })
}

const yTicks = computed(() => buildVerticalTicks(climateRange.value))
const auxiliaryTicks = computed(() => showAuxiliaryAxis.value ? buildVerticalTicks(auxiliaryRange.value) : [])

const xTicks = computed(() => {
  if (!weatherPoints.value.length && !interruptRows.value.length && !appStateRows.value.length) {
    return [] as Array<{ x: number; label: string }>
  }
  const count = 5
  return Array.from({ length: count }, (_, index) => {
    const timeMs = timeRange.value.min + ((timeRange.value.max - timeRange.value.min) / (count - 1)) * index
    return {
      x: scaleX(timeMs),
      label: formatShortTime(timeMs),
    }
  })
})

const windDirectionBands = computed(() => {
  if (!props.config.visibleDatasets.winddir) {
    return [] as Array<{ id: string; x: number; width: number; color: string; hover: HoverTarget }>
  }
  const entries = visibleWeatherPoints.value.filter((entry) => Number.isFinite(entry.windDirectionAngle))
  if (!entries.length) {
    return [] as Array<{ id: string; x: number; width: number; color: string; hover: HoverTarget }>
  }
  return entries.map((entry, index) => {
    const previous = entries[index - 1]
    const next = entries[index + 1]
    const currentX = scaleX(entry.timeMs)
    const startX = previous ? (scaleX(previous.timeMs) + currentX) / 2 : PLOT.left
    const endX = next ? (currentX + scaleX(next.timeMs)) / 2 : PLOT.right
    const x = Math.max(PLOT.left, startX)
    const width = Math.max(0, Math.min(PLOT.right, endX) - x)
    const timeLabelEnd = next ? formatDateTime(next.timeMs) : formatDateTime(timeRange.value.max)
    return {
      id: entry.id,
      x,
      width,
      color: withAlpha(windDirectionToColor(entry.windDirectionAngle), 0.16),
      hover: {
        id: `hover-winddir-band-${entry.id}`,
        x: x + width / 2,
        y: PLOT.top + 16,
        title: `Windrichtung · ${formatDateTime(entry.timeMs)}`,
        body: `${entry.winddir || 'Unbekannt'} · ${formatValue(entry.winds)} km/h · Bereich bis ${timeLabelEnd}`,
        description: `Windrichtung im Zeitraum ab ${formatDateTime(entry.timeMs)}: ${entry.winddir || 'Unbekannt'}, Wind ${formatValue(entry.winds)} Kilometer pro Stunde`,
      },
    }
  })
})

const windowSummary = computed(() => {
  const suffix = zoomRange.value ? ' · Zoom aktiv' : ''
  if (!visibleWeatherPoints.value.length) {
    return `Ansicht: ${formatDateTime(timeRange.value.min)} - ${formatDateTime(timeRange.value.max)}${suffix}`
  }
  return `Ansicht: ${formatDateTime(timeRange.value.min)} - ${formatDateTime(timeRange.value.max)} · ${visibleWeatherPoints.value.length} Messpunkte${suffix}`
})

const selectionRect = computed(() => {
  if (!zoomSelection.value) {
    return null
  }
  const minX = Math.min(zoomSelection.value.startX, zoomSelection.value.currentX)
  const maxX = Math.max(zoomSelection.value.startX, zoomSelection.value.currentX)
  return {
    x: minX,
    width: maxX - minX,
  }
})

function formatDateTime(timeMs: number): string {
  return new Intl.DateTimeFormat('de-DE', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(timeMs))
}

function formatDuration(durationMs: number): string {
  const totalMinutes = Math.max(1, Math.round(durationMs / 60_000))
  const days = Math.floor(totalMinutes / (24 * 60))
  const hours = Math.floor((totalMinutes % (24 * 60)) / 60)
  const minutes = totalMinutes % 60

  if (days > 0) {
    return hours > 0 ? `${days}d ${hours}h` : `${days}d`
  }
  if (hours > 0) {
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`
  }
  return `${minutes}m`
}

function parseWindDirection(value: string): number {
  const normalized = String(value || '').trim().toUpperCase()
  const lookup: Record<string, number> = {
    N: 0,
    NNE: 22.5,
    NE: 45,
    ENE: 67.5,
    E: 90,
    ESE: 112.5,
    SE: 135,
    SSE: 157.5,
    S: 180,
    SSW: 202.5,
    SW: 225,
    WSW: 247.5,
    W: 270,
    WNW: 292.5,
    NW: 315,
    NNW: 337.5,
  }
  return lookup[normalized] ?? Number.NaN
}

function interpolateColor(start: [number, number, number], end: [number, number, number], ratio: number): string {
  const mix = start.map((channel, index) => Math.round(channel + (end[index]! - channel) * ratio))
  return `rgb(${mix[0]}, ${mix[1]}, ${mix[2]})`
}

function windDirectionToColor(angle: number): string {
  const normalized = ((angle % 360) + 360) % 360
  const stops = [
    { angle: 0, color: [16, 16, 16] as [number, number, number] },
    { angle: 90, color: [37, 99, 235] as [number, number, number] },
    { angle: 180, color: [245, 245, 245] as [number, number, number] },
    { angle: 270, color: [250, 204, 21] as [number, number, number] },
    { angle: 360, color: [16, 16, 16] as [number, number, number] },
  ]

  for (let index = 1; index < stops.length; index += 1) {
    const previous = stops[index - 1]!
    const current = stops[index]!
    if (normalized <= current.angle) {
      const span = current.angle - previous.angle
      const ratio = span === 0 ? 0 : (normalized - previous.angle) / span
      return interpolateColor(previous.color, current.color, ratio)
    }
  }

  return 'rgb(16, 16, 16)'
}

function withAlpha(color: string, alpha: number): string {
  const match = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/)
  if (!match) {
    const hex = color.trim().match(/^#([\da-f]{6})$/i)
    if (!hex) {
      return color
    }
    const value = hex[1]!
    return `rgba(${Number.parseInt(value.slice(0, 2), 16)}, ${Number.parseInt(value.slice(2, 4), 16)}, ${Number.parseInt(value.slice(4, 6), 16)}, ${alpha})`
  }
  return `rgba(${match[1]}, ${match[2]}, ${match[3]}, ${alpha})`
}

const hoverTargets = computed(() => {
  const targets: HoverTarget[] = []

  for (const point of tempPoints.value) {
    const entry = visibleWeatherPoints.value.find((item) => item.id === point.id)
    if (!entry) continue
    targets.push({
      id: `hover-temp-${point.id}`,
      x: point.x,
      y: point.y,
      title: `Temperatur · ${formatDateTime(entry.timeMs)}`,
      body: `${formatValue(entry.tempValue)} °C`,
      description: `Temperatur am ${formatDateTime(entry.timeMs)}: ${formatValue(entry.tempValue)} Grad Celsius`,
    })
  }

  for (const point of windsPoints.value) {
    const entry = visibleWeatherPoints.value.find((item) => item.id === point.id)
    if (!entry) continue
    targets.push({
      id: `hover-winds-${point.id}`,
      x: point.x,
      y: point.y,
      title: `Windtempo · ${formatDateTime(entry.timeMs)}`,
      body: `${formatValue(entry.windsValue)} km/h`,
      description: `Windtempo am ${formatDateTime(entry.timeMs)}: ${formatValue(entry.windsValue)} Kilometer pro Stunde`,
    })
  }

  for (const point of humidityPoints.value) {
    const entry = visibleWeatherPoints.value.find((item) => item.id === point.id)
    if (!entry) continue
    targets.push({
      id: `hover-humidity-${point.id}`,
      x: point.x,
      y: point.y,
      title: `Luftfeuchte · ${formatDateTime(entry.timeMs)}`,
      body: `${formatValue(entry.humidityValue)} %`,
      description: `Luftfeuchte am ${formatDateTime(entry.timeMs)}: ${formatValue(entry.humidityValue)} Prozent`,
    })
  }

  for (const point of lightPoints.value) {
    const entry = visibleWeatherPoints.value.find((item) => item.id === point.id)
    if (!entry) continue
    targets.push({
      id: `hover-light-${point.id}`,
      x: point.x,
      y: point.y,
      title: `Licht · ${formatDateTime(entry.timeMs)}`,
      body: `${formatLightDisplayValue(entry.lightDisplayValue)} · Rohwert ${formatLightValue(entry.lightValue)}`,
      description: `Licht am ${formatDateTime(entry.timeMs)}: ${formatLightDisplayValue(entry.lightDisplayValue)}, Rohwert ${formatLightValue(entry.lightValue)}`,
    })
  }

  for (const point of pressurePoints.value) {
    const entry = visibleWeatherPoints.value.find((item) => item.id === point.id)
    if (!entry) continue
    targets.push({
      id: `hover-pressure-${point.id}`,
      x: point.x,
      y: point.y,
      title: `Druck · ${formatDateTime(entry.timeMs)}`,
      body: `${formatValue(entry.pressureValue)} hPa`,
      description: `Luftdruck am ${formatDateTime(entry.timeMs)}: ${formatValue(entry.pressureValue)} hPa`,
    })
  }

  for (const marker of interruptMarkers.value) {
    const entry = visibleInterruptRows.value.find((item) => item.id === marker.id)
    if (!entry) continue
    targets.push({
      id: `hover-interrupt-${marker.id}`,
      x: marker.x,
      y: marker.y,
      title: `OSSD Fehler · ${formatDateTime(entry.timeMs)}`,
      body: `Lichtgitter ${entry.lichtgitterNr}, OSSD ${entry.ossdNr}`,
      description: `OSSD Fehler am ${formatDateTime(entry.timeMs)}: Lichtgitter ${entry.lichtgitterNr}, OSSD ${entry.ossdNr}`,
    })
  }

  return targets
})

function updateTooltipPosition(event: PointerEvent): { left: number; top: number } | null {
  const element = chartSvg.value
  if (!element) {
    return null
  }
  const rect = element.getBoundingClientRect()
  return {
    left: Math.max(16, Math.min(rect.width - 16, event.clientX - rect.left + 14)),
    top: Math.max(16, Math.min(rect.height - 16, event.clientY - rect.top - 14)),
  }
}

function showTooltip(target: HoverTarget, event: PointerEvent): void {
  const position = updateTooltipPosition(event)
  tooltip.value = {
    title: target.title,
    body: target.body,
    left: position?.left ?? target.x,
    top: position?.top ?? target.y,
  }
}

function moveTooltip(event: PointerEvent): void {
  if (!tooltip.value) {
    return
  }
  const position = updateTooltipPosition(event)
  if (!position) {
    return
  }
  tooltip.value = { ...tooltip.value, ...position }
}

function hideTooltip(): void {
  tooltip.value = null
}

function toggleDataset(key: keyof ChartConfig['visibleDatasets']): void {
  draftConfig.value.visibleDatasets[key] = !draftConfig.value.visibleDatasets[key]
}

function applyPalette(palette: keyof typeof COLOR_PALETTES): void {
  draftConfig.value.colors = { ...COLOR_PALETTES[palette] }
}

function updateColor(key: ChartColorKey, value: string): void {
  draftConfig.value.colors[key] = value
}

function onTimeWindowChange(value: string): void {
  const nextValue = value as ChartConfig['timeWindow']
  draftConfig.value.timeWindow = nextValue
  draftConfig.value.windowSpanMode = 'preset'
  sliderValue.value = 50
  zoomRange.value = null
}

function onWindowSpanInput(value: number): void {
  draftConfig.value.windowSpanPercent = clampWindowSpan(fullSpan.value, value)
  draftConfig.value.windowSpanMode = 'manual'
  sliderValue.value = 50
  zoomRange.value = null
}

function applySettings(): void {
  const centeredByUserRangeChange =
    draftConfig.value.timeWindow !== props.config.timeWindow
    || draftConfig.value.windowSpanMode !== props.config.windowSpanMode
    || draftConfig.value.windowSpanPercent !== props.config.windowSpanPercent

  props.config.timeWindow = draftConfig.value.timeWindow
  props.config.windowSpanMode = draftConfig.value.windowSpanMode
  props.config.windowSpanPercent = draftConfig.value.windowSpanPercent
  props.config.autoY = draftConfig.value.autoY
  props.config.yMax = draftConfig.value.yMax
  props.config.tension = draftConfig.value.tension
  props.config.visibleDatasets = { ...draftConfig.value.visibleDatasets }
  props.config.colors = { ...draftConfig.value.colors }

  if (centeredByUserRangeChange) {
    sliderValue.value = 50
    zoomRange.value = null
  }
}

function resetDraftSettings(): void {
  draftConfig.value = cloneChartConfig(props.config)
}

function onSliderInput(value: number): void {
  sliderValue.value = value
  zoomRange.value = null
}

function shiftWindow(direction: -1 | 1): void {
  const nextValue = sliderValue.value + direction * PAN_STEP_PERCENT
  sliderValue.value = Math.max(0, Math.min(100, nextValue))
  zoomRange.value = null
}

function resetToLatest(): void {
  props.config.windowSpanMode = 'preset'
  sliderValue.value = 100
  zoomRange.value = null
}

function startZoomSelection(event: PointerEvent): void {
  if (!visibleWeatherPoints.value.length) {
    return
  }
  hideTooltip()
  const svgX = toSvgX(event)
  if (svgX === null) {
    return
  }
  zoomSelection.value = { startX: svgX, currentX: svgX }
}

function updateZoomSelection(event: PointerEvent): void {
  if (!zoomSelection.value) {
    return
  }
  const svgX = toSvgX(event)
  if (svgX === null) {
    return
  }
  zoomSelection.value = { ...zoomSelection.value, currentX: svgX }
}

function finishZoomSelection(event: PointerEvent): void {
  if (!zoomSelection.value) {
    return
  }
  const svgX = toSvgX(event)
  const endX = svgX ?? zoomSelection.value.currentX
  const minX = Math.min(zoomSelection.value.startX, endX)
  const maxX = Math.max(zoomSelection.value.startX, endX)

  if (maxX - minX >= 18) {
    zoomRange.value = {
      min: scaleTime(minX),
      max: scaleTime(maxX),
    }
  }

  zoomSelection.value = null
}

function cancelZoomSelection(): void {
  zoomSelection.value = null
  hideTooltip()
}

function toSvgX(event: PointerEvent): number | null {
  const element = chartSvg.value
  if (!element) {
    return null
  }
  const rect = element.getBoundingClientRect()
  if (rect.width <= 0) {
    return null
  }
  const relativeX = ((event.clientX - rect.left) / rect.width) * WIDTH
  return Math.min(PLOT.right, Math.max(PLOT.left, relativeX))
}

function scaleTime(svgX: number): number {
  const ratio = (svgX - PLOT.left) / (PLOT.right - PLOT.left)
  return baseTimeRange.value.min + ratio * (baseTimeRange.value.max - baseTimeRange.value.min)
}
</script>

<style scoped>
.ts-chart-empty {
  margin: 0;
  padding: 1.25rem 0 0.25rem;
  color: var(--text-muted);
  font-size: 0.92rem;
}

.ts-chart-shell {
  display: grid;
  gap: 0.9rem;
}

.ts-chart-summary {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.84rem;
}

.ts-chart-wind-legend {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.55rem;
  color: var(--text-muted);
  font-size: 0.76rem;
}

.ts-chart-wind-legend__label {
  color: var(--text);
  font-weight: 600;
}

.ts-chart-wind-legend__bar {
  width: 6.5rem;
  height: 0.65rem;
  border-radius: 999px;
  background: linear-gradient(90deg, rgb(16, 16, 16) 0%, rgb(37, 99, 235) 33%, rgb(245, 245, 245) 66%, rgb(250, 204, 21) 100%);
  border: 1px solid rgba(148, 163, 184, 0.22);
}

.ts-chart-wind-legend__item {
  white-space: nowrap;
}

.ts-chart-empty--window {
  padding-top: 0.15rem;
}

.ts-chart-canvas-frame {
  position: relative;
  overflow-x: auto;
}

.ts-chart-svg {
  width: 100%;
  height: 360px;
  display: block;
  overflow: visible;
}

.ts-chart-shell--expanded .ts-chart-svg {
  height: 520px;
}

.ts-chart-bg {
  fill: rgba(15, 23, 42, 0.45);
  stroke: rgba(148, 163, 184, 0.18);
}

.ts-chart-grid {
  stroke: rgba(148, 163, 184, 0.14);
  stroke-width: 1;
}

.ts-chart-grid--vertical {
  stroke-dasharray: 4 6;
}

.ts-chart-axis {
  stroke: rgba(226, 232, 240, 0.5);
  stroke-width: 1.2;
}

.ts-chart-axis--auxiliary {
  stroke: rgba(59, 130, 246, 0.4);
}

.ts-chart-wind-band {
  stroke: none;
}

.ts-chart-line {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.ts-chart-line--temp {
  stroke: #f97316;
}

.ts-chart-line--winds {
  stroke: #f59e0b;
}

.ts-chart-line--humidity {
  stroke: #22c55e;
}

.ts-chart-line--light {
  stroke: #3b82f6;
}

.ts-chart-line--pressure {
  stroke: #f43f5e;
  stroke-dasharray: 10 7;
}

.ts-chart-offline-band {
  fill: none;
  stroke-width: 1;
}

.ts-chart-interrupt {
  stroke: #ef4444;
  stroke-width: 2.4;
}

.ts-chart-interrupt__stem {
  stroke: rgba(239, 68, 68, 0.3);
  stroke-width: 1.2;
}

.ts-chart-selection {
  fill: rgba(56, 189, 248, 0.18);
  stroke: rgba(56, 189, 248, 0.75);
  stroke-width: 1.5;
  stroke-dasharray: 6 6;
}

.ts-chart-label {
  fill: rgba(226, 232, 240, 0.82);
  font-size: 11px;
}

.ts-chart-label--left {
  text-anchor: end;
}

.ts-chart-label--right {
  text-anchor: start;
}

.ts-chart-label--auxiliary {
  fill: rgba(255, 228, 230, 0.86);
}

.ts-chart-label--bottom {
  text-anchor: middle;
}

.ts-chart-caption {
  fill: rgba(226, 232, 240, 0.78);
  font-size: 12px;
  font-weight: 600;
}

.ts-chart-caption--right {
  text-anchor: end;
}

.ts-chart-caption--auxiliary {
  fill: rgba(255, 228, 230, 0.82);
}

.ts-chart-caption--wind {
  fill: rgba(226, 232, 240, 0.6);
  font-size: 10px;
}

.ts-chart-hover-target {
  fill: transparent;
  stroke: transparent;
  cursor: crosshair;
}

.ts-chart-tooltip {
  position: absolute;
  min-width: 12rem;
  max-width: min(20rem, calc(100% - 1.5rem));
  padding: 0.7rem 0.8rem;
  border-radius: 0.9rem;
  background: rgba(15, 23, 42, 0.94);
  border: 1px solid rgba(148, 163, 184, 0.24);
  box-shadow: 0 18px 38px rgba(15, 23, 42, 0.32);
  transform: translateY(-100%);
  pointer-events: none;
  z-index: 1;
}

.ts-chart-tooltip__title,
.ts-chart-tooltip__body {
  margin: 0;
}

.ts-chart-tooltip__title {
  color: var(--text);
  font-size: 0.8rem;
  font-weight: 600;
}

.ts-chart-tooltip__body {
  margin-top: 0.2rem;
  color: var(--text-muted);
  font-size: 0.76rem;
  line-height: 1.4;
}

@media (max-width: 900px) {
  .ts-chart-svg {
    height: 300px;
  }

  .ts-chart-shell--expanded .ts-chart-svg {
    height: 420px;
  }
}
</style>
