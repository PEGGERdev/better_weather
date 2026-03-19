export type TraceStatus = 'running' | 'passed' | 'failed'

export interface PageIntegrationTraceEntry {
  page: string
  container: string | null
  widget: string | null
  adapter: string | null
  step: string
  status: TraceStatus
  detail?: string
}

export class PageIntegrationTrace {
  private readonly entries: PageIntegrationTraceEntry[] = []

  record(entry: PageIntegrationTraceEntry): void {
    this.entries.push(entry)
  }

  snapshot(): PageIntegrationTraceEntry[] {
    return [...this.entries]
  }

  format(): string {
    return this.entries
      .map((entry) => {
        const scope = [entry.page, entry.container, entry.widget, entry.adapter]
          .filter(Boolean)
          .join(' > ')

        return `${entry.status.toUpperCase()} ${scope}: ${entry.step}${entry.detail ? ` (${entry.detail})` : ''}`
      })
      .join('\n')
  }
}
