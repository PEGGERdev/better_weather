<template>
  <BaseCard data-testid="widget-weather-details">
    <BaseSectionTitle title="Aktuelle Wetterdaten" subtitle="Gemessen vom Sensorknoten" />

    <p v-if="!weather" class="weather-panel__empty">Keine Wetterdaten geladen.</p>

    <div v-else class="weather-panel__grid" data-testid="widget-weather-details-grid">
      <WeatherMetric label="Zeit" :value="formatDateTime(weather.time)" />
      <WeatherMetric label="Temperatur" :value="weather.temp" unit="°C" />
      <WeatherMetric label="Druck" :value="weather.pressure" unit="hPa" />
      <WeatherMetric label="Licht" :value="weather.light" />
      <WeatherMetric label="Wind" :value="weather.winds" unit="km/h" />
      <WeatherMetric label="Windrichtung" :value="weather.winddir" />
      <WeatherMetric label="Luftfeuchte" :value="weather.humidity" unit="%" />
      <WeatherMetric label="Regen" :value="weather.rain" />
    </div>
  </BaseCard>
</template>

<script setup lang="ts">
import BaseCard from '../base/BaseCard.vue'
import BaseSectionTitle from '../base/BaseSectionTitle.vue'
import WeatherMetric from './WeatherMetric.vue'
import type { WeatherRecord } from '../../types/domain'
import { formatDateTime } from '@/utils/formatDateTime'

defineProps<{
  weather: WeatherRecord | null
}>()
</script>

<style scoped>
.weather-panel__empty {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.weather-panel__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.25rem 1rem;
}
</style>
