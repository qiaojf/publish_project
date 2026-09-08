export interface Department {
  id: number
  name: string
  enabled: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export interface DepartmentPayload {
  name: string
  enabled: boolean
  sort_order: number
}
