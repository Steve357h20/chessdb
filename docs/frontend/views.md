# 前端视图与路由 (`frontend/src/views/` + `frontend/src/router/`)

## 概述

视图层包含 19 个页面组件，对应系统的各个功能页面。路由层基于 Vue Router 4 实现，支持路由守卫（认证保护/游客限制）、懒加载、滚动行为恢复和动态标题。

## 路由配置 (`router/index.js`)

### 路由表

| 路径 | 名称 | 组件 | 认证 | 标题 |
|------|------|------|------|------|
| `/` | Home | Home.vue | - | 首页 |
| `/games` | GameList | GameList.vue | - | 棋谱库 |
| `/games/:id` | GameDetail | GameDetail.vue | - | 对局详情 |
| `/players` | PlayerList | PlayerList.vue | - | 棋手列表 |
| `/players/:id` | PlayerDetail | PlayerDetail.vue | - | 棋手详情 |
| `/upload` | Upload | Upload.vue | 需认证 | 上传棋谱 |
| `/analysis` | AnalysisQueue | AnalysisQueue.vue | 需认证 | 分析队列 |
| `/profile` | Profile | Profile.vue | 需认证 | 个人设置 |
| `/openings` | OpeningLibrary | OpeningLibrary.vue | - | 开局库 |
| `/help` | Help | Help.vue | - | 帮助中心 |
| `/puzzles` | PuzzleLibrary | PuzzleLibrary.vue | - | 残局库 |
| `/practice` | Practice | Practice.vue | - | AI对弈练习 |
| `/practice/history` | PracticeHistory | PracticeHistory.vue | - | 练习历史 |
| `/practice/review/:id` | PracticeReview | PracticeReview.vue | - | 练习复盘 |
| `/stats` | Stats | Stats.vue | - | 数据分析 |
| `/favorites` | Favorites | Favorites.vue | 需认证 | 我的收藏 |
| `/browsing` | BrowsingHistory | BrowsingHistory.vue | - | 最近浏览 |
| `/login` | Login | Login.vue | 游客 | 登录 |
| `/register` | Register | Login.vue | 游客 | 注册 |
| `/test` | ComponentTest | ComponentTest.vue | - | 组件测试 |
| `/:pathMatch(.*)*` | NotFound | Home.vue | - | 404 |

### 路由守卫

```javascript
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = `${to.meta.title} - ChessDB`

  const token = localStorage.getItem('token')

  // 需认证页面：未登录跳转登录页（携带 redirect 参数）
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // 游客页面：已登录跳转首页
  if (to.meta.guest && token) {
    next({ name: 'Home' })
    return
  }

  next()
})
```

### 路由特性

- **懒加载**: 所有组件使用 `() => import()` 动态导入
- **滚动恢复**: 优先恢复保存位置，其次处理锚点，默认滚动到顶部
- **HTML5 History**: 使用 `createWebHistory()` 模式

---

## 视图详解

### 1. Home — 首页

**路径**: `/` | **认证**: 无

系统入口页面，展示系统概览、快速入口、最近棋谱、统计数据等。

---

### 2. GameList — 棋谱库

**路径**: `/games` | **认证**: 无

**核心功能**: 棋谱列表浏览，支持分页、筛选（棋手/ECO/结果/日期）、排序、搜索。

**API 调用**: `getGames()`, `getGameFilters()`

---

### 3. GameDetail — 对局详情

**路径**: `/games/:id` | **认证**: 无

**核心功能**: 棋谱详情展示与回放分析，是系统最复杂的视图。

**子组件**: ChessBoard, GameController, MoveList, WinRateChart, MoveEvaluation, AnalysisOverlay, OpeningInfo

**核心交互流程**:
1. 加载棋谱数据和着法列表
2. 通过 GameController 控制回放
3. 点击 MoveList 跳转到指定着法
4. 启动异步分析 → 显示 AnalysisOverlay → 分析完成后展示 WinRateChart + MoveEvaluation
5. 支持收藏、浏览历史记录

**API 调用**: `getGame()`, `getGameMoves()`, `getGameAnalysis()`, `startAnalysis()`, `getAnalysisStatus()`, `checkCollection()`, `addCollection()`, `removeCollection()`, `recordBrowsing()`

---

### 4. PlayerList — 棋手列表

**路径**: `/players` | **认证**: 无

**核心功能**: 棋手列表浏览，支持分页、筛选（国家/头衔/等级分）、搜索。

**API 调用**: `getPlayers()`, `getPlayerFilters()`

---

### 5. PlayerDetail — 棋手详情

**路径**: `/players/:id` | **认证**: 无

**核心功能**: 棋手详情展示，包含基本信息、统计数据、对局列表。

**API 调用**: `getPlayer()`, `getPlayerStats()`, `getPlayerGames()`

---

### 6. Upload — 上传棋谱

**路径**: `/upload` | **认证**: 需认证

