import type { ContentItem } from './content'

export interface DashboardData {
  content_total?: number
  my_content_total?: number
  pending_review: number
  published: number
  publish_failed?: number
  rejected?: number
  recent_submissions: ContentItem[]
  recent_publishes: ContentItem[]
}
