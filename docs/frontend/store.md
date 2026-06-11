# 前端状态管理 (`frontend/src/store/`)

## 概述

状态管理层基于 Pinia 2.x 实现，采用 Composition API 风格（`defineStore` + setup 函数）。共 5 个 Store，分别管理用户认证、棋谱回放、练习对弈、主题切换和 UI 状态。

## 文件结构

```
store/
├── index.js          # Pinia 实例创建 + 统一导出
├── userStore.js      # 用户认证状态
├── gameStore.js      # 棋谱回放状态
├── practiceStore.js  # 练习对弈状态
├── themeStore.js     # 主题切换状态
└── uiStore.js        # UI 通用状态
```

---

## Store 详解

### 1. userStore — 用户认证状态

**Store ID**: `user`

#### 状态

| 属性 | 类型 | 初始值 | 说明 |
|------|------|--------|------|
| `user` | ref\<Object\|null\> | null | 当前用户信息 |
| `token` | ref\<string\> | localStorage.token 或 '' | JWT Token |
| `isLoggedIn` | computed | `!!token` | 是否已登录 |

#### 动作

| 动作 | 参数 | 说明 |
|------|------|------|
| `login(credentials)` | `{username, password}` | 登录 → 存储 Token + 用户信息到 localStorage |
| `register(data)` | `{username, email, password}` | 注册 |
| `fetchUser()` | - | 获取用户资料（Token 存在时） |
| `updateUserData(data)` | 更新数据 | 更新用户资料 |
| `logout()` | - | 登出 → 清除 Token + 用户信息 |
| `checkAuth()` | - | 检查认证状态（Token 有效性验证） |

**设计要点**:
- Token 持久化到 `localStorage`，页面刷新后自动恢复
- `checkAuth()` 在应用初始化时调用，验证 Token 是否仍有效
- 登出时即使 API 调用失败也清除本地状态

---

### 2. gameStore — 棋谱回放状态

**Store ID**: `game`

#### 状态

| 属性 | 类型 | 初始值 | 说明 |
|------|------|--------|------|
| `currentGame` | ref\<Object\|null\> | null | 当前棋谱数据 |
| `currentMove` | ref\<number\> | 0 | 当前着法序号（0=初始局面） |
| `isPlaying` | ref\<boolean\> | false | 是否自动播放 |
| `playSpeed` | ref\<number\> | 1000 | 播放速度(ms) |
| `moves` | ref\<Array\> | [] | 着法列表（含 FEN/SAN/eval_data） |
| `analysisData` | ref\<Array\|null\> | null | 分析数据 |
| `loading` | ref\<boolean\> | false | 加载状态 |

#### 计算属性

| 属性 | 说明 |
|------|------|
| `totalMoves` | 总着法数（moves.length - 1） |
| `currentFen` | 当前局面的 FEN |
| `currentLastMove` | 当前着法的起止格 {from, to} |
| `currentTurn` | 当前走棋方（white/black） |
| `currentEvalScore` | 当前着法评分 |
| `currentMoveEval` | 当前着法完整评价数据 |
| `displayMoves` | 格式化着法列表（按回合分组） |

#### 动作

| 动作 | 说明 |
|------|------|
| `loadGame(gameId)` | 加载棋谱 + 着法 + 分析数据 |
| `nextMove()` | 前进一着 |
| `prevMove()` | 后退一着 |
| `jumpToMove(n)` | 跳转到第 n 着 |
| `startAutoPlay()` | 开始自动播放 |
| `stopAutoPlay()` | 停止自动播放 |
| `setSpeed(speed)` | 设置播放速度 |
| `requestAnalysis(gameId, params)` | 请求分析 |
| `reset()` | 重置所有状态 |

**设计要点**:
- `moves[0]` 为初始局面（标准 FEN），`moves[1]` 起为实际着法
- `displayMoves` 将着法按回合分组为 `{move_number, white, black, white_eval, black_eval}`
- `loadGame` 同时尝试加载已有分析数据
- 自动播放使用 `setInterval`，切换速度时重新启动定时器

---

### 3. practiceStore — 练习对弈状态

**Store ID**: `practice`

#### 状态

| 属性 | 类型 | 初始值 | 说明 |
|------|------|--------|------|
| `sessionId` | ref\<string\|null\> | null | 练习会话ID |
| `currentFen` | ref\<string\> | 初始FEN | 当前局面 |
| `isUserTurn` | ref\<boolean\> | true | 是否用户回合 |
| `userColor` | ref\<string\> | 'white' | 用户执子颜色 |
| `difficulty` | ref\<string\> | 'medium' | 难度 |
| `mode` | ref\<string\|null\> | null | 模式（puzzle/from_game/custom） |
| `puzzleInfo` | ref\<Object\|null\> | null | 残局信息 |
| `startFen` | ref\<string\> | 初始FEN | 起始局面 |
| `moveHistory` | ref\<Array\> | [] | 走法历史 [{san, color}] |
| `isGameOver` | ref\<boolean\> | false | 对局是否结束 |
| `result` | ref\<string\|null\> | null | 对局结果 |
| `lastAiMove` | ref\<string\|null\> | null | AI 上一着 |
| `lastMoveFromTo` | ref\<Object\|null\> | null | 上一着起止格 |
| `hintsUsed` | ref\<number\> | 0 | 使用提示次数 |
| `undoCount` | ref\<number\> | 0 | 悔棋次数 |
| `startTime` | ref\<number\|null\> | null | 开始时间戳 |
| `hintData` | ref\<Object\|null\> | null | 提示数据 |
| `showHint` | ref\<boolean\> | false | 是否显示提示 |
| `loading` | ref\<boolean\> | false | 加载状态 |
| `aiThinking` | ref\<boolean\> | false | AI 思考中 |
| `error` | ref\<string\|null\> | null | 错误信息 |
| `puzzles` | ref\<Array\> | [] | 残局列表 |
| `sessionExpired` | ref\<boolean\> | false | 会话是否过期 |

