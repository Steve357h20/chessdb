import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

let isRefreshing = false
let pendingRequests = []

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code && res.code !== 200 && res.code !== 0) {
      const msg = res.message || res.msg || '请求失败'
      ElMessage.error(msg)
      return Promise.reject(new Error(msg))
    }
    return res
  },
  (error) => {
    if (!error.response) {
      ElMessage.error('网络连接失败，请检查网络')
      return Promise.reject(error)
    }

    const { status, data } = error.response
    const msg = data?.message || data?.msg || data?.detail || ''
    const errorCode = data?.error || ''

    switch (status) {
      case 400:
        ElMessage.error(msg || '请求参数错误')
        break
      case 401:
        handleTokenExpired()
        break
      case 403:
        ElMessage.error(msg || '没有操作权限')
        break
      case 404:
        ElMessage.error(msg || '请求的资源不存在')
        break
      case 410:
        error._sessionExpired = true
        break
      case 422:
        ElMessage.error(msg || '数据验证失败')
        break
      case 429:
        ElMessage.error('请求过于频繁，请稍后再试')
        break
      case 500:
        ElMessage.error(msg || '服务器内部错误')
        break
      default:
        ElMessage.error(msg || `请求失败 (${status})`)
    }

    return Promise.reject(error)
  }
)

function handleTokenExpired() {
  if (!isRefreshing) {
    isRefreshing = true
    ElMessage.error('登录已过期，请重新登录')
    localStorage.removeItem('token')
    pendingRequests.forEach((cb) => cb())
    pendingRequests = []
    setTimeout(() => {
      const currentPath = window.location.pathname
      if (currentPath !== '/login') {
        window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`
      }
      isRefreshing = false
    }, 1500)
  }

  return new Promise(() => {})
}

export default request
