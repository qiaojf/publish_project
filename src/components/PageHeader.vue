<script setup lang="ts">
defineProps<{ title: string; description?: string; eyebrow?: string }>()
</script>
<template>
  <div class="page-header">
    <div><span v-if="eyebrow" class="section-kicker">{{ eyebrow }}</span><h1>{{ title }}</h1><p v-if="description">{{ description }}</p></div>
    <div v-if="$slots.actions" class="header-actions"><slot name="actions" /></div>
  </div>
</template>
<style scoped>
.page-header { min-height: 55px; display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; }
h1 { margin: 4px 0 0; color: var(--ink); font-size: 25px; line-height: 1.25; font-weight: 680; letter-spacing: -.02em; }
p { margin: 6px 0 0; color: #747f92; font-size: 13px; }.header-actions { display: flex; gap: 10px; }
</style>
