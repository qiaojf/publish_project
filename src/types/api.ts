export interface PageParams {
  page?: number
  page_size?: number
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ApiEnvelope<T> {
  success: boolean
  data: T
  message?: string
}

export interface DeleteResult {
  deleted: boolean
}
