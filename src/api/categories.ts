import request from './request'
import { mockDb } from '@/mock/database'
import { useMock, unwrap } from './runtime'
import type { DeleteResult } from '@/types/api'
import type { Category, CategoryPayload } from '@/types/category'

export const getCategories = (includeDisabled = false): Promise<Category[]> => useMock
  ? mockDb.getCategories(includeDisabled)
  : request.get<Category[]>('/categories', { params: includeDisabled ? { include_disabled: true } : undefined }).then(unwrap)
export const createCategory = (data: CategoryPayload): Promise<Category> => useMock ? mockDb.createCategory(data) : request.post<Category>('/categories', data).then(unwrap)
export const updateCategory = (id: number, data: CategoryPayload): Promise<Category> => useMock ? mockDb.updateCategory(id, data) : request.put<Category>(`/categories/${id}`, data).then(unwrap)
export const updateCategoryStatus = (id: number, enabled: boolean): Promise<Category> => useMock ? mockDb.updateCategoryStatus(id, enabled) : request.patch<Category>(`/categories/${id}/status`, { enabled }).then(unwrap)
export const deleteCategory = async (id: number): Promise<DeleteResult> => useMock
  ? { deleted: await mockDb.deleteCategory(id) }
  : request.delete<DeleteResult>(`/categories/${id}`).then(unwrap)
