import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(false)
  const theme = ref(localStorage.getItem('theme') || 'light')
  const loading = ref(false)
  const notifications = ref([])

  let notifId = 0

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setTheme(newTheme) {
    theme.value = newTheme
    localStorage.setItem('theme', newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  function setLoading(val) {
    loading.value = val
  }

  function addNotification(notification) {
    const id = ++notifId
    const item = {
      id,
      type: notification.type || 'info',
      title: notification.title || '',
      message: notification.message || '',
      duration: notification.duration ?? 5000,
      timestamp: Date.now(),
    }
    notifications.value.push(item)

    if (item.duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, item.duration)
    }

    return id
  }

  function removeNotification(id) {
    const idx = notifications.value.findIndex((n) => n.id === id)
    if (idx !== -1) {
      notifications.value.splice(idx, 1)
    }
  }

  function clearNotifications() {
    notifications.value = []
  }

  setTheme(theme.value)

  return {
    sidebarCollapsed,
    theme,
    loading,
    notifications,
    toggleSidebar,
    setTheme,
    setLoading,
    addNotification,
    removeNotification,
    clearNotifications,
  }
})
