<template>
  <div class="profile-page">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="8" :md="6">
        <el-card class="pp-sidebar">
          <div class="pp-avatar-section">
            <el-avatar :size="80" :icon="UserFilled" class="pp-avatar" />
            <h3 class="pp-username">{{ userStore.user?.username || '用户' }}</h3>
            <p class="pp-email">{{ userStore.user?.email || '' }}</p>
          </div>
          <el-menu :default-active="activeTab" @select="onTabSelect">
            <el-menu-item index="info">
              <el-icon><User /></el-icon>
              <span>个人信息</span>
            </el-menu-item>
            <el-menu-item index="security">
              <el-icon><Lock /></el-icon>
              <span>安全设置</span>
            </el-menu-item>
            <el-menu-item index="preferences">
              <el-icon><Setting /></el-icon>
              <span>偏好设置</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="16" :md="18">
        <el-card class="pp-content">
          <div v-if="activeTab === 'info'">
            <div class="pp-section-header">
              <h3>个人信息</h3>
              <p>管理你的账户基本信息</p>
            </div>
            <el-form
              ref="infoFormRef"
              :model="infoForm"
              :rules="infoRules"
              label-width="100px"
              class="pp-form"
            >
              <el-form-item label="用户名" prop="username">
                <el-input v-model="infoForm.username" placeholder="请输入用户名">
                  <template #prepend><el-icon><User /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="infoForm.email" placeholder="请输入邮箱">
                  <template #prepend><el-icon><Message /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item label="注册时间">
                <el-input :model-value="formatDate(userStore.user?.created_at)" disabled>
                  <template #prepend><el-icon><Calendar /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item label="收藏数">
                <el-input :model-value="String(userStore.user?.collection_count ?? 0)" disabled>
                  <template #prepend><el-icon><Star /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="infoSaving" @click="saveInfo">保存修改</el-button>
                <el-button @click="resetInfoForm">重置</el-button>
              </el-form-item>
            </el-form>
          </div>

          <div v-if="activeTab === 'security'">
            <div class="pp-section-header">
              <h3>安全设置</h3>
              <p>修改密码以保护你的账户安全</p>
            </div>
            <el-form
              ref="securityFormRef"
              :model="securityForm"
              :rules="securityRules"
              label-width="100px"
              class="pp-form"
            >
              <el-form-item label="当前密码" prop="old_password">
                <el-input v-model="securityForm.old_password" type="password" placeholder="请输入当前密码" show-password>
                  <template #prepend><el-icon><Lock /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item label="新密码" prop="new_password">
                <el-input v-model="securityForm.new_password" type="password" placeholder="请输入新密码（至少6位）" show-password>
                  <template #prepend><el-icon><Lock /></el-icon></template>
                </el-input>
                <div class="pp-password-strength">
                  <div class="pp-strength-bar">
                    <div
                      class="pp-strength-fill"
                      :class="passwordStrengthClass"
                      :style="{ width: passwordStrengthPercent + '%' }"
                    />
                  </div>
                  <span class="pp-strength-text" :class="passwordStrengthClass">{{ passwordStrengthText }}</span>
                </div>
              </el-form-item>
              <el-form-item label="确认密码" prop="confirm_password">
                <el-input v-model="securityForm.confirm_password" type="password" placeholder="请再次输入新密码" show-password>
                  <template #prepend><el-icon><Lock /></el-icon></template>
                </el-input>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="securitySaving" @click="saveSecurity">修改密码</el-button>
                <el-button @click="resetSecurityForm">重置</el-button>
              </el-form-item>
            </el-form>

            <el-divider />
            <div class="pp-section-header">
              <h3>登录状态</h3>
              <p>当前登录信息</p>
            </div>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="登录状态">
                <el-tag type="success" size="small">已登录</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="Token有效期">24小时</el-descriptions-item>
            </el-descriptions>
          </div>

          <div v-if="activeTab === 'preferences'">
            <div class="pp-section-header">
              <h3>偏好设置</h3>
              <p>自定义你的使用体验</p>
            </div>
            <el-form label-width="120px" class="pp-form">
              <el-form-item label="主题">
                <el-radio-group v-model="prefsForm.theme" @change="onThemeChange">
                  <el-radio-button value="light">
                    <el-icon><Sunny /></el-icon> 浅色
                  </el-radio-button>
                  <el-radio-button value="dark">
                    <el-icon><Moon /></el-icon> 深色
                  </el-radio-button>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="棋盘方向">
                <el-radio-group v-model="prefsForm.boardOrientation">
                  <el-radio-button value="white">白方在下</el-radio-button>
                  <el-radio-button value="black">黑方在下</el-radio-button>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="自动播放速度">
                <el-slider
                  v-model="prefsForm.autoPlaySpeed"
                  :min="200"
                  :max="3000"
                  :step="100"
                  :format-tooltip="(v) => v + 'ms'"
                  style="max-width: 300px"
                />
              </el-form-item>
              <el-form-item label="分析深度">
                <el-select v-model="prefsForm.analysisDepth" style="width: 200px">
                  <el-option :value="10" label="快速 (depth 10)" />
                  <el-option :value="15" label="标准 (depth 15)" />
                  <el-option :value="20" label="深度 (depth 20)" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="savePreferences">保存偏好</el-button>
                <el-button @click="resetPreferences">恢复默认</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  UserFilled, User, Lock, Setting, Message, Calendar, Star,
  Sunny, Moon,
} from '@element-plus/icons-vue'
import { useUserStore, useUiStore } from '@/store'
import { updateProfile } from '@/api/auth'

