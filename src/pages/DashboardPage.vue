<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, DocumentAdd, Reading, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader.vue'
import ContentStatus from '@/components/ContentStatus.vue'
import { getDashboard } from '@/api/dashboard'
import { useAuthStore } from '@/stores/auth'
import { CONTENT_TYPES } from '@/constants'
import { formatDate } from '@/utils/format'
import type { DashboardData } from '@/types/dashboard'
import type { ContentType } from '@/types/content'

const auth = useAuthStore(); const router = useRouter(); const loading = ref(true); const data = ref<DashboardData>()
const contentTypeLabel = (value: ContentType) => CONTENT_TYPES[value]
const stats = computed(() => auth.isAdmin ? [
  { label: '内容总数', value: data.value?.content_total ?? 0, hint: '全平台内容' },
  { label: '待审核', value: data.value?.pending_review ?? 0, hint: '需要处理', tone: 'warning' },
  { label: '已发布', value: data.value?.published ?? 0, hint: '当前可访问', tone: 'success' },
  { label: '发布失败', value: data.value?.publish_failed ?? 0, hint: '等待重试', tone: 'danger' }
] : [
  { label: '我的内容', value: data.value?.my_content_total ?? 0, hint: '个人内容' },
  { label: '待审核', value: data.value?.pending_review ?? 0, hint: '审批进行中', tone: 'warning' },
  { label: '已发布', value: data.value?.published ?? 0, hint: '当前可访问', tone: 'success' },
  { label: '已驳回', value: data.value?.rejected ?? 0, hint: '需要修改', tone: 'danger' }
])
onMounted(async () => { try { data.value = await getDashboard() } catch (e) { ElMessage.error(e instanceof Error ? e.message : '首页数据加载失败') } finally { loading.value = false } })
</script>
<template>
  <div class="page-shell" v-loading="loading">
    <PageHeader :title="`${auth.user?.name}，上午好`" :description="auth.isAdmin ? '这里是今天的内容发布概况与待办。' : '继续处理你的内容，或检索已正式发布的资料。'" eyebrow="OVERVIEW" />
    <div class="stats-grid responsive-grid">
      <article v-for="(stat, index) in stats" :key="stat.label" class="stat-card paper-card" :class="stat.tone"><div class="stat-head"><span>{{ stat.label }}</span><i>0{{ index + 1 }}</i></div><strong>{{ stat.value }}</strong><small>{{ stat.hint }}</small></article>
    </div>
    <div class="quick-strip paper-card">
      <div><span class="section-kicker">QUICK ACTIONS</span><strong>快捷操作</strong></div>
      <button type="button" @click="router.push('/contents/new')"><el-icon><DocumentAdd /></el-icon>新建内容<ArrowRight /></button>
      <button v-if="auth.isAdmin" type="button" @click="router.push('/reviews')"><el-icon><Reading /></el-icon>查看待审核<ArrowRight /></button>
      <button v-else type="button" @click="router.push('/contents')"><el-icon><Reading /></el-icon>我的内容<ArrowRight /></button>
      <button type="button" @click="router.push('/search')"><el-icon><Search /></el-icon>内容检索<ArrowRight /></button>
    </div>
    <div class="dashboard-grid">
      <section class="paper-card data-section"><div class="section-head"><div><span class="section-kicker">RECENT INPUT</span><h2>{{ auth.isAdmin ? '最近提交' : '最近编辑' }}</h2></div><el-button link type="primary" @click="router.push('/contents')">查看全部</el-button></div>
        <el-table :data="data?.recent_submissions || []" empty-text="暂无内容"><el-table-column prop="title" label="标题" min-width="180"><template #default="scope"><button class="title-link" @click="router.push(`/contents/${scope.row.id}`)">{{ scope.row.title }}</button></template></el-table-column><el-table-column v-if="auth.isAdmin" prop="creator_name" label="提交人" width="100" /><el-table-column label="类型" width="105"><template #default="scope">{{ contentTypeLabel(scope.row.content_type) }}</template></el-table-column><el-table-column label="更新时间" width="150"><template #default="scope">{{ formatDate(scope.row.updated_at) }}</template></el-table-column><el-table-column label="状态" width="90"><template #default="scope"><ContentStatus kind="review" :status="scope.row.review_status" /></template></el-table-column></el-table>
      </section>
      <section class="paper-card data-section"><div class="section-head"><div><span class="section-kicker">RECENT OUTPUT</span><h2>最近发布</h2></div><el-button link type="primary" @click="router.push('/search')">去检索</el-button></div>
        <el-table :data="data?.recent_publishes || []" empty-text="暂无已发布内容"><el-table-column prop="title" label="标题" min-width="170" /><el-table-column label="类型" width="100"><template #default="scope">{{ contentTypeLabel(scope.row.content_type) }}</template></el-table-column><el-table-column label="发布时间" width="150"><template #default="scope">{{ formatDate(scope.row.published_at) }}</template></el-table-column><el-table-column label="状态" width="85"><template #default="scope"><ContentStatus kind="publish" :status="scope.row.publish_status" /></template></el-table-column></el-table>
      </section>
    </div>
  </div>
</template>
<style scoped>
.stats-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }.stat-card { position: relative; min-height: 128px; padding: 18px 20px; border-top: 3px solid #6e7b90; }.stat-card.warning { border-top-color: #c28a36; }.stat-card.success { border-top-color: #348067; }.stat-card.danger { border-top-color: #bb5753; }.stat-head { display: flex; justify-content: space-between; color: #5f697a; font-size: 13px; }.stat-head i { color: #b5bbc5; font: 11px Bahnschrift, sans-serif; font-style: normal; }.stat-card > strong { display: inline-block; margin-top: 12px; color: var(--ink); font: 34px/1 Bahnschrift, sans-serif; }.stat-card small { margin-left: 10px; color: #9aa2b0; }
.quick-strip { min-height: 76px; display: grid; grid-template-columns: 1.2fr repeat(3, 1fr); align-items: center; padding: 10px 18px; }.quick-strip > div { display: flex; flex-direction: column; gap: 4px; }.quick-strip > div strong { font-size: 14px; }.quick-strip button { height: 42px; display: flex; align-items: center; gap: 9px; padding: 0 18px; border: 0; border-left: 1px solid var(--line); color: #3d485a; background: transparent; cursor: pointer; }.quick-strip button:hover { color: var(--blue); background: #f8f9fb; }.quick-strip button svg:last-child { width: 13px; margin-left: auto; }
.dashboard-grid { display: grid; grid-template-columns: 1.15fr .85fr; gap: 16px; }.data-section { min-width: 0; padding: 0 17px 16px; }.section-head { min-height: 69px; display: flex; align-items: center; justify-content: space-between; }.section-head h2 { margin: 4px 0 0; font-size: 16px; }.title-link { padding: 0; color: var(--ink); border: 0; background: transparent; cursor: pointer; text-align: left; }.title-link:hover { color: var(--blue); }
</style>
