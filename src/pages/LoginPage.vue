<script setup lang="ts">
import { reactive, ref } from 'vue'
import { isAxiosError } from 'axios'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useMock } from '@/api/runtime'
import { COMPANY_LOGO_URL, COMPANY_SITE_URL } from '@/constants'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()
const form = reactive({ username: 'admin', password: 'admin123' })
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function submit() {
  if (!await formRef.value?.validate().catch(() => false)) return
  try {
    await auth.login(form.username.trim(), form.password)
    ElMessage.success(`欢迎回来，${auth.user?.name}`)
    router.replace(typeof route.query.redirect === 'string' ? route.query.redirect : '/')
  } catch (error) {
    const message = isAxiosError<{ message?: string }>(error) ? error.response?.data?.message : undefined
    ElMessage.error(message || (error instanceof Error ? error.message : '登录失败'))
  }
}
function useAccount(username: string, password: string) { form.username = username; form.password = password }
</script>
<template>
  <div class="login-page">
    <section class="login-context">
      <a class="context-top" :href="COMPANY_SITE_URL" target="_blank" rel="noopener noreferrer"><img :src="COMPANY_LOGO_URL" alt="Terabox" /><span>INTERNAL CONTENT DESK</span></a>
      <div class="context-main">
        <p class="section-kicker">PUBLISHING WORKFLOW / 2026</p>
        <h1>让每一次发布<br />都有清晰的来路。</h1>
        <p>从内容提交、审核确认到正式发布，所有状态与操作在同一条轨迹中完成。</p>
        <div class="flow-ledger">
          <div><i>01</i><span>创建内容</span></div><div><i>02</i><span>提交审核</span></div><div><i>03</i><span>自动发布</span></div><div><i>04</i><span>检索访问</span></div>
        </div>
      </div>
      <div class="context-foot">仅限公司内部授权账号使用 <span>·</span> 所有操作均留痕</div>
    </section>
    <section class="login-panel">
      <div class="login-form-wrap">
        <span class="panel-index">ACCESS / 01</span><h2>登录工作台</h2><p>输入你的内部账号以继续</p>
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @keyup.enter="submit">
          <el-form-item label="用户名" prop="username"><el-input v-model="form.username" size="large" placeholder="请输入用户名" :prefix-icon="User" /></el-form-item>
          <el-form-item label="密码" prop="password"><el-input v-model="form.password" size="large" type="password" show-password placeholder="请输入密码" :prefix-icon="Lock" /></el-form-item>
          <el-button type="primary" size="large" :loading="auth.loading" class="login-button" @click="submit">登录</el-button>
        </el-form>
        <div class="demo-accounts"><div class="demo-title"><span>{{ useMock ? 'Mock 演示账号' : '本地联调账号' }}</span></div><button type="button" @click="useAccount('admin', 'admin123')"><span><b>管理员</b><small>完整审核与系统配置权限</small></span><code>admin / admin123</code></button><button type="button" @click="useAccount('employee', 'employee123')"><span><b>普通员工</b><small>内容创建、提交与检索</small></span><code>employee / employee123</code></button></div>
      </div>
    </section>
  </div>
</template>
<style scoped>
.login-page { min-height: 100vh; display: grid; grid-template-columns: minmax(520px, 1.15fr) minmax(460px, .85fr); background: #fff; }
.login-context { position: relative; min-height: 100vh; display: flex; flex-direction: column; padding: 40px 52px 30px; color: #333; background: #f4f8e9; border-top: 6px solid var(--blue); }
.context-top { display: flex; flex-direction: column; align-items: flex-start; gap: 9px; width: max-content; }.context-top img { display: block; width: 190px; height: auto; }.context-top span { color: #777; font: 9px Montserrat, "Helvetica Neue", Arial, sans-serif; letter-spacing: .18em; }
.context-main { margin: auto 0; max-width: 660px; }.context-main .section-kicker { color: var(--blue); }.context-main h1 { margin: 18px 0 22px; color: #222; font-size: clamp(42px, 4.5vw, 67px); line-height: 1.13; letter-spacing: -.045em; font-weight: 620; }.context-main > p:not(.section-kicker) { max-width: 500px; color: #68705f; font-size: 15px; line-height: 1.9; }
.flow-ledger { margin-top: 64px; display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid #cad6b5; }.flow-ledger div { position: relative; padding-top: 17px; display: flex; flex-direction: column; gap: 8px; }.flow-ledger div::before { content: ''; position: absolute; top: -3px; left: 0; width: 6px; height: 6px; background: var(--accent); }.flow-ledger i { color: #879174; font: 11px Montserrat, "Helvetica Neue", Arial, sans-serif; font-style: normal; }.flow-ledger span { font-size: 13px; }
.context-foot { color: #7d856f; font-size: 11px; letter-spacing: .08em; }.context-foot span { margin: 0 8px; }
.login-panel { display: grid; place-items: center; padding: 50px; border-left: 1px solid var(--line); }.login-form-wrap { width: 100%; max-width: 390px; }.panel-index { color: var(--blue); font: 10px Montserrat, "Helvetica Neue", Arial, sans-serif; letter-spacing: .17em; }.login-form-wrap h2 { margin: 12px 0 8px; color: var(--ink); font-size: 28px; }.login-form-wrap > p { margin: 0 0 34px; color: #7c8595; font-size: 13px; }.login-button { width: 100%; margin-top: 6px; }
.demo-accounts { margin-top: 35px; border-top: 1px solid var(--line); }.demo-title { transform: translateY(-8px); text-align: center; }.demo-title span { padding: 0 12px; color: #9aa1ae; background: #fff; font-size: 11px; }.demo-accounts button { width: 100%; display: flex; align-items: center; justify-content: space-between; padding: 12px 0; color: inherit; border: 0; border-bottom: 1px solid #edf0f3; background: transparent; text-align: left; cursor: pointer; }.demo-accounts button:hover b { color: var(--blue); }.demo-accounts button span { display: flex; flex-direction: column; gap: 3px; }.demo-accounts b { font-size: 12px; }.demo-accounts small { color: #929aa8; }.demo-accounts code { color: #687388; font: 10px "Cascadia Mono", monospace; }
</style>
