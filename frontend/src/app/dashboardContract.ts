export const DASHBOARD_PAGE_ID = 'dashboard' as const

export const DASHBOARD_CONTAINERS = {
  left: 'left',
  right: 'right',
} as const

export type DashboardPageId = typeof DASHBOARD_PAGE_ID
export type DashboardContainer = (typeof DASHBOARD_CONTAINERS)[keyof typeof DASHBOARD_CONTAINERS]
