export type DuplicatePolicy = 'error' | 'replace'

export interface RegistryOptions {
  duplicatePolicy?: DuplicatePolicy
}

export class GenericRegistry<T> {
  private readonly items: Map<string, T>
  private readonly duplicatePolicy: DuplicatePolicy

  constructor(options: RegistryOptions = {}) {
    this.items = new Map<string, T>()
    this.duplicatePolicy = options.duplicatePolicy || 'error'
  }

  register(id: string, value: T): void {
    const key = String(id)
    if (this.duplicatePolicy === 'error' && this.items.has(key)) {
      throw new Error(`Registry already contains id=${key}`)
    }
    this.items.set(key, value)
  }

  get(id: string): T {
    const key = String(id)
    const value = this.items.get(key)
    if (!value) {
      throw new Error(`Unknown registry id=${key}`)
    }
    return value
  }

  snapshot(): Record<string, T> {
    const out: Record<string, T> = {}
    for (const [key, value] of this.items.entries()) {
      out[key] = value
    }
    return out
  }

  clear(): void {
    this.items.clear()
  }

  validate(requiredIds: string[], label: string): void {
    for (const id of requiredIds) {
      const key = String(id)
      if (!this.items.has(key)) {
        throw new Error(`Missing ${label} registration: ${key}`)
      }
    }
  }
}
