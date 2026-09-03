import type { PageParams } from './api'

export type ReviewStatus = 'draft' | 'pending' | 'approved' | 'rejected'
export type PublishStatus = 'unpublished' | 'publishing' | 'published' | 'failed'
export type ContentType = 'html' | 'dynamic' | 'ppt' | 'pdf' | 'word' | 'excel' | 'image' | 'file'

export interface ContentItem {
  id: number
  title: string
  description?: string | null
  category?: string | null
  content_type: ContentType
  file_name?: string | null
  file_size?: number | null
  content_body?: string | null
  created_by: number
  creator_name: string
  created_at: string
  updated_at: string
  submitted_at?: string | null
  review_status: ReviewStatus
  publish_status: PublishStatus
  publish_target_id?: number | null
  publish_target_name?: string | null
  published_at?: string | null
  view_url?: string | null
  reject_reason?: string | null
  failure_reason?: string | null
}

export interface ContentQuery extends PageParams {
  keyword?: string
  content_type?: ContentType | ''
  category?: string
  review_status?: ReviewStatus | ''
  publish_status?: PublishStatus | ''
}

export interface ContentPayload {
  title: string
  description: string
  category: string
  content_type: ContentType
  publish_target_id?: number
  file?: File
  file_name?: string
  file_size?: number
  content_body?: string
}

export type PreviewData =
  | { preview_type: 'url'; preview_url: string }
  | { preview_type: 'text'; content: string }
  | { preview_type: 'image'; preview_url: string }
  | { preview_type: 'pdf'; preview_url: string }
  | { preview_type: 'file'; preview_url?: string | null; file_name: string; file_size?: number | null }
  | { preview_type: 'unsupported' }
