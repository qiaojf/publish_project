<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, Link, Promotion, RefreshRight } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import ContentStatus from '@/components/ContentStatus.vue'
import ContentPreview from '@/components/ContentPreview.vue'
import PublishFlow from '@/components/PublishFlow.vue'
import { getContent, getContentPreview, republishContent, submitContent } from '@/api/contents'
import { getRequestErrorMessage } from '@/api/request'
import { CONTENT_TYPES } from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { formatDate, formatFileSize } from '@/utils/format'
import type { ContentItem, PreviewData } from '@/types/content'

const route = useRoute(); const router = useRouter(); const auth = useAuthStore(); const id = Number(route.params.id); const loading = ref(true); const previewLoading = ref(true); const content = ref<ContentItem>(); const preview = ref<PreviewData>()
const { t } = useI18n()
let publishPoll: ReturnType<typeof setTimeout> | undefined
const canEdit = computed(() => content.value && (auth.isAdmin || (content.value.created_by === auth.user?.id && content.value.review_status !== 'pending' && content.value.publish_status !== 'published')))
const canSubmit = computed(() => !auth.isAdmin && content.value && ['draft', 'rejected'].includes(content.value.review_status))
async function loadContent(showLoading = true) { if (showLoading) loading.value = true; try { content.value = await getContent(id) } catch (e) { if (showLoading) ElMessage.error(getRequestErrorMessage(e, 'content.loadFailed')) } finally { if (showLoading) loading.value = false } }
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
  if (content.value.publish_status === 'published') ElMessage.success(t('content.published'))
  else ElMessage.error(content.value.failure_reason || t('content.publishFailedCheckLog'))
}
async function submit() { try { await submitContent(id); ElMessage.success(t('content.submitted')); load() } catch (e) { ElMessage.error(getRequestErrorMessage(e, 'content.submitFailed')) } }
async function republish() { try { await ElMessageBox.confirm(t('content.republishApprovedConfirm'), t('content.republish'), { confirmButtonText: t('content.republish'), cancelButtonText: t('common.cancel') }); await republishContent(id); ElMessage.success(t('content.republishSucceeded')); load() } catch (e) { if (e instanceof Error) ElMessage.error(getRequestErrorMessage(e)) } }
onMounted(async () => { await load(); await pollPublishStatus() })
onBeforeUnmount(() => { if (publishPoll) clearTimeout(publishPoll) })
</script>
<template>
  <div class="page-shell" v-loading="loading">
    <PageHeader :title="content?.title || t('content.detail')" :description="content?.description ?? undefined" :eyebrow="t('kicker.contentRecord')"><template #actions><el-button :icon="ArrowLeft" @click="router.back()">{{ t('common.back') }}</el-button><el-button v-if="canEdit" :icon="Edit" @click="router.push(`/contents/${id}/edit`)">{{ t('common.edit') }}</el-button><el-button v-if="canSubmit" type="primary" :icon="Promotion" @click="submit">{{ t(content?.review_status === 'rejected' ? 'content.resubmit' : 'content.submitPublish') }}</el-button><el-button v-if="auth.isAdmin && content?.review_status === 'pending'" type="primary" @click="router.push(`/reviews/${id}`)">{{ t('review.enterReview') }}</el-button><el-button v-if="auth.isAdmin && content?.publish_status === 'failed'" type="warning" :icon="RefreshRight" @click="republish">{{ t('content.republish') }}</el-button><el-button v-if="content?.publish_status === 'published' && content.view_url" tag="a" :href="content.view_url" target="_blank" rel="noopener noreferrer" type="success" :icon="Link">{{ t('content.openContent') }}</el-button></template></PageHeader>
    <PublishFlow v-if="content" :content="content" />
    <el-alert v-if="route.query.publishing === '1' && ['unpublished', 'publishing'].includes(content?.publish_status || '')" :title="t('content.publishingTitle')" :description="t('content.publishingDescription')" type="info" :closable="false" show-icon />
    <el-alert v-if="content?.review_status === 'rejected'" :title="t('content.reviewRejected')" type="error" :closable="false" show-icon><template #default>{{ content.reject_reason }}</template></el-alert>
    <el-alert v-if="content?.publish_status === 'failed'" :title="t('content.approvedPublishFailed')" type="error" :closable="false" show-icon><template #default>{{ content.failure_reason }}<span v-if="auth.isAdmin"> {{ t('content.republishWithoutReview') }}</span></template></el-alert>
    <div v-if="content" class="detail-grid">
      <div class="main-column stack-12">
        <section class="paper-card detail-section"><div class="section-head"><span class="section-kicker">{{ t('kicker.information') }}</span><h2>{{ t('content.basicInformation') }}</h2></div><el-descriptions :column="2" border><el-descriptions-item :label="t('content.contentType')">{{ t(CONTENT_TYPES[content.content_type]) }}</el-descriptions-item><el-descriptions-item :label="t('content.category')">{{ content.category }}</el-descriptions-item><el-descriptions-item :label="t('content.creator')">{{ content.creator_name }}</el-descriptions-item><el-descriptions-item :label="t('content.originalFile')">{{ content.source_is_directory || (content.files?.length || 0) > 1 ? t('content.filesAndFolders', { count: content.files?.length || 0 }) : content.file_name || content.files?.[0]?.name || t('content.pageContent') }}<span v-if="content.file_size" class="muted"> · {{ formatFileSize(content.file_size) }}</span></el-descriptions-item><el-descriptions-item :label="t('common.createdAt')">{{ formatDate(content.created_at) }}</el-descriptions-item><el-descriptions-item :label="t('common.updatedAt')">{{ formatDate(content.updated_at) }}</el-descriptions-item></el-descriptions></section>
        <section class="paper-card detail-section"><div class="section-head"><span class="section-kicker">{{ t('kicker.preview') }}</span><h2>{{ t('content.preview') }}</h2></div><ContentPreview :content-id="id" :preview="preview" :loading="previewLoading" /></section>
      </div>
      <aside class="stack-12">
        <section class="paper-card detail-section"><div class="section-head"><span class="section-kicker">{{ t('kicker.status') }}</span><h2>{{ t('content.statusInformation') }}</h2></div><dl class="status-list"><div><dt>{{ t('content.reviewStatus') }}</dt><dd><ContentStatus kind="review" :status="content.review_status" /></dd></div><div><dt>{{ t('content.publishStatus') }}</dt><dd><ContentStatus kind="publish" :status="content.publish_status" /></dd></div><div><dt>{{ t('content.publishTarget') }}</dt><dd>{{ content.publish_target_name || t('common.notSelected') }}</dd></div><div><dt>{{ t('content.submittedAt') }}</dt><dd>{{ formatDate(content.submitted_at) }}</dd></div><div><dt>{{ t('content.publishedAt') }}</dt><dd>{{ formatDate(content.published_at) }}</dd></div></dl></section>
        <section v-if="content.view_url" class="paper-card url-card"><span class="section-kicker">{{ t('kicker.publishedUrl') }}</span><strong>{{ t('content.publicUrl') }}</strong><a :href="content.view_url" target="_blank" rel="noopener noreferrer" class="mono">{{ content.view_url }}</a><el-button tag="a" :href="content.view_url" target="_blank" rel="noopener noreferrer" type="primary" plain :icon="Link">{{ t('content.openNewWindow') }}</el-button></section>
      </aside>
    </div>
  </div>
</template>
<style scoped>
.detail-grid { display: grid; grid-template-columns: minmax(0, 1.8fr) minmax(300px, .7fr); gap: 14px; align-items: start; }.detail-section { padding: 0 20px 20px; }.section-head { min-height: 66px; display: flex; flex-direction: column; justify-content: center; border-bottom: 1px solid var(--line); margin-bottom: 18px; }.section-head h2 { margin: 4px 0 0; font-size: 16px; }.status-list { margin: 0; }.status-list div { min-height: 47px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #edf0f3; }.status-list div:last-child { border-bottom: 0; }.status-list dt { color: #7c8595; font-size: 12px; }.status-list dd { margin: 0; color: #394457; font-size: 12px; font-weight: 550; }.url-card { display: flex; flex-direction: column; gap: 12px; padding: 20px; border-left: 3px solid var(--blue); }.url-card strong { font-size: 14px; }.url-card a { overflow: hidden; color: var(--blue); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }.url-card .el-button { align-self: flex-start; }.muted { margin-left: 5px; font-size: 11px; }
</style>
