<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { getRequestErrorMessage } from '@/api/request'
import { COMPANY_LOGO_URL, COMPANY_SITE_URL } from '@/constants'
import LanguageSwitcher from '@/components/LanguageSwitcher/LanguageSwitcher.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const formRef = ref<FormInstance>()
const form = reactive({ username: '', password: '' })
const rules = computed<FormRules>(() => ({
  username: [{ required: true, message: t('validation.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: t('validation.passwordRequired'), trigger: 'blur' }]
}))

async function submit() {
  if (!await formRef.value?.validate().catch(() => false)) return
  try {
    await auth.login(form.username.trim(), form.password)
    ElMessage.success(t('login.welcome', { name: auth.user?.name || '' }))
    router.replace(typeof route.query.redirect === 'string' ? route.query.redirect : '/')
  } catch (error) {
    ElMessage.error(getRequestErrorMessage(error, 'login.failed'))
  }
}
</script>
<template>
  <div class="login-page">
    <div class="login-language"><LanguageSwitcher /></div>
    <section class="login-context">
      <a class="context-top" :href="COMPANY_SITE_URL" target="_blank" rel="noopener noreferrer"><img :src="COMPANY_LOGO_URL" alt="Terabox" /><span>{{ t('kicker.internalContentDesk') }}</span></a>
      <div class="context-main">
        <p class="section-kicker">{{ t('kicker.publishingWorkflow') }}</p>
        <h1>{{ t('login.heroLine1') }}<br />{{ t('login.heroLine2') }}</h1>
        <p>{{ t('login.heroDescription') }}</p>
        <div class="flow-ledger">
          <div><i>01</i><span>{{ t('login.stepCreate') }}</span></div><div><i>02</i><span>{{ t('login.stepSubmit') }}</span></div><div><i>03</i><span>{{ t('login.stepPublish') }}</span></div><div><i>04</i><span>{{ t('login.stepSearch') }}</span></div>
        </div>
      </div>
      <div class="context-foot">{{ t('login.authorizedOnly') }} <span>·</span> {{ t('login.audited') }}</div>
    </section>
    <section class="login-panel">
      <div class="login-form-wrap">
        <span class="panel-index">{{ t('kicker.access') }}</span><h2>{{ t('login.title') }}</h2>
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @keyup.enter="submit">
          <el-form-item :label="t('login.username')" prop="username"><el-input v-model="form.username" size="large" :placeholder="t('login.usernamePlaceholder')" :prefix-icon="User" /></el-form-item>
          <el-form-item :label="t('login.password')" prop="password"><el-input v-model="form.password" size="large" type="password" show-password :placeholder="t('login.passwordPlaceholder')" :prefix-icon="Lock" /></el-form-item>
          <el-button type="primary" size="large" :loading="auth.loading" class="login-button" @click="submit">{{ t('login.signIn') }}</el-button>
        </el-form>
      </div>
    </section>
  </div>
</template>
<style scoped>
.login-page { min-height: 100vh; display: grid; grid-template-columns: minmax(520px, 1.15fr) minmax(460px, .85fr); background: #fff; }
.login-language { position: fixed; top: 22px; right: 28px; z-index: 10; }
.login-context { position: relative; min-height: 100vh; display: flex; flex-direction: column; padding: 40px 52px 30px; color: #333; background: #f4f8e9; border-top: 6px solid var(--blue); }
.context-top { display: flex; flex-direction: column; align-items: flex-start; gap: 9px; width: max-content; }.context-top img { display: block; width: 190px; height: auto; }.context-top span { color: #777; font: 9px Montserrat, "Helvetica Neue", Arial, sans-serif; letter-spacing: .18em; }
.context-main { margin: auto 0; max-width: 660px; }.context-main .section-kicker { color: var(--blue); }.context-main h1 { margin: 18px 0 22px; color: #222; font-size: clamp(42px, 4.5vw, 67px); line-height: 1.13; letter-spacing: -.045em; font-weight: 620; }.context-main > p:not(.section-kicker) { max-width: 500px; color: #68705f; font-size: 15px; line-height: 1.9; }
.flow-ledger { margin-top: 64px; display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid #cad6b5; }.flow-ledger div { position: relative; padding-top: 17px; display: flex; flex-direction: column; gap: 8px; }.flow-ledger div::before { content: ''; position: absolute; top: -3px; left: 0; width: 6px; height: 6px; background: var(--accent); }.flow-ledger i { color: #879174; font: 11px Montserrat, "Helvetica Neue", Arial, sans-serif; font-style: normal; }.flow-ledger span { font-size: 13px; }
.context-foot { color: #7d856f; font-size: 11px; letter-spacing: .08em; }.context-foot span { margin: 0 8px; }
.login-panel { display: grid; place-items: center; padding: 50px; border-left: 1px solid var(--line); }.login-form-wrap { width: 100%; max-width: 390px; }.panel-index { color: var(--blue); font: 10px Montserrat, "Helvetica Neue", Arial, sans-serif; letter-spacing: .17em; }.login-form-wrap h2 { margin: 12px 0 34px; color: var(--ink); font-size: 28px; }.login-button { width: 100%; margin-top: 6px; }
</style>
