import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { DASHBOARD_PAGE_ID } from '@/app/dashboardContract'
import { registerDashboardWidgets } from '@/bootstrap/widgetRegistrations'
import { resetWidgetRegistry } from '@/core/widgetRegistry'

import { runDashboardPageIntegration } from './support/pageIntegrationHarness'

describe('dashboard page integration harness', () => {
  beforeEach(() => {
    resetWidgetRegistry()
    registerDashboardWidgets()

    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation(
      () => ({}) as CanvasRenderingContext2D,
    )

    vi.stubGlobal('navigator', {
      mediaDevices: {
        getUserMedia: vi.fn(async () => ({
          getTracks: () => [],
        })),
      },
    })

    vi.stubGlobal(
      'setInterval',
      vi.fn(() => 1),
    )
    vi.stubGlobal('clearInterval', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('runs registered widget smoke contracts with trace coverage', async () => {
    const result = await runDashboardPageIntegration(DASHBOARD_PAGE_ID)
    const entries = result.trace.snapshot()

    expect(result.testedWidgetIds).toEqual([
      'webcam',
      'ossdStatus',
      'timeSeries',
      'weatherDetails',
      'dashboardError',
    ])

    expect(entries.some((entry) => entry.step === 'resolve container widgets')).toBe(true)
    expect(entries.some((entry) => entry.widget === 'timeSeries')).toBe(true)
    expect(entries.some((entry) => entry.widget === 'dashboardError')).toBe(true)
    expect(entries.every((entry) => entry.status !== 'failed')).toBe(true)
  })
})
