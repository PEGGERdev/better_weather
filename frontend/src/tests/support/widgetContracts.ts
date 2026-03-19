import { expect } from 'vitest'
import type { VueWrapper } from '@vue/test-utils'

import type { WidgetState } from '@/core/widgetRegistry'

import { createDashboardTestState } from './dashboardTestState'

export interface WidgetSmokeTestContext {
  wrapper: VueWrapper<any>
  widgetState: WidgetState
}

export interface WidgetSmokeTestContract {
  id: string
  buildState?: () => WidgetState
  assert: (context: WidgetSmokeTestContext) => void | Promise<void>
}

export const widgetSmokeTestContracts: Record<string, WidgetSmokeTestContract> = {
  webcam: {
    id: 'webcam',
    buildState: () => createDashboardTestState(),
    assert: ({ wrapper }) => {
      expect(wrapper.find('[data-testid="widget-webcam"]').exists()).toBe(true)
      expect(wrapper.find('video').exists()).toBe(true)
    },
  },
  ossdStatus: {
    id: 'ossdStatus',
    buildState: () => createDashboardTestState(),
    assert: ({ wrapper }) => {
      expect(wrapper.find('[data-testid="widget-ossd-status"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="widget-ossd-history"]').exists()).toBe(true)
    },
  },
  timeSeries: {
    id: 'timeSeries',
    buildState: () => createDashboardTestState(),
    assert: ({ wrapper }) => {
      expect(wrapper.find('[data-testid="widget-time-series"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="widget-time-series-canvas"]').exists()).toBe(true)
    },
  },
  weatherDetails: {
    id: 'weatherDetails',
    buildState: () => createDashboardTestState(),
    assert: ({ wrapper }) => {
      expect(wrapper.find('[data-testid="widget-weather-details"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="widget-weather-details-grid"]').exists()).toBe(true)
    },
  },
  dashboardError: {
    id: 'dashboardError',
    buildState: () => createDashboardTestState({ error: 'Backend offline' }),
    assert: ({ wrapper }) => {
      expect(wrapper.find('[data-testid="widget-dashboard-error"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('Backend offline')
    },
  },
}
