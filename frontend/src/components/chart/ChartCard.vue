<template>
  <BaseCard class="chart-card" @click="onCardClick">
    <BaseSectionTitle title="Verlauf Wetterdaten" subtitle="Linien für Temperatur, Licht, Luftfeuchte + rote Kreuze für Lichtgitter-Interrupts" />
    <div class="chart-card__body" :class="{ expanded: isExpanded }">
      <TimeSeriesChart
        :weather="weather"
        :interrupts="interrupts"
        :config="ui.chartConfig"
        :collapsed="!isExpanded"
      />
    </div>
  </BaseCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import TimeSeriesChart from './TimeSeriesChart.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import BaseSectionTitle from '@/components/base/BaseSectionTitle.vue'
import { useUiStore } from '@/stores/uiStore'
import type { WeatherRecord, InterruptRecord } from '@/types/domain'

const props = defineProps<{
  id: string
  weather: WeatherRecord[]
  interrupts: InterruptRecord[]
}>()

const ui = useUiStore()
const isExpanded = computed(() => ui.expandedChart && ui.expandedChartId === props.id)

function onCardClick(e: MouseEvent) {
  // Prevent toggling when clicking interactive elements (if needed)
  if (isExpanded.value) {
    ui.collapseChart()
  } else {
    ui.expandChart(props.id)
    // optional: scrollIntoView smooth to top of layout
    // delay to let grid reflow, then scroll
    setTimeout(() => {
      const el = document.querySelector('.chart-area')
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 50)
  }
}
</script>

<style scoped>
.chart-card__body {
  position: relative;
  height: 320px;
  transition: height 300ms ease, box-shadow 300ms ease;
  overflow: hidden;
}
.chart-card__body.expanded {
  height: 520px;
}
.chart-card {
  cursor: pointer;
}
</style>
