<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import { createCategory, deleteCategory, updateCategory, updateCategoryStatus } from '@/api/categories'
import { getRequestErrorMessage } from '@/api/request'
import { getDepartments } from '@/api/departments'
import { CATEGORY_VISIBILITY } from '@/constants'
import { useCategoryStore } from '@/stores/categories'
import type { Category, CategoryPayload, CategoryVisibility } from '@/types/category'
import type { Department } from '@/types/department'

const categories = useCategoryStore()
const { t } = useI18n()
const dialogVisible = ref(false)
const editingId = ref<number>()
const saving = ref(false)
const departments = ref<Department[]>([])
const formRef = ref<FormInstance>()
const form = reactive<CategoryPayload>({ name: '', enabled: true, sort_order: 10, visibility_scope: 'all', department: null })
const visibilityLabel = (value: CategoryVisibility) => t(CATEGORY_VISIBILITY[value])
const rules = computed<FormRules>(() => ({
  name: [{ required: true, message: t('validation.categoryNameRequired'), trigger: 'blur' }],
  visibility_scope: [{ required: true, message: t('validation.visibilityRequired'), trigger: 'change' }],
  department: [{ validator: (_rule, value, callback) => { if (form.visibility_scope === 'department' && !value) callback(new Error(t('validation.visibilityDepartmentRequired'))); else callback() }, trigger: 'change' }]
}))

async function load(force = false) {
  try {
    const [, departmentItems] = await Promise.all([categories.load(true, force), getDepartments(true)])
    departments.value = departmentItems
  } catch (e) { ElMessage.error(getRequestErrorMessage(e, 'category.loadFailed')) }
}
function openCreate() {
  editingId.value = undefined
  const nextOrder = categories.items.reduce((maximum, item) => Math.max(maximum, item.sort_order), 0) + 10
  Object.assign(form, { name: '', enabled: true, sort_order: nextOrder, visibility_scope: 'all', department: null })
  dialogVisible.value = true
}
function openEdit(item: Category) {
  editingId.value = item.id
  Object.assign(form, { name: item.name, enabled: item.enabled, sort_order: item.sort_order, visibility_scope: item.visibility_scope, department: item.department })
  dialogVisible.value = true
}
function changeVisibility(value: CategoryVisibility) {
  if (value !== 'department') form.department = null
  formRef.value?.clearValidate('department')
}
async function save() {
  if (!await formRef.value?.validate().catch(() => false)) return
  saving.value = true
  try {
    if (editingId.value) await updateCategory(editingId.value, form)
    else await createCategory(form)
    ElMessage.success(t(editingId.value ? 'category.updated' : 'category.created'))
    dialogVisible.value = false
    categories.invalidate(); await load(true)
  } catch (e) { ElMessage.error(getRequestErrorMessage(e, 'common.saveFailed')) } finally { saving.value = false }
}
async function toggle(item: Category) {
  const enabled = !item.enabled
  try {
    if (!enabled) await ElMessageBox.confirm(t('category.disableConfirm', { name: item.name }), t('category.disableTitle'), { type: 'warning', confirmButtonText: t('common.disable'), cancelButtonText: t('common.cancel') })
    await updateCategoryStatus(item.id, enabled)
    ElMessage.success(t(enabled ? 'category.enabled' : 'category.disabled'))
    categories.invalidate(); await load(true)
  } catch (e) { if (e instanceof Error) ElMessage.error(e.message) }
}
async function remove(item: Category) {
  try {
    await ElMessageBox.confirm(t('category.deleteConfirm', { name: item.name }), t('category.deleteTitle'), { type: 'warning', confirmButtonText: t('common.delete'), cancelButtonText: t('common.cancel') })
    await deleteCategory(item.id)
    ElMessage.success(t('category.deleted'))
    categories.invalidate(); await load(true)
  } catch (e) { if (e instanceof Error) ElMessage.error(e.message) }
}
onMounted(() => load())
</script>

