import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import jaJP from './ja-JP'
import enUS from './en-US'
import { isAppLocale } from './types'
import type { AppLocale } from './types'

export { isAppLocale, SUPPORTED_LOCALES } from './types'
export type { AppLocale } from './types'

export const APP_LOCALE_STORAGE_KEY = 'app_locale'

export function resolveStoredLocale(): AppLocale {
  const stored = localStorage.getItem(APP_LOCALE_STORAGE_KEY)
  return isAppLocale(stored) ? stored : 'zh-CN'
}

export const i18n = createI18n({
  legacy: false,
  locale: resolveStoredLocale(),
  fallbackLocale: 'zh-CN',
  flatJson: true,
  missingWarn: false,
  fallbackWarn: false,
  messages: {
    'zh-CN': zhCN,
    'ja-JP': jaJP,
    'en-US': enUS
  }
})

export function getAppLocale(): AppLocale {
  const current = i18n.global.locale.value
  return isAppLocale(current) ? current : 'zh-CN'
}

export function setAppLocale(locale: AppLocale): void {
  i18n.global.locale.value = locale
  localStorage.setItem(APP_LOCALE_STORAGE_KEY, locale)
  document.documentElement.lang = locale
}

document.documentElement.lang = getAppLocale()
