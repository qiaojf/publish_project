import { getAppLocale } from '@/i18n'

export function formatDate(value?: string | null): string {
  if (!value) return '—'
  return new Intl.DateTimeFormat(getAppLocale(), {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false
  }).format(new Date(value))
}

export function formatFileSize(bytes?: number | null): string {
  if (!bytes) return '0 B'
  const formatter = new Intl.NumberFormat(getAppLocale(), { maximumFractionDigits: 1 })
  if (bytes < 1024) return `${formatter.format(bytes)} B`
  if (bytes < 1024 * 1024) return `${formatter.format(bytes / 1024)} KB`
  return `${formatter.format(bytes / 1024 / 1024)} MB`
}
