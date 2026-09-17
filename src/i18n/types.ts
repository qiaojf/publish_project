export const SUPPORTED_LOCALES = ['zh-CN', 'ja-JP', 'en-US'] as const
export type AppLocale = typeof SUPPORTED_LOCALES[number]

export function isAppLocale(value: unknown): value is AppLocale {
  return typeof value === 'string' && SUPPORTED_LOCALES.includes(value as AppLocale)
}
