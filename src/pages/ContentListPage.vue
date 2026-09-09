<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Folder, FolderOpened, Plus, RefreshRight, Search } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import ContentStatus from '@/components/ContentStatus.vue'
import { CONTENT_TYPES, PUBLISH_STATUS, REVIEW_STATUS } from '@/constants'
import { deleteContent, getContents, republishContent, submitContent } from '@/api/contents'
import { getDepartments } from '@/api/departments'
import { getPublishTargets } from '@/api/publishTargets'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/categories'
import { formatDate } from '@/utils/format'
import type { ContentItem, ContentQuery, ContentType, PublishStatus, ReviewStatus } from '@/types/content'
import type { Department } from '@/types/department'
import type { PublishTarget } from '@/types/publish'

interface ContentTreeRow {
  tree_id: string
  row_kind: 'target' | 'department' | 'content'
  title: string
  content_count?: number
  content?: ContentItem
  children?: ContentTreeRow[]
}

interface TreeTableRef {
  toggleRowExpansion: (row: ContentTreeRow, expanded?: boolean) => void
}

interface TargetTreeGroup {
  key: string
  row: ContentTreeRow
  departments: Map<string, ContentTreeRow>
}

const auth = useAuthStore()
const categories = useCategoryStore()
const router = useRouter()
const loading = ref(false)
const total = ref(0)
const items = ref<ContentItem[]>([])
const publishTargets = ref<PublishTarget[]>([])
const departments = ref<Department[]>([])
const tableRef = ref<TreeTableRef | null>(null)
const query = reactive<ContentQuery>({
  page: 1,
  page_size: 10,
  keyword: '',
  content_type: '',
  category: '',
  review_status: '',
  publish_status: ''
})

const treeItems = computed<ContentTreeRow[]>(() => {
  const targetMap = new Map(publishTargets.value.map((target) => [target.id, target]))
  const targetOrder = new Map(publishTargets.value.map((target, index) => [target.id, index]))
  const departmentOrder = new Map(departments.value.map((department, index) => [department.name.toLowerCase(), index]))
  const groups = new Map<string, TargetTreeGroup>()

  items.value.forEach((item) => {
    const targetKey = item.publish_target_id == null ? 'unassigned' : String(item.publish_target_id)
    let targetGroup = groups.get(targetKey)
    if (!targetGroup) {
      const configuredName = item.publish_target_id == null ? undefined : targetMap.get(item.publish_target_id)?.name
      targetGroup = {
        key: targetKey,
        row: {
          tree_id: `target-${targetKey}`,
          row_kind: 'target',
          title: configuredName || item.publish_target_name || '未指定发布配置',
          content_count: 0,
          children: []
        },
        departments: new Map()
      }
      groups.set(targetKey, targetGroup)
    }

    const departmentName = item.creator_department?.trim() || '未设置部门'
    const departmentKey = departmentName.toLowerCase()
    let departmentRow = targetGroup.departments.get(departmentKey)
    if (!departmentRow) {
      departmentRow = {
        tree_id: `target-${targetKey}-department-${departmentKey}`,
        row_kind: 'department',
        title: departmentName,
        content_count: 0,
        children: []
      }
      targetGroup.departments.set(departmentKey, departmentRow)
    }
    departmentRow.children?.push({
      tree_id: `content-${item.id}`,
      row_kind: 'content',
      title: item.title,
      content: item
    })
    departmentRow.content_count = (departmentRow.content_count || 0) + 1
    targetGroup.row.content_count = (targetGroup.row.content_count || 0) + 1
  })

  return [...groups.values()]
    .sort((left, right) => {
      const leftOrder = targetOrder.get(Number(left.key)) ?? Number.MAX_SAFE_INTEGER
      const rightOrder = targetOrder.get(Number(right.key)) ?? Number.MAX_SAFE_INTEGER
      return leftOrder - rightOrder || left.row.title.localeCompare(right.row.title, 'zh-CN')
    })
    .map((group) => {
      group.row.children = [...group.departments.entries()]
        .sort(([leftKey, left], [rightKey, right]) => {
          const leftOrder = departmentOrder.get(leftKey) ?? Number.MAX_SAFE_INTEGER
          const rightOrder = departmentOrder.get(rightKey) ?? Number.MAX_SAFE_INTEGER
          return leftOrder - rightOrder || left.title.localeCompare(right.title, 'zh-CN')
        })
        .map(([, row]) => row)
      return group.row
    })
})

const contentTypeLabel = (value: ContentType) => CONTENT_TYPES[value]

async function load() {
  loading.value = true
  try {
    const result = await getContents(query)
    items.value = result.items
    total.value = result.total
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '内容加载失败')
  } finally {
    loading.value = false
  }
}

async function loadGroupingOptions() {
  try {
    const [targets, departmentItems] = await Promise.all([getPublishTargets(), getDepartments()])
    publishTargets.value = targets
    departments.value = departmentItems
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '发布配置或部门加载失败')
  }
}

