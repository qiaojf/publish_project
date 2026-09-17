<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Connection, Plus } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import { createPublishTarget, deletePublishTarget, getPublishTargets, testPublishTarget, updatePublishTarget, updatePublishTargetStatus } from '@/api/publishTargets'
import { getRequestErrorMessage } from '@/api/request'
import { CONTENT_TYPES, PUBLISH_TARGET_TYPES } from '@/constants'
import type { ContentType } from '@/types/content'
import type { PublishTarget, PublishTargetPayload, PublishTargetType } from '@/types/publish'

interface ConfigField { key: string; labelKey: string; placeholderKey: string; hintKey?: string }

const CONFIG_FIELDS: Record<PublishTargetType, ConfigField[]> = {
  local: [],
  sftp: [
    { key: 'host', labelKey: 'publishTarget.field.host', placeholderKey: 'publishTarget.placeholder.host' },
    { key: 'port', labelKey: 'publishTarget.field.port', placeholderKey: 'publishTarget.placeholder.port' },
    { key: 'username', labelKey: 'publishTarget.field.username', placeholderKey: 'publishTarget.placeholder.username' },
    { key: 'remote_root', labelKey: 'publishTarget.field.remoteRoot', placeholderKey: 'publishTarget.placeholder.remoteRoot' },
    { key: 'base_url', labelKey: 'publishTarget.field.baseUrl', placeholderKey: 'publishTarget.placeholder.sftpBaseUrl' }
  ],
  github: [
    { key: 'owner', labelKey: 'publishTarget.field.owner', placeholderKey: 'publishTarget.placeholder.owner' },
    { key: 'repo', labelKey: 'publishTarget.field.repository', placeholderKey: 'publishTarget.placeholder.repository' },
    { key: 'branch', labelKey: 'publishTarget.field.branch', placeholderKey: 'publishTarget.placeholder.branch' },
    { key: 'repo_path', labelKey: 'publishTarget.field.repoPath', placeholderKey: 'publishTarget.placeholder.repoPath' }
  ],
  github_pages: [
    { key: 'owner', labelKey: 'publishTarget.field.owner', placeholderKey: 'publishTarget.placeholder.owner' },
    { key: 'repo', labelKey: 'publishTarget.field.repository', placeholderKey: 'publishTarget.placeholder.pagesRepository' },
    { key: 'branch', labelKey: 'publishTarget.field.pagesBranch', placeholderKey: 'publishTarget.placeholder.pagesBranch' },
    { key: 'repo_path', labelKey: 'publishTarget.field.repoPath', placeholderKey: 'publishTarget.placeholder.pagesRepoPath' },
    { key: 'base_url', labelKey: 'publishTarget.field.pagesBaseUrl', placeholderKey: 'publishTarget.placeholder.pagesBaseUrl' }
  ],
  onedrive: [
    { key: 'tenant_id', labelKey: 'publishTarget.field.tenantId', placeholderKey: 'publishTarget.placeholder.tenantId' },
    { key: 'client_id', labelKey: 'publishTarget.field.clientId', placeholderKey: 'publishTarget.placeholder.clientId' },
    { key: 'drive_id', labelKey: 'publishTarget.field.driveId', placeholderKey: 'publishTarget.placeholder.driveId' },
    { key: 'folder_path', labelKey: 'publishTarget.field.folderPath', placeholderKey: 'publishTarget.placeholder.folderPath' }
  ],
  dropbox: [{ key: 'folder_path', labelKey: 'publishTarget.field.folderPath', placeholderKey: 'publishTarget.placeholder.folderPath' }],
  instagram: [
    { key: 'ig_user_id', labelKey: 'publishTarget.field.instagramUserId', placeholderKey: 'publishTarget.placeholder.instagramUserId' },
    { key: 'api_version', labelKey: 'publishTarget.field.apiVersion', placeholderKey: 'publishTarget.placeholder.apiVersion' },
    { key: 'media_base_url', labelKey: 'publishTarget.field.mediaBaseUrl', placeholderKey: 'publishTarget.placeholder.mediaBaseUrl', hintKey: 'publishTarget.mediaBaseUrlHint' }
  ]
}
const ALL_CONTENT_TYPES = Object.keys(CONTENT_TYPES) as ContentType[]
const TARGET_CONTENT_TYPES: Record<PublishTargetType, ContentType[]> = {
  local: ALL_CONTENT_TYPES,
  sftp: ALL_CONTENT_TYPES,
  github: ALL_CONTENT_TYPES,
  github_pages: ALL_CONTENT_TYPES.filter((item) => item !== 'dynamic'),
  onedrive: ALL_CONTENT_TYPES,
  dropbox: ALL_CONTENT_TYPES,
  instagram: ['video']
}
const TARGET_TYPE_HINTS: Record<PublishTargetType, string> = {
  local: 'publishTarget.hint.local',
  sftp: 'publishTarget.hint.sftp',
  github: 'publishTarget.hint.github',
  github_pages: 'publishTarget.hint.githubPages',
  onedrive: 'publishTarget.hint.onedrive',
  dropbox: 'publishTarget.hint.dropbox',
  instagram: 'publishTarget.hint.instagram'
}

