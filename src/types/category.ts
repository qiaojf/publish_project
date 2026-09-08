export type CategoryVisibility = 'publisher' | 'department' | 'all'

export interface Category {
  id: number
  name: string
  enabled: boolean
  sort_order: number
  visibility_scope: CategoryVisibility
  department: string | null
  created_at: string
  updated_at: string
}

export interface CategoryPayload {
  name: string
  enabled: boolean
  sort_order: number
  visibility_scope: CategoryVisibility
  department?: string | null
}
