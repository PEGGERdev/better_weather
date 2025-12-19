<template>
  <div class="osss-row">
    <p class="osss-row__title">{{ title }}</p>
    <div class="osss-row__squares">
      <OSSDIndicatorSquare
        v-for="item in items"
        :key="item.label"
        :label="item.label"
        :active="item.active"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import OSSDIndicatorSquare from './OSSDIndicatorSquare.vue'

defineProps<{
  title: string
  items: { label: string; active: boolean }[]
}>()
</script>

<style scoped>
.osss-row {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.osss-row__title {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.osss-row__squares {
  display: flex;
  gap: 0.5rem;
}
</style>
