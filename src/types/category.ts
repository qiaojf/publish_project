export interface Category {
  id: number
  name: string
  enabled: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export interface CategoryPayload {
  name: string
  enabled: boolean
  sort_order: number
}
