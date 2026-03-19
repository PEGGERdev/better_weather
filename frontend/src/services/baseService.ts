import { toUserErrorMessage } from './apiErrors'

export class BaseService {
  serviceName: string
  _lastError: string

  constructor({ serviceName = 'service' } = {}) {
    this.serviceName = serviceName
    this._lastError = ''
  }

  lastError() {
    return this._lastError
  }

  clearError() {
    this._lastError = ''
  }

  captureError(error: unknown, fallbackMessage = '') {
    const fallback = fallbackMessage || `Unknown ${this.serviceName} error`
    this._lastError = toUserErrorMessage(error, fallback)
  }
}
