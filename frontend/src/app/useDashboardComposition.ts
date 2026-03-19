import { computed, type ComputedRef } from 'vue'

import { DASHBOARD_CONTAINERS, DASHBOARD_PAGE_ID } from '@/app/dashboardContract'
import { resolveWidgets, type ResolvedWidget, type WidgetState } from '@/core/widgetRegistry'

export interface DashboardComposition {
  leftWidgets: ComputedRef<ResolvedWidget[]>
  rightWidgets: ComputedRef<ResolvedWidget[]>
}

export function useDashboardComposition(
  widgetState: ComputedRef<WidgetState>,
): DashboardComposition {
  const leftWidgets = computed(() =>
    resolveWidgets(DASHBOARD_PAGE_ID, DASHBOARD_CONTAINERS.left, widgetState.value),
  )
  const rightWidgets = computed(() =>
    resolveWidgets(DASHBOARD_PAGE_ID, DASHBOARD_CONTAINERS.right, widgetState.value),
  )

  return {
    leftWidgets,
    rightWidgets,
  }
}
