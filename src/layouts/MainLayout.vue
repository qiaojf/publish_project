<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { COMPANY_LOGO_URL, COMPANY_SITE_URL, USER_ROLES } from '@/constants'
import { Bell, Collection, Document, Expand, Files, Fold, House, Reading, Search, Setting, SwitchButton, User } from '@element-plus/icons-vue'

const auth = useAuthStore()
const app = useAppStore()
const route = useRoute()
const router = useRouter()
const menus = computed(() => [
  { label: '工作台', path: '/', icon: House },
  { label: auth.isAdmin ? '内容管理' : '我的内容', path: '/contents', icon: Document },
  ...(auth.isAdmin ? [{ label: '审核管理', path: '/reviews', icon: Reading }] : []),
  { label: '内容检索', path: '/search', icon: Search },
  ...(auth.isAdmin ? [
    { label: '用户管理', path: '/users', icon: User },
    { label: '分类配置', path: '/settings/categories', icon: Files },
    { label: '发布配置', path: '/settings/publish-targets', icon: Setting },
    { label: '系统日志', path: '/logs', icon: Collection }
  ] : [])
])

async function handleLogout() {
  await ElMessageBox.confirm('确认退出当前账号吗？', '退出登录', { confirmButtonText: '退出', cancelButtonText: '取消' })
  await auth.logout()
  router.replace('/login')
}
</script>

<template>
  <div class="app-layout">
    <aside class="sidebar" :class="{ collapsed: app.sidebarCollapsed }">
      <div class="brand">
        <a class="brand-link" :href="COMPANY_SITE_URL" target="_blank" rel="noopener noreferrer" aria-label="Terabox 公司官网">
          <img :src="COMPANY_LOGO_URL" alt="Terabox" />
        </a>
      </div>
      <nav class="nav-list" aria-label="主导航">
        <router-link v-for="menu in menus" :key="menu.path" :to="menu.path" class="nav-item" :class="{ active: menu.path === '/' ? route.path === '/' : route.path.startsWith(menu.path) }">
          <el-icon><component :is="menu.icon" /></el-icon><span v-if="!app.sidebarCollapsed">{{ menu.label }}</span>
          <i v-if="menu.path === '/reviews' && !app.sidebarCollapsed" class="pending-dot" />
        </router-link>
      </nav>
      <div class="sidebar-foot">
        <button class="logout-button" type="button" @click="handleLogout"><el-icon><SwitchButton /></el-icon><span v-if="!app.sidebarCollapsed">退出登录</span></button>
      </div>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <button class="collapse-button" type="button" :aria-label="app.sidebarCollapsed ? '展开侧栏' : '收起侧栏'" @click="app.toggleSidebar">
          <el-icon><Expand v-if="app.sidebarCollapsed" /><Fold v-else /></el-icon>
        </button>
        <div class="breadcrumb"><span>内容发布台</span><b>/</b><strong>{{ route.meta.title }}</strong></div>
        <div class="topbar-actions">
          <button class="icon-button" type="button" aria-label="通知"><el-icon><Bell /></el-icon></button>
          <div class="user-chip">
            <span class="avatar">{{ auth.user?.name.slice(0, 1) }}</span>
            <div><strong>{{ auth.user?.name }}</strong><span>{{ auth.user ? USER_ROLES[auth.user.role] : '' }}</span></div>
          </div>
        </div>
      </header>
      <main class="main-content"><router-view /></main>
    </div>
  </div>
</template>

<style scoped>
.app-layout { display: flex; min-height: 100vh; }
.sidebar { position: fixed; inset: 0 auto 0 0; z-index: 20; width: 224px; display: flex; flex-direction: column; color: #555; background: #fff; border-right: 1px solid var(--line); transition: width .18s ease; }
.sidebar.collapsed { width: 72px; }
.brand { height: 72px; display: flex; align-items: center; padding: 0 17px; border-bottom: 1px solid var(--line); overflow: hidden; }
.brand-link { flex: 0 0 auto; width: 159px; overflow: hidden; }
.brand-link img { display: block; width: 159px; height: auto; }
.collapsed .brand-link { width: 38px; }
.nav-list { display: flex; flex-direction: column; gap: 3px; padding: 18px 10px; }
.nav-item { position: relative; height: 44px; display: flex; align-items: center; gap: 13px; padding: 0 13px; border-left: 2px solid transparent; color: #555; font-size: 14px; white-space: nowrap; transition: background .15s, color .15s; }
.nav-item:hover { color: var(--blue); background: #f7f9f3; }
.nav-item.active { color: #65920d; background: #f2f7e8; border-left-color: var(--blue); }
.nav-item .el-icon { flex: 0 0 18px; font-size: 18px; }
.pending-dot { margin-left: auto; width: 6px; height: 6px; border-radius: 50%; background: var(--accent); }
.sidebar-foot { margin-top: auto; padding: 12px 10px 18px; border-top: 1px solid var(--line); }
.logout-button { width: 100%; height: 42px; display: flex; align-items: center; gap: 13px; padding: 0 13px; color: #777; border: 0; background: transparent; cursor: pointer; }
.logout-button:hover { color: var(--blue); background: #f7f9f3; }
.workspace { width: calc(100% - 224px); min-height: 100vh; margin-left: 224px; transition: width .18s, margin .18s; }
.collapsed + .workspace { width: calc(100% - 72px); margin-left: 72px; }
.topbar { position: sticky; top: 0; z-index: 10; height: 64px; display: flex; align-items: center; padding: 0 26px; background: rgba(255,255,255,.96); border-bottom: 1px solid var(--line); }
.collapse-button, .icon-button { display: grid; place-items: center; width: 34px; height: 34px; border: 0; background: transparent; color: #616c80; cursor: pointer; border-radius: 4px; }
.collapse-button:hover, .icon-button:hover { background: #f0f2f5; color: var(--ink); }
.breadcrumb { margin-left: 15px; display: flex; gap: 9px; align-items: center; font-size: 13px; color: #8790a1; }
.breadcrumb b { font-weight: 400; color: #c3c9d2; }.breadcrumb strong { color: #394457; font-weight: 600; }
.topbar-actions { margin-left: auto; display: flex; align-items: center; gap: 15px; }
.icon-button { font-size: 18px; }
.user-chip { padding-left: 16px; border-left: 1px solid var(--line); display: flex; align-items: center; gap: 10px; }
.avatar { width: 32px; height: 32px; display: grid; place-items: center; border-radius: 50%; color: #fff; background: var(--blue); font-size: 13px; }
.user-chip div { display: flex; flex-direction: column; gap: 2px; }.user-chip strong { font-size: 13px; }.user-chip div span { color: #818b9e; font-size: 11px; }
.main-content { padding: 24px 28px 36px; }
</style>
