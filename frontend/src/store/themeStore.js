import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const mode = ref(localStorage.getItem('theme-mode') || 'auto')
  const systemPreference = ref('light')

  if (typeof window !== 'undefined') {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    systemPreference.value = mediaQuery.matches ? 'dark' : 'light'
    mediaQuery.addEventListener('change', (e) => {
      systemPreference.value = e.matches ? 'dark' : 'light'
    })
  }

  const isDark = computed(() => {
    if (mode.value === 'auto') return systemPreference.value === 'dark'
    return mode.value === 'dark'
  })

  watch(isDark, (val) => {
    document.documentElement.classList.toggle('dark', val)
  }, { immediate: true })

  function setMode(newMode) {
    mode.value = newMode
    localStorage.setItem('theme-mode', newMode)
  }

  function toggle() {
    if (mode.value === 'auto') {
      setMode(isDark.value ? 'light' : 'dark')
    } else {
      setMode(mode.value === 'dark' ? 'light' : 'dark')
    }
  }

  function init() {
    const saved = localStorage.getItem('theme-mode')
    if (saved && ['light', 'dark', 'auto'].includes(saved)) {
      mode.value = saved
    }
  }

  return { mode, systemPreference, isDark, setMode, toggle, init }
})