<template>
  <div class="page-shell">
    <PageHeader :title="t('nav.categories')" :description="t('category.description')" :eyebrow="t('kicker.contentTaxonomy')"><template #actions><el-button type="primary" :icon="Plus" @click="openCreate">{{ t('category.create') }}</el-button></template></PageHeader>
    <el-alert :title="t('category.alertTitle')" :description="t('category.alertDescription')" type="info" :closable="false" show-icon />
    <section class="paper-card table-panel">
      <div class="table-toolbar"><span class="table-count">{{ t('category.totalCount', { count: categories.items.length }) }}</span><span class="muted">{{ t('common.sortOrderHint') }}</span></div>
      <el-table v-loading="categories.loading" :data="categories.items">
        <el-table-column prop="name" :label="t('category.name')" min-width="240"><template #default="scope"><strong>{{ scope.row.name }}</strong></template></el-table-column>
        <el-table-column :label="t('category.viewers')" min-width="180"><template #default="scope"><span>{{ visibilityLabel(scope.row.visibility_scope) }}</span><small v-if="scope.row.visibility_scope === 'department'" class="visibility-department">{{ scope.row.department }}</small></template></el-table-column>
        <el-table-column prop="sort_order" :label="t('common.sortOrder')" width="110" />
        <el-table-column :label="t('common.status')" width="120"><template #default="scope"><el-tag :type="scope.row.enabled ? 'success' : 'info'">{{ t(scope.row.enabled ? 'common.enabled' : 'common.disabled') }}</el-tag></template></el-table-column>
        <el-table-column :label="t('common.actions')" width="220" fixed="right"><template #default="scope"><el-button link type="primary" @click="openEdit(scope.row)">{{ t('common.edit') }}</el-button><el-button link :type="scope.row.enabled ? 'warning' : 'success'" @click="toggle(scope.row)">{{ t(scope.row.enabled ? 'common.disable' : 'common.enable') }}</el-button><el-button link type="danger" @click="remove(scope.row)">{{ t('common.delete') }}</el-button></template></el-table-column>
      </el-table>
    </section>
    <el-dialog v-model="dialogVisible" :title="t(editingId ? 'category.edit' : 'category.create')" width="520px" @closed="formRef?.clearValidate()">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item :label="t('category.name')" prop="name"><el-input v-model="form.name" maxlength="100" show-word-limit :placeholder="t('category.namePlaceholder')" /></el-form-item>
        <el-form-item :label="t('category.viewers')" prop="visibility_scope"><el-radio-group v-model="form.visibility_scope" @change="changeVisibility"><el-radio value="publisher">{{ t('visibility.publisher') }}</el-radio><el-radio value="department">{{ t('visibility.department') }}</el-radio><el-radio value="all">{{ t('visibility.all') }}</el-radio></el-radio-group></el-form-item>
        <el-form-item v-if="form.visibility_scope === 'department'" :label="t('category.visibleDepartment')" prop="department"><el-select v-model="form.department" filterable :placeholder="t('department.select')" style="width:100%"><el-option v-for="item in departments" :key="item.id" :label="item.enabled ? item.name : t('common.disabledName', { name: item.name })" :value="item.name" :disabled="!item.enabled" /></el-select><span v-if="departments.length === 0" class="field-hint">{{ t('category.createDepartmentFirst') }}</span></el-form-item>
        <div class="dialog-grid"><el-form-item :label="t('common.sortOrder')"><el-input-number v-model="form.sort_order" :min="0" :max="9999" /></el-form-item>
        <el-form-item :label="t('common.status')"><el-radio-group v-model="form.enabled"><el-radio :value="true">{{ t('common.enable') }}</el-radio><el-radio :value="false">{{ t('common.disable') }}</el-radio></el-radio-group></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button><el-button type="primary" :loading="saving" @click="save">{{ t('common.save') }}</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.table-toolbar > .muted { font-size: 11px; }.visibility-department { display: block; margin-top: 3px; color: #8790a0; }.field-hint { display: block; color: var(--danger); font-size: 11px; }.dialog-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
</style>
