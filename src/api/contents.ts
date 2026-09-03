import request from './request'
import { mockDb } from '@/mock/database'
import { cleanParams, useMock, unwrap } from './runtime'
import type { DeleteResult, PageResult } from '@/types/api'
import type { ContentItem, ContentPayload, ContentQuery, PreviewData } from '@/types/content'

function toFormData(payload: ContentPayload) {
  const data = new FormData()
  Object.entries(payload).forEach(([key, value]) => { if (value !== undefined) data.append(key, value instanceof File ? value : String(value)) })
  return data
}
export const getContents = (params: ContentQuery): Promise<PageResult<ContentItem>> => useMock ? mockDb.getContents(params) : request.get<PageResult<ContentItem>>('/contents', { params: cleanParams(params) }).then(unwrap)
export const getContent = (id: number): Promise<ContentItem> => useMock ? mockDb.getContent(id) : request.get<ContentItem>(`/contents/${id}`).then(unwrap)
export const createContent = (data: ContentPayload): Promise<ContentItem> => useMock ? mockDb.createContent(data) : request.post<ContentItem>('/contents', toFormData(data)).then(unwrap)
export const updateContent = (id: number, data: ContentPayload): Promise<ContentItem> => useMock ? mockDb.updateContent(id, data) : request.put<ContentItem>(`/contents/${id}`, toFormData(data)).then(unwrap)
export const deleteContent = async (id: number): Promise<DeleteResult> => useMock
  ? { deleted: await mockDb.deleteContent(id) }
  : request.delete<DeleteResult>(`/contents/${id}`).then(unwrap)
export const submitContent = (id: number): Promise<ContentItem> => useMock ? mockDb.submitContent(id) : request.post<ContentItem>(`/contents/${id}/submit`).then(unwrap)
export const publishContent = (id: number): Promise<ContentItem> => useMock ? mockDb.publishContent(id) : request.post<ContentItem>(`/contents/${id}/publish`).then(unwrap)
export const republishContent = (id: number): Promise<ContentItem> => useMock ? mockDb.republishContent(id) : request.post<ContentItem>(`/contents/${id}/republish`).then(unwrap)
export const getContentPreview = (id: number): Promise<PreviewData> => useMock ? mockDb.preview(id) : request.get<PreviewData>(`/contents/${id}/preview`).then(unwrap)
export const getContentPreviewFile = (id: number): Promise<Blob> => request.get<Blob>(`/contents/${id}/preview/file`, { responseType: 'blob' }).then((response) => response.data)
