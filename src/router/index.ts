import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import MainLayout from '@/layouts/MainLayout.vue'

declare module 'vue-router' {
  interface RouteMeta { i18nKey?: string; requiresAuth?: boolean; adminOnly?: boolean }
}

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: () => import('@/pages/LoginPage.vue'), meta: { i18nKey: 'login.title' } },
  {
    path: '/', component: MainLayout, meta: { requiresAuth: true }, children: [
      { path: '', name: 'dashboard', component: () => import('@/pages/DashboardPage.vue'), meta: { i18nKey: 'nav.dashboard' } },
      { path: 'contents', name: 'contents', component: () => import('@/pages/ContentListPage.vue'), meta: { i18nKey: 'nav.contents' } },
      { path: 'contents/new', name: 'content-new', component: () => import('@/pages/ContentFormPage.vue'), meta: { i18nKey: 'content.create' } },
      { path: 'contents/:id', name: 'content-detail', component: () => import('@/pages/ContentDetailPage.vue'), meta: { i18nKey: 'content.detail' } },
      { path: 'contents/:id/edit', name: 'content-edit', component: () => import('@/pages/ContentFormPage.vue'), meta: { i18nKey: 'content.edit' } },
      { path: 'search', name: 'search', component: () => import('@/pages/SearchPage.vue'), meta: { i18nKey: 'nav.search' } },
      { path: 'reviews', name: 'reviews', component: () => import('@/pages/ReviewListPage.vue'), meta: { i18nKey: 'nav.reviews', adminOnly: true } },
      { path: 'reviews/:contentId', name: 'review-detail', component: () => import('@/pages/ReviewDetailPage.vue'), meta: { i18nKey: 'review.detail', adminOnly: true } },
      { path: 'users', name: 'users', component: () => import('@/pages/UserPage.vue'), meta: { i18nKey: 'nav.users', adminOnly: true } },
      { path: 'settings/departments', name: 'departments', component: () => import('@/pages/DepartmentPage.vue'), meta: { i18nKey: 'nav.departments', adminOnly: true } },
      { path: 'settings/categories', name: 'categories', component: () => import('@/pages/CategoryPage.vue'), meta: { i18nKey: 'nav.categories', adminOnly: true } },
      { path: 'settings/publish-targets', name: 'publish-targets', component: () => import('@/pages/PublishTargetPage.vue'), meta: { i18nKey: 'nav.publishTargets', adminOnly: true } },
      { path: 'logs', name: 'logs', component: () => import('@/pages/LogPage.vue'), meta: { i18nKey: 'nav.logs', adminOnly: true } }
    ]
  },
  { path: '/403', name: 'forbidden', component: () => import('@/pages/ForbiddenPage.vue'), meta: { i18nKey: 'errorPage.forbiddenTitle' } },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/pages/NotFoundPage.vue'), meta: { i18nKey: 'errorPage.notFoundTitle' } }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.initialized) await auth.restoreSession()
  if (to.name === 'login' && auth.isAuthenticated) return { name: 'dashboard' }
  if (to.meta.requiresAuth && !auth.isAuthenticated) return { name: 'login', query: { redirect: to.fullPath } }
  if (to.meta.adminOnly && !auth.isAdmin) return { name: 'forbidden' }
  return true
})

export default router
