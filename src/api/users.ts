import request from './request'
import { mockDb } from '@/mock/database'
import { cleanParams, useMock, unwrap } from './runtime'
import type { DeleteResult, PageResult } from '@/types/api'
import type { User, UserPayload, UserQuery, UserStatus } from '@/types/user'

export const getUsers = (params: UserQuery): Promise<PageResult<User>> => useMock ? mockDb.getUsers(params) : request.get<PageResult<User>>('/users', { params: cleanParams(params) }).then(unwrap)
export const getUser = (id: number): Promise<User> => useMock ? mockDb.getUser(id) : request.get<User>(`/users/${id}`).then(unwrap)
export const createUser = (data: UserPayload): Promise<User> => useMock ? mockDb.createUser(data) : request.post<User>('/users', data).then(unwrap)
export const updateUser = (id: number, data: UserPayload): Promise<User> => useMock ? mockDb.updateUser(id, data) : request.put<User>(`/users/${id}`, data).then(unwrap)
export const updateUserStatus = async (id: number, status: UserStatus): Promise<User> => {
  if (!useMock) return request.patch<User>(`/users/${id}/status`, { status }).then(unwrap)
  await mockDb.updateUserStatus(id, status)
  return mockDb.getUser(id)
}
export const deleteUser = async (id: number): Promise<DeleteResult> => useMock
  ? { deleted: await mockDb.deleteUser(id) }
  : request.delete<DeleteResult>(`/users/${id}`).then(unwrap)
