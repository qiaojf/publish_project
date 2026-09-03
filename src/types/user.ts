import type { PageParams } from './api'

export type UserRole = 'admin' | 'employee'
export type UserStatus = 'active' | 'disabled'

export interface CurrentUser {
  id: number
  username: string
  name: string
  role: UserRole
  status: UserStatus
}

export interface User extends CurrentUser {
  created_at: string
  updated_at: string
}

export interface UserQuery extends PageParams {
  keyword?: string
  role?: UserRole | ''
  status?: UserStatus | ''
}

export interface UserPayload {
  username: string
  name: string
  password?: string
  role: UserRole
  status: UserStatus
}
