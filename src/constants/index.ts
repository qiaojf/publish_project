import type { ContentType, PublishStatus, ReviewStatus } from '@/types/content'
import type { CategoryVisibility } from '@/types/category'
import type { PublishRecordStatus, PublishTargetType } from '@/types/publish'
import type { UserRole, UserStatus } from '@/types/user'

export const COMPANY_SITE_URL = 'https://terabox.jp/'
export const COMPANY_LOGO_URL = 'https://terabox.jp/images/logo.png'

export const REVIEW_STATUS: Record<ReviewStatus, string> = {
  draft: 'status.review.draft', pending: 'status.review.pending', approved: 'status.review.approved', rejected: 'status.review.rejected'
}

export const PUBLISH_STATUS: Record<PublishStatus, string> = {
  unpublished: 'status.publish.unpublished', publishing: 'status.publish.publishing', published: 'status.publish.published', failed: 'status.publish.failed'
}

export const PUBLISH_RECORD_STATUS: Record<PublishRecordStatus, string> = {
  publishing: 'status.publishRecord.publishing', success: 'status.publishRecord.success', failed: 'status.publishRecord.failed'
}

export const CONTENT_TYPES: Record<ContentType, string> = {
  html: 'contentType.html', dynamic: 'contentType.dynamic', ppt: 'contentType.ppt', pdf: 'contentType.pdf',
  word: 'contentType.word', excel: 'contentType.excel', image: 'contentType.image', video: 'contentType.video', file: 'contentType.file'
}

export const USER_ROLES: Record<UserRole, string> = { admin: 'role.admin', employee: 'role.employee' }
export const USER_STATUS: Record<UserStatus, string> = { active: 'userStatus.active', disabled: 'userStatus.disabled' }
export const CATEGORY_VISIBILITY: Record<CategoryVisibility, string> = {
  publisher: 'visibility.publisher', department: 'visibility.department', all: 'visibility.all'
}

export const PUBLISH_TARGET_TYPES: Record<PublishTargetType, string> = {
  local: 'publishTarget.type.local', sftp: 'publishTarget.type.sftp', github: 'publishTarget.type.github',
  github_pages: 'publishTarget.type.githubPages', onedrive: 'publishTarget.type.onedrive',
  dropbox: 'publishTarget.type.dropbox', instagram: 'publishTarget.type.instagram'
}

export const OPERATION_ACTIONS: Record<string, string> = {
  login: 'operation.login',
  create_content: 'operation.createContent',
  update_content: 'operation.updateContent',
  delete_content: 'operation.deleteContent',
  submit_content: 'operation.submitContent',
  approve_content: 'operation.approveContent',
  reject_content: 'operation.rejectContent',
  publish_content: 'operation.publishContent',
  republish_content: 'operation.republishContent',
  create_user: 'operation.createUser',
  update_user: 'operation.updateUser',
  enable_user: 'operation.enableUser',
  disable_user: 'operation.disableUser',
  delete_user: 'operation.deleteUser',
  create_department: 'operation.createDepartment',
  update_department: 'operation.updateDepartment',
  enable_department: 'operation.enableDepartment',
  disable_department: 'operation.disableDepartment',
  delete_department: 'operation.deleteDepartment',
  create_category: 'operation.createCategory',
  update_category: 'operation.updateCategory',
  enable_category: 'operation.enableCategory',
  disable_category: 'operation.disableCategory',
  delete_category: 'operation.deleteCategory',
  create_publish_target: 'operation.createPublishTarget',
  update_publish_target: 'operation.updatePublishTarget',
  enable_publish_target: 'operation.enablePublishTarget',
  disable_publish_target: 'operation.disablePublishTarget',
  test_publish_target: 'operation.testPublishTarget',
  delete_publish_target: 'operation.deletePublishTarget'
}


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
  word: '.doc,.docx', excel: '.xls,.xlsx', image: 'image/*', video: '.mp4,.mov', file: '*'
}
