<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Check, Promotion } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import ContentForm from '@/components/ContentForm.vue'
import { createContent, getContent, publishContent, submitContent, updateContent } from '@/api/contents'
import { getPublishTargets } from '@/api/publishTargets'
import { useMock } from '@/api/runtime'
import { useAuthStore } from '@/stores/auth'
import type { ContentItem, ContentPayload } from '@/types/content'
import type { PublishTarget } from '@/types/publish'

interface ContentFormExpose { model: ContentPayload; validate: () => Promise<boolean> | undefined }
const route = useRoute(); const router = useRouter(); const auth = useAuthStore(); const contentId = computed(() => Number(route.params.id) || undefined); const formRef = ref<ContentFormExpose>(); const initial = ref<ContentItem>(); const targets = ref<PublishTarget[]>([]); const loading = ref(false); const saving = ref(false)
onMounted(async () => { loading.value = true; try { targets.value = await getPublishTargets(); if (contentId.value) { initial.value = await getContent(contentId.value); if (!auth.isAdmin && (initial.value.created_by !== auth.user?.id || initial.value.review_status === 'pending')) { ElMessage.error('当前内容不可编辑'); router.replace(`/contents/${contentId.value}`) } } } catch (e) { ElMessage.error(e instanceof Error ? e.message : '表单加载失败') } finally { loading.value = false } })
async function validate() { if (!formRef.value) return false; const ok = await formRef.value.validate()?.catch(() => false); if (!ok) return false; const model = formRef.value.model; if (!['html', 'dynamic'].includes(model.content_type) && !model.files?.length && !initial.value?.files?.length && !initial.value?.file_name) { ElMessage.warning('请选择内容文件或文件夹'); return false } return true }
async function save(): Promise<ContentItem | undefined> { if (!await validate() || !formRef.value) return; saving.value = true; try { const item = contentId.value ? await updateContent(contentId.value, formRef.value.model) : await createContent(formRef.value.model); initial.value = item; ElMessage.success('草稿已保存'); return item } catch (e) { ElMessage.error(e instanceof Error ? e.message : '保存失败') } finally { saving.value = false } }
async function saveAndLeave() { const item = await save(); if (item) router.push(`/contents/${item.id}`) }
async function saveAndSubmit() { const item = await save(); if (!item) return; try { await submitContent(item.id); ElMessage.success('已提交发布审核，审核前不可继续编辑'); router.push(`/contents/${item.id}`) } catch (e) { ElMessage.error(e instanceof Error ? e.message : '提交失败') } }
async function saveAndPublish() { const item = await save(); if (!item) return; try { await ElMessageBox.confirm('确认保存并直接发布该内容吗？发布操作将由后端执行。', '保存并发布', { confirmButtonText: '确认发布', cancelButtonText: '取消' }); await publishContent(item.id); ElMessage.success('内容已发布'); router.push(`/contents/${item.id}`) } catch (e) { if (e instanceof Error) ElMessage.error(e.message) } }
</script>
<template>
  <div class="page-shell" v-loading="loading">
    <PageHeader :title="contentId ? '编辑内容' : '新建内容'" description="填写内容资料并选择适配的发布目标。服务器目录与发布操作由后端管理。" eyebrow="CONTENT EDITOR"><template #actions><el-button :icon="ArrowLeft" @click="router.back()">返回</el-button></template></PageHeader>
    <section class="paper-card editor-card"><div class="editor-head"><span class="step-no">01</span><div><h2>内容资料</h2><p>带 * 的字段为必填项</p></div></div><ContentForm v-if="!loading" ref="formRef" :initial="initial" :targets="targets" /></section>
    <div class="form-actions paper-card"><span>{{ useMock ? '当前操作将保存在 Mock 数据层。' : '当前操作将通过 FastAPI 写入本地 PostgreSQL。' }}</span><div><el-button @click="router.back()">取消</el-button><el-button :loading="saving" :icon="Check" @click="saveAndLeave">保存草稿</el-button><el-button v-if="!auth.isAdmin" type="primary" :loading="saving" :icon="Promotion" @click="saveAndSubmit">{{ initial?.review_status === 'rejected' ? '保存并重新提交' : '提交发布' }}</el-button><el-button v-else type="primary" :loading="saving" :icon="Promotion" @click="saveAndPublish">保存并发布</el-button></div></div>
  </div>
</template>
<style scoped>
.editor-card { padding: 23px 26px 28px; }.editor-head { display: flex; align-items: flex-start; gap: 13px; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--line); }.step-no { width: 30px; height: 30px; display: grid; place-items: center; color: #fff; background: var(--ink); font: 11px Bahnschrift, sans-serif; }.editor-head h2 { margin: 0; font-size: 16px; }.editor-head p { margin: 5px 0 0; color: #8b94a3; font-size: 11px; }.form-actions { position: sticky; bottom: 0; z-index: 5; min-height: 68px; display: flex; align-items: center; justify-content: space-between; padding: 12px 18px; }.form-actions > span { color: #8b94a3; font-size: 11px; }
</style>
