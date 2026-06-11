# 前端API层 (`frontend/src/api/`)

## 概述

API 层封装了所有与后端交互的 HTTP 请求，基于 Axios 实例化配置，提供统一的请求拦截、响应处理、错误处理和认证管理。每个业务模块对应一个独立文件，导出纯函数供组件和 Store 调用。

## 文件结构

```
api/
├── request.js       # Axios 实例 + 拦截器（核心）
├── auth.js          # 认证 API
├── games.js         # 棋谱管理 API
├── players.js       # 棋手管理 API
├── openings.js      # 开局管理 API
├── analysis.js      # 分析管理 API
├── collections.js   # 收藏管理 API
├── practice.js      # 练习管理 API
└── browsing.js      # 浏览历史 API
```

---

## 核心模块: request.js

### Axios 实例配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `baseURL` | `/api` | 统一前缀，由 Vite 代理转发 |
| `timeout` | 60000 | 超时 60 秒（适应长时间分析） |
| `Content-Type` | `application/json` | 默认 JSON 格式 |

### 请求拦截器

```javascript
// 自动附加 JWT Token
const token = localStorage.getItem('token')
if (token) {
  config.headers.Authorization = `Bearer ${token}`
}
```

**设计要点**: Token 存储在 `localStorage`，每次请求自动从本地读取并附加到 `Authorization` 头。

### 响应拦截器

**成功响应**: 直接返回 `response.data`（解包 Axios 响应对象）

**错误处理**:

| 状态码 | 处理方式 |
|--------|----------|
| 400 | `ElMessage.error` 提示参数错误 |
| 401 | 触发 Token 过期处理（跳转登录页） |
| 403 | `ElMessage.error` 提示无权限 |
| 404 | `ElMessage.error` 提示资源不存在 |
| 410 | 标记 `error._sessionExpired = true`（练习会话过期） |
| 422 | `ElMessage.error` 提示验证失败 |
| 429 | `ElMessage.error` 提示请求频繁 |
| 500 | `ElMessage.error` 提示服务器错误 |

### Token 过期处理 (`handleTokenExpired`)

```
1. 防重入: isRefreshing 标志防止多个 401 同时触发
2. 清除本地 Token
3. 执行所有待处理的请求回调
4. 1.5秒后跳转登录页（携带当前路径作为 redirect 参数）
```

**设计要点**: 使用 `isRefreshing` + `pendingRequests` 队列实现单次刷新，避免多个并发 401 响应导致重复跳转。

---

## 业务模块 API

### auth.js — 认证 API

| 函数 | 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|------|
| `login(credentials)` | POST | `/auth/login` | `{username, password}` | 用户登录 |
| `register(data)` | POST | `/auth/register` | `{username, email, password}` | 用户注册 |
| `getProfile()` | GET | `/auth/profile` | - | 获取用户资料 |
| `updateProfile(data)` | PUT | `/auth/profile` | `{username?, email?, old_password?, new_password?}` | 更新资料 |
| `logout()` | POST | `/auth/logout` | - | 用户登出 |

---

### games.js — 棋谱管理 API

| 函数 | 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|------|
| `getGames(params)` | GET | `/games` | 分页/筛选/排序参数 | 棋谱列表 |
| `getGameFilters()` | GET | `/games/filters` | - | 获取筛选选项 |
| `getGame(id)` | GET | `/games/:id` | - | 棋谱详情 |
| `uploadGames(files)` | POST | `/games/upload` | FormData(files) | 上传PGN文件 |
| `updateGame(id, data)` | PUT | `/games/:id` | 更新数据 | 更新棋谱 |
| `deleteGame(id)` | DELETE | `/games/:id` | - | 删除棋谱 |
| `analyzeGame(id, params)` | POST | `/games/:id/analyze` | 分析参数 | 同步分析 |
| `getGameMoves(id)` | GET | `/games/:id/moves` | - | 获取着法列表 |
| `getGameAnalysis(id)` | GET | `/games/:id/analysis` | - | 获取分析结果 |

**特殊处理**: `uploadGames` 使用 `FormData` + `multipart/form-data` Content-Type 支持文件上传，支持单文件和多文件。

---

### players.js — 棋手管理 API

| 函数 | 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|------|
| `getPlayers(params)` | GET | `/players` | 分页/筛选参数 | 棋手列表 |
| `getPlayerFilters()` | GET | `/players/filters` | - | 获取筛选选项 |
| `getPlayer(id)` | GET | `/players/:id` | - | 棋手详情 |
| `getPlayerGames(id, params)` | GET | `/players/:id/games` | 分页/颜色/结果 | 棋手对局 |
| `getPlayerStats(id)` | GET | `/players/:id/stats` | - | 棋手统计 |

---

### openings.js — 开局管理 API

| 函数 | 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|------|
| `getOpenings(params)` | GET | `/openings` | 分页/筛选参数 | 开局列表 |
| `getOpening(id)` | GET | `/openings/:id` | - | 开局详情 |
| `identifyOpening(moves)` | POST | `/openings/identify` | `{moves: [...]}` | 识别开局 |
| `getOpeningTree(eco)` | GET | `/openings/tree` | `{eco?}` | 开局分类树 |

