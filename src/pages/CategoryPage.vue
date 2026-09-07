<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import { createCategory, deleteCategory, updateCategory, updateCategoryStatus } from '@/api/categories'
import { useCategoryStore } from '@/stores/categories'
import type { Category, CategoryPayload } from '@/types/category'

const categories = useCategoryStore()
const dialogVisible = ref(false)
const editingId = ref<number>()
const saving = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<CategoryPayload>({ name: '', enabled: true, sort_order: 10 })
const rules: FormRules = { name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }] }

async function load(force = false) {
  try { await categories.load(true, force) } catch (e) { ElMessage.error(e instanceof Error ? e.message : '分类加载失败') }
}
function openCreate() {
  editingId.value = undefined
  const nextOrder = categories.items.reduce((maximum, item) => Math.max(maximum, item.sort_order), 0) + 10
  Object.assign(form, { name: '', enabled: true, sort_order: nextOrder })
  dialogVisible.value = true
}
function openEdit(item: Category) {
  editingId.value = item.id
  Object.assign(form, { name: item.name, enabled: item.enabled, sort_order: item.sort_order })
  dialogVisible.value = true
}
async function save() {
  if (!await formRef.value?.validate().catch(() => false)) return
  saving.value = true
  try {
    if (editingId.value) await updateCategory(editingId.value, form)
    else await createCategory(form)
    ElMessage.success(editingId.value ? '分类已更新，已有内容同步使用新名称' : '分类已创建')
    dialogVisible.value = false
    categories.invalidate(); await load(true)
  } catch (e) { ElMessage.error(e instanceof Error ? e.message : '保存失败') } finally { saving.value = false }
}
async function toggle(item: Category) {
  const enabled = !item.enabled
  try {
    if (!enabled) await ElMessageBox.confirm(`禁用“${item.name}”后，新建和编辑内容将不能再选择它，确认继续吗？`, '禁用分类', { type: 'warning', confirmButtonText: '禁用', cancelButtonText: '取消' })
    await updateCategoryStatus(item.id, enabled)
    ElMessage.success(enabled ? '分类已启用' : '分类已禁用')
    categories.invalidate(); await load(true)
  } catch (e) { if (e instanceof Error) ElMessage.error(e.message) }
}
async function remove(item: Category) {
  try {
    await ElMessageBox.confirm(`确认删除“${item.name}”吗？已被内容使用的分类不能删除，可改为禁用。`, '删除分类', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    await deleteCategory(item.id)
    ElMessage.success('分类已删除')
    categories.invalidate(); await load(true)
  } catch (e) { if (e instanceof Error) ElMessage.error(e.message) }
}
onMounted(() => load())
</script>

<template>
  <div class="page-shell">
    <PageHeader title="分类配置" description="维护内容使用的分类名称、显示顺序和启用状态。" eyebrow="CONTENT TAXONOMY"><template #actions><el-button type="primary" :icon="Plus" @click="openCreate">新增分类</el-button></template></PageHeader>
    <el-alert title="已有内容不会丢失" description="重命名分类会同步更新已有内容；已被内容使用的分类只能禁用，不能直接删除。" type="info" :closable="false" show-icon />
    <section class="paper-card table-panel">
      <div class="table-toolbar"><span class="table-count">共 {{ categories.items.length }} 个分类</span><span class="muted">按显示顺序从小到大排列</span></div>
      <el-table v-loading="categories.loading" :data="categories.items">
        <el-table-column prop="name" label="分类名称" min-width="240"><template #default="scope"><strong>{{ scope.row.name }}</strong></template></el-table-column>
        <el-table-column prop="sort_order" label="显示顺序" width="130" />
        <el-table-column label="状态" width="120"><template #default="scope"><el-tag :type="scope.row.enabled ? 'success' : 'info'">{{ scope.row.enabled ? '已启用' : '已禁用' }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="220" fixed="right"><template #default="scope"><el-button link type="primary" @click="openEdit(scope.row)">编辑</el-button><el-button link :type="scope.row.enabled ? 'warning' : 'success'" @click="toggle(scope.row)">{{ scope.row.enabled ? '禁用' : '启用' }}</el-button><el-button link type="danger" @click="remove(scope.row)">删除</el-button></template></el-table-column>
      </el-table>
    </section>
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑分类' : '新增分类'" width="480px" @closed="formRef?.clearValidate()">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="分类名称" prop="name"><el-input v-model="form.name" maxlength="100" show-word-limit placeholder="例如：客户案例" /></el-form-item>
        <el-form-item label="显示顺序"><el-input-number v-model="form.sort_order" :min="0" :max="9999" /></el-form-item>
        <el-form-item label="状态"><el-radio-group v-model="form.enabled"><el-radio :value="true">启用</el-radio><el-radio :value="false">禁用</el-radio></el-radio-group></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.table-toolbar > .muted { font-size: 11px; }
</style>