const loading = ref(false)
const { t } = useI18n()
const saving = ref(false)
const testingId = ref<number>()
const statusChangingId = ref<number>()
const targets = ref<PublishTarget[]>([])
const dialogVisible = ref(false)
const editingId = ref<number>()
const formRef = ref<FormInstance>()
const form = reactive<PublishTargetPayload>(emptyForm())
const contentTypeLabel = (value: ContentType) => t(CONTENT_TYPES[value])
const targetTypeLabel = (value: PublishTargetType) => t(PUBLISH_TARGET_TYPES[value])
const availableContentTypes = computed(() => TARGET_CONTENT_TYPES[form.target_type])
const rules = computed<FormRules>(() => ({
  name: [{ required: true, message: t('validation.publishTargetNameRequired'), trigger: 'blur' }],
  target_type: [{ required: true, message: t('validation.targetTypeRequired'), trigger: 'change' }],
  content_types: [{ type: 'array', required: true, min: 1, message: t('validation.oneContentTypeRequired'), trigger: 'change' }]
}))

function emptyForm(): PublishTargetPayload {
  return { name: '', target_type: 'local', content_types: [...ALL_CONTENT_TYPES], publish_root: '', base_url: '', config: {}, credential_ref: '', enabled: true }
}
async function load() { loading.value = true; try { targets.value = await getPublishTargets() } catch (e) { ElMessage.error(getRequestErrorMessage(e, 'publishTarget.loadFailed')) } finally { loading.value = false } }
function resetForType(type: PublishTargetType) {
  form.target_type = type
  const allowed = TARGET_CONTENT_TYPES[type]
  const retained = form.content_types.filter((item) => allowed.includes(item))
  form.content_types = retained.length ? retained : [...allowed]
  form.config = type === 'sftp' ? { port: 22 } : type === 'instagram' ? { api_version: 'v23.0' } : {}
  form.publish_root = ''
  form.base_url = ''
  form.credential_ref = ''
}
function openCreate() { editingId.value = undefined; Object.assign(form, emptyForm()); dialogVisible.value = true }
function openEdit(item: PublishTarget) {
  editingId.value = item.id
  Object.assign(form, {
    name: item.name,
    target_type: item.target_type,
    content_types: [...item.content_types],
    publish_root: item.publish_root || '',
    base_url: item.base_url || '',
    config: { ...(item.config || {}) },
    credential_ref: item.credential_ref || '',
    enabled: item.enabled
  })
  dialogVisible.value = true
}
function validateDynamic() {
  if (form.target_type === 'local') {
    if (!form.publish_root || !form.base_url) { ElMessage.warning(t('validation.localTargetPathsRequired')); return false }
    return true
  }
  const missing = CONFIG_FIELDS[form.target_type].find((field) => form.config[field.key] === undefined || form.config[field.key] === '')
  if (missing) { ElMessage.warning(t('validation.fieldRequired', { field: t(missing.labelKey) })); return false }
  if (!form.credential_ref) { ElMessage.warning(t('validation.credentialRefRequired')); return false }
  return true
}
async function save() {
  if (!await formRef.value?.validate().catch(() => false) || !validateDynamic()) return
  saving.value = true
  try {
    if (editingId.value) await updatePublishTarget(editingId.value, form)
    else await createPublishTarget(form)
    ElMessage.success(t(editingId.value ? 'publishTarget.updated' : 'publishTarget.created'))
    dialogVisible.value = false
    await load()
  } catch (e) { ElMessage.error(errorMessage(e, 'common.saveFailed')) } finally { saving.value = false }
}
async function testConnection(item: PublishTarget) {
  testingId.value = item.id
  try { await testPublishTarget(item.id); ElMessage.success(t('publishTarget.connectionSucceeded', { name: item.name })) } catch (e) { ElMessage.error(errorMessage(e, 'publishTarget.connectionFailed')) } finally { testingId.value = undefined }
}
function errorMessage(error: unknown, fallbackKey: string) { return getRequestErrorMessage(error, fallbackKey) }
async function toggle(item: PublishTarget, value: string | number | boolean) {
  const next = Boolean(value)
  statusChangingId.value = item.id
  try {
    if (!next) await ElMessageBox.confirm(t('publishTarget.disableConfirm', { name: item.name }), t('publishTarget.disableTitle'), { type: 'warning', confirmButtonText: t('common.disable'), cancelButtonText: t('common.cancel') })
    await updatePublishTargetStatus(item.id, next); ElMessage.success(t(next ? 'publishTarget.enabled' : 'publishTarget.disabled')); await load()
  } catch (e) { if (e instanceof Error) ElMessage.error(errorMessage(e, 'common.statusUpdateFailed')) }
  finally { statusChangingId.value = undefined }
}
async function remove(item: PublishTarget) {
  try {
    await ElMessageBox.confirm(t('publishTarget.deleteConfirm', { name: item.name }), t('publishTarget.deleteTitle'), { type: 'warning', confirmButtonText: t('common.delete'), cancelButtonText: t('common.cancel') })
    await deletePublishTarget(item.id); ElMessage.success(t('publishTarget.deleted')); await load()
  } catch (e) { if (e instanceof Error) ElMessage.error(errorMessage(e, 'common.deleteFailed')) }
}
function locationText(item: PublishTarget) {
  if (item.target_type === 'local') return item.publish_root || '—'
  if (item.target_type === 'sftp') return `${item.config?.host || '—'}:${item.config?.port || 22}${item.config?.remote_root || ''}`
  if (item.target_type === 'github' || item.target_type === 'github_pages') return `${item.config?.owner || '—'}/${item.config?.repo || '—'} @ ${item.config?.branch || '—'}`
  if (item.target_type === 'onedrive') return `Drive ${item.config?.drive_id || '—'} · ${item.config?.folder_path || ''}`
  if (item.target_type === 'instagram') return `Instagram ${item.config?.ig_user_id || '—'} · ${item.config?.media_base_url || ''}`
  return String(item.config?.folder_path || '—')
}
function accessUrl(item: PublishTarget) { return item.target_type === 'instagram' ? 'https://www.instagram.com/' : String(item.base_url || item.config?.base_url || '') }
onMounted(load)
</script>

