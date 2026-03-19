<template>
  <TwoColumnLayout>
    <template #left>
      <DashboardWidgetFrame
        v-for="(item, index) in leftColumnWidgets"
        :key="item.id"
        :title="item.title"
        :expanded="expandedWidgetId === item.id"
        :can-move-up="index > 0"
        :can-move-down="index < leftColumnWidgets.length - 1"
        column-toggle-label="Nach rechts"
        @move-up="moveWidget(item.id, 'left', -1)"
        @move-down="moveWidget(item.id, 'left', 1)"
        @toggle-column="moveWidgetToOtherColumn(item.id, 'left')"
        @toggle-expand="toggleExpanded(item.id)"
      >
        <component :is="item.component" v-bind="withWidgetState(item, false)" />
      </DashboardWidgetFrame>
    </template>

    <template #right>
      <DashboardWidgetFrame
        v-for="(item, index) in rightColumnWidgets"
        :key="item.id"
        :title="item.title"
        :expanded="expandedWidgetId === item.id"
        :can-move-up="index > 0"
        :can-move-down="index < rightColumnWidgets.length - 1"
        column-toggle-label="Nach links"
        @move-up="moveWidget(item.id, 'right', -1)"
        @move-down="moveWidget(item.id, 'right', 1)"
        @toggle-column="moveWidgetToOtherColumn(item.id, 'right')"
        @toggle-expand="toggleExpanded(item.id)"
      >
        <component :is="item.component" v-bind="withWidgetState(item, false)" />
      </DashboardWidgetFrame>
    </template>
  </TwoColumnLayout>

  <div v-if="expandedWidget" class="app-shell-overlay" @click.self="toggleExpanded(expandedWidget.id)">
    <div class="app-shell-overlay__panel">
      <DashboardWidgetFrame
        :title="expandedWidget.title"
        :expanded="true"
        :can-move-up="false"
        :can-move-down="false"
        :can-toggle-column="false"
        column-toggle-label="Ansicht"
        @toggle-expand="toggleExpanded(expandedWidget.id)"
      >
        <component :is="expandedWidget.component" v-bind="withWidgetState(expandedWidget, true)" />
      </DashboardWidgetFrame>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import DashboardWidgetFrame from '@/components/dashboard/DashboardWidgetFrame.vue'
import TwoColumnLayout from '@/components/layout/TwoColumnLayout.vue'
import type { ResolvedWidget } from '@/core/widgetRegistry'

const props = defineProps<{
  leftWidgets: ResolvedWidget[]
  rightWidgets: ResolvedWidget[]
}>()

const leftColumnWidgets = ref<ResolvedWidget[]>([])
const rightColumnWidgets = ref<ResolvedWidget[]>([])
const expandedWidgetId = ref<string | null>(null)

watch(
  () => ({ left: props.leftWidgets, right: props.rightWidgets }),
  ({ left, right }) => {
    const incomingById = new Map([...left, ...right].map((item) => [item.id, item]))
    const preferredColumnEntries: Array<[string, 'left' | 'right']> = [
      ...left.map((item): [string, 'left' | 'right'] => [item.id, 'left']),
      ...right.map((item): [string, 'left' | 'right'] => [item.id, 'right']),
    ]
    const preferredColumns = new Map<string, 'left' | 'right'>(preferredColumnEntries)

    const currentColumns = new Map<string, 'left' | 'right'>()
    for (const item of leftColumnWidgets.value) currentColumns.set(item.id, 'left')
    for (const item of rightColumnWidgets.value) currentColumns.set(item.id, 'right')

    const nextLeftIds = leftColumnWidgets.value
      .map((item) => item.id)
      .filter((id) => incomingById.has(id) && currentColumns.get(id) === 'left')
    const nextRightIds = rightColumnWidgets.value
      .map((item) => item.id)
      .filter((id) => incomingById.has(id) && currentColumns.get(id) === 'right')

    for (const item of [...left, ...right]) {
      if (nextLeftIds.includes(item.id) || nextRightIds.includes(item.id)) {
        continue
      }
      if (preferredColumns.get(item.id) === 'left') {
        nextLeftIds.push(item.id)
      } else {
        nextRightIds.push(item.id)
      }
    }

    leftColumnWidgets.value = nextLeftIds.map((id) => incomingById.get(id)!).filter(Boolean)
    rightColumnWidgets.value = nextRightIds.map((id) => incomingById.get(id)!).filter(Boolean)
  },
  { immediate: true },
)

const expandedWidget = computed(() => {
  const allWidgets = [...leftColumnWidgets.value, ...rightColumnWidgets.value]
  return allWidgets.find((item) => item.id === expandedWidgetId.value) ?? null
})

watch(expandedWidget, (widget) => {
  if (!widget) {
    expandedWidgetId.value = null
  }
})

function moveWidget(id: string, column: 'left' | 'right', delta: -1 | 1): void {
  const target = column === 'left' ? leftColumnWidgets : rightColumnWidgets
  const index = target.value.findIndex((item) => item.id === id)
  if (index < 0) {
    return
  }
  const nextIndex = index + delta
  if (nextIndex < 0 || nextIndex >= target.value.length) {
    return
  }
  const next = [...target.value]
  const [item] = next.splice(index, 1)
  next.splice(nextIndex, 0, item!)
  target.value = next
}

function moveWidgetToOtherColumn(id: string, from: 'left' | 'right'): void {
  const source = from === 'left' ? leftColumnWidgets : rightColumnWidgets
  const destination = from === 'left' ? rightColumnWidgets : leftColumnWidgets
  const index = source.value.findIndex((item) => item.id === id)
  if (index < 0) {
    return
  }
  const nextSource = [...source.value]
  const [item] = nextSource.splice(index, 1)
  source.value = nextSource
  destination.value = [...destination.value, item!]
}

function toggleExpanded(id: string): void {
  expandedWidgetId.value = expandedWidgetId.value === id ? null : id
}

function withWidgetState(item: ResolvedWidget, expanded: boolean): Record<string, unknown> {
  return {
    ...item.props,
    expanded,
    collapsed: false,
  }
}
</script>

<style scoped>
.app-shell-overlay {
  position: fixed;
  inset: 0;
  z-index: 30;
  padding: 1.5rem;
  background: rgba(2, 6, 23, 0.72);
  backdrop-filter: blur(10px);
  overflow: auto;
}

.app-shell-overlay__panel {
  max-width: 1400px;
  margin: 0 auto;
}

@media (max-width: 900px) {
  .app-shell-overlay {
    padding: 0.8rem;
  }
}
</style>
