import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import TimeSeriesChart from '@/components/chart/TimeSeriesChart.vue'
import type { ChartConfig } from '@/stores/uiStore'
import type { AppStateRecord, InterruptRecord, WeatherRecord } from '@/types/domain'

function dispatchPointerEvent(element: Element, type: string, clientX: number): void {
  const event = new Event(type, { bubbles: true })
  Object.defineProperty(event, 'clientX', { value: clientX })
  Object.defineProperty(event, 'clientY', { value: 160 })
  element.dispatchEvent(event)
}

function createChartConfig(): ChartConfig {
  return {
    visibleDatasets: {
      temp: true,
      winds: true,
      humidity: true,
      light: true,
      pressure: false,
      winddir: true,
      interrupts: true,
    },
    timeWindow: '24h',
    timeUnit: 'hour',
    windowSpanPercent: 100,
    windowSpanMode: 'preset',
    tension: 0.4,
    autoY: true,
    yMax: null,
    colors: {
      temp: '#e76f51',
      winds: '#e9c46a',
      humidity: '#2a9d8f',
      light: '#4cc9f0',
      pressure: '#ff6b6b',
      interrupts: '#d62828',
      offline: '#6d597a',
    },
  }
}

function createWeather(): WeatherRecord[] {
  return [
    { _id: 'w1', temp: 18, pressure: 1000, light: 120, winds: 2, winddir: 'N', rain: 0, humidity: 40, time: '2026-03-08T00:00:00Z' },
    { _id: 'w2', temp: 19, pressure: 1001, light: 180, winds: 2, winddir: 'N', rain: 0, humidity: 44, time: '2026-03-08T12:00:00Z' },
    { _id: 'w3', temp: 20, pressure: 1002, light: 260, winds: 2, winddir: 'N', rain: 0, humidity: 48, time: '2026-03-09T00:00:00Z' },
    { _id: 'w4', temp: 21, pressure: 1003, light: 320, winds: 2, winddir: 'N', rain: 0, humidity: 51, time: '2026-03-09T12:00:00Z' },
    { _id: 'w5', temp: 22, pressure: 1004, light: 390, winds: 2, winddir: 'N', rain: 0, humidity: 55, time: '2026-03-10T00:00:00Z' },
  ]
}

function createInterrupts(): InterruptRecord[] {
  return [
    { _id: 'i1', time: '2026-03-08T06:00:00Z', lichtgitterNr: 1, ossdNr: 1, ossdStatus: 'E' },
    { _id: 'i2', time: '2026-03-09T18:00:00Z', lichtgitterNr: 1, ossdNr: 2, ossdStatus: 'E' },
  ]
}

function createAppStates(): AppStateRecord[] {
  return [
    { _id: 's1', time: '2026-03-09T03:00:00Z', state: 'stop' },
    { _id: 's2', time: '2026-03-09T09:00:00Z', state: 'start' },
  ]
}

