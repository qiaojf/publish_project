import type { ContentType } from './content'
import type { PageParams } from './api'

export type PublishTargetType = 'local' | 'sftp' | 'github' | 'github_pages' | 'onedrive' | 'dropbox'

export interface PublishTarget {
  id: number
  name: string
  content_types: ContentType[]
  target_type: PublishTargetType
  config?: Record<string, string | number | boolean>
  credential_ref?: string | null
  publish_root?: string
  base_url?: string
  created_by?: number
  enabled: boolean
  created_at: string
  updated_at?: string
}

export interface PublishTargetPayload {
  name: string
  content_types: ContentType[]
  target_type: PublishTargetType
  config: Record<string, string | number | boolean>
  credential_ref?: string
  publish_root?: string
  base_url?: string
  enabled: boolean
}

export interface OperationLog {
  id: number
  created_at: string
  user_id: number
  user_name: string
  action: string
  object: string
  description: string
}

export interface PublishLog {
  id: number
  created_at: string
  content_id: number
  content_title: string
  content_type: ContentType
  target_name: string
  status: PublishRecordStatus
  view_url?: string | null
  failure_reason?: string | null
}

export interface OperationLogQuery extends PageParams {
  user_id?: number
  action?: string
  date_from?: string
  date_to?: string
}

export interface PublishLogQuery extends PageParams {
  keyword?: string
  content_type?: ContentType | ''
  status?: PublishRecordStatus | ''
  date_from?: string
  date_to?: string
}

export type PublishRecordStatus = 'publishing' | 'success' | 'failed'
