import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/games',
    name: 'GameList',
    component: () => import('@/views/GameList.vue'),
    meta: { title: '棋谱库' },
  },
  {
    path: '/games/:id',
    name: 'GameDetail',
    component: () => import('@/views/GameDetail.vue'),
    meta: { title: '对局详情' },
  },
  {
    path: '/players',
    name: 'PlayerList',
    component: () => import('@/views/PlayerList.vue'),
    meta: { title: '棋手列表' },
  },
  {
    path: '/players/:id',
    name: 'PlayerDetail',
    component: () => import('@/views/PlayerDetail.vue'),
    meta: { title: '棋手详情' },
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/Upload.vue'),
    meta: { title: '上传棋谱', requiresAuth: true },
  },
  {
    path: '/analysis',
    name: 'AnalysisQueue',
    component: () => import('@/views/AnalysisQueue.vue'),
    meta: { title: '分析队列', requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { title: '个人设置', requiresAuth: true },
  },
  {
    path: '/openings',
    name: 'OpeningLibrary',
    component: () => import('@/views/OpeningLibrary.vue'),
    meta: { title: '开局库' },
  },
  {
    path: '/help',
    name: 'Help',
    component: () => import('@/views/Help.vue'),
    meta: { title: '帮助中心' },
  },
  {
    path: '/puzzles',
    name: 'PuzzleLibrary',
    component: () => import('@/views/PuzzleLibrary.vue'),
    meta: { title: '残局库' },
  },
  {
    path: '/practice',
    name: 'Practice',
    component: () => import('@/views/Practice.vue'),
    meta: { title: 'AI对弈练习' },
  },
  {
    path: '/practice/history',
    name: 'PracticeHistory',
    component: () => import('@/views/PracticeHistory.vue'),
    meta: { title: '练习历史' },
  },
  {
    path: '/practice/review/:id',
    name: 'PracticeReview',
    component: () => import('@/views/PracticeReview.vue'),
    meta: { title: '练习复盘' },
  },
  {
    path: '/stats',
    name: 'Stats',
    component: () => import('@/views/Stats.vue'),
    meta: { title: '数据分析' },
  },
  {
    path: '/favorites',
    name: 'Favorites',
    component: () => import('@/views/Favorites.vue'),
    meta: { title: '我的收藏', requiresAuth: true },
  },
  {
    path: '/browsing',
    name: 'BrowsingHistory',
    component: () => import('@/views/BrowsingHistory.vue'),
    meta: { title: '最近浏览' },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Login.vue'),
    meta: { title: '注册', guest: true },
  },
  {
    path: '/test',
    name: 'ComponentTest',
    component: () => import('@/views/ComponentTest.vue'),
    meta: { title: '组件测试' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/Home.vue'),
    meta: { title: '页面未找到' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    }
    return { top: 0, behavior: 'smooth' }
  },
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || '国际象棋数据管理系统'} - ChessDB`

  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta.guest && token) {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router
