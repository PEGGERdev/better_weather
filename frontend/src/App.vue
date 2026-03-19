<template>
  <AppShell :left-widgets="leftWidgets" :right-widgets="rightWidgets" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppShell from '@/app/AppShell.vue'
import { useChartConfig } from '@/app/useChartConfig'
import { useDashboardComposition } from '@/app/useDashboardComposition'
import { useDashboardRuntime } from '@/app/useDashboardRuntime'
import { useController } from '@/core/injection'
import { DashboardController } from './controllers/dashboardController'
import type { WidgetState } from './core/widgetRegistry'

const dashboard = useController<DashboardController>('dashboard')

const { weather, interrupts, appStates, loading, error, latestWeather } = useDashboardRuntime(dashboard)
const { chartConfig } = useChartConfig()

const widgetState = computed<WidgetState>(() => ({
  weather: weather.value,
  interrupts: interrupts.value,
  appStates: appStates.value,
  loading: loading.value,
  error: error.value,
  latestWeather: latestWeather.value,
  chartConfig: chartConfig.value,
}))

const { leftWidgets, rightWidgets } = useDashboardComposition(widgetState)
</script>
