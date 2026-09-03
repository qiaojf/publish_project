import axios, { AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('publish-console-token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

request.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ message?: string }>) => {
    const status = error.response?.status
    if (status === 401) {
      localStorage.removeItem('publish-console-token')
      localStorage.removeItem('publish-console-user')
      if (location.pathname !== '/login') location.href = '/login'
    } else if (status === 403) {
      if (location.pathname !== '/403') location.href = '/403'
    } else {
      ElMessage.error(error.response?.data?.message || (error.request ? '网络连接失败，请稍后重试' : '请求处理失败'))
    }
    return Promise.reject(error)
  }
)

export default request
