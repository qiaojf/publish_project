<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, Link, Promotion, RefreshRight } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import ContentStatus from '@/components/ContentStatus.vue'
import ContentPreview from '@/components/ContentPreview.vue'
import PublishFlow from '@/components/PublishFlow.vue'
import { getContent, getContentPreview, republishContent, submitContent } from '@/api/contents'
import { CONTENT_TYPES } from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { formatDate, formatFileSize } from '@/utils/format'
import type { ContentItem, PreviewData } from '@/types/content'

const route = useRoute(); const router = useRouter(); const auth = useAuthStore(); const id = Number(route.params.id); const loading = ref(true); const previewLoading = ref(true); const content = ref<ContentItem>(); const preview = ref<PreviewData>()
let publishPoll: ReturnType<typeof setTimeout> | undefined
const canEdit = computed(() => content.value && (auth.isAdmin || (content.value.created_by === auth.user?.id && content.value.review_status !== 'pending' && content.value.publish_status !== 'published')))
const canSubmit = computed(() => !auth.isAdmin && content.value && ['draft', 'rejected'].includes(content.value.review_status))
async function loadContent(showLoading = true) { if (showLoading) loading.value = true; try { content.value = await getContent(id) } catch (e) { if (showLoading) ElMessage.error(e instanceof Error ? e.message : '内容加载失败') } finally { if (showLoading) loading.value = false } }
async function load() { await loadContent(); previewLoading.value = true; try { preview.value = await getContentPreview(id) } finally { previewLoading.value = false } }
async function pollPublishStatus() {
  if (route.query.publishing !== '1') return
  await loadContent(false)
  if (!content.value || ['unpublished', 'publishing'].includes(content.value.publish_status)) {
    publishPoll = setTimeout(pollPublishStatus, 2500)
    return
  }
  const { publishing: _publishing, ...query } = route.query
  void _publishing
  await router.replace({ query })
  if (content.value.publish_status === 'published') ElMessage.success('内容已发布')
  else ElMessage.error(content.value.failure_reason || '发布失败，请检查发布记录')
}
async function submit() { try { await submitContent(id); ElMessage.success('已提交发布审核'); load() } catch (e) { ElMessage.error(e instanceof Error ? e.message : '提交失败') } }
async function republish() { try { await ElMessageBox.confirm('确认重新执行发布吗？审核状态将保持通过。', '重新发布', { confirmButtonText: '重新发布', cancelButtonText: '取消' }); await republishContent(id); ElMessage.success('重新发布成功'); load() } catch (e) { if (e instanceof Error) ElMessage.error(e.message) } }
onMounted(async () => { await load(); await pollPublishStatus() })
onBeforeUnmount(() => { if (publishPoll) clearTimeout(publishPoll) })
</script>
<template>
  <div class="page-shell" v-loading="loading">
    <PageHeader :title="content?.title || '内容详情'" :description="content?.description ?? undefined" eyebrow="CONTENT RECORD"><template #actions><el-button :icon="ArrowLeft" @click="router.back()">返回</el-button><el-button v-if="canEdit" :icon="Edit" @click="router.push(`/contents/${id}/edit`)">编辑</el-button><el-button v-if="canSubmit" type="primary" :icon="Promotion" @click="submit">{{ content?.review_status === 'rejected' ? '重新提交' : '提交发布' }}</el-button><el-button v-if="auth.isAdmin && content?.review_status === 'pending'" type="primary" @click="router.push(`/reviews/${id}`)">进入审核</el-button><el-button v-if="auth.isAdmin && content?.publish_status === 'failed'" type="warning" :icon="RefreshRight" @click="republish">重新发布</el-button><el-button v-if="content?.publish_status === 'published' && content.view_url" tag="a" :href="content.view_url" target="_blank" rel="noopener noreferrer" type="success" :icon="Link">打开内容</el-button></template></PageHeader>
    <PublishFlow v-if="content" :content="content" />
    <el-alert v-if="route.query.publishing === '1' && ['unpublished', 'publishing'].includes(content?.publish_status || '')" title="正在发布内容" description="页面已跳转，后端正在上传并等待目标部署完成；状态会自动刷新。" type="info" :closable="false" show-icon />
    <el-alert v-if="content?.review_status === 'rejected'" title="审核已驳回" type="error" :closable="false" show-icon><template #default>{{ content.reject_reason }}</template></el-alert>
    <el-alert v-if="content?.publish_status === 'failed'" title="审核已通过，但自动发布失败" type="error" :closable="false" show-icon><template #default>{{ content.failure_reason }}<span v-if="auth.isAdmin"> 可使用“重新发布”再次执行发布，无需重新审核。</span></template></el-alert>
    <div v-if="content" class="detail-grid">
      <div class="main-column stack-12">
        <section class="paper-card detail-section"><div class="section-head"><span class="section-kicker">INFORMATION</span><h2>基本信息</h2></div><el-descriptions :column="2" border><el-descriptions-item label="内容类型">{{ CONTENT_TYPES[content.content_type] }}</el-descriptions-item><el-descriptions-item label="分类">{{ content.category }}</el-descriptions-item><el-descriptions-item label="创建人">{{ content.creator_name }}</el-descriptions-item><el-descriptions-item label="原始文件">{{ content.source_is_directory || (content.files?.length || 0) > 1 ? `${content.files?.length || 0} 个文件 / 文件夹` : content.file_name || content.files?.[0]?.name || '页面内容' }}<span v-if="content.file_size" class="muted"> · {{ formatFileSize(content.file_size) }}</span></el-descriptions-item><el-descriptions-item label="创建时间">{{ formatDate(content.created_at) }}</el-descriptions-item><el-descriptions-item label="更新时间">{{ formatDate(content.updated_at) }}</el-descriptions-item></el-descriptions></section>
        <section class="paper-card detail-section"><div class="section-head"><span class="section-kicker">PREVIEW</span><h2>内容预览</h2></div><ContentPreview :content-id="id" :preview="preview" :loading="previewLoading" /></section>
      </div>
      <aside class="stack-12">
        <section class="paper-card detail-section"><div class="section-head"><span class="section-kicker">STATUS</span><h2>状态信息</h2></div><dl class="status-list"><div><dt>审核状态</dt><dd><ContentStatus kind="review" :status="content.review_status" /></dd></div><div><dt>发布状态</dt><dd><ContentStatus kind="publish" :status="content.publish_status" /></dd></div><div><dt>发布目标</dt><dd>{{ content.publish_target_name || '未选择' }}</dd></div><div><dt>提交时间</dt><dd>{{ formatDate(content.submitted_at) }}</dd></div><div><dt>发布时间</dt><dd>{{ formatDate(content.published_at) }}</dd></div></dl></section>
        <section v-if="content.view_url" class="paper-card url-card"><span class="section-kicker">PUBLISHED URL</span><strong>正式访问地址</strong><a :href="content.view_url" target="_blank" rel="noopener noreferrer" class="mono">{{ content.view_url }}</a><el-button tag="a" :href="content.view_url" target="_blank" rel="noopener noreferrer" type="primary" plain :icon="Link">在新窗口打开</el-button></section>
      </aside>
    </div>
  </div>
</template>
<style scoped>
.detail-grid { display: grid; grid-template-columns: minmax(0, 1.8fr) minmax(300px, .7fr); gap: 14px; align-items: start; }.detail-section { padding: 0 20px 20px; }.section-head { min-height: 66px; display: flex; flex-direction: column; justify-content: center; border-bottom: 1px solid var(--line); margin-bottom: 18px; }.section-head h2 { margin: 4px 0 0; font-size: 16px; }.status-list { margin: 0; }.status-list div { min-height: 47px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #edf0f3; }.status-list div:last-child { border-bottom: 0; }.status-list dt { color: #7c8595; font-size: 12px; }.status-list dd { margin: 0; color: #394457; font-size: 12px; font-weight: 550; }.url-card { display: flex; flex-direction: column; gap: 12px; padding: 20px; border-left: 3px solid var(--blue); }.url-card strong { font-size: 14px; }.url-card a { overflow: hidden; color: var(--blue); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }.url-card .el-button { align-self: flex-start; }.muted { margin-left: 5px; font-size: 11px; }
</style>