---

### analysis.js — 分析管理 API

| 函数 | 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|------|
| `startAnalysis(gameId, params)` | POST | `/analysis/game/:id/start` | 分析参数 | 启动异步分析 |
| `getAnalysisStatus(gameId)` | GET | `/analysis/game/:id/status` | - | 分析状态 |
| `getAnalysisResult(gameId)` | GET | `/analysis/game/:id` | - | 分析结果 |
| `getMoveAnalysis(gameId, moveNumber)` | GET | `/analysis/game/:id/move/:n` | - | 单着分析 |
| `getTaskStatus(taskId)` | GET | `/analysis/tasks/:id` | - | 任务状态 |
| `listAnalysisTasks()` | GET | `/analysis/tasks` | - | 任务列表 |
| `cancelAnalysisTask(taskId)` | DELETE | `/analysis/tasks/:id` | - | 取消任务 |
| `getEngineInfo()` | GET | `/analysis/engines` | - | 引擎信息 |

---

### collections.js — 收藏管理 API

| 函数 | 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|------|
| `getCollections(params)` | GET | `/collections` | 分页参数 | 收藏列表 |
| `addCollection(gameId, note)` | POST | `/collections` | `{game_id, note}` | 添加收藏 |
| `removeCollection(collectionId)` | DELETE | `/collections/:id` | - | 删除收藏 |
| `checkCollection(gameId)` | GET | `/collections/check/:gameId` | - | 检查是否已收藏 |
| `updateCollectionNote(collectionId, note)` | PUT | `/collections/:id` | `{note}` | 更新备注 |

---

### practice.js — 练习管理 API

| 函数 | 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|------|
| `getPuzzles(params)` | GET | `/practice/puzzles` | 分页/筛选 | 残局列表 |
| `getPuzzle(puzzleId)` | GET | `/practice/puzzles/:id` | - | 残局详情 |
| `createPuzzle(data)` | POST | `/practice/puzzles` | 残局数据 | 创建残局 |
| `deletePuzzle(puzzleId)` | DELETE | `/practice/puzzles/:id` | - | 删除残局 |
| `startPractice(data)` | POST | `/practice/start` | 模式/难度等 | 开始练习 |
| `makeMove(data)` | POST | `/practice/move` | `{session_id, san}` | 走子 |
| `undoMove(data)` | POST | `/practice/undo` | `{session_id}` | 悔棋 |
| `getHint(data)` | POST | `/practice/hint` | `{session_id}` | 获取提示 |
| `resignPractice(data)` | POST | `/practice/resign` | `{session_id}` | 认输 |
| `getPracticeStatus(sessionId)` | GET | `/practice/status/:id` | - | 对局状态 |
| `getPracticeHistory(params)` | GET | `/practice/history` | 分页参数 | 练习历史 |
| `getPracticeDetail(practiceId)` | GET | `/practice/history/:id` | - | 练习详情 |
| `searchGames(params)` | GET | `/practice/search_games` | 搜索参数 | 搜索棋谱 |
| `startPracticeAnalysis(practiceId)` | POST | `/practice/analyze/:id` | - | 启动复盘分析 |
| `getPracticeAnalysisStatus(practiceId)` | GET | `/practice/analyze/:id/status` | - | 复盘分析状态 |
| `getPracticeAnalysisResult(practiceId)` | GET | `/practice/analyze/:id/result` | - | 复盘分析结果 |

---

### browsing.js — 浏览历史 API

| 函数 | 方法 | 路径 | 参数 | 说明 |
|------|------|------|------|------|
| `getBrowsingHistory(params)` | GET | `/browsing` | 分页参数 | 浏览历史 |
| `recordBrowsing(gameId)` | POST | `/browsing` | `{game_id}` | 记录浏览 |
| `deleteBrowsing(gameId)` | DELETE | `/browsing/:gameId` | - | 删除记录 |
| `clearBrowsing()` | POST | `/browsing/clear` | - | 清空历史 |

---

## API 调用统计

| 模块 | 函数数量 | 认证要求 |
|------|----------|----------|
| auth | 5 | login/register 无需认证 |
| games | 9 | upload/update/delete/analyze 需认证 |
| players | 5 | 全部无需认证 |
| openings | 4 | 全部无需认证 |
| analysis | 8 | start 需认证 |
| collections | 5 | 全部需认证 |
| practice | 16 | 部分 optional 认证 |
| browsing | 4 | 全部需认证 |
| **合计** | **56** | - |

## 设计模式

1. **单例 Axios**: 所有模块共享同一个 `request` 实例，统一拦截器行为
2. **纯函数导出**: 每个 API 函数是无状态的纯函数，参数明确，返回 Promise
3. **自动认证**: 请求拦截器自动附加 Token，调用方无需关心认证细节
4. **统一错误处理**: 响应拦截器统一处理错误提示，410 状态码通过 `_sessionExpired` 标记供业务层识别
5. **FormData 上传**: 文件上传自动构建 FormData，设置正确的 Content-Type
