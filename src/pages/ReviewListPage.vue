<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { RefreshRight, Search } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import ContentStatus from '@/components/ContentStatus.vue'
import { getReviews } from '@/api/reviews'
import { getRequestErrorMessage } from '@/api/request'
import { CONTENT_TYPES } from '@/constants'
import { useCategoryStore } from '@/stores/categories'
import { formatDate } from '@/utils/format'
import type { ContentItem, ContentType } from '@/types/content'
import type { ReviewQuery } from '@/types/review'

const router = useRouter(); const categories = useCategoryStore(); const loading = ref(false); const items = ref<ContentItem[]>([]); const total = ref(0); const dateRange = ref<[string, string]>()
const { t } = useI18n()
const query = reactive<ReviewQuery>({ page: 1, page_size: 10, status: 'pending', keyword: '', content_type: '', category: '', submitted_by: '' })
const contentTypeLabel = (value: ContentType) => t(CONTENT_TYPES[value])
async function load() { loading.value = true; query.date_from = dateRange.value?.[0]; query.date_to = dateRange.value?.[1]; try { const result = await getReviews(query); items.value = result.items; total.value = result.total } catch (e) { ElMessage.error(getRequestErrorMessage(e, 'review.listLoadFailed')) } finally { loading.value = false } }
function reset() { Object.assign(query, { page: 1, keyword: '', content_type: '', category: '', submitted_by: '', status: 'pending' }); dateRange.value = undefined; load() }
onMounted(() => { void categories.load().catch(() => ElMessage.error(t('category.loadFailed'))); void load() })
</script>
<template>
  <div class="page-shell">
    <PageHeader :title="t('nav.reviews')" :description="t('review.listDescription')" :eyebrow="t('kicker.reviewQueue')" />
    <section class="queue-banner paper-card"><div><span class="queue-number">{{ total }}</span><span><strong>{{ t('review.pendingItems') }}</strong><small>{{ t('review.autoPublishHint') }}</small></span></div><i>{{ t('kicker.queuePending') }}</i></section>
    <section class="paper-card filter-panel"><el-form inline><el-form-item :label="t('common.keyword')"><el-input v-model="query.keyword" clearable :placeholder="t('content.title')" /></el-form-item><el-form-item :label="t('content.contentType')"><el-select v-model="query.content_type" clearable :placeholder="t('common.allTypes')" style="width:150px"><el-option v-for="(label, value) in CONTENT_TYPES" :key="value" :label="t(label)" :value="value as ContentType" /></el-select></el-form-item><el-form-item :label="t('content.category')"><el-select v-model="query.category" clearable :placeholder="t('common.allCategories')" style="width:130px"><el-option v-for="item in categories.activeNames" :key="item" :label="item" :value="item" /></el-select></el-form-item><el-form-item :label="t('review.submitter')"><el-input v-model="query.submitted_by" clearable :placeholder="t('user.name')" style="width:120px" /></el-form-item><el-form-item :label="t('review.submittedDate')"><el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD" :start-placeholder="t('common.startDate')" :end-placeholder="t('common.endDate')" style="width:240px" /></el-form-item><el-form-item><el-button type="primary" :icon="Search" @click="query.page = 1; load()">{{ t('common.query') }}</el-button><el-button :icon="RefreshRight" @click="reset">{{ t('common.reset') }}</el-button></el-form-item></el-form></section>
    <section class="paper-card table-panel"><div class="table-toolbar"><span class="table-count">{{ t('review.orderHint') }}</span></div><el-table v-loading="loading" :data="items"><el-table-column prop="title" :label="t('content.title')" min-width="230" /><el-table-column :label="t('common.type')" width="130"><template #default="scope">{{ contentTypeLabel(scope.row.content_type) }}</template></el-table-column><el-table-column prop="category" :label="t('content.category')" width="110" /><el-table-column prop="creator_name" :label="t('review.submitter')" width="110" /><el-table-column :label="t('content.submittedAt')" width="160"><template #default="scope">{{ formatDate(scope.row.submitted_at) }}</template></el-table-column><el-table-column prop="publish_target_name" :label="t('review.targetLocation')" min-width="150" /><el-table-column :label="t('common.status')" width="100"><template #default="scope"><ContentStatus kind="review" :status="scope.row.review_status" /></template></el-table-column><el-table-column :label="t('common.actions')" width="130" fixed="right"><template #default="scope"><el-button link @click="router.push(`/contents/${scope.row.id}`)">{{ t('common.view') }}</el-button><el-button link type="primary" @click="router.push(`/reviews/${scope.row.id}`)">{{ t('common.review') }}</el-button></template></el-table-column></el-table><div class="pagination-wrap"><el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size" :total="total" layout="total, sizes, prev, pager, next" @change="load" /></div></section>
  </div>
</template>
<style scoped>
.queue-banner { min-height: 90px; display: flex; align-items: center; justify-content: space-between; padding: 14px 22px; border-left: 4px solid var(--accent); background: #fffdfa; }.queue-banner > div { display: flex; align-items: center; gap: 16px; }.queue-number { color: var(--accent); font: 40px Bahnschrift, sans-serif; }.queue-banner div span:last-child { display: flex; flex-direction: column; gap: 4px; }.queue-banner strong { font-size: 14px; }.queue-banner small { color: #8b94a3; }.queue-banner > i { color: #b9a98e; font: 10px Bahnschrift, sans-serif; font-style: normal; letter-spacing: .15em; }.filter-panel :deep(.el-form-item) { margin-bottom: 12px; }
</style>
