<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { isAxiosError } from 'axios'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Connection, Plus } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import { createPublishTarget, deletePublishTarget, getPublishTargets, testPublishTarget, updatePublishTarget, updatePublishTargetStatus } from '@/api/publishTargets'
import { CONTENT_TYPES } from '@/constants'
import type { ContentType } from '@/types/content'
import type { PublishTarget, PublishTargetPayload, PublishTargetType } from '@/types/publish'

interface ConfigField { key: string; label: string; placeholder: string; hint?: string }

const TARGET_TYPES: Record<PublishTargetType, string> = {
  local: '公司服务器目录（Local）',
  sftp: '公司远程服务器（SFTP）',
  github: 'GitHub Repository',
  github_pages: 'GitHub Pages',
  onedrive: 'Microsoft OneDrive',
  dropbox: 'Dropbox'
}
const CONFIG_FIELDS: Record<PublishTargetType, ConfigField[]> = {
  local: [],
  sftp: [
    { key: 'host', label: '服务器地址', placeholder: '192.168.1.100' },
    { key: 'port', label: '端口', placeholder: '22' },
    { key: 'username', label: '用户名', placeholder: 'publisher' },
    { key: 'remote_root', label: '远程根目录', placeholder: '/var/www/company-content/' },
    { key: 'base_url', label: '访问 URL 根地址', placeholder: 'https://internal.company/content/' }
  ],
  github: [
    { key: 'owner', label: 'Owner', placeholder: 'company' },
    { key: 'repo', label: 'Repository', placeholder: 'internal-content' },
    { key: 'branch', label: 'Branch', placeholder: 'main' },
    { key: 'repo_path', label: '仓库目录', placeholder: 'published/' }
  ],
  github_pages: [
    { key: 'owner', label: 'Owner', placeholder: 'company' },
    { key: 'repo', label: 'Repository', placeholder: 'published-content' },
    { key: 'branch', label: 'Pages Branch', placeholder: 'gh-pages' },
    { key: 'repo_path', label: '仓库目录', placeholder: 'content/' },
    { key: 'base_url', label: 'Pages URL 根地址', placeholder: 'https://company.github.io/published-content/' }
  ],
  onedrive: [
    { key: 'tenant_id', label: 'Tenant ID', placeholder: 'Microsoft Entra Tenant ID' },
    { key: 'client_id', label: 'Client ID', placeholder: '应用 Client ID' },
    { key: 'drive_id', label: 'Drive ID', placeholder: '目标 Drive ID' },
    { key: 'folder_path', label: '文件夹路径', placeholder: '/Company/Published/' }
  ],
  dropbox: [{ key: 'folder_path', label: '文件夹路径', placeholder: '/Company/Published/' }]
}
const ALL_CONTENT_TYPES = Object.keys(CONTENT_TYPES) as ContentType[]
const TARGET_CONTENT_TYPES: Record<PublishTargetType, ContentType[]> = {
  local: ALL_CONTENT_TYPES,
  sftp: ALL_CONTENT_TYPES,
  github: ALL_CONTENT_TYPES,
  github_pages: ALL_CONTENT_TYPES.filter((item) => item !== 'dynamic'),
  onedrive: ALL_CONTENT_TYPES,
  dropbox: ALL_CONTENT_TYPES
}
const TARGET_TYPE_HINTS: Record<PublishTargetType, string> = {
  local: '公司服务器可按部门或用途建发布区，所有内容类型均可自由组合。',
  sftp: '远程公司服务器支持所有内容类型自由组合。',
  github: 'GitHub Repository 支持所有类型；超过 100 MiB 的单文件使用 Git LFS。',
  github_pages: 'GitHub Pages 是静态站点，仅排除依赖后端运行的动态页面，且不支持 Git LFS。',
  onedrive: 'OneDrive 支持所有文件类型；大文件由上传会话分块传输。',
  dropbox: 'Dropbox 支持所有文件类型；超过 150 MiB 使用上传会话分块传输。'
}

const loading = ref(false)
const saving = ref(false)
const testingId = ref<number>()
const statusChangingId = ref<number>()
const targets = ref<PublishTarget[]>([])
const dialogVisible = ref(false)
const editingId = ref<number>()
const formRef = ref<FormInstance>()
const form = reactive<PublishTargetPayload>(emptyForm())
const contentTypeLabel = (value: ContentType) => CONTENT_TYPES[value]
const targetTypeLabel = (value: PublishTargetType) => TARGET_TYPES[value]
const availableContentTypes = computed(() => TARGET_CONTENT_TYPES[form.target_type])
const rules: FormRules = {
  name: [{ required: true, message: '请输入发布目标名称', trigger: 'blur' }],
  target_type: [{ required: true, message: '请选择目标类型', trigger: 'change' }],
  content_types: [{ type: 'array', required: true, min: 1, message: '至少选择一种内容类型', trigger: 'change' }]
}

