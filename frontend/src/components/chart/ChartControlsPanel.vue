<template>
  <section class="chart-controls" data-testid="widget-time-series-controls">
    <div class="chart-controls__header">
      <div>
        <p class="chart-controls__eyebrow">Diagrammsteuerung</p>
        <p class="chart-controls__summary">{{ summary }}</p>
      </div>

      <div class="chart-controls__header-actions">
        <button
          type="button"
          class="chart-controls__apply"
          :disabled="!hasPendingChanges"
          @click="$emit('apply-settings')"
        >
          Einstellungen anwenden
        </button>

        <button
          type="button"
          class="chart-controls__reset-draft"
          :disabled="!hasPendingChanges"
          @click="$emit('reset-draft')"
        >
          Entwurf verwerfen
        </button>

        <button
          type="button"
          class="chart-controls__reset"
          :disabled="!canReset"
          @click="$emit('reset')"
        >
          Auf aktuellste Ansicht
        </button>
      </div>
    </div>

    <div class="chart-controls__group">
      <span class="chart-controls__label">Datenreihen</span>
      <div class="chart-controls__series">
        <button
          v-for="item in datasetControls"
          :key="item.key"
          type="button"
          class="chart-controls__toggle"
          :class="{ 'chart-controls__toggle--active': item.active }"
          @click="$emit('toggle-dataset', item.key)"
        >
          <span class="chart-controls__swatch" :style="{ background: item.swatch }"></span>
          {{ item.label }}
        </button>
      </div>
    </div>

    <div class="chart-controls__group chart-controls__group--colors">
      <div class="chart-controls__palette-row">
        <span class="chart-controls__label">Farben</span>
        <div class="chart-controls__palette-actions">
          <button type="button" class="chart-controls__nav" @click="$emit('apply-palette', 'default')">Standard</button>
          <button type="button" class="chart-controls__nav" @click="$emit('apply-palette', 'colorblind')">Farbenblind</button>
          <button type="button" class="chart-controls__nav" @click="$emit('apply-palette', 'highContrast')">Kontrast+</button>
        </div>
      </div>

      <div class="chart-controls__color-grid">
        <label v-for="item in colorControls" :key="item.key" class="chart-controls__color-field">
          <span class="chart-controls__color-label">{{ item.label }}</span>
          <input
            :value="item.value"
            class="chart-controls__color-input"
            type="color"
            @input="$emit('update-color', item.key, ($event.target as HTMLInputElement).value)"
          />
        </label>
      </div>
    </div>

    <div class="chart-controls__group chart-controls__group--window">
      <label class="chart-controls__field">
        <span class="chart-controls__label">Zeitraum</span>
        <select :value="timeWindow" @change="$emit('update-time-window', ($event.target as HTMLSelectElement).value)">
          <option v-for="option in timeWindowOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>

      <div class="chart-controls__pan">
        <div class="chart-controls__duration-header">
          <span class="chart-controls__label">Zeitraum manuell skalieren</span>
          <span class="chart-controls__duration-value">{{ windowSpanLabel }}</span>
        </div>
        <input
          :value="String(windowSpanPercent)"
          type="range"
          min="1"
          max="100"
          step="1"
          class="chart-controls__slider"
          data-testid="widget-time-series-span-slider"
          @input="$emit('update-window-span', Number(($event.target as HTMLInputElement).value))"
        />
      </div>

      <div v-if="canPanWindow" class="chart-controls__pan">
        <span class="chart-controls__label">Fenster verschieben</span>
        <div class="chart-controls__pan-row">
          <button type="button" class="chart-controls__nav" @click="$emit('shift-window', -1)">Frueher</button>
          <input
            :value="String(sliderValue)"
            type="range"
            min="0"
            max="100"
            step="0.5"
            class="chart-controls__slider"
            data-testid="widget-time-series-window-slider"
            @input="$emit('update-slider', Number(($event.target as HTMLInputElement).value))"
          />
          <button type="button" class="chart-controls__nav" @click="$emit('shift-window', 1)">Spaeter</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { ChartColorKey, ChartConfig } from '@/stores/uiStore'

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

type TimeWindowOption = {
  value: ChartConfig['timeWindow']
  label: string
}

