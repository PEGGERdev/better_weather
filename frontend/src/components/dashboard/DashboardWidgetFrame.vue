<template>
  <section class="widget-frame" :class="{ 'widget-frame--expanded': expanded }">
    <header class="widget-frame__header">
      <p class="widget-frame__title">{{ title }}</p>

      <div class="widget-frame__actions">
        <button type="button" class="widget-frame__action" :disabled="!canMoveUp" @click="$emit('move-up')">
          Hoch
        </button>
        <button type="button" class="widget-frame__action" :disabled="!canMoveDown" @click="$emit('move-down')">
          Runter
        </button>
        <button type="button" class="widget-frame__action" :disabled="!canToggleColumn" @click="$emit('toggle-column')">
          {{ columnToggleLabel }}
        </button>
        <button type="button" class="widget-frame__action widget-frame__action--primary" @click="$emit('toggle-expand')">
          {{ expanded ? 'Schliessen' : 'Expandieren' }}
        </button>
      </div>
    </header>

    <div class="widget-frame__body">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  title: string
  expanded: boolean
  canMoveUp: boolean
  canMoveDown: boolean
  canToggleColumn?: boolean
  columnToggleLabel: string
}>(), {
  canToggleColumn: true,
})

defineEmits<{
  'move-up': []
  'move-down': []
  'toggle-column': []
  'toggle-expand': []
}>()
</script>

<style scoped>
.widget-frame {
  display: grid;
  gap: 0.65rem;
}

.widget-frame__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.widget-frame__title {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.widget-frame__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.45rem;
}

.widget-frame__action {
  appearance: none;
  border: 1px solid rgba(148, 163, 184, 0.24);
  background: rgba(15, 23, 42, 0.5);
  color: var(--text-muted);
  border-radius: 999px;
  padding: 0.45rem 0.72rem;
  font: inherit;
  font-size: 0.75rem;
  cursor: pointer;
}

.widget-frame__action:disabled {
  opacity: 0.4;
  cursor: default;
}

.widget-frame__action--primary {
  color: var(--text);
  border-color: rgba(56, 189, 248, 0.36);
  background: rgba(14, 116, 144, 0.26);
}

.widget-frame__body {
  min-width: 0;
}

@media (max-width: 900px) {
  .widget-frame__header {
    align-items: flex-start;
    flex-direction: column;
  }

  .widget-frame__actions {
    justify-content: flex-start;
  }
}
</style>
