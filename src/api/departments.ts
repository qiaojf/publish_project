import request from './request'
import { mockDb } from '@/mock/database'
import { useMock, unwrap } from './runtime'
import type { DeleteResult } from '@/types/api'
import type { Department, DepartmentPayload } from '@/types/department'

export const getDepartments = (includeDisabled = false): Promise<Department[]> => useMock
  ? mockDb.getDepartments(includeDisabled)
  : request.get<Department[]>('/departments', { params: includeDisabled ? { include_disabled: true } : undefined }).then(unwrap)
export const createDepartment = (data: DepartmentPayload): Promise<Department> => useMock ? mockDb.createDepartment(data) : request.post<Department>('/departments', data).then(unwrap)
export const updateDepartment = (id: number, data: DepartmentPayload): Promise<Department> => useMock ? mockDb.updateDepartment(id, data) : request.put<Department>(`/departments/${id}`, data).then(unwrap)
export const updateDepartmentStatus = (id: number, enabled: boolean): Promise<Department> => useMock ? mockDb.updateDepartmentStatus(id, enabled) : request.patch<Department>(`/departments/${id}/status`, { enabled }).then(unwrap)
export const deleteDepartment = async (id: number): Promise<DeleteResult> => useMock
  ? { deleted: await mockDb.deleteDepartment(id) }
  : request.delete<DeleteResult>(`/departments/${id}`).then(unwrap)
