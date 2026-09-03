import type { ContentType, PublishStatus, ReviewStatus } from '@/types/content'
import type { PublishRecordStatus } from '@/types/publish'
import type { UserRole, UserStatus } from '@/types/user'

export const COMPANY_SITE_URL = 'https://terabox.jp/'
export const COMPANY_LOGO_URL = 'https://terabox.jp/images/logo.png'

export const REVIEW_STATUS: Record<ReviewStatus, string> = {
  draft: '草稿', pending: '待审核', approved: '审核通过', rejected: '已驳回'
}

export const PUBLISH_STATUS: Record<PublishStatus, string> = {
  unpublished: '未发布', publishing: '发布中', published: '已发布', failed: '发布失败'
}

export const PUBLISH_RECORD_STATUS: Record<PublishRecordStatus, string> = {
  publishing: '发布中', success: '发布成功', failed: '发布失败'
}

export const CONTENT_TYPES: Record<ContentType, string> = {
  html: 'HTML 静态页面', dynamic: '动态页面', ppt: 'PPT / PPTX', pdf: 'PDF',
  word: 'Word', excel: 'Excel', image: '图片', file: '普通文件'
}

export const USER_ROLES: Record<UserRole, string> = { admin: '管理员', employee: '普通员工' }
export const USER_STATUS: Record<UserStatus, string> = { active: '启用', disabled: '禁用' }

export const CATEGORIES = ['制度规范', '产品资料', '销售方案', '培训材料', '品牌素材', '公共资源']

export const REVIEW_TAG_TYPES: Record<ReviewStatus, 'info' | 'warning' | 'success' | 'danger'> = {
  draft: 'info', pending: 'warning', approved: 'success', rejected: 'danger'
}

export const PUBLISH_TAG_TYPES: Record<PublishStatus, 'info' | 'warning' | 'success' | 'danger'> = {
  unpublished: 'info', publishing: 'warning', published: 'success', failed: 'danger'
}

export const PUBLISH_RECORD_TAG_TYPES: Record<PublishRecordStatus, 'warning' | 'success' | 'danger'> = {
  publishing: 'warning', success: 'success', failed: 'danger'
}

export const FILE_ACCEPT: Record<ContentType, string> = {
  html: '.html,.htm', dynamic: '.html,.zip', ppt: '.ppt,.pptx', pdf: '.pdf',
  word: '.doc,.docx', excel: '.xls,.xlsx', image: 'image/*', file: '*'
}
