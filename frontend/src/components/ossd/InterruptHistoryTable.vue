<template>
  <div class="interrupt-history">
    <p v-if="!interrupts.length" class="interrupt-history__empty">
      Keine Interrupts vorhanden.
    </p>
    <table v-else class="interrupt-history__table">
      <thead>
        <tr>
          <th>Zeit</th>
          <th>LG</th>
          <th>OSSD</th>
          <th>Status</th>
          <th>ID</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(entry, index) in interrupts" :key="entry._id ?? `${entry.time}-${index}`">
          <td>{{ formatDateTime(entry.time) }}</td>
          <td>{{ entry.lichtgitterNr }}</td>
          <td>{{ entry.ossdNr }}</td>
          <td>{{ entry.ossdStatus }}</td>
          <td>{{ entry._id ?? '-' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import type { InterruptRecord } from '../../types/domain'
import { formatDateTime } from '@/utils/formatDateTime'

defineProps<{
  interrupts: InterruptRecord[]
}>()
</script>

<style scoped>
.interrupt-history__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.interrupt-history__table th,
.interrupt-history__table td {
  border: 1px solid rgba(55, 65, 81, 0.8);
  padding: 0.25rem 0.4rem;
  text-align: left;
}

.interrupt-history__table th {
  background-color: rgba(15, 23, 42, 0.8);
}

.interrupt-history__empty {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-muted);
}
</style>
