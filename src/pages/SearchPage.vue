<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Calendar, Link, RefreshRight, Search } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import { searchContents, type SearchQuery } from '@/api/search'
import { getDepartments } from '@/api/departments'
import { getPublishTargets } from '@/api/publishTargets'
import { CONTENT_TYPES } from '@/constants'
import { useCategoryStore } from '@/stores/categories'
import { formatDate } from '@/utils/format'
import type { ContentItem, ContentType } from '@/types/content'
import type { Department } from '@/types/department'
import type { PublishTarget } from '@/types/publish'

const router = useRouter()
const categories = useCategoryStore()
const loading = ref(false)
const searched = ref(false)
const items = ref<ContentItem[]>([])
const total = ref(0)
const dateRange = ref<[string, string]>()
const publishTargets = ref<PublishTarget[]>([])
const departments = ref<Department[]>([])
const query = reactive<SearchQuery>({
  page: 1,
  page_size: 8,
  keyword: '',
  content_type: '',
  category: '',
  publish_target_id: '',
  department: ''
})

async function search() {
  loading.value = true
  query.date_from = dateRange.value?.[0]
  query.date_to = dateRange.value?.[1]
  try {
    const result = await searchContents(query)
    items.value = result.items
    total.value = result.total
    searched.value = true
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '检索失败')
  } finally {
    loading.value = false
  }
}

async function loadFilterOptions() {
  try {
    const [targets, departmentItems] = await Promise.all([getPublishTargets(), getDepartments()])
    publishTargets.value = targets
    departments.value = departmentItems
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '检索条件加载失败')
  }
}

function reset() {
  Object.assign(query, {
    page: 1,
    keyword: '',
    content_type: '',
    category: '',
    publish_target_id: '',
    department: ''
  })
  dateRange.value = undefined
  void search()
}

onMounted(() => {
  void categories.load().catch(() => ElMessage.error('分类加载失败'))
  void loadFilterOptions()
  void search()
})
</script>

<template>
  <div class="page-shell">
    <PageHeader title="内容检索" description="只检索已正式发布且当前账号可访问的内容。" eyebrow="PUBLISHED LIBRARY" />
    <section class="search-console paper-card">
      <div class="search-line">
        <el-input v-model="query.keyword" size="large" clearable placeholder="请输入内容标题或关键词" :prefix-icon="Search" @keyup.enter="query.page = 1; search()" />
        <el-button type="primary" size="large" :icon="Search" @click="query.page = 1; search()">搜索</el-button>
      </div>
      <div class="search-filters">
        <el-select v-model="query.publish_target_id" clearable placeholder="全部发布名称">
          <el-option v-for="target in publishTargets" :key="target.id" :label="target.name" :value="target.id" />
        </el-select>
        <el-select v-model="query.department" clearable placeholder="全部所属部门">
          <el-option v-for="department in departments" :key="department.id" :label="department.name" :value="department.name" />
        </el-select>
        <el-select v-model="query.content_type" clearable placeholder="全部内容类型">
          <el-option v-for="(label, value) in CONTENT_TYPES" :key="value" :label="label" :value="value as ContentType" />
        </el-select>
        <el-select v-model="query.category" clearable placeholder="全部分类">
          <el-option v-for="item in categories.activeNames" :key="item" :label="item" :value="item" />
        </el-select>
        <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD" start-placeholder="发布开始日期" end-placeholder="发布结束日期" :prefix-icon="Calendar" />
        <el-button :icon="RefreshRight" @click="reset">重置</el-button>
      </div>
    </section>
    <div class="result-meta">
      <div><span class="section-kicker">SEARCH RESULT</span><strong>找到 {{ total }} 项已发布内容</strong></div>
      <span>未发布与审核中的内容不会出现在这里</span>
    </div>
    <section v-loading="loading" class="result-list">
      <article v-for="item in items" :key="item.id" class="result-card paper-card">
        <div class="type-rail"><span>{{ item.content_type.toUpperCase() }}</span></div>
        <div class="result-copy">
          <div class="result-top"><span>{{ item.category }}</span><time>{{ formatDate(item.published_at) }}</time></div>
          <h2>{{ item.title }}</h2>
          <p>{{ item.description || '暂无内容简介' }}</p>
          <div class="result-foot">
            <span>发布名称：{{ item.publish_target_name || '未设置' }} · 所属部门：{{ item.creator_department || '未设置' }}</span>
            <div>
              <el-button link @click="router.push(`/contents/${item.id}`)">查看详情</el-button>
              <el-button v-if="item.view_url" tag="a" :href="item.view_url" target="_blank" rel="noopener noreferrer" type="primary" plain size="small" :icon="Link">打开内容</el-button>
            </div>
          </div>
        </div>
      </article>
      <el-empty v-if="searched && !loading && items.length === 0" description="没有找到符合条件的已发布内容" />
    </section>
    <div v-if="total > 0" class="pagination-wrap">
      <el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size" :total="total" :page-sizes="[8, 16, 32]" layout="total, sizes, prev, pager, next" @change="search" />
    </div>
  </div>
</template>

<style scoped>
.search-console { padding: 24px; border-top: 3px solid var(--blue); }
.search-line { display: grid; grid-template-columns: 1fr 110px; gap: 10px; }
.search-line :deep(.el-input__wrapper) { font-size: 15px; }
.search-filters { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 14px; }
.search-filters .el-select { width: 180px; }
.search-filters :deep(.el-date-editor) { width: 320px; }
.result-meta { display: flex; align-items: flex-end; justify-content: space-between; margin: 2px 0 -2px; }
.result-meta div { display: flex; flex-direction: column; gap: 5px; }
.result-meta strong { font-size: 15px; }
.result-meta > span { color: #8d95a4; font-size: 11px; }
.result-list { min-height: 180px; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.result-card { min-width: 0; display: grid; grid-template-columns: 52px 1fr; overflow: hidden; }
.type-rail { display: grid; place-items: center; background: #eef2f6; border-right: 1px solid var(--line); }
.type-rail span { transform: rotate(-90deg); color: #5e718c; font: 10px Bahnschrift, sans-serif; letter-spacing: .14em; white-space: nowrap; }
.result-copy { min-width: 0; padding: 17px 19px 14px; }
.result-top { display: flex; justify-content: space-between; color: #8b94a3; font-size: 11px; }
.result-top > span { color: #876524; }
.result-copy h2 { margin: 12px 0 7px; color: var(--ink); font-size: 16px; }
.result-copy p { height: 42px; margin: 0; overflow: hidden; color: #6d7789; font-size: 12px; line-height: 1.75; }
.result-foot { min-height: 42px; display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; margin-top: 8px; padding-top: 10px; border-top: 1px solid #edf0f3; }
.result-foot > span { color: #8a93a2; font-size: 10px; }
@media (max-width: 980px) { .result-list { grid-template-columns: 1fr; } }
</style>
