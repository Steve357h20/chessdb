# 前端组件与组合式函数 (`frontend/src/components/` + `frontend/src/composables/`)

## 概述

组件层包含 10 个可复用的 Vue 3 组件，覆盖棋盘渲染、对局控制、着法列表、分析图表等核心功能。组合式函数层提供 1 个分析覆盖层状态管理钩子。所有组件使用 `<script setup>` + Composition API 编写。

## 文件结构

```
components/
├── ChessBoard.vue        # 通用棋盘组件（查看+交互）
├── PracticeBoard.vue     # 练习专用棋盘（AI对弈）
├── GameController.vue    # 对局播放控制器
├── MoveList.vue          # 着法列表
├── WinRateChart.vue      # 胜率曲线图
├── MoveEvaluation.vue    # 着法评价面板
├── AnalysisOverlay.vue   # 分析进度覆盖层（Canvas动画）
├── OpeningInfo.vue       # 开局信息（占位组件）
├── ThemeSwitch.vue       # 主题切换
└── HelpTooltip.vue       # 帮助提示

composables/
└── useAnalysisOverlay.js # 分析覆盖层状态钩子
```

---

## 组件详解

### 1. ChessBoard — 通用棋盘组件

**核心功能**: 渲染 8×8 棋盘，支持查看模式和交互模式（点击/拖拽走子），支持棋盘翻转、坐标显示、着法高亮。

**Props**:

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `fen` | String | 初始FEN | 当前局面 |
| `lastMove` | Object | null | 上一着 {from, to} |
| `orientation` | String | 'white' | 棋盘朝向 |
| `interactive` | Boolean | false | 是否可交互走子 |
| `showCoordinates` | Boolean | true | 显示坐标 |
| `highlightSquares` | Array | [] | 自定义高亮格子 |
| `boardSize` | Number | 480 | 棋盘像素大小 |
| `moveAnnotation` | Object | null | 着法标注 {symbol, class, label} |

**Events**: `move-made(from, to, promotion)`, `square-click(square)`, `piece-click({square, piece})`

**Expose 方法**: `move()`, `setPosition()`, `flip()`, `highlight()`, `getFen()`, `getChess()`

**实现要点**:
- 基于 `chess.js` 的 `Chess` 类管理棋局状态
- Unicode 棋子渲染（♔♕♖♗♘♙♚♛♜♝♞♟）
- 拖拽走子支持鼠标和触摸事件
- 升变弹窗（后/车/象/马）
- 合法着法提示（空格圆点/吃子圆环）
- 着法标注覆盖（妙手/好着/失误等颜色标记）

---

### 2. PracticeBoard — 练习专用棋盘

**核心功能**: 专为 AI 对弈设计的棋盘，增加 AI 思考状态、提示高亮、将军/将杀视觉效果。

**Props**:

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `fen` | String | 初始FEN | 当前局面 |
| `userColor` | String | 'white' | 用户执子颜色 |
| `lastAiMove` | Object | null | AI上一着 |
| `lastUserMove` | Object | null | 用户上一着 |
| `lastMoveFromTo` | Object | null | 上一着起止格 |
| `hintMove` | String | '' | 提示着法(SAN) |
| `isUserTurn` | Boolean | true | 是否用户回合 |
| `isAiThinking` | Boolean | false | AI是否思考中 |
| `boardSize` | Number | 560 | 棋盘大小 |
| `inCheck` | Boolean | false | 是否被将军 |
| `inCheckmate` | Boolean | false | 是否被将杀 |

**Events**: `move-submit(san)` — 用户走子时触发，传出 SAN 格式着法

**与 ChessBoard 的区别**:
- AI 思考进度条（旋转 Loading 图标）
- AI 走子高亮（橙色 vs 用户走子黄色）
- 提示着法高亮（蓝色圆点/圆环）
- 将军视觉效果（红色径向渐变）
- 将杀视觉效果（深红色背景）
- 非用户回合禁止操作
- 走子以 SAN 格式提交（由父组件处理 API 交互）

---

### 3. GameController — 对局播放控制器

**核心功能**: 棋谱回放控制，支持播放/暂停、前进/后退、跳转、变速、进度条拖拽、键盘快捷键。

**Props**:

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `currentMove` | Number | 0 | 当前着法序号 |
| `totalMoves` | Number | 0 | 总着法数 |
| `isPlaying` | Boolean | false | 是否自动播放 |
| `playSpeed` | Number | 1000 | 播放间隔(ms) |
| `turnInfo` | String | null | 当前走棋方 |
| `evalScore` | Number | null | 当前评分 |

**Events**: `play`, `pause`, `next`, `prev`, `first`, `last`, `jump-to(n)`, `speed-change(ms)`

**播放速度选项**: 0.5x(2000ms), 1x(1000ms), 2x(500ms), 5x(200ms)

**键盘快捷键**: 空格(播放/暂停), ←(后退), →(前进), Home(开头), End(结尾)

**评分显示**: 支持厘兵值和将杀距离（如 +2.5, -M3）

---

### 4. MoveList — 着法列表

**核心功能**: 以标准棋谱格式（1. e4 e5 2. Nf3 Nc6 ...）展示着法，支持点击跳转、评价标注、键盘导航、自动滚动。

**Props**:

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `moves` | Array | [] | 着法数据 |
| `currentMove` | Number | 0 | 当前着法序号 |
| `showEvaluation` | Boolean | true | 显示评价标注 |

**Events**: `move-click(halfMove)` — 点击着法时触发

**评价标注**: 使用 `chessUtils.classifyMove()` 分类，显示 !!/!/!?/?!/??/?? 符号，颜色编码对应评价等级。

**键盘导航**: ↑/←(后退), ↓/→(前进), Home(开头), End(结尾)

