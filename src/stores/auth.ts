import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'
import type { CurrentUser } from '@/types/user'

const USER_KEY = 'publish-console-user'

function loadSavedUser(): CurrentUser | null {
  const saved = localStorage.getItem(USER_KEY)
  if (!saved) return null
  try { return JSON.parse(saved) as CurrentUser } catch { return null }
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<CurrentUser | null>(loadSavedUser())
  const initialized = ref(false)
  const loading = ref(false)
  const isAuthenticated = computed(() => Boolean(user.value && localStorage.getItem('publish-console-token')))
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isEmployee = computed(() => user.value?.role === 'employee')

  async function login(username: string, password: string) {
    loading.value = true
    try {
      const result = await authApi.login(username, password)
      localStorage.setItem('publish-console-token', result.token)
      await getCurrentUser()
    } finally { loading.value = false }
  }

  async function getCurrentUser() {
    const current = await authApi.getCurrentUser()
    user.value = current
    localStorage.setItem(USER_KEY, JSON.stringify(current))
    initialized.value = true
    return current
  }

  async function restoreSession() {
    if (!localStorage.getItem('publish-console-token')) { initialized.value = true; user.value = null; return null }
    try { return await getCurrentUser() } catch { clearSession(); return null }
  }

  function clearSession() {
    user.value = null
    localStorage.removeItem(USER_KEY)
    localStorage.removeItem('publish-console-token')
  }

  async function logout() {
    try { await authApi.logout() } finally { clearSession() }
  }

  return { user, initialized, loading, isAuthenticated, isAdmin, isEmployee, login, logout, getCurrentUser, restoreSession }
})
