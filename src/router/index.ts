import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import MainLayout from '@/layouts/MainLayout.vue'

declare module 'vue-router' {
  interface RouteMeta { title?: string; requiresAuth?: boolean; adminOnly?: boolean }
}

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: () => import('@/pages/LoginPage.vue'), meta: { title: '登录' } },
  {
    path: '/', component: MainLayout, meta: { requiresAuth: true }, children: [
      { path: '', name: 'dashboard', component: () => import('@/pages/DashboardPage.vue'), meta: { title: '工作台' } },
      { path: 'contents', name: 'contents', component: () => import('@/pages/ContentListPage.vue'), meta: { title: '内容管理' } },
      { path: 'contents/new', name: 'content-new', component: () => import('@/pages/ContentFormPage.vue'), meta: { title: '新建内容' } },
      { path: 'contents/:id', name: 'content-detail', component: () => import('@/pages/ContentDetailPage.vue'), meta: { title: '内容详情' } },
      { path: 'contents/:id/edit', name: 'content-edit', component: () => import('@/pages/ContentFormPage.vue'), meta: { title: '编辑内容' } },
      { path: 'search', name: 'search', component: () => import('@/pages/SearchPage.vue'), meta: { title: '内容检索' } },
      { path: 'reviews', name: 'reviews', component: () => import('@/pages/ReviewListPage.vue'), meta: { title: '审核管理', adminOnly: true } },
      { path: 'reviews/:contentId', name: 'review-detail', component: () => import('@/pages/ReviewDetailPage.vue'), meta: { title: '审核详情', adminOnly: true } },
      { path: 'users', name: 'users', component: () => import('@/pages/UserPage.vue'), meta: { title: '用户管理', adminOnly: true } },
      { path: 'settings/departments', name: 'departments', component: () => import('@/pages/DepartmentPage.vue'), meta: { title: '部门配置', adminOnly: true } },
      { path: 'settings/categories', name: 'categories', component: () => import('@/pages/CategoryPage.vue'), meta: { title: '分类配置', adminOnly: true } },
      { path: 'settings/publish-targets', name: 'publish-targets', component: () => import('@/pages/PublishTargetPage.vue'), meta: { title: '发布配置', adminOnly: true } },
      { path: 'logs', name: 'logs', component: () => import('@/pages/LogPage.vue'), meta: { title: '系统日志', adminOnly: true } }
    ]
  },
  { path: '/403', name: 'forbidden', component: () => import('@/pages/ForbiddenPage.vue'), meta: { title: '无权访问' } },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/pages/NotFoundPage.vue'), meta: { title: '页面不存在' } }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.initialized) await auth.restoreSession()
  document.title = `${to.meta.title || '内容发布台'} · 内容发布台`
  if (to.name === 'login' && auth.isAuthenticated) return { name: 'dashboard' }
  if (to.meta.requiresAuth && !auth.isAuthenticated) return { name: 'login', query: { redirect: to.fullPath } }
  if (to.meta.adminOnly && !auth.isAdmin) return { name: 'forbidden' }
  return true
})

export default router