---

### 5. WinRateChart — 胜率曲线图

**核心功能**: 基于 ECharts 的双轴图表，展示胜率曲线和评分曲线，支持点击跳转、当前着法标记、暗色主题。

**Props**:

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `analysisData` | Array | [] | 分析数据 |
| `currentMove` | Number | 0 | 当前着法 |
| `height` | Number | 300 | 图表高度 |
| `playerColor` | String | 'w' | 玩家颜色 |

**Events**: `move-select(halfMove)` — 点击图表时触发

**图表特性**:
- 左Y轴: 胜率(0-100%)，蓝色实线 + 渐变面积
- 右Y轴: 评分(-10~+10兵)，灰色虚线
- 50% 参考线（虚线）
- 当前着法标记（金色竖线）
- 数据缩放（滚轮+滑块）
- 3点移动平均平滑
- 自动跟随当前着法显示 tooltip

---

### 6. MoveEvaluation — 着法评价面板

**核心功能**: 展示单步着法的详细评价信息，包括评价徽章、分数、胜率、差距、AI推荐、预测续着、评论。

**Props**:

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `evaluation` | Object | null | 评价数据 |

**评价徽章映射**:

| 符号 | 标签 | 颜色 |
|------|------|------|
| `!!` | 妙手 | 金色 #FFD700 |
| `!` | 好着 | 绿色 #32CD32 |
| `!?` | 有趣 | 蓝色 #4169E1 |
| `?!` | 疑问 | 橙色 #FF8C00 |
| `?` | 坏着 | 红橙 #FF4500 |
| `??` | 大坏着 | 深红 #8B0000 |

**NAG 映射**: 1→!, 2→?, 3→!!, 4→??, 5→!?, 6→?!

**特殊效果**: 严重失误(??/?)时触发红色闪烁动画。

---

### 7. AnalysisOverlay — 分析进度覆盖层

**核心功能**: 分析进行中显示的 Canvas 动画覆盖层，包含棋子波纹干涉动画和两车追逐动画。

**Props**:

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `visible` | Boolean | false | 是否显示 |
| `progress` | Number | 0 | 分析进度(0-100) |
| `topOffset` | Number | 0 | 顶部偏移 |

**Events**: `dismiss` — 点击"后台分析"按钮

**动画系统**:
- **波纹干涉**: 棋子作为波源，计算多源波纹干涉场，渲染彩色波纹效果
- **棋子生命周期**: 淡入(600ms) → 停留(3000ms) → 淡出(800ms) → 波纹延迟(300ms) → 波纹淡出(800ms)
- **两车追逐**: 白车和黑车在2×2网格上循环追逐动画
- **点击交互**: 点击覆盖层任意位置生成新棋子
- **自动生成**: 每2秒随机生成一个棋子（最多5个同时存活）
- **降采样渲染**: 使用4倍降采样离屏Canvas计算波纹，再缩放到主Canvas

**性能优化**: DPR适配、ResizeObserver响应式、降采样计算、requestAnimationFrame循环。

---

### 8. OpeningInfo — 开局信息（占位组件）

**当前状态**: 空组件，仅包含空的 `<template>` 和 `<script setup>`，预留用于展示开局详细信息。

---

### 9. ThemeSwitch — 主题切换

**核心功能**: 下拉菜单切换亮色/暗色/跟随系统三种主题模式。

**选项**: 亮色模式(Sunny图标)、暗色模式(Moon图标)、跟随系统(Monitor图标)

**状态管理**: 通过 `useThemeStore()` 读写主题模式。

---

### 10. HelpTooltip — 帮助提示

**核心功能**: 简单的帮助提示组件，显示问号图标，hover 显示提示文本。

**Props**: `content`(必填), `placement`('top'), `effect`('dark'), `size`(14)

---

## 组合式函数

### useAnalysisOverlay.js

**导出**:

| 函数/属性 | 说明 |
|-----------|------|
| `overlayVisible` | ref<boolean> — 覆盖层可见性 |
| `dismissOverlay()` | 隐藏覆盖层 |
| `resetOverlay()` | 重置为可见 |
| `watchAnalyzing(analyzingRef)` | 监听分析状态，重新分析时重置覆盖层 |

**使用场景**: 在 GameAnalysis 视图中管理分析覆盖层的显示/隐藏逻辑。

---

## 组件依赖关系

```
GameAnalysis 视图
├── ChessBoard          ← 棋盘渲染
├── GameController      ← 回放控制
├── MoveList            ← 着法列表
├── WinRateChart        ← 胜率图表
├── MoveEvaluation      ← 着法评价
├── AnalysisOverlay     ← 分析覆盖层
│   └── useAnalysisOverlay  ← 覆盖层状态
├── OpeningInfo         ← 开局信息（占位）
└── HelpTooltip         ← 帮助提示

Practice 视图
├── PracticeBoard       ← 练习棋盘
└── HelpTooltip         ← 帮助提示

AppLayout
├── ThemeSwitch         ← 主题切换
└── HelpTooltip         ← 帮助提示
```

## 通用设计模式

1. **Composition API**: 所有组件使用 `<script setup>` 语法，Props/Emits 类型声明
2. **chess.js 集成**: ChessBoard 和 PracticeBoard 内部维护 `Chess` 实例管理棋局状态
3. **Unicode 棋子**: 使用 Unicode 字符渲染棋子，白方描边+阴影，黑方纯色
4. **Expose 模式**: ChessBoard 通过 `defineExpose` 暴露方法供父组件命令式调用
5. **CSS 变量**: 所有组件使用 CSS 变量（`var(--card-bg)` 等）支持主题切换
6. **响应式尺寸**: 棋盘大小通过 Props 传入，内部计算格子/棋子尺寸