function reset() {
  Object.assign(query, { page: 1, keyword: '', content_type: '', category: '', review_status: '', publish_status: '' })
  void load()
}

async function remove(item?: ContentItem) {
  if (!item) return
  try {
    await ElMessageBox.confirm(`删除“${item.title}”后无法恢复，确认继续吗？`, '删除内容', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消'
    })
    await deleteContent(item.id)
    ElMessage.success('内容已删除')
    void load()
  } catch (error) {
    if (error instanceof Error) ElMessage.error(error.message)
  }
}

async function submit(item?: ContentItem) {
  if (!item) return
  try {
    await submitContent(item.id)
    ElMessage.success('已提交发布审核')
    void load()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '提交失败')
  }
}

async function republish(item?: ContentItem) {
  if (!item) return
  try {
    await ElMessageBox.confirm('确认重新执行发布吗？该操作不会重新审核。', '重新发布', {
      confirmButtonText: '重新发布', cancelButtonText: '取消'
    })
    await republishContent(item.id)
    ElMessage.success('重新发布成功')
    void load()
  } catch (error) {
    if (error instanceof Error) ElMessage.error(error.message)
  }
}

function canEdit(item?: ContentItem) {
  return Boolean(item && (auth.isAdmin || (item.created_by === auth.user?.id && item.review_status !== 'pending' && item.publish_status !== 'published')))
}

function canDelete(item?: ContentItem) {
  return Boolean(item && (auth.isAdmin || (item.created_by === auth.user?.id && item.review_status !== 'pending' && item.publish_status !== 'published')))
}

function canSubmit(item?: ContentItem) {
  return Boolean(item && !auth.isAdmin && ['draft', 'rejected'].includes(item.review_status))
}

function tableRowClassName({ row }: { row: ContentTreeRow }) {
  if (row.row_kind === 'target') return 'target-row'
  return row.row_kind === 'department' ? 'department-row' : ''
}

function toggleTreeRow(row: ContentTreeRow) {
  if (row.row_kind !== 'content') tableRef.value?.toggleRowExpansion(row)
}

onMounted(() => {
  void categories.load().catch(() => ElMessage.error('分类加载失败'))
  void loadGroupingOptions()
  void load()
})
</script>

