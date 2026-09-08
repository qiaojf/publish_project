import request from './request'
import { mockDb } from '@/mock/database'
import { useMock, unwrap } from './runtime'
import type { DeleteResult } from '@/types/api'
import type { PublishTarget, PublishTargetPayload } from '@/types/publish'

function normalizedPayload(data: PublishTargetPayload): PublishTargetPayload {
  return {
    ...data,
    name: data.name.trim(),
    content_types: [...new Set(data.content_types)],
    config: { ...data.config },
    credential_ref: data.credential_ref?.trim() || undefined,
    publish_root: data.publish_root?.trim() || undefined,
    base_url: data.base_url?.trim() || undefined
  }
}

export const getPublishTargets = (): Promise<PublishTarget[]> => useMock ? mockDb.getTargets() : request.get<PublishTarget[]>('/publish-targets').then(unwrap)
export const createPublishTarget = (data: PublishTargetPayload): Promise<PublishTarget> => {
  const payload = normalizedPayload(data)
  return useMock ? mockDb.createTarget(payload) : request.post<PublishTarget>('/publish-targets', payload).then(unwrap)
}
export const updatePublishTarget = (id: number, data: PublishTargetPayload): Promise<PublishTarget> => {
  const payload = normalizedPayload(data)
  return useMock ? mockDb.updateTarget(id, payload) : request.put<PublishTarget>(`/publish-targets/${id}`, payload).then(unwrap)
}
export const updatePublishTargetStatus = async (id: number, enabled: boolean): Promise<PublishTarget> => {
  if (!useMock) return request.patch<PublishTarget>(`/publish-targets/${id}/status`, { enabled }).then(unwrap)
  await mockDb.updateTargetStatus(id, enabled)
  const target = (await mockDb.getTargets()).find((item) => item.id === id)
  if (!target) throw new Error('发布目标不存在')
  return target
}
export const deletePublishTarget = async (id: number): Promise<DeleteResult> => useMock
  ? { deleted: await mockDb.deleteTarget(id) }
  : request.delete<DeleteResult>(`/publish-targets/${id}`).then(unwrap)
export const testPublishTarget = (id: number): Promise<{ connected: boolean }> => useMock
  ? Promise.resolve({ connected: true })
  : request.post<{ connected: boolean }>(`/publish-targets/${id}/test`, undefined, { timeout: 120 * 1000 }).then(unwrap)