const userStore = useUserStore()
const uiStore = useUiStore()

const activeTab = ref('info')
const infoFormRef = ref(null)
const securityFormRef = ref(null)
const infoSaving = ref(false)
const securitySaving = ref(false)

const infoForm = reactive({
  username: '',
  email: '',
})

const securityForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const prefsForm = reactive({
  theme: localStorage.getItem('theme') || 'light',
  boardOrientation: localStorage.getItem('boardOrientation') || 'white',
  autoPlaySpeed: parseInt(localStorage.getItem('autoPlaySpeed') || '1000'),
  analysisDepth: parseInt(localStorage.getItem('analysisDepth') || '20'),
})

const infoRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 80, message: '用户名需3-80个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱', trigger: 'blur' },
  ],
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== securityForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const securityRules = {
  old_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const passwordStrength = computed(() => {
  const pwd = securityForm.new_password
  if (!pwd) return 0
  let score = 0
  if (pwd.length >= 6) score += 1
  if (pwd.length >= 10) score += 1
  if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score += 1
  if (/\d/.test(pwd)) score += 1
  if (/[^a-zA-Z0-9]/.test(pwd)) score += 1
  return score
})

const passwordStrengthPercent = computed(() => passwordStrength.value * 20)

const passwordStrengthClass = computed(() => {
  const s = passwordStrength.value
  if (s <= 1) return 'strength-weak'
  if (s <= 3) return 'strength-medium'
  return 'strength-strong'
})

const passwordStrengthText = computed(() => {
  const s = passwordStrength.value
  if (s <= 1) return '弱'
  if (s <= 3) return '中'
  return '强'
})

function onTabSelect(tab) {
  activeTab.value = tab
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '-'
  return d.toLocaleString('zh-CN')
}

function resetInfoForm() {
  infoForm.username = userStore.user?.username || ''
  infoForm.email = userStore.user?.email || ''
}

function resetSecurityForm() {
  securityForm.old_password = ''
  securityForm.new_password = ''
  securityForm.confirm_password = ''
}

async function saveInfo() {
  if (!infoFormRef.value) return
  await infoFormRef.value.validate()
  infoSaving.value = true
  try {
    await updateProfile({ username: infoForm.username, email: infoForm.email })
    await userStore.fetchUser()
    ElMessage.success('个人信息已更新')
  } catch (e) {
    console.error('Update profile error:', e)
  } finally {
    infoSaving.value = false
  }
}

async function saveSecurity() {
  if (!securityFormRef.value) return
  await securityFormRef.value.validate()
  securitySaving.value = true
  try {
    await updateProfile({
      old_password: securityForm.old_password,
      new_password: securityForm.new_password,
    })
    ElMessage.success('密码已修改，请重新登录')
    securityForm.old_password = ''
    securityForm.new_password = ''
    securityForm.confirm_password = ''
    userStore.logout()
    window.location.href = '/login'
  } catch (e) {
    console.error('Change password error:', e)
  } finally {
    securitySaving.value = false
  }
}

function onThemeChange(theme) {
  uiStore.setTheme(theme)
}

function savePreferences() {
  localStorage.setItem('boardOrientation', prefsForm.boardOrientation)
  localStorage.setItem('autoPlaySpeed', String(prefsForm.autoPlaySpeed))
  localStorage.setItem('analysisDepth', String(prefsForm.analysisDepth))
  ElMessage.success('偏好设置已保存')
}

function resetPreferences() {
  prefsForm.theme = 'light'
  prefsForm.boardOrientation = 'white'
  prefsForm.autoPlaySpeed = 1000
  prefsForm.analysisDepth = 20
  uiStore.setTheme('light')
  localStorage.removeItem('boardOrientation')
  localStorage.removeItem('autoPlaySpeed')
  localStorage.removeItem('analysisDepth')
  ElMessage.success('已恢复默认设置')
}

onMounted(async () => {
  if (userStore.isLoggedIn && !userStore.user) {
    await userStore.fetchUser()
  }
  infoForm.username = userStore.user?.username || ''
  infoForm.email = userStore.user?.email || ''
})
</script>

<style scoped>
.profile-page {
  max-width: 1000px;
  margin: 0 auto;
}

.pp-sidebar {
  position: sticky;
  top: 80px;
}

.pp-avatar-section {
  text-align: center;
  padding: 20px 0 16px;
  border-bottom: 1px solid var(--border-color-lighter);
  margin-bottom: 8px;
}

.pp-avatar {
  background: #409eff;
  font-size: 36px;
}

.pp-username {
  margin: 12px 0 4px;
  font-size: 18px;
  color: var(--text-color);
}

.pp-email {
  margin: 0;
  font-size: 13px;
  color: var(--text-color-secondary);
}

.pp-content {
  min-height: 500px;
}

.pp-section-header {
  margin-bottom: 24px;
}

.pp-section-header h3 {
  margin: 0 0 4px;
  font-size: 18px;
  color: var(--text-color);
}

.pp-section-header p {
  margin: 0;
  font-size: 13px;
  color: var(--text-color-secondary);
}

.pp-form {
  max-width: 500px;
}

.pp-form-tip {
  font-size: 12px;
  color: var(--text-color-placeholder);
  margin-top: 4px;
}

.pp-password-strength {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.pp-strength-bar {
  flex: 1;
  height: 6px;
  background: #e4e7ed;
  border-radius: 3px;
  overflow: hidden;
}

.pp-strength-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s, background 0.3s;
}

.strength-weak .pp-strength-fill,
.pp-strength-fill.strength-weak {
  background: #f56c6c;
}

.strength-medium .pp-strength-fill,
.pp-strength-fill.strength-medium {
  background: #e6a23c;
}

.strength-strong .pp-strength-fill,
.pp-strength-fill.strength-strong {
  background: #67c23a;
}

.pp-strength-text {
  font-size: 12px;
  font-weight: 600;
  min-width: 20px;
}

.pp-strength-text.strength-weak {
  color: #f56c6c;
}

.pp-strength-text.strength-medium {
  color: #e6a23c;
}

.pp-strength-text.strength-strong {
  color: #67c23a;
}

@media (max-width: 768px) {
  .pp-sidebar {
    position: static;
    margin-bottom: 16px;
  }
}
</style>
