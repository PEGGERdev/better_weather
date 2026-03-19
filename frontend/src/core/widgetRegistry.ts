import { markRaw } from 'vue'

import type { DashboardContainer, DashboardPageId } from '@/app/dashboardContract'

import { GenericRegistry } from './registry'

export interface WidgetState {
  weather: unknown[]
  interrupts: unknown[]
  appStates: unknown[]
  loading: boolean
  error: string | null
  latestWeather: unknown | null
  chartConfig: unknown
}

export interface WidgetDefinition {
  id: string
  title: string
  page: DashboardPageId
  container: DashboardContainer
  order: number
  component: unknown
  props: (state: WidgetState) => Record<string, unknown>
  visible?: (state: WidgetState) => boolean
  test?: WidgetTestMetadata
}

export interface WidgetTestMetadata {
  contractId: string
  traceLabel?: string
}

export interface ResolvedWidget {
  id: string
  title: string
  component: unknown
  props: Record<string, unknown>
}

const widgetRegistry = new GenericRegistry<WidgetDefinition>()

export function registerWidget(definition: WidgetDefinition): void {
  widgetRegistry.register(definition.id, definition)
}

export function getWidgetsByContainer(
  page: DashboardPageId,
  container: DashboardContainer,
): WidgetDefinition[] {
  return Object.values(widgetRegistry.snapshot())
    .filter((item) => item.page === page && item.container === container)
    .sort((a, b) => a.order - b.order)
}

export function resolveWidgets(
  page: DashboardPageId,
  container: DashboardContainer,
  state: WidgetState,
): ResolvedWidget[] {
  return getWidgetsByContainer(page, container)
    .filter((item) => (item.visible ? item.visible(state) : true))
    .map((item) => ({
      id: item.id,
      title: item.title,
      component: markRaw(item.component as object),
      props: item.props(state),
    }))
}

export function resetWidgetRegistry(): void {
  widgetRegistry.clear()
}

export function validateWidgetRegistry(requiredIds: string[]): void {
  widgetRegistry.validate(requiredIds, 'widget')
}
