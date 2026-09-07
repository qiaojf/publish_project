import request from './request'
import { mockDb } from '@/mock/database'
import { useMock, unwrap } from './runtime'
import type { DeleteResult } from '@/types/api'
import type { PublishTarget, PublishTargetPayload } from '@/types/publish'

export const getPublishTargets = (): Promise<PublishTarget[]> => useMock ? mockDb.getTargets() : request.get<PublishTarget[]>('/publish-targets').then(unwrap)
export const createPublishTarget = (data: PublishTargetPayload): Promise<PublishTarget> => useMock ? mockDb.createTarget(data) : request.post<PublishTarget>('/publish-targets', data).then(unwrap)
export const updatePublishTarget = (id: number, data: PublishTargetPayload): Promise<PublishTarget> => useMock ? mockDb.updateTarget(id, data) : request.put<PublishTarget>(`/publish-targets/${id}`, data).then(unwrap)
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
