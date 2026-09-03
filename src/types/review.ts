import type { ContentItem } from './content'
import type { PageParams } from './api'

export interface ReviewRecord {
  id: number
  content_id: number
  action: 'submit' | 'approve' | 'reject'
  from_status: string | null
  to_status: string
  operated_by: number
  operator_name: string
  comment: string | null
  created_at: string
}

export interface ReviewDetail {
  content: ContentItem
  publish_target: import('./publish').PublishTarget | null
  history: ReviewRecord[]
}

export interface ReviewQuery extends PageParams {
  keyword?: string
  content_type?: import('./content').ContentType | ''
  category?: string
  submitted_by?: string
  date_from?: string
  date_to?: string
  status?: import('./content').ReviewStatus | ''
}
