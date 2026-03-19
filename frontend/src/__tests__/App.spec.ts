import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { buildAppContext } from '@/bootstrap/appBootstrap'
import { registerDashboardWidgets } from '@/bootstrap/widgetRegistrations'
import { APP_CTX_KEY } from '@/core/injection'
import App from '../App.vue'

function mountApp() {
  registerDashboardWidgets()

  return mount(App, {
    global: {
      provide: {
        [APP_CTX_KEY as symbol]: buildAppContext(),
      },
    },
  })
}

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        status: 200,
        text: async () => JSON.stringify([]),
      })),
    )

    vi.stubGlobal('navigator', {
      mediaDevices: {
        getUserMedia: vi.fn(),
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

  it('mounts and renders main sections', () => {
    const wrapper = mountApp()

    expect(wrapper.text()).toContain('Lichtgitter OSSD')
    expect(wrapper.text()).toContain('Aktuelle Wetterdaten')
  })

  it('shows OSSD status panel', () => {
    const wrapper = mountApp()

    expect(wrapper.text()).toContain('Lichtgitter 1')
    expect(wrapper.text()).toContain('Lichtgitter 2')
  })
})
