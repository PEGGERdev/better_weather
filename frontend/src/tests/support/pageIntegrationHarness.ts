import { mount, type VueWrapper } from '@vue/test-utils'

import AppShell from '@/app/AppShell.vue'
import {
  DASHBOARD_CONTAINERS,
  type DashboardContainer,
  type DashboardPageId,
} from '@/app/dashboardContract'
import {
  getWidgetsByContainer,
  resolveWidgets,
  type WidgetDefinition,
  type WidgetState,
} from '@/core/widgetRegistry'

import { PageIntegrationTrace } from './pageIntegrationTrace'
import { widgetSmokeTestContracts } from './widgetContracts'

export interface PageIntegrationResult {
  trace: PageIntegrationTrace
  testedWidgetIds: string[]
}

export async function runDashboardPageIntegration(
  page: DashboardPageId,
): Promise<PageIntegrationResult> {
  const trace = new PageIntegrationTrace()
  const testedWidgetIds: string[] = []

  for (const container of Object.values(DASHBOARD_CONTAINERS)) {
    trace.record({
      page,
      container,
      widget: null,
      adapter: null,
      step: 'resolve container widgets',
      status: 'running',
    })

    const definitions = getWidgetsByContainer(page, container)

    trace.record({
      page,
      container,
      widget: null,
      adapter: null,
      step: 'resolve container widgets',
      status: 'passed',
      detail: `${definitions.length} registered`,
    })

    for (const definition of definitions) {
      await exerciseWidget(page, container, definition, trace)
      testedWidgetIds.push(definition.id)
    }
  }

  return {
    trace,
    testedWidgetIds,
  }
}

async function exerciseWidget(
  page: DashboardPageId,
  container: DashboardContainer,
  definition: WidgetDefinition,
  trace: PageIntegrationTrace,
): Promise<void> {
  const contractId = definition.test?.contractId
  const adapterLabel = definition.test?.traceLabel || contractId || definition.id

  if (!contractId) {
    throw new Error(`Missing widget test metadata for ${definition.id}`)
  }

  const contract = widgetSmokeTestContracts[contractId]
  if (!contract) {
    throw new Error(`Unknown widget smoke test contract: ${contractId}`)
  }

  const widgetState = contract.buildState ? contract.buildState() : createEmptyState()

  trace.record({
    page,
    container,
    widget: definition.id,
    adapter: adapterLabel,
    step: 'resolve visible widgets',
    status: 'running',
  })

  const leftWidgets = resolveWidgets(page, DASHBOARD_CONTAINERS.left, widgetState)
  const rightWidgets = resolveWidgets(page, DASHBOARD_CONTAINERS.right, widgetState)
  const resolvedIds = [...leftWidgets, ...rightWidgets].map((widget) => widget.id)

  if (!resolvedIds.includes(definition.id)) {
    trace.record({
      page,
      container,
      widget: definition.id,
      adapter: adapterLabel,
      step: 'resolve visible widgets',
      status: 'failed',
      detail: 'widget not visible for smoke state',
    })
    throw new Error(trace.format())
  }

  trace.record({
    page,
    container,
    widget: definition.id,
    adapter: adapterLabel,
    step: 'resolve visible widgets',
    status: 'passed',
  })

  let wrapper: VueWrapper<any> | null = null

  try {
    trace.record({
      page,
      container,
      widget: definition.id,
      adapter: adapterLabel,
      step: 'mount page shell',
      status: 'running',
    })

    wrapper = mount(AppShell, {
      props: {
        leftWidgets,
        rightWidgets,
      },
    })

    trace.record({
      page,
      container,
      widget: definition.id,
      adapter: adapterLabel,
      step: 'mount page shell',
      status: 'passed',
    })

    trace.record({
      page,
      container,
      widget: definition.id,
      adapter: adapterLabel,
      step: 'run widget smoke contract',
      status: 'running',
    })

    await contract.assert({ wrapper, widgetState })

    trace.record({
      page,
      container,
      widget: definition.id,
      adapter: adapterLabel,
      step: 'run widget smoke contract',
      status: 'passed',
    })
  } catch (error) {
    trace.record({
      page,
      container,
      widget: definition.id,
      adapter: adapterLabel,
      step: 'run widget smoke contract',
      status: 'failed',
      detail: error instanceof Error ? error.message : String(error),
    })
    throw new Error(trace.format())
  } finally {
    wrapper?.unmount()
  }
}

function createEmptyState() {
  return {
    weather: [],
    interrupts: [],
    appStates: [],
    loading: false,
    error: null,
    latestWeather: null,
    chartConfig: {},
  } satisfies WidgetState
}
