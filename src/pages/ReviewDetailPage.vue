<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { ArrowLeft, Check, Close } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import ContentPreview from '@/components/ContentPreview.vue'
import PublishFlow from '@/components/PublishFlow.vue'
import { approveReview, getReviewDetail, rejectReview } from '@/api/reviews'
import { getContentPreview } from '@/api/contents'
import { CONTENT_TYPES } from '@/constants'
import { formatDate, formatFileSize } from '@/utils/format'
import type { PreviewData } from '@/types/content'
import type { ReviewDetail } from '@/types/review'

const route = useRoute(); const router = useRouter(); const id = Number(route.params.contentId); const loading = ref(true); const actionLoading = ref(false); const detail = ref<ReviewDetail>(); const preview = ref<PreviewData>(); const rejectVisible = ref(false); const rejectFormRef = ref<FormInstance>(); const rejectForm = reactive({ comment: '' }); const rejectRules: FormRules = { comment: [{ required: true, message: '请填写明确的驳回原因', trigger: 'blur' }, { min: 5, message: '驳回原因至少 5 个字', trigger: 'blur' }] }
async function load() { loading.value = true; try { const [result, previewResult] = await Promise.all([getReviewDetail(id), getContentPreview(id)]); detail.value = result; preview.value = previewResult } catch (e) { ElMessage.error(e instanceof Error ? e.message : '审核详情加载失败') } finally { loading.value = false } }
async function approve() { try { await ElMessageBox.confirm('确认审核通过并发布该内容吗？', '审核通过并发布', { type: 'warning', confirmButtonText: '通过并发布', cancelButtonText: '取消' }); actionLoading.value = true; const result = await approveReview(id, '内容与发布目标确认无误'); if (result.publish_status === 'published') ElMessage.success('审核通过，内容已成功发布'); else ElMessage.warning('审核已通过，但自动发布失败，请检查发布结果'); await load() } catch (e) { if (e instanceof Error) ElMessage.error(e.message) } finally { actionLoading.value = false } }
async function reject() { if (!await rejectFormRef.value?.validate().catch(() => false)) return; actionLoading.value = true; try { await rejectReview(id, rejectForm.comment); ElMessage.success('内容已驳回，员工可修改后重新提交'); rejectVisible.value = false; await load() } catch (e) { ElMessage.error(e instanceof Error ? e.message : '驳回失败') } finally { actionLoading.value = false } }
onMounted(load)
</script>
<template>
  <div class="page-shell" v-loading="loading">
    <PageHeader :title="detail?.content.title || '审核详情'" description="核对内容、原始文件与目标发布位置，在当前页面完成审核。" eyebrow="REVIEW INSPECTION"><template #actions><el-button :icon="ArrowLeft" @click="router.push('/reviews')">返回队列</el-button><template v-if="detail?.content.review_status === 'pending'"><el-button type="danger" plain :icon="Close" @click="rejectVisible = true">驳回</el-button><el-button type="primary" :icon="Check" :loading="actionLoading" @click="approve">审核通过并发布</el-button></template></template></PageHeader>
    <PublishFlow v-if="detail" :content="detail.content" />
    <el-alert v-if="detail?.content.publish_status === 'failed'" title="审核成功，但自动发布失败" :description="detail.content.failure_reason" type="error" :closable="false" show-icon />
    <div v-if="detail" class="review-grid">
      <div class="stack-12">
        <section class="paper-card review-section"><div class="section-head"><span class="section-kicker">CONTENT CHECK</span><h2>内容与文件</h2></div><el-descriptions :column="2" border><el-descriptions-item label="内容类型">{{ CONTENT_TYPES[detail.content.content_type] }}</el-descriptions-item><el-descriptions-item label="分类">{{ detail.content.category }}</el-descriptions-item><el-descriptions-item label="创建人">{{ detail.content.creator_name }}</el-descriptions-item><el-descriptions-item label="提交时间">{{ formatDate(detail.content.submitted_at) }}</el-descriptions-item><el-descriptions-item label="原始文件" :span="2">{{ detail.content.file_name || '页面内容' }} <span class="muted">{{ detail.content.file_size ? `· ${formatFileSize(detail.content.file_size)}` : '' }}</span></el-descriptions-item></el-descriptions><div class="description-block"><span>内容简介</span><p>{{ detail.content.description || '未填写简介' }}</p></div></section>
        <section class="paper-card review-section"><div class="section-head"><span class="section-kicker">PREVIEW</span><h2>内容预览</h2></div><ContentPreview :content-id="id" :preview="preview" /></section>
      </div>
      <aside class="stack-12">
        <section class="paper-card review-section target-card"><div class="section-head"><span class="section-kicker">DESTINATION</span><h2>发布目标核对</h2></div><dl><div><dt>目标名称</dt><dd>{{ detail.publish_target?.name }}</dd></div><div><dt>适用类型</dt><dd>{{ detail.publish_target?.content_types.map(item => CONTENT_TYPES[item]).join('、') }}</dd></div><div><dt>服务器发布根目录</dt><dd class="mono path">{{ detail.publish_target?.publish_root }}</dd></div><div><dt>URL 根地址</dt><dd class="mono path">{{ detail.publish_target?.base_url }}</dd></div><div><dt>当前状态</dt><dd><el-tag :type="detail.publish_target?.enabled ? 'success' : 'danger'">{{ detail.publish_target?.enabled ? '启用' : '禁用' }}</el-tag></dd></div></dl></section>
        <section class="paper-card review-section"><div class="section-head"><span class="section-kicker">AUDIT TRAIL</span><h2>历史审核记录</h2></div><el-timeline><el-timeline-item v-for="record in detail.history" :key="record.id" :timestamp="formatDate(record.created_at)" placement="top" :type="record.action === 'approve' ? 'success' : record.action === 'reject' ? 'danger' : 'primary'"><strong>{{ record.operator_name }}</strong><p>{{ record.comment }}</p></el-timeline-item></el-timeline></section>
      </aside>
    </div>
    <el-dialog v-model="rejectVisible" title="驳回发布申请" width="500px"><el-alert title="驳回后，内容将返回给创建人修改并可重新提交。" type="warning" :closable="false" show-icon /><el-form ref="rejectFormRef" :model="rejectForm" :rules="rejectRules" label-position="top" style="margin-top:18px"><el-form-item label="驳回原因" prop="comment"><el-input v-model="rejectForm.comment" type="textarea" :rows="5" maxlength="300" show-word-limit placeholder="请说明需要修改的具体内容" /></el-form-item></el-form><template #footer><el-button @click="rejectVisible = false">取消</el-button><el-button type="danger" :loading="actionLoading" @click="reject">确认驳回</el-button></template></el-dialog>
  </div>
</template>
<style scoped>
.review-grid { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(320px, .75fr); gap: 14px; align-items: start; }.review-section { padding: 0 20px 20px; }.section-head { min-height: 66px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 18px; border-bottom: 1px solid var(--line); }.section-head h2 { margin: 4px 0 0; font-size: 16px; }.description-block { margin-top: 18px; padding: 14px 16px; background: #f7f8fa; }.description-block span { color: #7b8494; font-size: 11px; }.description-block p { margin: 6px 0 0; font-size: 13px; line-height: 1.7; }.target-card { border-top: 3px solid var(--accent); }.target-card dl { margin: 0; }.target-card dl div { padding: 10px 0; border-bottom: 1px solid #edf0f3; }.target-card dl div:last-child { border: 0; }.target-card dt { margin-bottom: 5px; color: #8891a0; font-size: 11px; }.target-card dd { margin: 0; font-size: 12px; font-weight: 550; }.target-card .path { overflow-wrap: anywhere; color: #4a5c77; font-size: 10px; font-weight: 400; }.el-timeline { padding-left: 5px; }.el-timeline p { margin: 4px 0 0; color: #697487; font-size: 12px; line-height: 1.6; }
</style>
