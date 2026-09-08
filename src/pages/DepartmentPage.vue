<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import { createDepartment, deleteDepartment, getDepartments, updateDepartment, updateDepartmentStatus } from '@/api/departments'
import type { Department, DepartmentPayload } from '@/types/department'

const loading = ref(false)
const saving = ref(false)
const items = ref<Department[]>([])
const editingId = ref<number>()
const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<DepartmentPayload>({ name: '', enabled: true, sort_order: 10 })
const rules: FormRules = { name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }] }

async function load() {
  loading.value = true
  try { items.value = await getDepartments(true) }
  catch (error) { ElMessage.error(error instanceof Error ? error.message : '部门加载失败') }
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
    ElMessage.success(editingId.value ? '部门已更新，关联用户和分类已同步' : '部门已创建')
    dialogVisible.value = false
    await load()
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '保存失败') }
  finally { saving.value = false }
}
async function toggle(item: Department) {
  const enabled = !item.enabled
  try {
    if (!enabled) await ElMessageBox.confirm(`禁用“${item.name}”后将不能再分配给用户或分类，确认继续吗？`, '禁用部门', { type: 'warning', confirmButtonText: '禁用', cancelButtonText: '取消' })
    await updateDepartmentStatus(item.id, enabled)
    ElMessage.success(enabled ? '部门已启用' : '部门已禁用')
    await load()
  } catch (error) { if (error instanceof Error) ElMessage.error(error.message) }
}
async function remove(item: Department) {
  try {
    await ElMessageBox.confirm(`确认删除“${item.name}”吗？已被用户或分类使用的部门不能删除。`, '删除部门', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    await deleteDepartment(item.id)
    ElMessage.success('部门已删除')
    await load()
  } catch (error) { if (error instanceof Error) ElMessage.error(error.message) }
}
onMounted(load)
</script>

<template>
  <div class="page-shell">
    <PageHeader title="部门配置" description="统一维护用户所属部门及分类的部门可见范围。" eyebrow="DEPARTMENT DIRECTORY"><template #actions><el-button type="primary" :icon="Plus" @click="openCreate">新增部门</el-button></template></PageHeader>
    <el-alert title="部门名称统一管理" description="重命名部门会同步更新关联用户和分类；已被使用的部门只能禁用，不能直接删除。" type="info" :closable="false" show-icon />
    <section class="paper-card table-panel">
      <div class="table-toolbar"><span class="table-count">共 {{ items.length }} 个部门</span><span class="muted">按显示顺序从小到大排列</span></div>
      <el-table v-loading="loading" :data="items">
        <el-table-column prop="name" label="部门名称" min-width="260"><template #default="scope"><strong>{{ scope.row.name }}</strong></template></el-table-column>
        <el-table-column prop="sort_order" label="显示顺序" width="130" />
        <el-table-column label="状态" width="130"><template #default="scope"><el-tag :type="scope.row.enabled ? 'success' : 'info'">{{ scope.row.enabled ? '已启用' : '已禁用' }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="220" fixed="right"><template #default="scope"><el-button link type="primary" @click="openEdit(scope.row)">编辑</el-button><el-button link :type="scope.row.enabled ? 'warning' : 'success'" @click="toggle(scope.row)">{{ scope.row.enabled ? '禁用' : '启用' }}</el-button><el-button link type="danger" @click="remove(scope.row)">删除</el-button></template></el-table-column>
      </el-table>
    </section>
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑部门' : '新增部门'" width="480px" @closed="formRef?.clearValidate()">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="部门名称" prop="name"><el-input v-model="form.name" maxlength="100" show-word-limit placeholder="例如：销售部" /></el-form-item>
        <div class="dialog-grid"><el-form-item label="显示顺序"><el-input-number v-model="form.sort_order" :min="0" :max="9999" /></el-form-item><el-form-item label="状态"><el-radio-group v-model="form.enabled"><el-radio :value="true">启用</el-radio><el-radio :value="false">禁用</el-radio></el-radio-group></el-form-item></div>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.table-toolbar > .muted { font-size: 11px; }.dialog-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
</style>