**核心功能**: PGN 文件上传和文本导入。

**API 调用**: `uploadGames()`（文件上传）, `uploadGames()`（文本导入，对应后端 `/games/upload-pgn`）

---

### 7. AnalysisQueue — 分析队列

**路径**: `/analysis` | **认证**: 需认证

**核心功能**: 查看和管理异步分析任务，显示任务状态、进度、结果。

**API 调用**: `listAnalysisTasks()`, `getTaskStatus()`, `cancelAnalysisTask()`, `getEngineInfo()`

---

### 8. Profile — 个人设置

**路径**: `/profile` | **认证**: 需认证

**核心功能**: 用户资料编辑，支持修改用户名、邮箱、密码。

**API 调用**: `getProfile()`, `updateProfile()`

---

### 9. OpeningLibrary — 开局库

**路径**: `/openings` | **认证**: 无

**核心功能**: 开局库浏览，支持 ECO 分类树、开局搜索、开局详情。

**API 调用**: `getOpenings()`, `getOpening()`, `getOpeningTree()`, `identifyOpening()`

---

### 10. Help — 帮助中心

**路径**: `/help` | **认证**: 无

**核心功能**: 系统使用帮助和说明文档。

---

### 11. PuzzleLibrary — 残局库

**路径**: `/puzzles` | **认证**: 无

**核心功能**: 残局题目浏览，按分类和难度筛选，支持创建自定义残局。

**API 调用**: `getPuzzles()`, `getPuzzle()`, `createPuzzle()`, `deletePuzzle()`

---

### 12. Practice — AI对弈练习

**路径**: `/practice` | **认证**: 无（可选认证）

**核心功能**: AI 对弈练习，支持三种模式（残局/从棋谱/自定义FEN），五档难度。

**子组件**: PracticeBoard

**核心交互流程**:
1. 选择模式（残局/从棋谱/自定义）
2. 选择难度和执子颜色
3. 开始对局 → PracticeBoard 交互走子
4. AI 自动应着（显示思考动画）
5. 支持悔棋、提示、认输
6. 对局结束自动保存

**API 调用**: `startPractice()`, `makeMove()`, `undoMove()`, `getHint()`, `resignPractice()`, `getPracticeStatus()`, `getPuzzles()`, `searchGames()`

**会话过期处理**: 检测 410 状态码的 `_sessionExpired` 标记，提示用户重新开始。

---

### 13. PracticeHistory — 练习历史

**路径**: `/practice/history` | **认证**: 无（可选认证）

**核心功能**: 查看历史练习记录列表。

**API 调用**: `getPracticeHistory()`

---

### 14. PracticeReview — 练习复盘

**路径**: `/practice/review/:id` | **认证**: 无（可选认证）

**核心功能**: 复盘练习对局，查看走法历史和复盘分析结果。

**子组件**: ChessBoard, GameController, MoveList

**API 调用**: `getPracticeDetail()`, `startPracticeAnalysis()`, `getPracticeAnalysisStatus()`, `getPracticeAnalysisResult()`

---

### 15. Stats — 数据分析

**路径**: `/stats` | **认证**: 无

**核心功能**: 数据统计与分析，使用 ECharts 展示各种图表。

---

### 16. Favorites — 我的收藏

**路径**: `/favorites` | **认证**: 需认证

**核心功能**: 查看和管理收藏的棋谱。

**API 调用**: `getCollections()`, `removeCollection()`, `updateCollectionNote()`

---

### 17. BrowsingHistory — 最近浏览

**路径**: `/browsing` | **认证**: 需认证

**核心功能**: 查看和管理浏览历史。

**API 调用**: `getBrowsingHistory()`, `deleteBrowsing()`, `clearBrowsing()`

---

### 18. Login — 登录/注册

**路径**: `/login` 或 `/register` | **认证**: 游客

**核心功能**: 用户登录和注册，通过路由名称区分模式。

**API 调用**: `login()`, `register()`

**登录成功流程**: 存储 Token → 跳转 redirect 参数指定页面或首页

---

### 19. ComponentTest — 组件测试

**路径**: `/test` | **认证**: 无

**核心功能**: 开发调试用，测试各组件的渲染和交互。

---

## 视图分类

### 按功能域

| 域 | 视图 |
|----|------|
| 棋谱管理 | GameList, GameDetail, Upload |
| 棋手管理 | PlayerList, PlayerDetail |
| 开局库 | OpeningLibrary |
| 分析 | AnalysisQueue, Stats |
| 练习 | PuzzleLibrary, Practice, PracticeHistory, PracticeReview |
| 个人 | Login, Profile, Favorites, BrowsingHistory |
| 系统 | Home, Help, ComponentTest |

### 按认证要求

| 类型 | 视图 |
|------|------|
| 需认证 | Upload, AnalysisQueue, Profile, Favorites |
| 游客专属 | Login(/register) |
| 公开 | 其余所有视图 |
