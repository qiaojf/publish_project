<script setup lang="ts">
import { computed, watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import ja from 'element-plus/es/locale/lang/ja'
import en from 'element-plus/es/locale/lang/en'

const route = useRoute()
const { t, locale } = useI18n()
const elementLocale = computed(() => {
  if (locale.value === 'ja-JP') return ja
  if (locale.value === 'en-US') return en
  return zhCn
})

watchEffect(() => {
  void locale.value
  const titleKey = typeof route.meta.i18nKey === 'string' ? route.meta.i18nKey : 'app.name'
  document.title = `${t(titleKey)} · ${t('app.shortName')}`
})
</script>

<template>
  <el-config-provider :locale="elementLocale">
    <router-view />
  </el-config-provider>
</template>
