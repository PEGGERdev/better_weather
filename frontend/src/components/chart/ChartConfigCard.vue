<template>
  <BaseCard class="config-card">
    <BaseSectionTitle title="Chart konfigurieren" subtitle="Wähle Linien, Zeiteinheit und Darstellung" />
    <div class="config-body">
      <div class="row">
        <label><input type="checkbox" v-model="local.visibleDatasets.temp" /> Temperatur</label>
        <label><input type="checkbox" v-model="local.visibleDatasets.light" /> Licht</label>
        <label><input type="checkbox" v-model="local.visibleDatasets.humidity" /> Luftfeuchte</label>
      </div>

      <div class="row">
        <label>Time unit
          <select v-model="local.timeUnit">
            <option value="minute">Minute</option>
            <option value="hour">Hour</option>
            <option value="day">Day</option>
          </select>
        </label>

        <label>Tension
          <input type="range" min="0" max="1" step="0.01" v-model.number="local.tension" />
        </label>
      </div>

      <div class="row">
        <label><input type="checkbox" v-model="local.autoY" /> automatische Y-Skala</label>
        <label v-if="!local.autoY">Y-Max
          <input type="number" v-model.number="local.yMax" />
        </label>
      </div>

      <div class="actions">
        <button @click="apply">Anwenden</button>
        <button @click="reset">Reset</button>
      </div>
    </div>
  </BaseCard>
</template>

<script setup lang="ts">
import { reactive, toRefs } from 'vue'
import BaseCard from '@/components/base/BaseCard.vue'
import BaseSectionTitle from '@/components/base/BaseSectionTitle.vue'
import { useUiStore } from '@/stores/uiStore'

const ui = useUiStore()

// local copy so changes only applied on Anwenden
const local = reactive(JSON.parse(JSON.stringify(ui.chartConfig)))

function apply() {
  ui.setChartConfig(local)
}

function reset() {
  // reset to defaults (could load from store defaults)
  ui.setChartConfig({
    visibleDatasets: { temp: true, light: true, humidity: true },
    timeUnit: 'minute',
    tension: 0.25,
    autoY: true,
    yMax: null
  })
}
</script>

<style scoped>
.config-body {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.row {
  display:flex;
  gap:1rem;
  align-items:center;
  flex-wrap:wrap;
}
.actions {
  display:flex;
  gap:0.5rem;
  justify-content:flex-end;
  margin-top:0.6rem;
}
</style>
