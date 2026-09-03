<script setup lang="ts">
import { useRouter } from 'vue-router'
import { DocumentDelete } from '@element-plus/icons-vue'
const router = useRouter()
</script>
<template><div class="error-page"><div class="error-mark"><el-icon><DocumentDelete /></el-icon></div><span class="error-code">404 / NOT FOUND</span><h1>页面没有找到</h1><p>地址可能已变更，或你访问的内容记录已经不存在。</p><el-button type="primary" @click="router.push('/')">返回工作台</el-button></div></template>
<style scoped>.error-page { min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #f2f4f7; text-align: center; }.error-mark { width: 64px; height: 64px; display: grid; place-items: center; margin-bottom: 20px; color: #fff; background: var(--ink); font-size: 28px; }.error-code { color: #a37834; font: 11px Bahnschrift, sans-serif; letter-spacing: .16em; }.error-page h1 { margin: 13px 0 9px; font-size: 26px; }.error-page p { max-width: 450px; margin: 0 0 24px; color: #748094; font-size: 13px; line-height: 1.8; }</style>
