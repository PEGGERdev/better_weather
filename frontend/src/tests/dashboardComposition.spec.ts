import { beforeEach, describe, expect, it } from 'vitest'

import { DASHBOARD_CONTAINERS, DASHBOARD_PAGE_ID } from '@/app/dashboardContract'
import { registerDashboardWidgets } from '@/bootstrap/widgetRegistrations'
import { resetWidgetRegistry, resolveWidgets, type WidgetState } from '@/core/widgetRegistry'

function createWidgetState(overrides: Partial<WidgetState> = {}): WidgetState {
  return {
    weather: [],
    interrupts: [],
    appStates: [],
    loading: false,
    error: null,
    latestWeather: null,
    chartConfig: {},
    ...overrides,
  }
}

describe('dashboard composition', () => {
  beforeEach(() => {
    resetWidgetRegistry()
    registerDashboardWidgets()
  })

  it('resolves left container widgets in registration order', () => {
    const widgets = resolveWidgets(
      DASHBOARD_PAGE_ID,
      DASHBOARD_CONTAINERS.left,
      createWidgetState(),
    )

    expect(widgets.map((widget) => widget.id)).toEqual(['webcam', 'ossdStatus'])
  })

  it('hides conditional widgets until their visibility rules pass', () => {
    const widgets = resolveWidgets(
      DASHBOARD_PAGE_ID,
      DASHBOARD_CONTAINERS.right,
      createWidgetState(),
    )

    expect(widgets.map((widget) => widget.id)).toEqual(['weatherDetails'])
  })

  it('shows data and error widgets when the state enables them', () => {
    const widgets = resolveWidgets(
      DASHBOARD_PAGE_ID,
      DASHBOARD_CONTAINERS.right,
      createWidgetState({
        weather: [{ time: '2026-03-11T14:00:00+00:00' }],
        error: 'Backend offline',
        latestWeather: { temp: 21.4 },
      }),
    )

    expect(widgets.map((widget) => widget.id)).toEqual([
      'timeSeries',
      'weatherDetails',
      'dashboardError',
    ])
  })
})
