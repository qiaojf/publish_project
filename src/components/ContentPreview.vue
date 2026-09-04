<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Document } from '@element-plus/icons-vue'
import { getContentPreviewFile, getContentPreviewSourceFile } from '@/api/contents'
import { formatFileSize } from '@/utils/format'
import type { PreviewData } from '@/types/content'

const props = defineProps<{ contentId?: number; preview?: PreviewData; loading?: boolean }>()
const objectUrl = ref('')
const sourceLoading = ref(false)
const sourceError = ref(false)
let requestVersion = 0

const displayUrl = computed(() => objectUrl.value || (
  props.preview && 'preview_url' in props.preview ? props.preview.preview_url || '' : ''
))

function revokeObjectUrl() {
  if (objectUrl.value) URL.revokeObjectURL(objectUrl.value)
  objectUrl.value = ''
}

async function loadProtectedSource() {
  const version = ++requestVersion
  revokeObjectUrl()
  sourceError.value = false
  sourceLoading.value = false
  const preview = props.preview
  if (!preview || !['image', 'pdf'].includes(preview.preview_type) || !props.contentId || !('preview_url' in preview) || !(preview.preview_url || '').startsWith('/')) return
  sourceLoading.value = true
  try {
    const blob = await getContentPreviewFile(props.contentId)
    const url = URL.createObjectURL(blob)
    if (version === requestVersion) objectUrl.value = url
    else URL.revokeObjectURL(url)
  } catch {
    if (version === requestVersion) sourceError.value = true
  } finally {
    if (version === requestVersion) sourceLoading.value = false
  }
}

async function downloadSource() {
  if (!props.contentId || props.preview?.preview_type !== 'file') return
  const blob = await getContentPreviewFile(props.contentId)
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = props.preview.file_name
  anchor.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 0)
}

async function downloadListedFile(relativePath: string, fileName: string) {
  if (!props.contentId) return
  const blob = await getContentPreviewSourceFile(props.contentId, relativePath)
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = fileName
  anchor.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 0)
}

watch(() => [props.preview, props.contentId], loadProtectedSource, { immediate: true })
onBeforeUnmount(() => { requestVersion += 1; revokeObjectUrl() })
</script>
<template>
  <div v-loading="loading || sourceLoading" class="preview-stage">
    <template v-if="preview?.preview_type === 'url'"><iframe :src="preview.preview_url" title="内容预览" /></template>
    <template v-else-if="preview?.preview_type === 'image' && displayUrl"><img :src="displayUrl" alt="内容预览" /></template>
    <template v-else-if="preview?.preview_type === 'pdf' && displayUrl"><iframe :src="displayUrl" title="PDF 文档预览" /></template>
    <template v-else-if="preview?.preview_type === 'text'"><iframe :srcdoc="preview.content" sandbox="allow-same-origin" title="内容预览" /></template>
    <div v-else-if="sourceError" class="file-preview"><el-icon><Document /></el-icon><strong>预览文件读取失败</strong><p>请稍后重试，或检查源文件是否仍然存在。</p></div>
    <div v-else-if="preview?.preview_type === 'files'" class="multi-file-preview">
      <div class="multi-file-head"><el-icon><Document /></el-icon><div><strong>{{ preview.files.length }} 个文件</strong><span>多个文件或文件夹不显示内容预览</span></div></div>
      <ul><li v-for="item in preview.files" :key="item.relative_path"><span><strong>{{ item.relative_path }}</strong><small>{{ formatFileSize(item.size) }}</small></span><el-button v-if="item.download_url" link type="primary" @click="downloadListedFile(item.relative_path, item.name)">下载</el-button></li></ul>
    </div>
    <div v-else-if="preview?.preview_type === 'file'" class="file-preview"><el-icon><Document /></el-icon><strong>{{ preview.file_name }}</strong><span>{{ formatFileSize(preview.file_size) }}</span><p>该文件格式无法在浏览器内还原，下载原始文件可查看完整内容。</p><el-button v-if="preview.preview_url" type="primary" plain @click="downloadSource">下载原始文件</el-button></div>
    <el-empty v-else description="当前文件暂不支持在线预览" :image-size="78" />
  </div>
</template>
<style scoped>
.preview-stage { min-height: 300px; display: grid; place-items: center; background: #f5f6f8; border: 1px solid var(--line); }
iframe { width: 100%; height: 560px; border: 0; background: white; }img { max-width: 100%; max-height: 560px; object-fit: contain; }
.file-preview { display: flex; flex-direction: column; align-items: center; gap: 8px; color: #647086; }.file-preview .el-icon { font-size: 48px; color: var(--blue); }.file-preview strong { color: var(--ink); }.file-preview span { font-size: 12px; }.file-preview p { margin: 8px 0 0; color: #8790a0; font-size: 12px; }
.multi-file-preview { width: min(720px, calc(100% - 36px)); margin: 18px; align-self: stretch; }.multi-file-head { display: flex; align-items: center; gap: 11px; padding: 13px 15px; color: var(--blue); border: 1px solid var(--line); background: #fff; }.multi-file-head > .el-icon { font-size: 28px; }.multi-file-head > div { display: flex; flex-direction: column; gap: 3px; }.multi-file-head strong { color: var(--ink); font-size: 14px; }.multi-file-head span { color: #8790a0; font-size: 11px; }.multi-file-preview ul { max-height: 420px; margin: 0; padding: 0; overflow: auto; border: 1px solid var(--line); border-top: 0; background: #fff; list-style: none; }.multi-file-preview li { min-height: 48px; display: flex; align-items: center; gap: 12px; padding: 7px 14px; border-bottom: 1px solid #edf0f3; }.multi-file-preview li:last-child { border-bottom: 0; }.multi-file-preview li > span { min-width: 0; display: flex; flex: 1; flex-direction: column; gap: 3px; }.multi-file-preview li strong { overflow: hidden; color: #334155; font-size: 12px; font-weight: 550; text-overflow: ellipsis; white-space: nowrap; }.multi-file-preview li small { color: #8a93a2; font-size: 10px; }
</style>
