import request from './request'
import { useMock, unwrap } from './runtime'
import { mockDb } from '@/mock/database'
import type { CurrentUser } from '@/types/user'

export interface LoginResult { token: string; user: CurrentUser }
export const login = (username: string, password: string): Promise<LoginResult> => useMock ? mockDb.login(username, password) : request.post<LoginResult>('/auth/login', { username, password }).then(unwrap)
export const logout = (): Promise<void> => useMock ? mockDb.logout() : request.post<void>('/auth/logout').then(unwrap)
export const getCurrentUser = (): Promise<CurrentUser> => useMock ? mockDb.me() : request.get<CurrentUser>('/auth/me').then(unwrap)
