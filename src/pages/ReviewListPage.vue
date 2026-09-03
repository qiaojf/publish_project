<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { RefreshRight, Search } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import ContentStatus from '@/components/ContentStatus.vue'
import { getReviews } from '@/api/reviews'
import { CATEGORIES, CONTENT_TYPES } from '@/constants'
import { formatDate } from '@/utils/format'
import type { ContentItem, ContentType } from '@/types/content'
import type { ReviewQuery } from '@/types/review'

const router = useRouter(); const loading = ref(false); const items = ref<ContentItem[]>([]); const total = ref(0); const dateRange = ref<[string, string]>()
const query = reactive<ReviewQuery>({ page: 1, page_size: 10, status: 'pending', keyword: '', content_type: '', category: '', submitted_by: '' })
const contentTypeLabel = (value: ContentType) => CONTENT_TYPES[value]
async function load() { loading.value = true; query.date_from = dateRange.value?.[0]; query.date_to = dateRange.value?.[1]; try { const result = await getReviews(query); items.value = result.items; total.value = result.total } catch (e) { ElMessage.error(e instanceof Error ? e.message : '审核列表加载失败') } finally { loading.value = false } }
function reset() { Object.assign(query, { page: 1, keyword: '', content_type: '', category: '', submitted_by: '', status: 'pending' }); dateRange.value = undefined; load() }
onMounted(load)
</script>
<template>
  <div class="page-shell">
    <PageHeader title="审核管理" description="集中处理员工提交的发布申请。默认显示待审核内容。" eyebrow="REVIEW QUEUE" />
    <section class="queue-banner paper-card"><div><span class="queue-number">{{ total }}</span><span><strong>项待审核</strong><small>审核通过后将立即触发后端自动发布</small></span></div><i>QUEUE / PENDING</i></section>
    <section class="paper-card filter-panel"><el-form inline><el-form-item label="关键词"><el-input v-model="query.keyword" clearable placeholder="内容标题" /></el-form-item><el-form-item label="内容类型"><el-select v-model="query.content_type" clearable placeholder="全部类型" style="width:150px"><el-option v-for="(label, value) in CONTENT_TYPES" :key="value" :label="label" :value="value as ContentType" /></el-select></el-form-item><el-form-item label="分类"><el-select v-model="query.category" clearable placeholder="全部分类" style="width:130px"><el-option v-for="item in CATEGORIES" :key="item" :label="item" :value="item" /></el-select></el-form-item><el-form-item label="提交人"><el-input v-model="query.submitted_by" clearable placeholder="姓名" style="width:120px" /></el-form-item><el-form-item label="提交日期"><el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD" start-placeholder="开始日期" end-placeholder="结束日期" style="width:240px" /></el-form-item><el-form-item><el-button type="primary" :icon="Search" @click="query.page = 1; load()">查询</el-button><el-button :icon="RefreshRight" @click="reset">重置</el-button></el-form-item></el-form></section>
    <section class="paper-card table-panel"><div class="table-toolbar"><span class="table-count">待审核内容按提交时间倒序排列</span></div><el-table v-loading="loading" :data="items"><el-table-column prop="title" label="标题" min-width="230" /><el-table-column label="类型" width="130"><template #default="scope">{{ contentTypeLabel(scope.row.content_type) }}</template></el-table-column><el-table-column prop="category" label="分类" width="110" /><el-table-column prop="creator_name" label="提交人" width="110" /><el-table-column label="提交时间" width="160"><template #default="scope">{{ formatDate(scope.row.submitted_at) }}</template></el-table-column><el-table-column prop="publish_target_name" label="目标发布位置" min-width="150" /><el-table-column label="状态" width="100"><template #default="scope"><ContentStatus kind="review" :status="scope.row.review_status" /></template></el-table-column><el-table-column label="操作" width="130" fixed="right"><template #default="scope"><el-button link @click="router.push(`/contents/${scope.row.id}`)">查看</el-button><el-button link type="primary" @click="router.push(`/reviews/${scope.row.id}`)">审核</el-button></template></el-table-column></el-table><div class="pagination-wrap"><el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size" :total="total" layout="total, sizes, prev, pager, next" @change="load" /></div></section>
  </div>
</template>
<style scoped>
.queue-banner { min-height: 90px; display: flex; align-items: center; justify-content: space-between; padding: 14px 22px; border-left: 4px solid var(--accent); background: #fffdfa; }.queue-banner > div { display: flex; align-items: center; gap: 16px; }.queue-number { color: var(--accent); font: 40px Bahnschrift, sans-serif; }.queue-banner div span:last-child { display: flex; flex-direction: column; gap: 4px; }.queue-banner strong { font-size: 14px; }.queue-banner small { color: #8b94a3; }.queue-banner > i { color: #b9a98e; font: 10px Bahnschrift, sans-serif; font-style: normal; letter-spacing: .15em; }.filter-panel :deep(.el-form-item) { margin-bottom: 12px; }
</style>
