<template>
  <header class="section-title">
    <h2 class="section-title__title">{{ title }}</h2>
    <p v-if="subtitle" class="section-title__subtitle">
      {{ subtitle }}
    </p>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
}>()
</script>

<style scoped>
.section-title {
  margin-bottom: 0.75rem;
}

.section-title__title {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

.section-title__subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  color: var(--text-muted);
}
</style>
