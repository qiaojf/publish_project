import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { getCategories } from '@/api/categories'
import type { Category } from '@/types/category'

export const useCategoryStore = defineStore('categories', () => {
  const items = ref<Category[]>([])
  const loading = ref(false)
  const loadedWithDisabled = ref(false)
  const activeNames = computed(() => items.value.filter((item) => item.enabled).map((item) => item.name))

  async function load(includeDisabled = false, force = false) {
    if (!force && items.value.length && (!includeDisabled || loadedWithDisabled.value)) return items.value
    loading.value = true
    try {
      items.value = await getCategories(includeDisabled)
      loadedWithDisabled.value = includeDisabled
      return items.value
    } finally { loading.value = false }
  }

  function invalidate() {
    items.value = []
    loadedWithDisabled.value = false
  }

  return { items, loading, activeNames, load, invalidate }
})
