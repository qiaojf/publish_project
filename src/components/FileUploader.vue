<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Close, Document, FolderOpened, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { FILE_ACCEPT } from '@/constants'
import { formatFileSize } from '@/utils/format'
import type { ContentFile, ContentType, UploadSelection } from '@/types/content'

const props = defineProps<{
  modelValue?: UploadSelection[]
  contentType: ContentType
  existingFiles?: ContentFile[]
}>()
const emit = defineEmits<{ 'update:modelValue': [value: UploadSelection[]] }>()
const dragging = ref(false)
const filesInput = ref<HTMLInputElement>()
const folderInput = ref<HTMLInputElement>()
const selected = computed(() => props.modelValue || [])
const shownFiles = computed<ContentFile[]>(() => selected.value.length
  ? selected.value.map((item) => ({ name: item.file.name, relative_path: item.relative_path, size: item.file.size }))
  : (props.existingFiles || []))
const showingExisting = computed(() => !selected.value.length && Boolean(props.existingFiles?.length))
const totalSize = computed(() => shownFiles.value.reduce((total, item) => total + (item.size || 0), 0))

onMounted(() => folderInput.value?.setAttribute('webkitdirectory', ''))

function isPrimaryFile(file: File) {
  const accept = FILE_ACCEPT[props.contentType]
  if (accept === '*' || (accept === 'image/*' && file.type.startsWith('image/'))) return true
  return accept.split(',').some((ext) => file.name.toLowerCase().endsWith(ext))
}

function select(fileList?: FileList | null) {
  if (!fileList?.length) return
  const files = Array.from(fileList)
  const selections = files.map((file) => ({ file, relative_path: file.webkitRelativePath || file.name }))
  const isBundle = selections.length > 1 || selections.some((item) => item.relative_path.includes('/'))
  if ((!isBundle && !isPrimaryFile(files[0])) || (isBundle && !files.some(isPrimaryFile))) {
    ElMessage.error(`请选择符合 ${FILE_ACCEPT[props.contentType]} 要求的主文件`)
    return
  }
  emit('update:modelValue', selections)
}

function onInput(event: Event) {
  select((event.target as HTMLInputElement).files)
  ;(event.target as HTMLInputElement).value = ''
}
function onDrop(event: DragEvent) { dragging.value = false; select(event.dataTransfer?.files) }
function remove(index: number) { emit('update:modelValue', selected.value.filter((_, itemIndex) => itemIndex !== index)) }
function clear() { emit('update:modelValue', []) }
</script>

<template>
  <div class="uploader">
    <div v-if="!shownFiles.length" class="dropzone" :class="{ dragging }" tabindex="0" role="button" @click="filesInput?.click()" @keydown.enter="filesInput?.click()" @dragover.prevent="dragging = true" @dragleave.prevent="dragging = false" @drop.prevent="onDrop">
      <el-icon><UploadFilled /></el-icon>
      <strong>拖拽文件到此处，或点击选择多个文件</strong>
      <span>也可使用下方“选择文件夹”保留目录结构</span>
    </div>
    <div v-else class="file-panel">
      <div class="file-summary">
        <span><el-icon><FolderOpened /></el-icon></span>
        <div><strong>{{ shownFiles.length }} 个文件</strong><small>总计 {{ formatFileSize(totalSize) }}{{ showingExisting ? ' · 已保存文件' : ' · 待上传' }}</small></div>
        <el-button v-if="!showingExisting" link type="danger" @click="clear">全部移除</el-button>
      </div>
      <ul class="file-list">
        <li v-for="(item, index) in shownFiles" :key="`${item.relative_path}-${index}`">
          <el-icon><Document /></el-icon>
          <span><strong>{{ item.relative_path }}</strong><small>{{ formatFileSize(item.size) }}</small></span>
          <button v-if="!showingExisting" type="button" aria-label="移除文件" @click="remove(index)"><el-icon><Close /></el-icon></button>
        </li>
      </ul>
      <p v-if="showingExisting" class="replace-tip">重新选择文件或文件夹会整体替换当前文件。</p>
    </div>
    <div class="picker-row">
      <el-button plain @click="filesInput?.click()">选择文件（可多选）</el-button>
      <el-button plain @click="folderInput?.click()">选择文件夹</el-button>
      <span>主文件格式：{{ FILE_ACCEPT[contentType] }}</span>
    </div>
    <input ref="filesInput" hidden type="file" multiple :accept="FILE_ACCEPT[contentType]" @change="onInput" />
    <input ref="folderInput" hidden type="file" multiple @change="onInput" />
  </div>
</template>

<style scoped>
.uploader { width: 100%; }.dropzone { height: 136px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 7px; color: #657085; border: 1px dashed #bec6d2; background: #fafbfc; cursor: pointer; transition: border .15s, background .15s; }.dropzone:hover, .dropzone.dragging, .dropzone:focus { border-color: var(--blue); background: #f5f8fb; outline: none; }.dropzone .el-icon { color: var(--blue); font-size: 28px; }.dropzone strong { color: #414c60; font-size: 13px; }.dropzone span { font-size: 12px; }.file-panel { border: 1px solid var(--line); background: #fbfcfd; }.file-summary { min-height: 58px; display: flex; align-items: center; gap: 11px; padding: 8px 13px; border-bottom: 1px solid var(--line); }.file-summary > span { width: 34px; height: 34px; display: grid; place-items: center; color: var(--blue); background: #eaf0f7; }.file-summary > div { display: flex; flex-direction: column; gap: 3px; }.file-summary small, .file-list small { color: #7b8597; font-size: 11px; }.file-summary .el-button { margin-left: auto; }.file-list { max-height: 220px; margin: 0; padding: 4px 0; overflow: auto; list-style: none; }.file-list li { display: grid; grid-template-columns: 18px 1fr 26px; gap: 9px; align-items: center; min-height: 42px; padding: 5px 13px; border-bottom: 1px solid #edf0f3; }.file-list li:last-child { border-bottom: 0; }.file-list li > span { display: flex; min-width: 0; flex-direction: column; gap: 2px; }.file-list strong { overflow: hidden; font-size: 12px; font-weight: 550; text-overflow: ellipsis; white-space: nowrap; }.file-list button { border: 0; background: transparent; color: #8a93a3; cursor: pointer; }.replace-tip { margin: 0; padding: 8px 13px; color: #7b8597; border-top: 1px solid var(--line); font-size: 11px; }.picker-row { display: flex; align-items: center; gap: 8px; margin-top: 9px; }.picker-row > span { margin-left: 4px; color: #8992a2; font-size: 11px; }
</style>
