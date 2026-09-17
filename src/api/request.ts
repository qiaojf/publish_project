import axios, { AxiosError } from 'axios'
import { getAppLocale, i18n } from '@/i18n'

interface ApiErrorBody { message?: string; error_code?: string }

const ERROR_CODE_KEYS: Record<string, string> = {
  AUTH_INVALID_CREDENTIALS: 'errorCode.authInvalidCredentials',
  AUTH_USER_DISABLED: 'errorCode.authUserDisabled',
  AUTH_UNAUTHORIZED: 'errorCode.authUnauthorized',
  AUTH_FORBIDDEN: 'errorCode.authForbidden',
  USER_NOT_FOUND: 'errorCode.userNotFound',
  USER_USERNAME_EXISTS: 'errorCode.userUsernameExists',
  CONTENT_NOT_FOUND: 'errorCode.contentNotFound',
  CONTENT_NOT_EDITABLE: 'errorCode.contentNotEditable',
  CONTENT_NOT_OWNER: 'errorCode.contentNotOwner',
  CONTENT_ALREADY_PUBLISHING: 'errorCode.contentAlreadyPublishing',
  REVIEW_INVALID_STATUS: 'errorCode.reviewInvalidStatus',
  REVIEW_COMMENT_REQUIRED: 'errorCode.reviewCommentRequired',
  PUBLISH_TARGET_NOT_FOUND: 'errorCode.publishTargetNotFound',
  PUBLISH_TARGET_DISABLED: 'errorCode.publishTargetDisabled',
  PUBLISH_TARGET_TYPE_MISMATCH: 'errorCode.publishTargetTypeMismatch',
  PUBLISH_TARGET_CREDENTIAL_MISSING: 'errorCode.publishTargetCredentialMissing',
  PUBLISH_CONNECTION_FAILED: 'errorCode.publishConnectionFailed',
  PUBLISH_AUTHENTICATION_FAILED: 'errorCode.publishAuthenticationFailed',
  PUBLISH_FAILED: 'errorCode.publishFailed',
  FILE_TOO_LARGE: 'errorCode.fileTooLarge',
  FILE_TYPE_NOT_SUPPORTED: 'errorCode.fileTypeNotSupported',
  UPLOAD_FAILED: 'errorCode.uploadFailed'
}

export function getRequestErrorMessage(error: unknown, fallbackKey = 'error.requestFailed'): string {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    const errorCode = error.response?.data?.error_code
    if (errorCode && ERROR_CODE_KEYS[errorCode]) return i18n.global.t(ERROR_CODE_KEYS[errorCode])
    if (error.response?.data?.message) return error.response.data.message
    if (error.request) return i18n.global.t('error.network')
  }
  return error instanceof Error && error.message ? error.message : i18n.global.t(fallbackKey)
}

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('publish-console-token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  config.headers['Accept-Language'] = getAppLocale()
  return config
})

request.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorBody>) => {
    const status = error.response?.status
    error.message = getRequestErrorMessage(error)
    if (status === 401) {
      localStorage.removeItem('publish-console-token')
      localStorage.removeItem('publish-console-user')
      if (location.pathname !== '/login') location.href = '/login'
    } else if (status === 403) {
      if (location.pathname !== '/login' && location.pathname !== '/403') location.href = '/403'
    }
    return Promise.reject(error)
  }
)

export default request