describe('TimeSeriesChart', () => {
  it('toggles visible datasets from the toolbar', async () => {
    const config = createChartConfig()
    config.visibleDatasets.pressure = true
    const wrapper = mount(TimeSeriesChart, {
      props: {
        weather: createWeather(),
        interrupts: createInterrupts(),
        appStates: createAppStates(),
        config,
      },
    })

    expect(wrapper.findAll('.ts-chart-line').length).toBe(5)

    await wrapper.findAll('button').find((item) => item.text() === 'Temperatur')!.trigger('click')
    expect(config.visibleDatasets.temp).toBe(true)

    await wrapper.findAll('button').find((item) => item.text() === 'Einstellungen anwenden')!.trigger('click')

    expect(config.visibleDatasets.temp).toBe(false)
    expect(wrapper.findAll('.ts-chart-line').length).toBe(4)
  })

  it('filters the time window and lets the user move through it', async () => {
    const config = createChartConfig()
    const wrapper = mount(TimeSeriesChart, {
      props: {
        weather: createWeather(),
        interrupts: createInterrupts(),
        appStates: createAppStates(),
        config,
      },
    })

    const initialSummary = wrapper.get('[data-testid="widget-time-series-window-label"]').text()
    const slider = wrapper.get('[data-testid="widget-time-series-window-slider"]')

    await slider.setValue('0')

    const shiftedSummary = wrapper.get('[data-testid="widget-time-series-window-label"]').text()

    expect(shiftedSummary).not.toBe(initialSummary)

    await wrapper.get('select').setValue('6h')
    expect(config.timeWindow).toBe('24h')

    await wrapper.findAll('button').find((item) => item.text() === 'Einstellungen anwenden')!.trigger('click')

    expect(config.timeWindow).toBe('6h')
    expect(Number((wrapper.get('[data-testid="widget-time-series-window-slider"]').element as HTMLInputElement).value)).toBe(50)
    expect(wrapper.get('[data-testid="widget-time-series-window-label"]').text()).toContain('Messpunkte')
  })

  it('supports drag zoom and resetting to the latest view', async () => {
    const config = createChartConfig()
    const wrapper = mount(TimeSeriesChart, {
      attachTo: document.body,
      props: {
        weather: createWeather(),
        interrupts: createInterrupts(),
        appStates: createAppStates(),
        config,
      },
    })

    const svg = wrapper.get('[data-testid="widget-time-series-canvas"]')
    Object.defineProperty(svg.element, 'getBoundingClientRect', {
      value: () => ({ left: 0, width: 960, top: 0, height: 360, right: 960, bottom: 360 }),
    })

    const beforeZoom = wrapper.get('[data-testid="widget-time-series-window-label"]').text()

    dispatchPointerEvent(svg.element, 'pointerdown', 180)
    dispatchPointerEvent(svg.element, 'pointermove', 560)
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.ts-chart-selection').exists()).toBe(true)
    dispatchPointerEvent(svg.element, 'pointerup', 560)
    await wrapper.vm.$nextTick()

    const afterZoom = wrapper.get('[data-testid="widget-time-series-window-label"]').text()
    expect(afterZoom).toContain('Zoom aktiv')
    expect(afterZoom).not.toBe(beforeZoom)

    await wrapper.findAll('button').find((item) => item.text() === 'Auf aktuellste Ansicht')!.trigger('click')

    expect(wrapper.get('[data-testid="widget-time-series-window-label"]').text()).not.toContain('Zoom aktiv')
    wrapper.unmount()
  })

  it('shows hover details for rendered data streams', async () => {
    const config = createChartConfig()
    config.visibleDatasets.pressure = true
    const wrapper = mount(TimeSeriesChart, {
      attachTo: document.body,
      props: {
        weather: createWeather(),
        interrupts: createInterrupts(),
        appStates: createAppStates(),
        config,
      },
    })

    const firstHoverTarget = wrapper.find('.ts-chart-hover-target')
    dispatchPointerEvent(firstHoverTarget.element, 'pointerenter', 220)
    await wrapper.vm.$nextTick()

    const tooltipText = wrapper.find('.ts-chart-tooltip').text()
    expect(tooltipText).toContain('Temperatur')
    expect(tooltipText).toContain('20.00')

    wrapper.unmount()
  })

  it('renders offline bands and no visible data point markers', () => {
    const wrapper = mount(TimeSeriesChart, {
      props: {
        weather: createWeather(),
        interrupts: createInterrupts(),
        appStates: createAppStates(),
        config: createChartConfig(),
      },
    })

    expect(wrapper.findAll('.ts-chart-offline-band').length).toBe(1)
    expect(wrapper.findAll('.ts-chart-point').length).toBe(0)
  })

  it('lets the user switch to accessible color palettes', async () => {
    const config = createChartConfig()
    const wrapper = mount(TimeSeriesChart, {
      props: {
        weather: createWeather(),
        interrupts: createInterrupts(),
        appStates: createAppStates(),
        config,
      },
    })

    await wrapper.findAll('button').find((item) => item.text() === 'Farbenblind')!.trigger('click')

    expect(config.colors.temp).toBe('#e76f51')

    await wrapper.findAll('button').find((item) => item.text() === 'Einstellungen anwenden')!.trigger('click')

    expect(config.colors.temp).toBe('#d55e00')
    expect(wrapper.find('.ts-chart-line--temp').attributes('style')).toContain('stroke: #d55e00')
  })

  it('lets the user manually scale the visible time span', async () => {
    const config = createChartConfig()
    const wrapper = mount(TimeSeriesChart, {
      props: {
        weather: createWeather(),
        interrupts: createInterrupts(),
        appStates: createAppStates(),
        config,
      },
    })

    const before = wrapper.get('[data-testid="widget-time-series-window-label"]').text()

    await wrapper.get('[data-testid="widget-time-series-span-slider"]').setValue('40')
    expect(config.windowSpanMode).toBe('preset')

    await wrapper.findAll('button').find((item) => item.text() === 'Einstellungen anwenden')!.trigger('click')

    const after = wrapper.get('[data-testid="widget-time-series-window-label"]').text()
    expect(config.windowSpanMode).toBe('manual')
    expect(config.windowSpanPercent).toBe(40)
    expect(Number((wrapper.get('[data-testid="widget-time-series-window-slider"]').element as HTMLInputElement).value)).toBe(50)
    expect(after).not.toBe(before)
  })

  it('lets the user discard unapplied settings changes', async () => {
    const config = createChartConfig()
    const wrapper = mount(TimeSeriesChart, {
      props: {
        weather: createWeather(),
        interrupts: createInterrupts(),
        appStates: createAppStates(),
        config,
      },
    })

    await wrapper.findAll('button').find((item) => item.text() === 'Temperatur')!.trigger('click')
    await wrapper.findAll('button').find((item) => item.text() === 'Entwurf verwerfen')!.trigger('click')

    expect(config.visibleDatasets.temp).toBe(true)
    expect(wrapper.findAll('.ts-chart-line').length).toBe(4)
  })
})
