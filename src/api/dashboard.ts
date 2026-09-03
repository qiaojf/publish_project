import request from './request'
import { mockDb } from '@/mock/database'
import { useMock, unwrap } from './runtime'
import type { DashboardData } from '@/types/dashboard'

export const getDashboard = (): Promise<DashboardData> => useMock ? mockDb.dashboard() : request.get<DashboardData>('/dashboard').then(unwrap)