function emptyForm(): PublishTargetPayload {
  return { name: '', target_type: 'local', content_types: [...ALL_CONTENT_TYPES], publish_root: '', base_url: '', config: {}, credential_ref: '', enabled: true }
}
async function load() { loading.value = true; try { targets.value = await getPublishTargets() } catch (e) { ElMessage.error(e instanceof Error ? e.message : '发布配置加载失败') } finally { loading.value = false } }
function resetForType(type: PublishTargetType) {
  form.target_type = type
  const allowed = TARGET_CONTENT_TYPES[type]
  const retained = form.content_types.filter((item) => allowed.includes(item))
  form.content_types = retained.length ? retained : [...allowed]
  form.config = type === 'sftp' ? { port: 22 } : {}
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
    if (!form.publish_root || !form.base_url) { ElMessage.warning('请填写服务器发布根目录和 URL 根地址'); return false }
    return true
  }
  const missing = CONFIG_FIELDS[form.target_type].find((field) => form.config[field.key] === undefined || form.config[field.key] === '')
  if (missing) { ElMessage.warning(`请填写${missing.label}`); return false }
  if (!form.credential_ref) { ElMessage.warning('请填写凭证引用'); return false }
  return true
}
async function save() {
  if (!await formRef.value?.validate().catch(() => false) || !validateDynamic()) return
  saving.value = true
  try {
    if (editingId.value) await updatePublishTarget(editingId.value, form)
    else await createPublishTarget(form)
    ElMessage.success(editingId.value ? '发布目标已更新' : '发布目标已创建')
    dialogVisible.value = false
    await load()
  } catch (e) { ElMessage.error(errorMessage(e, '保存失败')) } finally { saving.value = false }
}
async function testConnection(item: PublishTarget) {
  testingId.value = item.id
  try { await testPublishTarget(item.id); ElMessage.success(`${item.name} 连接成功`) } catch (e) { ElMessage.error(errorMessage(e, '连接失败')) } finally { testingId.value = undefined }
}
function errorMessage(error: unknown, fallback: string) {
  const serverMessage = isAxiosError<{ message?: string }>(error) ? error.response?.data?.message : undefined
  return serverMessage || (error instanceof Error ? error.message : fallback)
}
async function toggle(item: PublishTarget, value: string | number | boolean) {
  const next = Boolean(value)
  statusChangingId.value = item.id
  try {
    if (!next) await ElMessageBox.confirm(`禁用“${item.name}”后，新内容将无法选择此目标，确认继续吗？`, '禁用发布目标', { type: 'warning', confirmButtonText: '禁用', cancelButtonText: '取消' })
    await updatePublishTargetStatus(item.id, next); ElMessage.success(next ? '发布目标已启用' : '发布目标已禁用'); await load()
  } catch (e) { if (e instanceof Error) ElMessage.error(errorMessage(e, '状态更新失败')) }
  finally { statusChangingId.value = undefined }
}
async function remove(item: PublishTarget) {
  try {
    await ElMessageBox.confirm(`确认删除“${item.name}”吗？已被内容引用时后端会拒绝删除。`, '删除发布目标', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    await deletePublishTarget(item.id); ElMessage.success('发布目标已删除'); await load()
  } catch (e) { if (e instanceof Error) ElMessage.error(errorMessage(e, '删除失败')) }
}
function locationText(item: PublishTarget) {
  if (item.target_type === 'local') return item.publish_root || '—'
  if (item.target_type === 'sftp') return `${item.config?.host || '—'}:${item.config?.port || 22}${item.config?.remote_root || ''}`
  if (item.target_type === 'github' || item.target_type === 'github_pages') return `${item.config?.owner || '—'}/${item.config?.repo || '—'} @ ${item.config?.branch || '—'}`
  if (item.target_type === 'onedrive') return `Drive ${item.config?.drive_id || '—'} · ${item.config?.folder_path || ''}`
  return String(item.config?.folder_path || '—')
}
function accessUrl(item: PublishTarget) { return String(item.base_url || item.config?.base_url || '') }
onMounted(load)
</script>

<template>
  <div class="page-shell">
    <PageHeader title="发布配置" description="可按部门或业务用途建立发布区，并为每个发布区组合多种内容类型。" eyebrow="DESTINATION ADAPTERS"><template #actions><el-button type="primary" :icon="Plus" @click="openCreate">新增发布目标</el-button></template></PageHeader>
    <el-alert title="目标能力与凭证隔离" description="内容类型按目标平台能力选择；Token、密码、Client Secret 和私钥只从服务器环境变量读取。" type="warning" :closable="false" show-icon />
    <section class="paper-card table-panel">
      <div class="table-toolbar"><span class="table-count">{{ targets.length }} 个发布目标</span><span class="muted">每个目标由独立 Adapter 负责连接与上传</span></div>
      <el-table v-loading="loading" :data="targets">
        <el-table-column prop="name" label="名称" min-width="155"><template #default="scope"><strong>{{ scope.row.name }}</strong></template></el-table-column>
        <el-table-column label="目标类型" width="190"><template #default="scope"><span class="target-type">{{ targetTypeLabel(scope.row.target_type) }}</span></template></el-table-column>
        <el-table-column label="支持内容类型" min-width="220"><template #default="scope"><el-tag v-for="type in scope.row.content_types" :key="type" type="info" effect="plain" class="type-tag">{{ contentTypeLabel(type) }}</el-tag></template></el-table-column>
        <el-table-column label="目标位置" min-width="230"><template #default="scope"><span class="mono path-text">{{ locationText(scope.row) }}</span><a v-if="accessUrl(scope.row)" class="mono url-text" :href="accessUrl(scope.row)" target="_blank" rel="noopener noreferrer">{{ accessUrl(scope.row) }}</a></template></el-table-column>
        <el-table-column label="状态" width="90"><template #default="scope"><el-switch :model-value="scope.row.enabled" :loading="statusChangingId === scope.row.id" inline-prompt active-text="启" inactive-text="停" @change="toggle(scope.row, $event)" /></template></el-table-column>
        <el-table-column label="操作" width="220" fixed="right"><template #default="scope"><el-button link type="success" :icon="Connection" :loading="testingId === scope.row.id" @click="testConnection(scope.row)">测试连接</el-button><el-button link type="primary" @click="openEdit(scope.row)">编辑</el-button><el-button link type="danger" @click="remove(scope.row)">删除</el-button></template></el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑发布目标' : '新增发布目标'" width="680px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="form-grid"><el-form-item label="名称" prop="name"><el-input v-model="form.name" placeholder="例如：公司文档发布区" /></el-form-item><el-form-item label="目标类型" prop="target_type"><el-select v-model="form.target_type" style="width:100%" @change="resetForType"><el-option v-for="(label, value) in TARGET_TYPES" :key="value" :label="label" :value="value" /></el-select></el-form-item></div>
        <el-form-item label="支持内容类型（可多选）" prop="content_types"><el-select v-model="form.content_types" multiple collapse-tags :max-collapse-tags="4" placeholder="选择一种或多种类型" style="width:100%"><el-option v-for="type in availableContentTypes" :key="type" :label="CONTENT_TYPES[type]" :value="type" /></el-select><span class="form-hint">{{ TARGET_TYPE_HINTS[form.target_type] }}</span></el-form-item>
        <template v-if="form.target_type === 'local'">
          <el-form-item label="服务器发布根目录"><el-input v-model="form.publish_root" class="mono-input" placeholder="C:\company\published 或 /data/company/published" /><span class="form-hint">路径由后端使用，不会暴露给普通员工。</span></el-form-item>
          <el-form-item label="URL 根地址"><el-input v-model="form.base_url" class="mono-input" placeholder="https://internal.example.com/content/" /></el-form-item>
        </template>
        <template v-else>
          <div class="adapter-strip"><span>{{ TARGET_TYPES[form.target_type] }}</span><strong>非敏感连接配置</strong></div>
          <div class="config-grid"><el-form-item v-for="field in CONFIG_FIELDS[form.target_type]" :key="field.key" :label="field.label"><el-input v-model="form.config[field.key]" class="mono-input" :placeholder="field.placeholder" /><span v-if="field.hint" class="form-hint">{{ field.hint }}</span></el-form-item></div>
          <el-form-item label="凭证引用"><el-input v-model="form.credential_ref" class="mono-input" placeholder="例如：github_company_pages" /><span class="form-hint">这里只填写引用名。Secret 从 PUBLISH_CREDENTIAL_... 环境变量读取，保存后不会回显 Secret。</span></el-form-item>
        </template>
        <el-form-item label="是否启用"><el-switch v-model="form.enabled" active-text="启用" inactive-text="禁用" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="save">保存配置</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.type-tag { margin: 2px 4px 2px 0; }.target-type { display: inline-flex; padding: 4px 8px; color: #234f84; border-left: 3px solid var(--blue); background: #edf4fb; font-size: 11px; font-weight: 650; }.path-text, .url-text { display: block; overflow-wrap: anywhere; font-size: 10px; }.url-text { margin-top: 4px; color: var(--blue); }.muted { font-size: 11px; }.form-grid, .config-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; }.mono-input :deep(input) { font-family: "Cascadia Mono", monospace; font-size: 11px; }.form-hint { margin-top: 5px; color: #8a93a2; font-size: 11px; }.adapter-strip { display: flex; align-items: center; gap: 10px; margin: 2px 0 16px; padding: 10px 12px; color: #5f6c80; border-left: 3px solid var(--blue); background: #f4f7fa; font-size: 11px; }.adapter-strip span { color: var(--blue); font-weight: 700; }.adapter-strip strong { color: #344054; font-size: 12px; }
</style>
