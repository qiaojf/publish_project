import type { AxiosResponse } from 'axios'
import type { ApiEnvelope } from '@/types/api'

export const useMock = import.meta.env.VITE_USE_MOCK === 'true'

export function unwrap<T>(response: AxiosResponse<ApiEnvelope<T> | T>): T {
  const body = response.data
  if (typeof body === 'object' && body !== null && 'success' in body && 'data' in body) return (body as ApiEnvelope<T>).data
  return body as T
}

export function cleanParams(params: object): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== '' && value !== undefined && value !== null)
  )
}
