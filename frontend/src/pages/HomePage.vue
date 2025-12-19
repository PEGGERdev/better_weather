<!-- src/pages/HomePage.vue -->
<template>
  <div class="home-root">
    <div :class="['dashboard-grid', { 'expanded': ui.expandedChart }]">
      <!-- Prominent chart area -->
      <div class="grid-item chart-area" :data-expanded="ui.expandedChart && ui.expandedChartId === 'weather'">
        <ChartCard
          id="weather"
          :weather="weather"
          :interrupts="interrupts"
        />
      </div>

      <!-- Chart config appears directly below the expanded chart -->
      <div v-if="ui.expandedChart && ui.expandedChartId === 'weather'" class="grid-item config-area">
        <ChartConfigCard />
      </div>

      <!-- Latest Interrupts -->
      <div class="grid-item interrupts-area">
        <LatestInterrupts :interrupts="interrupts" />
      </div>

      <!-- Other cards (small) go here; they will flow below -->
      <div class="grid-item others-area">
        <slot name="others" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUiStore } from '@/stores/uiStore'
import ChartCard from '@/components/chart/ChartCard.vue'
import ChartConfigCard from '@/components/chart/ChartConfigCard.vue'
import LatestInterrupts from '@/components/ossd/LatestInterrupts.vue'
import type { WeatherRecord, InterruptRecord } from '@/types/domain'
import { computed } from 'vue'

const props = defineProps<{
  weather: WeatherRecord[]
  interrupts: InterruptRecord[]
}>();

const ui = useUiStore()
const weather = computed(() => props.weather)
const interrupts = computed(() => props.interrupts)
</script>

<style scoped>
.home-root {
  padding: 1.2rem;
}

/* Grid: by default two-column layout, when chart expanded switch to single-column with chart on top */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-auto-rows: min-content;
  gap: 1rem;
  align-items: start;
}

/* when chart is expanded we force a single column and center the chart */
.dashboard-grid.expanded {
  grid-template-columns: 1fr;
}

/* chart area should be larger */
.chart-area {
  grid-column: 1 / -1;
  transition: transform 300ms ease, max-height 300ms ease;
}

/* additional style when expanded to emphasize */
.chart-area[data-expanded="true"] {
  transform: translateY(-1rem);
  /* allow it to be larger */
  min-height: 520px;
}

/* config area */
.config-area {
  grid-column: 1 / -1;
}

/* interrupts small card */
.interrupts-area {
  min-width: 280px;
}

/* more precise responsive tweaks */
@media (min-width: 1000px) {
  .dashboard-grid {
    grid-template-columns: 2fr 1fr;
  }
  .chart-area { grid-column: 1 / 2; }
  .interrupts-area { grid-column: 2 / 3; }
  .others-area { grid-column: 1 / -1; }
  .dashboard-grid.expanded {
    grid-template-columns: 1fr; /* single column when expanded */
  }
}
</style>