<template>
  <div class="page-shell">
    <PageHeader
      :title="auth.isAdmin ? '内容管理' : '我的内容'"
      :description="auth.isAdmin ? '按发布名称和所属部门展开全平台内容，追踪审核与发布状态。' : '按发布名称和所属部门展开你创建的内容，并跟踪发布结果。'"
      eyebrow="CONTENT REGISTER"
    >
      <template #actions><el-button type="primary" :icon="Plus" @click="router.push('/contents/new')">新建内容</el-button></template>
    </PageHeader>

    <section class="paper-card filter-panel">
      <el-form inline :model="query">
        <el-form-item label="关键词"><el-input v-model="query.keyword" clearable placeholder="标题或简介" @keyup.enter="query.page = 1; load()" /></el-form-item>
        <el-form-item label="内容类型"><el-select v-model="query.content_type" clearable placeholder="全部类型" style="width:150px"><el-option v-for="(label, value) in CONTENT_TYPES" :key="value" :label="label" :value="value as ContentType" /></el-select></el-form-item>
        <el-form-item label="分类"><el-select v-model="query.category" clearable placeholder="全部分类" style="width:130px"><el-option v-for="item in categories.activeNames" :key="item" :label="item" :value="item" /></el-select></el-form-item>
        <el-form-item label="审核状态"><el-select v-model="query.review_status" clearable placeholder="全部" style="width:120px"><el-option v-for="(label, value) in REVIEW_STATUS" :key="value" :label="label" :value="value as ReviewStatus" /></el-select></el-form-item>
        <el-form-item label="发布状态"><el-select v-model="query.publish_status" clearable placeholder="全部" style="width:120px"><el-option v-for="(label, value) in PUBLISH_STATUS" :key="value" :label="label" :value="value as PublishStatus" /></el-select></el-form-item>
        <el-form-item><el-button type="primary" :icon="Search" @click="query.page = 1; load()">查询</el-button><el-button :icon="RefreshRight" @click="reset">重置</el-button></el-form-item>
      </el-form>
    </section>

    <section class="paper-card table-panel">
      <div class="table-toolbar"><span class="table-count">共 {{ total }} 条内容</span><span class="muted">发布名称为一级、所属部门为二级、内容为三级；点击名称可展开或收起</span></div>
      <el-table ref="tableRef" v-loading="loading" :data="treeItems" row-key="tree_id" default-expand-all :indent="24" :tree-props="{ children: 'children' }" :row-class-name="tableRowClassName">
        <el-table-column label="发布名称 / 所属部门 / 内容标题" min-width="290" show-overflow-tooltip>
          <template #default="scope">
            <button v-if="scope.row.row_kind === 'target'" class="tree-toggle target-node" type="button" @click="toggleTreeRow(scope.row)"><el-icon><FolderOpened /></el-icon><strong>{{ scope.row.title }}</strong><el-tag size="small" type="info" effect="plain">当前页 {{ scope.row.content_count || 0 }} 条</el-tag></button>
            <button v-else-if="scope.row.row_kind === 'department'" class="tree-toggle department-node" type="button" @click="toggleTreeRow(scope.row)"><el-icon><Folder /></el-icon><strong>{{ scope.row.title }}</strong><el-tag size="small" type="info" effect="plain">{{ scope.row.content_count || 0 }} 条</el-tag></button>
            <span v-else-if="scope.row.content" class="content-node"><button class="title-link" @click="router.push(`/contents/${scope.row.content.id}`)">{{ scope.row.content.title }}</button><small v-if="scope.row.content.failure_reason" class="row-alert">{{ scope.row.content.failure_reason }}</small></span>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="130"><template #default="scope"><span v-if="scope.row.content">{{ contentTypeLabel(scope.row.content.content_type) }}</span></template></el-table-column>
        <el-table-column label="分类" width="105"><template #default="scope">{{ scope.row.content?.category }}</template></el-table-column>
        <el-table-column v-if="auth.isAdmin" label="创建人" width="100"><template #default="scope">{{ scope.row.content?.creator_name }}</template></el-table-column>
        <el-table-column label="审核状态" width="100"><template #default="scope"><ContentStatus v-if="scope.row.content" kind="review" :status="scope.row.content.review_status" /></template></el-table-column>
        <el-table-column label="发布状态" width="100"><template #default="scope"><ContentStatus v-if="scope.row.content" kind="publish" :status="scope.row.content.publish_status" /></template></el-table-column>
        <el-table-column label="更新时间" width="155"><template #default="scope"><span v-if="scope.row.content">{{ formatDate(scope.row.content.updated_at) }}</span></template></el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="scope">
            <template v-if="scope.row.content">
              <el-button link type="primary" @click="router.push(`/contents/${scope.row.content.id}`)">查看</el-button>
              <el-button v-if="canEdit(scope.row.content)" link type="primary" @click="router.push(`/contents/${scope.row.content.id}/edit`)">编辑</el-button>
              <el-button v-if="auth.isAdmin && scope.row.content.review_status === 'pending'" link type="warning" @click="router.push(`/reviews/${scope.row.content.id}`)">审核</el-button>
              <el-button v-if="scope.row.content.publish_status === 'failed' && auth.isAdmin" link type="warning" @click="republish(scope.row.content)">重新发布</el-button>
              <el-button v-if="scope.row.content.publish_status === 'published' && scope.row.content.view_url" tag="a" :href="scope.row.content.view_url" target="_blank" rel="noopener noreferrer" link type="success">打开页面</el-button>
              <el-button v-if="canSubmit(scope.row.content)" link type="warning" @click="submit(scope.row.content)">{{ scope.row.content.review_status === 'rejected' ? '重新提交' : '提交发布' }}</el-button>
              <el-button v-if="canDelete(scope.row.content)" link type="danger" @click="remove(scope.row.content)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap"><el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size" :total="total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next" @change="load" /></div>
    </section>
  </div>
</template>

<style scoped>
.title-link { display: block; padding: 0; color: var(--ink); border: 0; background: transparent; cursor: pointer; text-align: left; font-weight: 600; }
.title-link:hover { color: var(--blue); }
.content-node { display: inline-flex; min-width: 0; flex-direction: column; vertical-align: middle; }
.row-alert { display: block; max-width: 260px; margin-top: 4px; overflow: hidden; color: var(--danger); text-overflow: ellipsis; white-space: nowrap; }
.tree-toggle { display: inline-flex; align-items: center; gap: 8px; padding: 2px 0; color: var(--ink); border: 0; background: transparent; cursor: pointer; text-align: left; }
.tree-toggle:hover strong { color: var(--brand-dark); }
.tree-toggle .el-icon { font-size: 17px; }
.target-node .el-icon { color: var(--brand); }
.target-node strong { font-size: 13px; }
.department-node .el-icon { color: #7c8797; }
.department-node strong { color: #4d5868; font-size: 12px; }
.filter-panel :deep(.el-form-item) { margin-bottom: 12px; }
.table-toolbar > .muted { font-size: 11px; }
:deep(.target-row td.el-table__cell) { background: #f6f8f2; }
:deep(.target-row:hover > td.el-table__cell) { background: #f0f4e8 !important; }
:deep(.department-row td.el-table__cell) { background: #fafbf8; }
:deep(.department-row:hover > td.el-table__cell) { background: #f5f7f1 !important; }
</style>
