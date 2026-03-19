import TimeSeriesChart from '@/components/chart/TimeSeriesChart.vue'
import DashboardErrorCard from '@/components/dashboard/DashboardErrorCard.vue'
import OSSDStatusPanel from '@/components/ossd/OSSDStatusPanel.vue'
import WeatherDetailsPanel from '@/components/weather/WeatherDetailsPanel.vue'
import WebcamPanel from '@/components/webcam/WebcamPanel.vue'
import { DASHBOARD_CONTAINERS, DASHBOARD_PAGE_ID } from '@/app/dashboardContract'
import {
  registerWidget,
  resetWidgetRegistry,
  validateWidgetRegistry,
  type WidgetState,
} from '@/core/widgetRegistry'

export function registerDashboardWidgets(): void {
  resetWidgetRegistry()

  registerWidget({
    id: 'webcam',
    title: 'Webcam',
    page: DASHBOARD_PAGE_ID,
    container: DASHBOARD_CONTAINERS.left,
    order: 10,
    component: WebcamPanel,
    props: (_state: WidgetState) => ({}),
    test: {
      contractId: 'webcam',
      traceLabel: 'Webcam panel',
    },
  })

  registerWidget({
    id: 'ossdStatus',
    title: 'OSSD Status',
    page: DASHBOARD_PAGE_ID,
    container: DASHBOARD_CONTAINERS.left,
    order: 20,
    component: OSSDStatusPanel,
    props: (state: WidgetState) => ({
      interrupts: state.interrupts,
      loading: state.loading,
    }),
    test: {
      contractId: 'ossdStatus',
      traceLabel: 'OSSD status panel',
    },
  })

  registerWidget({
    id: 'timeSeries',
    title: 'Zeitverlauf',
    page: DASHBOARD_PAGE_ID,
    container: DASHBOARD_CONTAINERS.right,
    order: 10,
    component: TimeSeriesChart,
    props: (state: WidgetState) => ({
      weather: state.weather,
      interrupts: state.interrupts,
      appStates: state.appStates,
      config: state.chartConfig,
    }),
    visible: (state: WidgetState) => !!state.weather.length,
    test: {
      contractId: 'timeSeries',
      traceLabel: 'Time series chart',
    },
  })

  registerWidget({
    id: 'weatherDetails',
    title: 'Wetterdetails',
    page: DASHBOARD_PAGE_ID,
    container: DASHBOARD_CONTAINERS.right,
    order: 20,
    component: WeatherDetailsPanel,
    props: (state: WidgetState) => ({
      weather: state.latestWeather,
    }),
    test: {
      contractId: 'weatherDetails',
      traceLabel: 'Weather details panel',
    },
  })

  registerWidget({
    id: 'dashboardError',
    title: 'Fehlerstatus',
    page: DASHBOARD_PAGE_ID,
    container: DASHBOARD_CONTAINERS.right,
    order: 30,
    component: DashboardErrorCard,
    props: (state: WidgetState) => ({
      error: state.error,
    }),
    visible: (state: WidgetState) => !!state.error,
    test: {
      contractId: 'dashboardError',
      traceLabel: 'Dashboard error card',
    },
  })

  validateWidgetRegistry(['webcam', 'ossdStatus', 'timeSeries', 'weatherDetails', 'dashboardError'])
}
