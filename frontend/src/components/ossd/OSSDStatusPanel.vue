<template>
  <BaseCard>
    <BaseSectionTitle
      title="Lichtgitter OSSD"
      subtitle="Aktueller Status & letzte Interrupts"
    />

    <div class="osss-panel">
      <OSSDIndicatorRow
        title="Lichtgitter 1"
        :items="row1"
      />
      <OSSDIndicatorRow
        title="Lichtgitter 2"
        :items="row2"
      />
    </div>

    <h3 class="osss-panel__subheadline">Letzte 4 Interrupts</h3>
    <InterruptHistoryTable :interrupts="lastInterrupts" />

    <p v-if="loading" class="osss-panel__loading">Lade Daten…</p>
  </BaseCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseCard from '../base/BaseCard.vue'
import BaseSectionTitle from '../base/BaseSectionTitle.vue'
import OSSDIndicatorRow from './OSSDIndicatorRow.vue'
import InterruptHistoryTable from './InterruptHistoryTable.vue'
import type { InterruptRecord, LichtgitterNr, OssdNr } from '../../types/domain'

const props = defineProps<{
  interrupts: InterruptRecord[]
  loading: boolean
}>()

const sortedInterruptsDesc = computed(() =>
  [...props.interrupts].sort(
    (a, b) => new Date(b.time).getTime() - new Date(a.time).getTime()
  )
)

const lastInterrupts = computed(() => sortedInterruptsDesc.value.slice(0, 4))

function isActive(lichtgitterNr: LichtgitterNr, ossdNr: OssdNr): boolean {
  const recent = lastInterrupts.value
  return recent.some(
    i =>
      i.lichtgitterNr === lichtgitterNr &&
      i.ossdNr === ossdNr &&
      i.ossdStatus === 'INT'
  )
}

const row1 = computed(() => [
  { label: 'LG1 OSSD1', active: isActive(1, 1) },
  { label: 'LG1 OSSD2', active: isActive(1, 2) }
])

const row2 = computed(() => [
  { label: 'LG2 OSSD1', active: isActive(2, 1) },
  { label: 'LG2 OSSD2', active: isActive(2, 2) }
])
</script>

<style scoped>
.osss-panel {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.osss-panel__subheadline {
  font-size: 0.9rem;
  margin: 0 0 0.25rem;
  color: var(--text-muted);
}

.osss-panel__loading {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}
</style>
