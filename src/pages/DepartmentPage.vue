<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import { createDepartment, deleteDepartment, getDepartments, updateDepartment, updateDepartmentStatus } from '@/api/departments'
import { getRequestErrorMessage } from '@/api/request'
import type { Department, DepartmentPayload } from '@/types/department'

const loading = ref(false)
const { t } = useI18n()
const saving = ref(false)
const items = ref<Department[]>([])
const editingId = ref<number>()
const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<DepartmentPayload>({ name: '', enabled: true, sort_order: 10 })
const rules = computed<FormRules>(() => ({ name: [{ required: true, message: t('validation.departmentNameRequired'), trigger: 'blur' }] }))

async function load() {
  loading.value = true
  try { items.value = await getDepartments(true) }
  catch (error) { ElMessage.error(getRequestErrorMessage(error, 'department.loadFailed')) }
  finally { loading.value = false }
}
function openCreate() {
  editingId.value = undefined
  const nextOrder = items.value.reduce((maximum, item) => Math.max(maximum, item.sort_order), 0) + 10
  Object.assign(form, { name: '', enabled: true, sort_order: nextOrder })
  dialogVisible.value = true
}
function openEdit(item: Department) {
  editingId.value = item.id
  Object.assign(form, { name: item.name, enabled: item.enabled, sort_order: item.sort_order })
  dialogVisible.value = true
}
async function save() {
  if (!await formRef.value?.validate().catch(() => false)) return
  saving.value = true
  try {
    if (editingId.value) await updateDepartment(editingId.value, form)
    else await createDepartment(form)
    ElMessage.success(t(editingId.value ? 'department.updated' : 'department.created'))
    dialogVisible.value = false
    await load()
  } catch (error) { ElMessage.error(getRequestErrorMessage(error, 'common.saveFailed')) }
  finally { saving.value = false }
}
async function toggle(item: Department) {
  const enabled = !item.enabled
  try {
    if (!enabled) await ElMessageBox.confirm(t('department.disableConfirm', { name: item.name }), t('department.disableTitle'), { type: 'warning', confirmButtonText: t('common.disable'), cancelButtonText: t('common.cancel') })
    await updateDepartmentStatus(item.id, enabled)
    ElMessage.success(t(enabled ? 'department.enabled' : 'department.disabled'))
    await load()
  } catch (error) { if (error instanceof Error) ElMessage.error(error.message) }
}
async function remove(item: Department) {
  try {
    await ElMessageBox.confirm(t('department.deleteConfirm', { name: item.name }), t('department.deleteTitle'), { type: 'warning', confirmButtonText: t('common.delete'), cancelButtonText: t('common.cancel') })
    await deleteDepartment(item.id)
    ElMessage.success(t('department.deleted'))
    await load()
  } catch (error) { if (error instanceof Error) ElMessage.error(error.message) }
}
onMounted(load)
</script>

<template>
  <div class="page-shell">
    <PageHeader :title="t('nav.departments')" :description="t('department.description')" :eyebrow="t('kicker.departmentDirectory')"><template #actions><el-button type="primary" :icon="Plus" @click="openCreate">{{ t('department.create') }}</el-button></template></PageHeader>
    <el-alert :title="t('department.alertTitle')" :description="t('department.alertDescription')" type="info" :closable="false" show-icon />
    <section class="paper-card table-panel">
      <div class="table-toolbar"><span class="table-count">{{ t('department.totalCount', { count: items.length }) }}</span><span class="muted">{{ t('common.sortOrderHint') }}</span></div>
      <el-table v-loading="loading" :data="items">
        <el-table-column prop="name" :label="t('department.name')" min-width="260"><template #default="scope"><strong>{{ scope.row.name }}</strong></template></el-table-column>
        <el-table-column prop="sort_order" :label="t('common.sortOrder')" width="130" />
        <el-table-column :label="t('common.status')" width="130"><template #default="scope"><el-tag :type="scope.row.enabled ? 'success' : 'info'">{{ t(scope.row.enabled ? 'common.enabled' : 'common.disabled') }}</el-tag></template></el-table-column>
        <el-table-column :label="t('common.actions')" width="220" fixed="right"><template #default="scope"><el-button link type="primary" @click="openEdit(scope.row)">{{ t('common.edit') }}</el-button><el-button link :type="scope.row.enabled ? 'warning' : 'success'" @click="toggle(scope.row)">{{ t(scope.row.enabled ? 'common.disable' : 'common.enable') }}</el-button><el-button link type="danger" @click="remove(scope.row)">{{ t('common.delete') }}</el-button></template></el-table-column>
      </el-table>
    </section>
    <el-dialog v-model="dialogVisible" :title="t(editingId ? 'department.edit' : 'department.create')" width="480px" @closed="formRef?.clearValidate()">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item :label="t('department.name')" prop="name"><el-input v-model="form.name" maxlength="100" show-word-limit :placeholder="t('department.namePlaceholder')" /></el-form-item>
        <div class="dialog-grid"><el-form-item :label="t('common.sortOrder')"><el-input-number v-model="form.sort_order" :min="0" :max="9999" /></el-form-item><el-form-item :label="t('common.status')"><el-radio-group v-model="form.enabled"><el-radio :value="true">{{ t('common.enable') }}</el-radio><el-radio :value="false">{{ t('common.disable') }}</el-radio></el-radio-group></el-form-item></div>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button><el-button type="primary" :loading="saving" @click="save">{{ t('common.save') }}</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.table-toolbar > .muted { font-size: 11px; }.dialog-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
</style>
