<template>
  <BaseCard v-if="error" data-testid="widget-dashboard-error">
    <p>Fehler beim Laden der Daten: {{ error }}</p>
  </BaseCard>
</template>

<script setup lang="ts">
import BaseCard from '@/components/base/BaseCard.vue'

defineProps<{
  error: string | null
}>()
</script>
