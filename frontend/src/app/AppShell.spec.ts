import { describe, expect, it } from 'vitest'
import { defineComponent, markRaw } from 'vue'
import { mount } from '@vue/test-utils'

import AppShell from '@/app/AppShell.vue'
import type { ResolvedWidget } from '@/core/widgetRegistry'

const StubWidget = defineComponent({
  props: {
    label: {
      type: String,
      required: true,
    },
    expanded: {
      type: Boolean,
      default: false,
    },
  },
  template: '<div class="stub-widget">{{ label }} {{ expanded ? "expanded" : "base" }}</div>',
})

function createWidget(id: string, title: string, label: string): ResolvedWidget {
  return {
    id,
    title,
    component: markRaw(StubWidget),
    props: { label },
  }
}

describe('AppShell', () => {
  it('supports expanding and moving widgets between columns', async () => {
    const wrapper = mount(AppShell, {
      props: {
        leftWidgets: [createWidget('left-a', 'Left A', 'Left A')],
        rightWidgets: [createWidget('right-a', 'Right A', 'Right A')],
      },
    })

    const leftFrame = wrapper.findAllComponents({ name: 'DashboardWidgetFrame' })[0]!
    await leftFrame.findAll('button').find((button) => button.text() === 'Expandieren')!.trigger('click')

    expect(wrapper.find('.app-shell-overlay').exists()).toBe(true)
    expect(wrapper.find('.app-shell-overlay').text()).toContain('expanded')

    await leftFrame.findAll('button').find((button) => button.text() === 'Nach rechts')!.trigger('click')

    expect(wrapper.text()).toContain('Left A')
    expect(wrapper.find('.two-column-layout__column--right').text()).toContain('Left A')
  })
})
