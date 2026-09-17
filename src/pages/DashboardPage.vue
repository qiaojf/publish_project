<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ArrowRight, DocumentAdd, Reading, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import ContentStatus from '@/components/ContentStatus.vue'
import { getDashboard } from '@/api/dashboard'
import { getRequestErrorMessage } from '@/api/request'
import { useAuthStore } from '@/stores/auth'
import { CONTENT_TYPES } from '@/constants'
import { formatDate } from '@/utils/format'
import type { DashboardData } from '@/types/dashboard'
import type { ContentType } from '@/types/content'

const auth = useAuthStore(); const router = useRouter(); const loading = ref(true); const data = ref<DashboardData>()
const { t } = useI18n()
const contentTypeLabel = (value: ContentType) => t(CONTENT_TYPES[value])
const stats = computed(() => auth.isAdmin ? [
  { label: t('dashboard.totalContent'), value: data.value?.content_total ?? 0, hint: t('dashboard.platformContent') },
  { label: t('status.review.pending'), value: data.value?.pending_review ?? 0, hint: t('dashboard.needsAction'), tone: 'warning' },
  { label: t('status.publish.published'), value: data.value?.published ?? 0, hint: t('dashboard.availableNow'), tone: 'success' },
  { label: t('status.publish.failed'), value: data.value?.publish_failed ?? 0, hint: t('dashboard.awaitingRetry'), tone: 'danger' }
] : [
  { label: t('nav.myContents'), value: data.value?.my_content_total ?? 0, hint: t('dashboard.personalContent') },
  { label: t('status.review.pending'), value: data.value?.pending_review ?? 0, hint: t('dashboard.reviewInProgress'), tone: 'warning' },
  { label: t('status.publish.published'), value: data.value?.published ?? 0, hint: t('dashboard.availableNow'), tone: 'success' },
  { label: t('status.review.rejected'), value: data.value?.rejected ?? 0, hint: t('dashboard.needsRevision'), tone: 'danger' }
])
onMounted(async () => { try { data.value = await getDashboard() } catch (e) { ElMessage.error(getRequestErrorMessage(e, 'dashboard.loadFailed')) } finally { loading.value = false } })
</script>
<template>
  <div class="page-shell" v-loading="loading">
    <PageHeader :title="t('dashboard.greeting', { name: auth.user?.name || '' })" :description="t(auth.isAdmin ? 'dashboard.adminDescription' : 'dashboard.employeeDescription')" :eyebrow="t('kicker.overview')" />
    <div class="stats-grid responsive-grid">
      <article v-for="(stat, index) in stats" :key="stat.label" class="stat-card paper-card" :class="stat.tone"><div class="stat-head"><span>{{ stat.label }}</span><i>0{{ index + 1 }}</i></div><strong>{{ stat.value }}</strong><small>{{ stat.hint }}</small></article>
    </div>
    <div class="quick-strip paper-card">
      <div><span class="section-kicker">{{ t('kicker.quickActions') }}</span><strong>{{ t('dashboard.quickActions') }}</strong></div>
      <button type="button" @click="router.push('/contents/new')"><el-icon><DocumentAdd /></el-icon>{{ t('content.create') }}<ArrowRight /></button>
      <button v-if="auth.isAdmin" type="button" @click="router.push('/reviews')"><el-icon><Reading /></el-icon>{{ t('dashboard.viewPending') }}<ArrowRight /></button>
      <button v-else type="button" @click="router.push('/contents')"><el-icon><Reading /></el-icon>{{ t('nav.myContents') }}<ArrowRight /></button>
      <button type="button" @click="router.push('/search')"><el-icon><Search /></el-icon>{{ t('nav.search') }}<ArrowRight /></button>
    </div>
    <div class="dashboard-grid">
      <section class="paper-card data-section"><div class="section-head"><div><span class="section-kicker">{{ t('kicker.recentInput') }}</span><h2>{{ t(auth.isAdmin ? 'dashboard.recentSubmissions' : 'dashboard.recentEdits') }}</h2></div><el-button link type="primary" @click="router.push('/contents')">{{ t('common.viewAll') }}</el-button></div>
        <el-table :data="data?.recent_submissions || []" :empty-text="t('common.noContent')"><el-table-column prop="title" :label="t('content.title')" min-width="180"><template #default="scope"><button class="title-link" @click="router.push(`/contents/${scope.row.id}`)">{{ scope.row.title }}</button></template></el-table-column><el-table-column v-if="auth.isAdmin" prop="creator_name" :label="t('review.submitter')" width="100" /><el-table-column :label="t('common.type')" width="105"><template #default="scope">{{ contentTypeLabel(scope.row.content_type) }}</template></el-table-column><el-table-column :label="t('common.updatedAt')" width="150"><template #default="scope">{{ formatDate(scope.row.updated_at) }}</template></el-table-column><el-table-column :label="t('common.status')" width="90"><template #default="scope"><ContentStatus kind="review" :status="scope.row.review_status" /></template></el-table-column></el-table>
      </section>
      <section class="paper-card data-section"><div class="section-head"><div><span class="section-kicker">{{ t('kicker.recentOutput') }}</span><h2>{{ t('dashboard.recentPublishes') }}</h2></div><el-button link type="primary" @click="router.push('/search')">{{ t('dashboard.goSearch') }}</el-button></div>
        <el-table :data="data?.recent_publishes || []" :empty-text="t('dashboard.noPublished')"><el-table-column prop="title" :label="t('content.title')" min-width="170" /><el-table-column :label="t('common.type')" width="100"><template #default="scope">{{ contentTypeLabel(scope.row.content_type) }}</template></el-table-column><el-table-column :label="t('content.publishedAt')" width="150"><template #default="scope">{{ formatDate(scope.row.published_at) }}</template></el-table-column><el-table-column :label="t('common.status')" width="85"><template #default="scope"><ContentStatus kind="publish" :status="scope.row.publish_status" /></template></el-table-column></el-table>
      </section>
    </div>
  </div>
