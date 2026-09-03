import request from './request'
import { mockDb } from '@/mock/database'
import { cleanParams, useMock, unwrap } from './runtime'
import type { PageResult } from '@/types/api'
import type { ContentItem } from '@/types/content'
import type { ReviewDetail, ReviewQuery } from '@/types/review'

export const getReviews = (params: ReviewQuery): Promise<PageResult<ContentItem>> => useMock ? mockDb.getReviews(params) : request.get<PageResult<ContentItem>>('/reviews', { params: cleanParams(params) }).then(unwrap)
export const getReviewDetail = (id: number): Promise<ReviewDetail> => useMock ? mockDb.getReviewDetail(id) : request.get<ReviewDetail>(`/reviews/${id}`).then(unwrap)
export const approveReview = (id: number, comment?: string): Promise<ContentItem> => useMock ? mockDb.approve(id, comment) : request.post<ContentItem>(`/reviews/${id}/approve`, { comment }).then(unwrap)
export const rejectReview = (id: number, comment: string): Promise<ContentItem> => useMock ? mockDb.reject(id, comment) : request.post<ContentItem>(`/reviews/${id}/reject`, { comment }).then(unwrap)
