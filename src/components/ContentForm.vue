<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance, FormRules } from 'element-plus'
import FileUploader from './FileUploader.vue'
import { CONTENT_TYPES } from '@/constants'
import type { ContentItem, ContentPayload, ContentType } from '@/types/content'
import type { PublishTarget } from '@/types/publish'

const props = defineProps<{ initial?: ContentItem; targets: PublishTarget[]; categories: string[] }>()
const { t } = useI18n()
const model = reactive<ContentPayload>({ title: '', description: '', category: '', content_type: 'ppt', publish_target_id: undefined, content_body: '', files: [] })
const formEl = ref<FormInstance>()
const filteredTargets = computed(() => props.targets.filter((item) => item.enabled && item.content_types.includes(model.content_type)))
const needsTextBody = computed(() => ['html', 'dynamic'].includes(model.content_type))
const existingFiles = computed(() => props.initial?.files?.length
  ? props.initial.files
  : props.initial?.file_name ? [{ name: props.initial.file_name, relative_path: props.initial.file_name, size: props.initial.file_size }] : [])
const rules = computed<FormRules<ContentPayload>>(() => ({
  title: [{ required: true, message: t('validation.contentTitleRequired'), trigger: 'blur' }],
  category: [{ required: true, message: t('validation.categoryRequired'), trigger: 'change' }],
  content_type: [{ required: true, message: t('validation.contentTypeRequired'), trigger: 'change' }],
  publish_target_id: [{ required: true, message: t('validation.publishTargetRequired'), trigger: 'change' }]
}))

watch(() => props.initial, (value) => {
  if (!value) return
  Object.assign(model, { title: value.title, description: value.description || '', category: value.category || '', content_type: value.content_type, publish_target_id: value.publish_target_id || undefined, content_body: value.content_body === 'null' ? '' : value.content_body || '', file_name: value.file_name || undefined, file_size: value.file_size || undefined, files: [] })
}, { immediate: true })
watch(() => model.content_type, () => { model.files = []; if (!filteredTargets.value.some((item) => item.id === model.publish_target_id)) model.publish_target_id = undefined })

defineExpose({ model, validate: () => formEl.value?.validate() })
</script>
<template>
  <el-form ref="formEl" :model="model" :rules="rules" label-position="top" class="content-form">
    <div class="form-grid">
      <el-form-item :label="t('content.title')" prop="title"><el-input v-model="model.title" maxlength="80" show-word-limit :placeholder="t('content.titlePlaceholder')" /></el-form-item>
      <el-form-item :label="t('content.category')" prop="category"><el-select v-model="model.category" :placeholder="t('content.selectCategory')"><el-option v-for="item in categories" :key="item" :label="item" :value="item" /></el-select></el-form-item>
    </div>
    <el-form-item :label="t('content.description')"><el-input v-model="model.description" type="textarea" :rows="3" maxlength="300" show-word-limit :placeholder="t('content.descriptionPlaceholder')" /></el-form-item>
    <div class="form-grid">
      <el-form-item :label="t('content.contentType')" prop="content_type"><el-select v-model="model.content_type"><el-option v-for="(label, value) in CONTENT_TYPES" :key="value" :label="t(label)" :value="value as ContentType" /></el-select></el-form-item>
      <el-form-item :label="t('content.publishTarget')" prop="publish_target_id"><el-select v-model="model.publish_target_id" :placeholder="t('content.selectPublishTarget')"><el-option v-for="target in filteredTargets" :key="target.id" :label="target.name" :value="target.id" /></el-select><span class="field-help">{{ t('content.publishTargetHint') }}</span></el-form-item>
    </div>
    <el-form-item v-if="needsTextBody" :label="t('content.pageContent')"><el-input v-model="model.content_body" type="textarea" :rows="8" :placeholder="t('content.pageContentPlaceholder')" /></el-form-item>
    <el-form-item :label="t(needsTextBody ? 'content.filesOptional' : 'content.files')" :required="!needsTextBody"><FileUploader v-model="model.files" :content-type="model.content_type" :existing-files="existingFiles" /></el-form-item>
  </el-form>
</template>
<style scoped>
.content-form { max-width: 920px; }.form-grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 22px; }.el-select { width: 100%; }.field-help { display: block; margin-top: 5px; color: #8992a2; font-size: 11px; }
</style>
