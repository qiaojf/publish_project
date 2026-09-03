<script setup lang="ts">
import { computed, ref } from 'vue'
import { Document, UploadFilled, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { FILE_ACCEPT } from '@/constants'
import { formatFileSize } from '@/utils/format'
import type { ContentType } from '@/types/content'

const props = defineProps<{ modelValue?: File; contentType: ContentType; existingName?: string; existingSize?: number }>()
const emit = defineEmits<{ 'update:modelValue': [value: File | undefined] }>()
const dragging = ref(false)
const input = ref<HTMLInputElement>()
const displayName = computed(() => props.modelValue?.name || props.existingName)
const displaySize = computed(() => props.modelValue?.size || props.existingSize)

function validFile(file: File) {
  const accept = FILE_ACCEPT[props.contentType]
  if (accept === '*' || accept === 'image/*' && file.type.startsWith('image/')) return true
  return accept.split(',').some((ext) => file.name.toLowerCase().endsWith(ext))
}
function select(file?: File) {
  if (!file) return
  if (!validFile(file)) { ElMessage.error(`文件格式不符合 ${FILE_ACCEPT[props.contentType]} 要求`); return }
  emit('update:modelValue', file)
}
function onInput(event: Event) { select((event.target as HTMLInputElement).files?.[0]) }
function onDrop(event: DragEvent) { dragging.value = false; select(event.dataTransfer?.files[0]) }
function remove() { emit('update:modelValue', undefined); if (input.value) input.value.value = '' }
</script>
<template>
  <div>
    <div v-if="!displayName" class="dropzone" :class="{ dragging }" tabindex="0" role="button" @click="input?.click()" @keydown.enter="input?.click()" @dragover.prevent="dragging = true" @dragleave.prevent="dragging = false" @drop.prevent="onDrop">
      <el-icon><UploadFilled /></el-icon><strong>拖拽文件到此处，或点击选择</strong><span>支持格式：{{ FILE_ACCEPT[contentType] }}</span>
    </div>
    <div v-else class="file-chip"><span class="file-icon"><el-icon><Document /></el-icon></span><div><strong>{{ displayName }}</strong><span>{{ formatFileSize(displaySize) }}</span></div><button type="button" aria-label="移除文件" @click="remove"><el-icon><Close /></el-icon></button></div>
    <input ref="input" hidden type="file" :accept="FILE_ACCEPT[contentType]" @change="onInput" />
  </div>
</template>
<style scoped>
.dropzone { height: 136px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 7px; color: #657085; border: 1px dashed #bec6d2; background: #fafbfc; cursor: pointer; transition: border .15s, background .15s; }
.dropzone:hover, .dropzone.dragging, .dropzone:focus { border-color: var(--blue); background: #f5f8fb; outline: none; }.dropzone .el-icon { color: var(--blue); font-size: 28px; }.dropzone strong { color: #414c60; font-size: 13px; }.dropzone span { font-size: 12px; }
.file-chip { height: 66px; display: flex; align-items: center; gap: 12px; padding: 10px 14px; border: 1px solid var(--line); background: #fbfcfd; }
.file-icon { width: 38px; height: 38px; display: grid; place-items: center; color: var(--blue); background: #eaf0f7; }.file-chip div { display: flex; flex-direction: column; gap: 4px; }.file-chip strong { font-size: 13px; }.file-chip div span { color: #7b8597; font-size: 12px; }.file-chip button { margin-left: auto; border: 0; background: transparent; color: #8a93a3; cursor: pointer; }
</style>
