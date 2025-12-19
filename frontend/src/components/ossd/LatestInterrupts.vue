<template>
  <BaseCard>
    <BaseSectionTitle title="Letzte Interrupts" subtitle="Neueste Lichtgitter-Interrupts" />
    <ul class="interrupt-list">
      <li v-for="i in recent" :key="i._id">
        <div class="time">{{ formatTime(i.time) }}</div>
        <div class="meta">Status: {{ i.ossdStatus }} — fk_weather: {{ i.fk_weather }}</div>
      </li>
    </ul>
  </BaseCard>
</template>

<script setup lang="ts">
import BaseCard from '@/components/base/BaseCard.vue'
import BaseSectionTitle from '@/components/base/BaseSectionTitle.vue'
import type { InterruptRecord } from '@/types/domain'
import { computed } from 'vue'

const props = defineProps<{ interrupts: InterruptRecord[] }>()
const recent = computed(() => {
  return [...props.interrupts].sort((a,b) => new Date(b.time).getTime() - new Date(a.time).getTime()).slice(0, 8)
})

function formatTime(t: string|Date) {
  return new Date(t).toLocaleString()
}
</script>

<style scoped>
.interrupt-list {
  list-style:none;
  padding:0;
  margin:0;
  display:flex;
  flex-direction:column;
  gap:0.5rem;
}
.time { font-weight:600; }
.meta { font-size:0.85rem; color:var(--muted) }
</style>
