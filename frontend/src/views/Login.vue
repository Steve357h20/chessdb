<template>
  <div class="login-page">
    <el-card class="lp-card">
      <div class="lp-header">
        <span class="lp-logo">♚</span>
        <h2>{{ isLogin ? '登录' : '注册' }}</h2>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="onSubmit"
      >
        <el-form-item v-if="!isLogin" label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item v-if="!isLogin" label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" type="email" />
        </el-form-item>

        <el-form-item v-if="isLogin" label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="submitting"
            style="width: 100%"
            native-type="submit"
          >{{ isLogin ? '登录' : '注册' }}</el-button>
        </el-form-item>
      </el-form>

      <div class="lp-switch">
        <span v-if="isLogin">
          还没有账号？<el-link type="primary" @click="toggleMode">立即注册</el-link>
        </span>
        <span v-else>
          已有账号？<el-link type="primary" @click="toggleMode">去登录</el-link>
        </span>
      </div>

      <div class="lp-demo-hint">
        <el-divider>演示账号</el-divider>
        <p>用户名: admin &nbsp; 密码: admin123</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login as loginApi, register as registerApi } from '@/api/auth'
import { useUserStore } from '@/store'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isLogin = ref(true)
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({
  username: '',
  email: '',
  password: '',
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 80, message: '用户名长度3-80字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
}

const rules = ref(loginRules)

function toggleMode() {
  isLogin.value = !isLogin.value
  rules.value = isLogin.value ? loginRules : registerRules
  form.username = ''
  form.email = ''
  form.password = ''
}

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate()

  submitting.value = true
  try {
    if (isLogin.value) {
      const res = await loginApi({
        username: form.username,
        password: form.password,
      })
      const data = res.data || res
      if (data.access_token) {
        localStorage.setItem('token', data.access_token)
        userStore.token = data.access_token
      }
      if (data.user) {
        userStore.user = data.user
      }
      ElMessage.success('登录成功')
    } else {
      const res = await registerApi({
        username: form.username,
        email: form.email,
        password: form.password,
      })
      ElMessage.success('注册成功，请登录')
      isLogin.value = true
      rules.value = loginRules
      return
    }

    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) {
    console.error('Auth error:', e)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 70vh;
}

.lp-card {
  width: 400px;
  max-width: 90vw;
}

.lp-header {
  text-align: center;
  margin-bottom: 24px;
}

.lp-logo {
  font-size: 40px;
  color: #409eff;
}

.lp-header h2 {
  margin: 8px 0 0;
  color: var(--text-color);
}

.lp-switch {
  text-align: center;
  font-size: 14px;
  color: var(--text-color-secondary);
}

.lp-demo-hint {
  margin-top: 8px;
}

.lp-demo-hint p {
  text-align: center;
  font-size: 13px;
  color: var(--text-color-placeholder);
  margin: 0;
}
</style>
