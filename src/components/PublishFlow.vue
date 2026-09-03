<script setup lang="ts">
import { computed } from 'vue'
import type { ContentItem } from '@/types/content'
const props = defineProps<{ content: ContentItem }>()
const active = computed(() => {
  if (props.content.publish_status === 'published' || props.content.publish_status === 'failed') return 4
  if (props.content.review_status === 'approved') return 3
  if (props.content.review_status === 'pending' || props.content.review_status === 'rejected') return 2
  return 1
})
const labels = ['内容就绪', '提交审核', '审核处理', '自动发布']
</script>
<template>
  <div class="publish-flow">
    <div v-for="(label, index) in labels" :key="label" class="flow-step" :class="{ active: index + 1 <= active, failed: index === 3 && content.publish_status === 'failed' }">
      <span>{{ index + 1 }}</span><strong>{{ label }}</strong><i v-if="index < labels.length - 1" />
    </div>
  </div>
</template>
<style scoped>
.publish-flow { display: grid; grid-template-columns: repeat(4, 1fr); padding: 17px 20px; border: 1px solid var(--line); background: #fafbfc; }
.flow-step { position: relative; display: flex; align-items: center; gap: 8px; color: #9aa2b0; }.flow-step span { position: relative; z-index: 2; width: 25px; height: 25px; display: grid; place-items: center; border: 1px solid #cad0da; border-radius: 50%; background: #fff; font: 11px Bahnschrift, sans-serif; }.flow-step strong { position: relative; z-index: 2; padding-right: 10px; background: #fafbfc; font-size: 12px; font-weight: 600; }.flow-step i { position: absolute; left: 25px; right: 0; height: 1px; background: #d9dee6; }.flow-step.active { color: var(--blue); }.flow-step.active span { color: #fff; border-color: var(--blue); background: var(--blue); }.flow-step.active i { background: #8ca4bf; }.flow-step.failed { color: var(--danger); }.flow-step.failed span { border-color: var(--danger); background: var(--danger); }
</style>
