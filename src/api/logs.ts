import request from './request'
import { mockDb } from '@/mock/database'
import { cleanParams, useMock, unwrap } from './runtime'
import type { PageResult } from '@/types/api'
import type { OperationLog, OperationLogQuery, PublishLog, PublishLogQuery } from '@/types/publish'

type BackendOperationLog = Omit<OperationLog, 'object'> & { target: string }
const operationActionMap: Record<string, string> = {
  登录: 'login',
  新建内容: 'create_content',
  编辑内容: 'update_content',
  删除内容: 'delete_content',
  提交审核: 'submit_content',
  审核通过: 'approve_content',
  审核驳回: 'reject_content',
  发布内容: 'publish_content',
  重新发布: 'republish_content',
  新增用户: 'create_user',
  编辑用户: 'update_user',
  新增发布配置: 'create_publish_target',
  编辑发布配置: 'update_publish_target'
}
const operationActionLabel = Object.fromEntries(
  Object.entries(operationActionMap).map(([label, value]) => [value, label])
)

export const getOperationLogs = async (params: OperationLogQuery): Promise<PageResult<OperationLog>> => {
  if (useMock) return mockDb.getOperationLogs(params)
  const backendParams = { ...params, action: params.action ? operationActionMap[params.action] || params.action : undefined }
  const result = unwrap(await request.get<PageResult<BackendOperationLog>>('/logs/operations', { params: cleanParams(backendParams) }))
  return {
    ...result,
    items: result.items.map((item) => ({
      ...item,
      action: operationActionLabel[item.action] || item.action,
      object: item.target
    }))
  }
}

export const getPublishLogs = async (params: PublishLogQuery): Promise<PageResult<PublishLog>> => {
  if (useMock) return mockDb.getPublishLogs(params)
  return unwrap(await request.get<PageResult<PublishLog>>('/publish-records', { params: cleanParams(params) }))
}
