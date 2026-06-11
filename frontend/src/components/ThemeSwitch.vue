<template>
  <el-dropdown trigger="click" @command="handleCommand">
    <el-button :icon="currentIcon" circle class="theme-switch-btn" />
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="light" :class="{ 'is-active': store.mode === 'light' }">
          <el-icon><Sunny /></el-icon> 亮色模式
        </el-dropdown-item>
        <el-dropdown-item command="dark" :class="{ 'is-active': store.mode === 'dark' }">
          <el-icon><Moon /></el-icon> 暗色模式
        </el-dropdown-item>
        <el-dropdown-item command="auto" :class="{ 'is-active': store.mode === 'auto' }">
          <el-icon><Monitor /></el-icon> 跟随系统
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { Sunny, Moon, Monitor } from '@element-plus/icons-vue'
import { useThemeStore } from '@/store/themeStore'

const store = useThemeStore()

const currentIcon = computed(() => {
  if (store.mode === 'auto') return Monitor
  return store.isDark ? Moon : Sunny
})

function handleCommand(command) {
  store.setMode(command)
}
</script>

<style scoped>
.theme-switch-btn {
  border-color: var(--border-color);
  background: var(--card-bg);
  color: var(--text-color);
}

.theme-switch-btn:hover {
  background: var(--hover-bg);
  color: var(--text-color);
}

:deep(.is-active) {
  color: var(--el-color-primary);
  font-weight: 600;
}
</style>