</template>
<style scoped>
.stats-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }.stat-card { position: relative; min-height: 128px; padding: 18px 20px; border-top: 3px solid #6e7b90; }.stat-card.warning { border-top-color: #c28a36; }.stat-card.success { border-top-color: #348067; }.stat-card.danger { border-top-color: #bb5753; }.stat-head { display: flex; justify-content: space-between; color: #5f697a; font-size: 13px; }.stat-head i { color: #b5bbc5; font: 11px Bahnschrift, sans-serif; font-style: normal; }.stat-card > strong { display: inline-block; margin-top: 12px; color: var(--ink); font: 34px/1 Bahnschrift, sans-serif; }.stat-card small { margin-left: 10px; color: #9aa2b0; }
.quick-strip { min-height: 76px; display: grid; grid-template-columns: 1.2fr repeat(3, 1fr); align-items: center; padding: 10px 18px; }.quick-strip > div { display: flex; flex-direction: column; gap: 4px; }.quick-strip > div strong { font-size: 14px; }.quick-strip button { height: 42px; display: flex; align-items: center; gap: 9px; padding: 0 18px; border: 0; border-left: 1px solid var(--line); color: #3d485a; background: transparent; cursor: pointer; }.quick-strip button:hover { color: var(--blue); background: #f8f9fb; }.quick-strip button svg:last-child { width: 13px; margin-left: auto; }
.dashboard-grid { display: grid; grid-template-columns: 1.15fr .85fr; gap: 16px; }.data-section { min-width: 0; padding: 0 17px 16px; }.section-head { min-height: 69px; display: flex; align-items: center; justify-content: space-between; }.section-head h2 { margin: 4px 0 0; font-size: 16px; }.title-link { padding: 0; color: var(--ink); border: 0; background: transparent; cursor: pointer; text-align: left; }.title-link:hover { color: var(--blue); }
</style>
