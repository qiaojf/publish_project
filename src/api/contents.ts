import request from './request'
import { mockDb } from '@/mock/database'
import { cleanParams, useMock, unwrap } from './runtime'
import type { DeleteResult, PageResult } from '@/types/api'
import type { ContentItem, ContentPayload, ContentQuery, PreviewData } from '@/types/content'

function toFormData(payload: ContentPayload) {
  const data = new FormData()
  Object.entries(payload).forEach(([key, value]) => {
    if (value === undefined || value === null || key === 'files' || key === 'file_name' || key === 'file_size') return
    data.append(key, String(value))
  })
  payload.files?.forEach((item) => {
    data.append('files', item.file, item.file.name)
    data.append('file_paths', item.relative_path)
  })
  return data
}
const UPLOAD_TIMEOUT_MS = 10 * 60 * 1000
const PUBLISH_TIMEOUT_MS = 11 * 60 * 1000
export const getContents = (params: ContentQuery): Promise<PageResult<ContentItem>> => useMock ? mockDb.getContents(params) : request.get<PageResult<ContentItem>>('/contents', { params: cleanParams(params) }).then(unwrap)
export const getContent = (id: number): Promise<ContentItem> => useMock ? mockDb.getContent(id) : request.get<ContentItem>(`/contents/${id}`).then(unwrap)
export const createContent = (data: ContentPayload): Promise<ContentItem> => useMock ? mockDb.createContent(data) : request.post<ContentItem>('/contents', toFormData(data), { timeout: UPLOAD_TIMEOUT_MS }).then(unwrap)
export const updateContent = (id: number, data: ContentPayload): Promise<ContentItem> => useMock ? mockDb.updateContent(id, data) : request.put<ContentItem>(`/contents/${id}`, toFormData(data), { timeout: UPLOAD_TIMEOUT_MS }).then(unwrap)
export const deleteContent = async (id: number): Promise<DeleteResult> => useMock
  ? { deleted: await mockDb.deleteContent(id) }
  : request.delete<DeleteResult>(`/contents/${id}`).then(unwrap)
export const submitContent = (id: number): Promise<ContentItem> => useMock ? mockDb.submitContent(id) : request.post<ContentItem>(`/contents/${id}/submit`).then(unwrap)
export const publishContent = (id: number): Promise<ContentItem> => useMock ? mockDb.publishContent(id) : request.post<ContentItem>(`/contents/${id}/publish`, undefined, { timeout: PUBLISH_TIMEOUT_MS }).then(unwrap)
export const republishContent = (id: number): Promise<ContentItem> => useMock ? mockDb.republishContent(id) : request.post<ContentItem>(`/contents/${id}/republish`, undefined, { timeout: PUBLISH_TIMEOUT_MS }).then(unwrap)
export const getContentPreview = (id: number): Promise<PreviewData> => useMock ? mockDb.preview(id) : request.get<PreviewData>(`/contents/${id}/preview`).then(unwrap)
export const getContentPreviewFile = (id: number): Promise<Blob> => request.get<Blob>(`/contents/${id}/preview/file`, { responseType: 'blob' }).then((response) => response.data)
export const getContentPreviewSourceFile = (id: number, relativePath: string): Promise<Blob> => {
  const encoded = relativePath.split('/').map(encodeURIComponent).join('/')
  return request.get<Blob>(`/contents/${id}/preview/files/${encoded}`, { responseType: 'blob' }).then((response) => response.data)
}
