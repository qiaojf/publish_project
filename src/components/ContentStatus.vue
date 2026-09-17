<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { PUBLISH_RECORD_STATUS, PUBLISH_RECORD_TAG_TYPES, PUBLISH_STATUS, PUBLISH_TAG_TYPES, REVIEW_STATUS, REVIEW_TAG_TYPES } from '@/constants'
import type { PublishStatus, ReviewStatus } from '@/types/content'
import type { PublishRecordStatus } from '@/types/publish'

const props = defineProps<{ kind: 'review' | 'publish' | 'publish-record'; status: ReviewStatus | PublishStatus | PublishRecordStatus }>()
const { t } = useI18n()
const isPublishing = computed(() => props.kind !== 'review' && props.status === 'publishing')
</script>
<template>
  <el-tag v-if="kind === 'review'" :type="REVIEW_TAG_TYPES[status as ReviewStatus]" effect="light">{{ t(REVIEW_STATUS[status as ReviewStatus]) }}</el-tag>
  <el-tag v-else-if="kind === 'publish'" :type="PUBLISH_TAG_TYPES[status as PublishStatus]" effect="light"><span v-if="isPublishing" class="spinner" />{{ t(PUBLISH_STATUS[status as PublishStatus]) }}</el-tag>
  <el-tag v-else :type="PUBLISH_RECORD_TAG_TYPES[status as PublishRecordStatus]" effect="light"><span v-if="isPublishing" class="spinner" />{{ t(PUBLISH_RECORD_STATUS[status as PublishRecordStatus]) }}</el-tag>
</template>
<style scoped>
.spinner { display: inline-block; width: 9px; height: 9px; margin-right: 5px; border: 1.5px solid currentColor; border-right-color: transparent; border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
