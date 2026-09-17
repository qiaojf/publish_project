<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Check, Promotion } from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader.vue'
import ContentForm from '@/components/ContentForm.vue'
import { createContent, getContent, publishContent, submitContent, updateContent } from '@/api/contents'
import { getRequestErrorMessage } from '@/api/request'
import { getPublishTargets } from '@/api/publishTargets'
import { useMock } from '@/api/runtime'
import { useAuthStore } from '@/stores/auth'
import { useCategoryStore } from '@/stores/categories'
import type { ContentItem, ContentPayload } from '@/types/content'
import type { PublishTarget } from '@/types/publish'

interface ContentFormExpose { model: ContentPayload; validate: () => Promise<boolean> | undefined }
const route = useRoute(); const router = useRouter(); const auth = useAuthStore(); const categories = useCategoryStore(); const contentId = computed(() => Number(route.params.id) || undefined); const formRef = ref<ContentFormExpose>(); const initial = ref<ContentItem>(); const targets = ref<PublishTarget[]>([]); const loading = ref(false); const saving = ref(false)
const { t } = useI18n()
onMounted(async () => { loading.value = true; try { const [loadedTargets] = await Promise.all([getPublishTargets(), categories.load()]); targets.value = loadedTargets; if (contentId.value) { initial.value = await getContent(contentId.value); if (!auth.isAdmin && (initial.value.created_by !== auth.user?.id || initial.value.review_status === 'pending')) { ElMessage.error(t('content.notEditable')); router.replace(`/contents/${contentId.value}`) } } } catch (e) { ElMessage.error(getRequestErrorMessage(e, 'content.formLoadFailed')) } finally { loading.value = false } })
async function validate() { if (!formRef.value) return false; const ok = await formRef.value.validate()?.catch(() => false); if (!ok) return false; const model = formRef.value.model; if (!['html', 'dynamic'].includes(model.content_type) && !model.files?.length && !initial.value?.files?.length && !initial.value?.file_name) { ElMessage.warning(t('validation.contentFilesRequired')); return false } return true }
async function save(): Promise<ContentItem | undefined> { if (!await validate() || !formRef.value) return; saving.value = true; try { const item = contentId.value ? await updateContent(contentId.value, formRef.value.model) : await createContent(formRef.value.model); initial.value = item; ElMessage.success(t('content.draftSaved')); return item } catch (e) { ElMessage.error(getRequestErrorMessage(e, 'common.saveFailed')) } finally { saving.value = false } }
async function saveAndLeave() { const item = await save(); if (item) router.push(`/contents/${item.id}`) }
async function saveAndSubmit() { const item = await save(); if (!item) return; try { await submitContent(item.id); ElMessage.success(t('content.submittedLocked')); router.push(`/contents/${item.id}`) } catch (e) { ElMessage.error(getRequestErrorMessage(e, 'content.submitFailed')) } }
async function saveAndPublish() { const item = await save(); if (!item) return; try { await ElMessageBox.confirm(t('content.savePublishConfirm'), t('content.savePublish'), { confirmButtonText: t('content.confirmPublish'), cancelButtonText: t('common.cancel') }); const publishing = publishContent(item.id); await router.push({ path: `/contents/${item.id}`, query: { publishing: '1' } }); await publishing } catch (e) { if (route.query.publishing === '1') await router.replace({ path: `/contents/${item.id}` }); if (e instanceof Error) ElMessage.error(getRequestErrorMessage(e)) } }
</script>
<template>
  <div class="page-shell" v-loading="loading">
    <PageHeader :title="t(contentId ? 'content.edit' : 'content.create')" :description="t('content.formDescription')" :eyebrow="t('kicker.contentEditor')"><template #actions><el-button :icon="ArrowLeft" @click="router.back()">{{ t('common.back') }}</el-button></template></PageHeader>
    <section class="paper-card editor-card"><div class="editor-head"><span class="step-no">01</span><div><h2>{{ t('content.information') }}</h2><p>{{ t('common.requiredHint') }}</p></div></div><ContentForm v-if="!loading" ref="formRef" :initial="initial" :targets="targets" :categories="categories.activeNames" /></section>
    <div class="form-actions paper-card"><span>{{ t(useMock ? 'content.mockStorageHint' : 'content.apiStorageHint') }}</span><div><el-button @click="router.back()">{{ t('common.cancel') }}</el-button><el-button :loading="saving" :icon="Check" @click="saveAndLeave">{{ t('content.saveDraft') }}</el-button><el-button v-if="!auth.isAdmin" type="primary" :loading="saving" :icon="Promotion" @click="saveAndSubmit">{{ t(initial?.review_status === 'rejected' ? 'content.saveResubmit' : 'content.submitPublish') }}</el-button><el-button v-else type="primary" :loading="saving" :icon="Promotion" @click="saveAndPublish">{{ t('content.savePublish') }}</el-button></div></div>
  </div>
</template>
<style scoped>
.editor-card { padding: 23px 26px 28px; }.editor-head { display: flex; align-items: flex-start; gap: 13px; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--line); }.step-no { width: 30px; height: 30px; display: grid; place-items: center; color: #fff; background: var(--ink); font: 11px Bahnschrift, sans-serif; }.editor-head h2 { margin: 0; font-size: 16px; }.editor-head p { margin: 5px 0 0; color: #8b94a3; font-size: 11px; }.form-actions { position: sticky; bottom: 0; z-index: 5; min-height: 68px; display: flex; align-items: center; justify-content: space-between; padding: 12px 18px; }.form-actions > span { color: #8b94a3; font-size: 11px; }
</style>