<template>
  <div class="page-shell">
    <PageHeader :title="t('nav.publishTargets')" :description="t('publishTarget.description')" :eyebrow="t('kicker.destinationAdapters')"><template #actions><el-button type="primary" :icon="Plus" @click="openCreate">{{ t('publishTarget.create') }}</el-button></template></PageHeader>
    <el-alert :title="t('publishTarget.alertTitle')" :description="t('publishTarget.alertDescription')" type="warning" :closable="false" show-icon />
    <section class="paper-card table-panel">
      <div class="table-toolbar"><span class="table-count">{{ t('publishTarget.totalCount', { count: targets.length }) }}</span><span class="muted">{{ t('publishTarget.adapterHint') }}</span></div>
      <el-table v-loading="loading" :data="targets">
        <el-table-column prop="name" :label="t('publishTarget.name')" min-width="155"><template #default="scope"><strong>{{ scope.row.name }}</strong></template></el-table-column>
        <el-table-column :label="t('publishTarget.targetType')" width="190"><template #default="scope"><span class="target-type">{{ targetTypeLabel(scope.row.target_type) }}</span></template></el-table-column>
        <el-table-column :label="t('publishTarget.supportedTypes')" min-width="220"><template #default="scope"><el-tag v-for="type in scope.row.content_types" :key="type" type="info" effect="plain" class="type-tag">{{ contentTypeLabel(type) }}</el-tag></template></el-table-column>
        <el-table-column :label="t('publishTarget.location')" min-width="230"><template #default="scope"><span class="mono path-text">{{ locationText(scope.row) }}</span><a v-if="accessUrl(scope.row)" class="mono url-text" :href="accessUrl(scope.row)" target="_blank" rel="noopener noreferrer">{{ accessUrl(scope.row) }}</a></template></el-table-column>
        <el-table-column :label="t('common.status')" width="90"><template #default="scope"><el-switch :model-value="scope.row.enabled" :loading="statusChangingId === scope.row.id" inline-prompt :active-text="t('common.onShort')" :inactive-text="t('common.offShort')" @change="toggle(scope.row, $event)" /></template></el-table-column>
        <el-table-column :label="t('common.actions')" width="220" fixed="right"><template #default="scope"><el-button link type="success" :icon="Connection" :loading="testingId === scope.row.id" @click="testConnection(scope.row)">{{ t('publishTarget.testConnection') }}</el-button><el-button link type="primary" @click="openEdit(scope.row)">{{ t('common.edit') }}</el-button><el-button link type="danger" @click="remove(scope.row)">{{ t('common.delete') }}</el-button></template></el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" :title="t(editingId ? 'publishTarget.edit' : 'publishTarget.create')" width="680px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="form-grid"><el-form-item :label="t('publishTarget.name')" prop="name"><el-input v-model="form.name" :placeholder="t('publishTarget.namePlaceholder')" /></el-form-item><el-form-item :label="t('publishTarget.targetType')" prop="target_type"><el-select v-model="form.target_type" style="width:100%" @change="resetForType"><el-option v-for="(label, value) in PUBLISH_TARGET_TYPES" :key="value" :label="t(label)" :value="value" /></el-select></el-form-item></div>
        <el-form-item :label="t('publishTarget.supportedTypesMultiple')" prop="content_types"><el-select v-model="form.content_types" multiple collapse-tags :max-collapse-tags="4" :placeholder="t('publishTarget.selectTypes')" style="width:100%"><el-option v-for="type in availableContentTypes" :key="type" :label="t(CONTENT_TYPES[type])" :value="type" /></el-select><span class="form-hint">{{ t(TARGET_TYPE_HINTS[form.target_type]) }}</span></el-form-item>
        <template v-if="form.target_type === 'local'">
          <el-form-item :label="t('publishTarget.publishRoot')"><el-input v-model="form.publish_root" class="mono-input" :placeholder="t('publishTarget.publishRootPlaceholder')" /><span class="form-hint">{{ t('publishTarget.publishRootHint') }}</span></el-form-item>
          <el-form-item :label="t('publishTarget.baseUrl')"><el-input v-model="form.base_url" class="mono-input" :placeholder="t('publishTarget.baseUrlPlaceholder')" /><span class="form-hint">{{ t('publishTarget.baseUrlHint') }}</span></el-form-item>
        </template>
        <template v-else>
          <div class="adapter-strip"><span>{{ t(PUBLISH_TARGET_TYPES[form.target_type]) }}</span><strong>{{ t('publishTarget.nonSensitiveConfig') }}</strong></div>
          <el-alert v-if="form.target_type === 'instagram'" class="instagram-alert" :title="t('publishTarget.instagramAlertTitle')" :description="t('publishTarget.instagramAlertDescription')" type="info" :closable="false" show-icon />
          <div class="config-grid"><el-form-item v-for="field in CONFIG_FIELDS[form.target_type]" :key="field.key" :label="t(field.labelKey)"><el-input v-model="form.config[field.key]" class="mono-input" :placeholder="t(field.placeholderKey)" /><span v-if="field.hintKey" class="form-hint">{{ t(field.hintKey) }}</span></el-form-item></div>
          <el-form-item :label="t('publishTarget.credentialRef')"><el-input v-model="form.credential_ref" class="mono-input" :placeholder="t('publishTarget.credentialPlaceholder')" /><span class="form-hint">{{ t('publishTarget.credentialHint') }}</span></el-form-item>
        </template>
        <el-form-item :label="t('publishTarget.enabledQuestion')"><el-switch v-model="form.enabled" :active-text="t('common.enable')" :inactive-text="t('common.disable')" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button><el-button type="primary" :loading="saving" @click="save">{{ t('publishTarget.saveConfig') }}</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.type-tag { margin: 2px 4px 2px 0; }.target-type { display: inline-flex; padding: 4px 8px; color: #234f84; border-left: 3px solid var(--blue); background: #edf4fb; font-size: 11px; font-weight: 650; }.path-text, .url-text { display: block; overflow-wrap: anywhere; font-size: 10px; }.url-text { margin-top: 4px; color: var(--blue); }.muted { font-size: 11px; }.form-grid, .config-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; }.mono-input :deep(input) { font-family: "Cascadia Mono", monospace; font-size: 11px; }.form-hint { margin-top: 5px; color: #8a93a2; font-size: 11px; }.adapter-strip { display: flex; align-items: center; gap: 10px; margin: 2px 0 16px; padding: 10px 12px; color: #5f6c80; border-left: 3px solid var(--blue); background: #f4f7fa; font-size: 11px; }.adapter-strip span { color: var(--blue); font-weight: 700; }.adapter-strip strong { color: #344054; font-size: 12px; }.instagram-alert { margin: -4px 0 16px; }
</style>
