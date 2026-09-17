<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { getAppLocale, setAppLocale, type AppLocale } from '@/i18n'

defineProps<{ compact?: boolean }>()

const { t } = useI18n()
const locale = computed({
  get: getAppLocale,
  set: (value: AppLocale) => setAppLocale(value)
})
const options: Array<{ value: AppLocale; label: string }> = [
  { value: 'zh-CN', label: '简体中文' },
  { value: 'ja-JP', label: '日本語' },
  { value: 'en-US', label: 'English' }
]
</script>

<template>
  <el-select v-model="locale" class="language-switcher" :class="{ compact }" :aria-label="t('language.label')" :placeholder="t('language.label')">
    <el-option v-for="option in options" :key="option.value" :label="option.label" :value="option.value" />
  </el-select>
</template>

<style scoped>
.language-switcher { width: 122px; }.language-switcher.compact { width: 110px; }
</style>