defineProps<{
  datasetControls: DatasetControl[]
  colorControls: ColorControl[]
  timeWindow: ChartConfig['timeWindow']
  timeWindowOptions: TimeWindowOption[]
  summary: string
  sliderValue: number
  windowSpanPercent: number
  windowSpanLabel: string
  canPanWindow: boolean
  canReset: boolean
  hasPendingChanges: boolean
}>()

defineEmits<{
  'toggle-dataset': [key: keyof ChartConfig['visibleDatasets']]
  'apply-palette': [palette: 'default' | 'colorblind' | 'highContrast']
  'update-color': [key: ChartColorKey, value: string]
  'update-time-window': [value: string]
  'update-window-span': [value: number]
  'update-slider': [value: number]
  'shift-window': [direction: -1 | 1]
  'apply-settings': []
  'reset-draft': []
  reset: []
}>()
</script>

<style scoped>
.chart-controls {
  display: grid;
  gap: 1rem;
  padding: 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.72), rgba(15, 23, 42, 0.4));
}

.chart-controls__header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.75rem 1rem;
  align-items: flex-start;
}

.chart-controls__header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.chart-controls__eyebrow {
  margin: 0 0 0.2rem;
  font-size: 0.74rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent);
}

.chart-controls__summary {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.84rem;
}

.chart-controls__group {
  display: grid;
  gap: 0.55rem;
}

.chart-controls__group--window {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.chart-controls__label {
  color: var(--text-muted);
  font-size: 0.78rem;
}

.chart-controls__series {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
}

.chart-controls__toggle,
.chart-controls__apply,
.chart-controls__reset-draft,
.chart-controls__nav,
.chart-controls__reset {
  appearance: none;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: rgba(15, 23, 42, 0.5);
  color: var(--text);
  border-radius: 999px;
  padding: 0.55rem 0.8rem;
  font: inherit;
  font-size: 0.82rem;
  cursor: pointer;
  transition: border-color 160ms ease, color 160ms ease, background 160ms ease, opacity 160ms ease;
}

.chart-controls__toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-muted);
}

.chart-controls__toggle--active {
  color: var(--text);
  border-color: rgba(56, 189, 248, 0.45);
  background: rgba(14, 116, 144, 0.24);
}

.chart-controls__apply {
  border-color: rgba(74, 222, 128, 0.35);
  background: rgba(20, 83, 45, 0.34);
}

.chart-controls__reset-draft {
  border-color: rgba(251, 191, 36, 0.28);
  background: rgba(120, 53, 15, 0.3);
}

.chart-controls__apply:disabled,
.chart-controls__reset-draft:disabled,
.chart-controls__reset:disabled {
  opacity: 0.45;
  cursor: default;
}

.chart-controls__swatch {
  width: 0.8rem;
  height: 0.8rem;
  border-radius: 999px;
  display: inline-block;
}

.chart-controls__group--colors {
  gap: 0.75rem;
}

.chart-controls__palette-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1rem;
  justify-content: space-between;
  align-items: center;
}

.chart-controls__palette-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.chart-controls__color-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
}

.chart-controls__color-field {
  display: grid;
  gap: 0.35rem;
}

.chart-controls__color-label {
  color: var(--text-muted);
  font-size: 0.76rem;
}

.chart-controls__color-input {
  width: 100%;
  min-height: 2.5rem;
  border-radius: 0.85rem;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: rgba(15, 23, 42, 0.74);
  padding: 0.3rem;
}

.chart-controls__field {
  display: grid;
  gap: 0.35rem;
}

.chart-controls__field select {
  width: 100%;
  border-radius: 0.85rem;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: rgba(15, 23, 42, 0.74);
  color: var(--text);
  padding: 0.65rem 0.8rem;
  font: inherit;
}

.chart-controls__pan {
  display: grid;
  gap: 0.35rem;
}

.chart-controls__duration-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.chart-controls__duration-value {
  color: var(--text);
  font-size: 0.78rem;
}

.chart-controls__pan-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 0.75rem;
  align-items: center;
}

.chart-controls__slider {
  width: 100%;
}

@media (max-width: 900px) {
  .chart-controls__pan-row {
    grid-template-columns: 1fr;
  }
}
</style>
