<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, RefreshRight, Search } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import ContentStatus from '@/components/ContentStatus.vue'
import { CONTENT_TYPES, PUBLISH_STATUS, REVIEW_STATUS } from '@/constants'
import { deleteContent, getContents, republishContent, submitContent } from '@/api/contents'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/categories'
import { formatDate } from '@/utils/format'
import type { ContentItem, ContentQuery, ContentType, PublishStatus, ReviewStatus } from '@/types/content'

const auth = useAuthStore(); const categories = useCategoryStore(); const router = useRouter(); const loading = ref(false); const total = ref(0); const items = ref<ContentItem[]>([])
const query = reactive<ContentQuery>({ page: 1, page_size: 10, keyword: '', content_type: '', category: '', review_status: '', publish_status: '' })
const contentTypeLabel = (value: ContentType) => CONTENT_TYPES[value]
async function load() { loading.value = true; try { const result = await getContents(query); items.value = result.items; total.value = result.total } catch (e) { ElMessage.error(e instanceof Error ? e.message : '内容加载失败') } finally { loading.value = false } }
function reset() { Object.assign(query, { page: 1, keyword: '', content_type: '', category: '', review_status: '', publish_status: '' }); load() }
async function remove(item: ContentItem) { try { await ElMessageBox.confirm(`删除“${item.title}”后无法恢复，确认继续吗？`, '删除内容', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }); await deleteContent(item.id); ElMessage.success('内容已删除'); load() } catch (e) { if (e instanceof Error) ElMessage.error(e.message) } }
async function submit(item: ContentItem) { try { await submitContent(item.id); ElMessage.success('已提交发布审核'); load() } catch (e) { ElMessage.error(e instanceof Error ? e.message : '提交失败') } }
async function republish(item: ContentItem) { try { await ElMessageBox.confirm('确认重新执行发布吗？该操作不会重新审核。', '重新发布', { confirmButtonText: '重新发布', cancelButtonText: '取消' }); await republishContent(item.id); ElMessage.success('重新发布成功'); load() } catch (e) { if (e instanceof Error) ElMessage.error(e.message) } }
function canEdit(item: ContentItem) { return auth.isAdmin || (item.created_by === auth.user?.id && item.review_status !== 'pending' && item.publish_status !== 'published') }
function canDelete(item: ContentItem) { return auth.isAdmin || (item.created_by === auth.user?.id && item.review_status !== 'pending' && item.publish_status !== 'published') }
function canSubmit(item: ContentItem) { return !auth.isAdmin && ['draft', 'rejected'].includes(item.review_status) }
onMounted(() => { void categories.load().catch(() => ElMessage.error('分类加载失败')); void load() })
</script>
<template>
  <div class="page-shell">
    <PageHeader :title="auth.isAdmin ? '内容管理' : '我的内容'" :description="auth.isAdmin ? '管理全平台内容，追踪审核与发布状态。' : '创建内容、提交审核并跟踪发布结果。'" eyebrow="CONTENT REGISTER"><template #actions><el-button type="primary" :icon="Plus" @click="router.push('/contents/new')">新建内容</el-button></template></PageHeader>
    <section class="paper-card filter-panel"><el-form inline :model="query"><el-form-item label="关键词"><el-input v-model="query.keyword" clearable placeholder="标题或简介" @keyup.enter="query.page = 1; load()" /></el-form-item><el-form-item label="内容类型"><el-select v-model="query.content_type" clearable placeholder="全部类型" style="width:150px"><el-option v-for="(label, value) in CONTENT_TYPES" :key="value" :label="label" :value="value as ContentType" /></el-select></el-form-item><el-form-item label="分类"><el-select v-model="query.category" clearable placeholder="全部分类" style="width:130px"><el-option v-for="item in categories.activeNames" :key="item" :label="item" :value="item" /></el-select></el-form-item><el-form-item label="审核状态"><el-select v-model="query.review_status" clearable placeholder="全部" style="width:120px"><el-option v-for="(label, value) in REVIEW_STATUS" :key="value" :label="label" :value="value as ReviewStatus" /></el-select></el-form-item><el-form-item label="发布状态"><el-select v-model="query.publish_status" clearable placeholder="全部" style="width:120px"><el-option v-for="(label, value) in PUBLISH_STATUS" :key="value" :label="label" :value="value as PublishStatus" /></el-select></el-form-item><el-form-item><el-button type="primary" :icon="Search" @click="query.page = 1; load()">查询</el-button><el-button :icon="RefreshRight" @click="reset">重置</el-button></el-form-item></el-form></section>
    <section class="paper-card table-panel"><div class="table-toolbar"><span class="table-count">共 {{ total }} 条内容</span><span class="muted">{{ auth.isAdmin ? '显示所有创建人的内容' : '仅显示你创建的内容' }}</span></div>
      <el-table v-loading="loading" :data="items"><el-table-column prop="title" label="标题" min-width="210" show-overflow-tooltip><template #default="scope"><button class="title-link" @click="router.push(`/contents/${scope.row.id}`)">{{ scope.row.title }}</button><small v-if="scope.row.failure_reason" class="row-alert">{{ scope.row.failure_reason }}</small></template></el-table-column><el-table-column label="类型" width="130"><template #default="scope">{{ contentTypeLabel(scope.row.content_type) }}</template></el-table-column><el-table-column prop="category" label="分类" width="105" /><el-table-column v-if="auth.isAdmin" prop="creator_name" label="创建人" width="100" /><el-table-column label="审核状态" width="100"><template #default="scope"><ContentStatus kind="review" :status="scope.row.review_status" /></template></el-table-column><el-table-column label="发布状态" width="100"><template #default="scope"><ContentStatus kind="publish" :status="scope.row.publish_status" /></template></el-table-column><el-table-column label="更新时间" width="155"><template #default="scope">{{ formatDate(scope.row.updated_at) }}</template></el-table-column><el-table-column label="操作" width="250" fixed="right"><template #default="scope"><el-button link type="primary" @click="router.push(`/contents/${scope.row.id}`)">查看</el-button><el-button v-if="canEdit(scope.row)" link type="primary" @click="router.push(`/contents/${scope.row.id}/edit`)">编辑</el-button><el-button v-if="auth.isAdmin && scope.row.review_status === 'pending'" link type="warning" @click="router.push(`/reviews/${scope.row.id}`)">审核</el-button><el-button v-if="scope.row.publish_status === 'failed' && auth.isAdmin" link type="warning" @click="republish(scope.row)">重新发布</el-button><el-button v-if="scope.row.publish_status === 'published' && scope.row.view_url" tag="a" :href="scope.row.view_url" target="_blank" rel="noopener noreferrer" link type="success">打开页面</el-button><el-button v-if="canSubmit(scope.row)" link type="warning" @click="submit(scope.row)">{{ scope.row.review_status === 'rejected' ? '重新提交' : '提交发布' }}</el-button><el-button v-if="canDelete(scope.row)" link type="danger" @click="remove(scope.row)">删除</el-button></template></el-table-column></el-table>
      <div class="pagination-wrap"><el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size" :total="total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next" @change="load" /></div>
    </section>
  </div>
</template>
<style scoped>
.title-link { display: block; padding: 0; color: var(--ink); border: 0; background: transparent; cursor: pointer; text-align: left; font-weight: 600; }.title-link:hover { color: var(--blue); }.row-alert { display: block; max-width: 260px; margin-top: 4px; overflow: hidden; color: var(--danger); text-overflow: ellipsis; white-space: nowrap; }.filter-panel :deep(.el-form-item) { margin-bottom: 12px; }.table-toolbar > .muted { font-size: 11px; }
</style>
