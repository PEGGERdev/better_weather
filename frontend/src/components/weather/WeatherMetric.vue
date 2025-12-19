<template>
  <div class="weather-metric">
    <span class="weather-metric__label">{{ label }}</span>
    <span class="weather-metric__value">
      {{ value }}
      <span v-if="unit" class="weather-metric__unit">{{ unit }}</span>
    </span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  unit?: string
}>()
</script>

<style scoped>
.weather-metric {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  padding: 0.15rem 0;
}

.weather-metric__label {
  color: var(--text-muted);
}

.weather-metric__value {
  font-weight: 500;
}

.weather-metric__unit {
  margin-left: 0.15rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}
</style>