#### 计算属性

| 属性 | 说明 |
|------|------|
| `currentTurn` | 当前走棋方 |
| `positions` | 完整局面列表（从起始FEN逐步推演） |

#### 动作

| 动作 | 说明 |
|------|------|
| `loadPuzzles(params)` | 加载残局列表 |
| `startFromPuzzle(puzzleId, color, diff)` | 从残局开始练习 |
| `startFromGame(gameId, fromMove, color, diff)` | 从棋谱开始练习 |
| `startCustom(fen, color, diff)` | 自定义FEN开始练习 |
| `submitMove(san)` | 提交走子（含AI应着延迟） |
| `undo()` | 悔棋（撤回用户+AI两步） |
| `requestHint()` | 获取提示 |
| `resign()` | 认输 |
| `reset()` | 重置所有状态 |

**设计要点**:
- **AI 延迟**: `submitMove` 中 AI 应着前添加 400-1200ms 随机延迟，模拟思考
- **会话过期**: 检测 410 状态码，设置 `sessionExpired` 标志
- **本地 FEN 重建**: 悔棋时通过 `chess.js` 从 `startFen` 重新推演所有着法获取当前 FEN
- **走法历史**: 同时维护服务端状态和本地 `moveHistory`，用于复盘

---

### 4. themeStore — 主题切换状态

**Store ID**: `theme`

#### 状态

| 属性 | 类型 | 初始值 | 说明 |
|------|------|--------|------|
| `mode` | ref\<string\> | localStorage 或 'auto' | 主题模式（light/dark/auto） |
| `systemPreference` | ref\<string\> | 系统偏好 | 系统暗色模式偏好 |
| `isDark` | computed | 根据mode和系统偏好计算 | 当前是否暗色 |

#### 动作

| 动作 | 说明 |
|------|------|
| `setMode(newMode)` | 设置主题模式（持久化到 localStorage） |
| `toggle()` | 切换主题（auto→实际反色，light↔dark） |
| `init()` | 初始化（从 localStorage 恢复） |

**设计要点**:
- 通过 `matchMedia('(prefers-color-scheme: dark)')` 监听系统主题变化
- `isDark` 变化时自动切换 `document.documentElement.classList` 的 `dark` 类
- 三种模式: light(亮色), dark(暗色), auto(跟随系统)
- `init()` 在 `main.js` 中应用启动时调用

---

### 5. uiStore — UI 通用状态

**Store ID**: `ui`

#### 状态

| 属性 | 类型 | 初始值 | 说明 |
|------|------|--------|------|
| `sidebarCollapsed` | ref\<boolean\> | false | 侧边栏是否折叠 |
| `theme` | ref\<string\> | localStorage 或 'light' | 主题（与 themeStore 独立） |
| `loading` | ref\<boolean\> | false | 全局加载状态 |
| `notifications` | ref\<Array\> | [] | 通知列表 |

#### 动作

| 动作 | 说明 |
|------|------|
| `toggleSidebar()` | 切换侧边栏折叠 |
| `setTheme(newTheme)` | 设置主题（持久化 + 设置 data-theme 属性） |
| `setLoading(val)` | 设置全局加载状态 |
| `addNotification(notification)` | 添加通知（自动定时移除） |
| `removeNotification(id)` | 移除通知 |
| `clearNotifications()` | 清空所有通知 |

**通知格式**:
```javascript
{
  id: number,         // 自增ID
  type: 'info'|'success'|'warning'|'error',
  title: string,
  message: string,
  duration: number,   // 自动消失时间(ms)，0=不消失
  timestamp: number,
}
```

**设计要点**: `setTheme` 同时设置 `data-theme` 属性和 localStorage，与 `themeStore` 存在功能重叠（历史遗留）。

---

## Store 间关系

```
userStore ←── Login/Register 视图
    │
    ├── token → request.js 拦截器（自动附加）
    └── isLoggedIn → 路由守卫

gameStore ←── GameDetail 视图
    │
    ├── moves → MoveList 组件
    ├── currentFen → ChessBoard 组件
    ├── analysisData → WinRateChart 组件
    └── currentMoveEval → MoveEvaluation 组件

practiceStore ←── Practice 视图
    │
    ├── currentFen → PracticeBoard 组件
    ├── moveHistory → 复盘
    └── sessionExpired → 错误处理

themeStore ←── ThemeSwitch 组件
    │
    └── isDark → document.documentElement.classList

uiStore ←── AppLayout
    └── sidebarCollapsed → 侧边栏
```

## 通用设计模式

1. **Composition API 风格**: 所有 Store 使用 `defineStore('id', () => {})` setup 语法
2. **持久化**: Token 和主题偏好存储在 `localStorage`
3. **API 集成**: userStore、gameStore、practiceStore 直接调用 API 层函数
4. **错误处理**: practiceStore 统一处理会话过期（410），其他 Store 依赖 request.js 拦截器
5. **响应式计算**: 棋盘 FEN、评价数据等通过 computed 实时计算
