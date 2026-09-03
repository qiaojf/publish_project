import request from './request'
import { mockDb } from '@/mock/database'
import { cleanParams, useMock, unwrap } from './runtime'
import type { PageResult } from '@/types/api'
import type { ContentItem, ContentQuery } from '@/types/content'

export interface SearchQuery extends ContentQuery { date_from?: string; date_to?: string }
export const searchContents = (params: SearchQuery): Promise<PageResult<ContentItem>> => useMock ? mockDb.search(params) : request.get<PageResult<ContentItem>>('/search', { params: cleanParams(params) }).then(unwrap)
