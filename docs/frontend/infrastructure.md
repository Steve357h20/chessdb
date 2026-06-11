# 前端基础设施层 (`frontend/src/styles/` + `frontend/src/utils/` + `frontend/src/layouts/` + `frontend/vite.config.js`)

## 概述

基础设施层包含样式系统、工具函数、布局组件和构建配置，为整个前端应用提供设计规范、通用逻辑和开发环境支持。

## 文件结构

```
styles/
├── variables.scss    # SCSS 变量定义
├── mixins.scss       # SCSS 混入定义
├── theme.css         # CSS 自定义属性（亮色/暗色主题）
└── global.scss       # 全局样式 + 工具类

utils/
└── chessUtils.js     # 国际象棋工具函数

layouts/
└── MainLayout.vue    # 主布局组件

根级配置:
├── vite.config.js    # Vite 构建配置
├── package.json      # 项目依赖与脚本
├── index.html        # HTML 入口
├── .env              # 开发环境变量
└── .env.production   # 生产环境变量
```

---

## 1. 样式系统

### variables.scss — SCSS 变量

**分类**:

| 分类 | 变量数 | 说明 |
|------|--------|------|
| 品牌色 | 4 | primary/light/lighter/dark (#1a237e 系列) |
| 语义色 | 5×3 | success/warning/error/info + light/dark 变体 |
| 文本色 | 4 | primary/regular/secondary/placeholder |
| 背景色 | 4 | primary/regular/secondary/dark |
| 边框色 | 3 | default/light/lighter |
| 棋盘色 | 9 | light/dark/highlight/last-move/selected/legal-move/capture/check/arrow |
| 着法评价色 | 6 | brilliant/great/good/inaccuracy/mistake/blunder |
| 评分色 | 3 | positive/negative/neutral |
| 尺寸 | 7 | header/footer/sidebar/board |
| 圆角 | 4 | small/medium/large/round |
| 阴影 | 3 | small/medium/large |
| 字号 | 8 | xs(12px) ~ xxl(24px) |
| Z-index | 5 | sidebar/header/drawer/modal/notification |
| 断点 | 3 | mobile(768px)/tablet(992px)/desktop(1200px) |
| 过渡 | 3 | fast(0.15s)/normal(0.3s)/slow(0.5s) |

---

### mixins.scss — SCSS 混入

**布局混入**:

| 混入 | 说明 |
|------|------|
| `flex-center` | 居中 Flex 布局 |
| `flex-between` | 两端对齐 Flex 布局 |
| `flex-column` | 纵向 Flex 布局 |
| `flex-column-center` | 纵向居中 Flex 布局 |

**文本混入**:

| 混入 | 说明 |
|------|------|
| `text-ellipsis` | 单行文本溢出省略 |
| `text-ellipsis-lines($lines)` | 多行文本溢出省略 |

**UI 混入**:

| 混入 | 说明 |
|------|------|
| `scrollbar($width)` | 自定义滚动条样式 |
| `card($padding, $radius, $shadow)` | 卡片样式 |
| `theme-dark` | 暗色主题选择器 |

**响应式混入**:

| 混入 | 说明 |
|------|------|
| `responsive(mobile/tablet/desktop/large)` | 通用响应式 |
| `mobile` | max-width: 768px |
| `tablet` | max-width: 992px |
| `desktop` | min-width: 993px |

**棋盘混入**:

| 混入 | 说明 |
|------|------|
| `chess-square($is-light)` | 棋盘格子样式 |
| `chess-board` | 8×8 网格棋盘 |
| `highlight-square($color)` | 格子高亮 |
| `legal-move-dot` | 合法走子圆点 |
| `legal-capture-ring` | 合法吃子圆环 |

---

### theme.css — CSS 自定义属性

**亮色主题** (`:root`):

定义 25 个 CSS 自定义属性，涵盖背景色、文本色、边框色、卡片、头部、侧边栏、滚动条等。

**暗色主题** (`html.dark`):

覆盖所有 25 个 CSS 自定义属性为暗色值，通过 `html.dark` 类切换。

**切换机制**: `themeStore.isDark` 变化时，`document.documentElement.classList.toggle('dark', val)` 添加/移除 `dark` 类。

---

### global.scss — 全局样式

**内容**:
1. **CSS Reset**: box-sizing/margin/padding 清零
2. **基础排版**: 字体、行高、标题层级(h1-h6)
3. **工具类**:
   - 布局: `.flex-center`, `.flex-between`, `.flex-column`
   - 文本: `.text-ellipsis`, `.text-primary/regular/secondary/...`
   - 间距: `.mt-4/8/12/16/24`, `.mb-4/8/12/16/24`, `.ml-4/8`, `.mr-4/8`
   - 内边距: `.p-8/12/16/24`
   - 间隙: `.gap-4/8/12/16`
   - 尺寸: `.w-full`, `.h-full`
   - 交互: `.cursor-pointer`, `.select-none`
   - 着法评价: `.move-brilliant/great/good/inaccuracy/mistake/blunder`
   - 评分: `.eval-positive/negative/neutral`
4. **动画**: fadeIn/Out, slideIn(Up/Down/Left/Right), pulse, spin
5. **Vue 过渡**: `.fade-*`, `.slide-up-*`
6. **响应式隐藏**: `.hide-mobile/tablet/desktop`

---

## 2. 工具函数 (`chessUtils.js`)

### FEN 解析

| 函数 | 说明 |
|------|------|
| `parseFEN(fen)` | 解析 FEN → {board, turn, castling, enPassant, halfmove, fullmove} |
| `getPieceAt(fen, square)` | 获取指定格子棋子 |
| `isLightSquare(square)` | 判断格子颜色 |

### 坐标转换

| 函数 | 说明 |
|------|------|
| `squareToCoords(square)` | 格子名→坐标 {col, row} |
| `coordsToSquare(col, row)` | 坐标→格子名 |

### 着法解析

| 函数 | 说明 |
|------|------|
| `sanToCoords(san)` | SAN → {from, to, piece, promotion, castling} |
| `coordsToSan(from, to, promotion)` | 坐标 → SAN |
| `uciToCoords(uci)` | UCI → {from, to, promotion} |
| `parseMove(san, fen)` | 解析 SAN（结合 FEN 推断起始格） |

### 合法着法生成

| 函数 | 说明 |
|------|------|
| `getLegalMoves(fen)` | 生成所有合法着法（含升变、易位、吃过路兵） |

**内部函数**: `addPawnMoves`, `addKnightMoves`, `addSlidingMoves`, `addKingMoves`, `addCastlingMoves`

### 评分与评价

| 函数 | 说明 |
|------|------|
| `scoreToWinRate(score)` | 厘兵值 → 胜率(Logistic) |
| `nagToSymbol(nag)` | NAG 数字 → 符号字符串 |
| `formatScore(score, type)` | 格式化评分显示 |
| `formatEval(evalCp, evalType)` | 格式化评价显示 |
| `classifyMove(evalDelta, isBestMove, positionComplexity)` | 着法分类评价 |

**classifyMove 分类逻辑**:

| 评分差(cp) | isBestMove | 分类 | 符号 |
|-----------|------------|------|------|
| - | true + complex | brilliant | !! |
| - | true | great | ! |
| < 15 | - | great | ! |
| < 35 | - | good | (无) |
| < 60 | - | interesting | !? |
| < 100 | - | inaccuracy | ?! |
| < 200 | - | mistake | ? |
| >= 200 | - | blunder | ?? |

### 通用工具

| 函数 | 说明 |
|------|------|
| `debounce(fn, delay)` | 防抖 |
| `throttle(fn, delay)` | 节流 |
| `formatDate(date)` | 日期格式化 (YYYY-MM-DD HH:mm) |
| `truncate(str, length)` | 字符串截断 |
| `resultLabel(result)` | 对局结果中文标签 |

### NAG 符号映射

| NAG | 符号 | 含义 |
|-----|------|------|
| 1 | ! | 好着 |
| 2 | ? | 坏着 |
| 3 | !! | 妙手 |
| 4 | ?? | 严重失误 |
| 5 | !? | 有趣 |
| 6 | ?! | 疑问 |
| 7 | □ | 唯一着 |
| 10 | = | 均势 |
| 13 | ∞ | 不确定 |
| 14 | += | 白稍优 |
| 15 | =+ | 黑稍优 |
| 16 | ± | 白优 |
| 17 | ∓ | 黑优 |
| 18 | +- | 白胜势 |
| 19 | -+ | 黑胜势 |

---

## 3. 布局组件 (`MainLayout.vue`)

### 结构

```
el-container (main-layout)
├── el-header (60px)
│   ├── Logo + 导航菜单
│   ├── 搜索框
│   ├── ThemeSwitch
│   └── 用户菜单/登录按钮
├── el-container (body)
│   ├── el-aside (200px, 可折叠)
│   │   ├── 快速导航
│   │   ├── 最近浏览
│   │   ├── 我的收藏
│   │   └── 帮助中心
│   └── el-main
│       ├── 面包屑导航
│       └── router-view (带过渡动画)
├── el-footer (40px)
└── el-drawer (移动端侧边栏)
```

### 核心功能

| 功能 | 说明 |
|------|------|
| **顶部导航** | 7个主要功能入口（棋谱库/棋手/开局库/残局库/AI对弈/数据分析/上传） |
| **搜索** | 回车跳转棋谱库搜索 |
| **侧边栏** | 快速导航 + 最近浏览 + 我的收藏（可折叠） |
| **面包屑** | 基于路由路径自动生成 |
| **路由过渡** | `ml-fade` 淡入淡出动画 |
| **欢迎弹窗** | 首次访问显示快速入门（localStorage 标记关闭） |
| **移动端适配** | <768px 隐藏侧边栏，使用 Drawer 替代 |
| **用户菜单** | 已登录: 个人设置/分析队列/退出; 未登录: 登录/注册 |

### 响应式断点

| 断点 | 行为 |
|------|------|
| > 992px | 完整导航 + 侧边栏 |
| 768-992px | 隐藏导航菜单，显示侧边栏切换按钮 |
| < 768px | 隐藏 Logo 文字/用户名，使用 Drawer 替代侧边栏 |

---

## 4. 构建配置 (`vite.config.js`)

### 开发服务器

| 配置 | 值 |
|------|-----|
| 端口 | 3000 |
| API 代理 | `/api` → `http://localhost:5000` |

### 构建配置

| 配置 | 值 |
|------|-----|
| 目标 | ES2020 |
| 输出目录 | `dist` |
| Source Map | 关闭 |
| 压缩 | esbuild |
| Chunk 警告阈值 | 1500KB |

### 代码分割

| Chunk | 模块 |
|-------|------|
| `element-plus` | Element Plus 组件库 |
| `echarts` | ECharts + vue-echarts |

### 插件

| 插件 | 说明 |
|------|------|
| `@vitejs/plugin-vue` | Vue 3 SFC 支持 |
| `unplugin-auto-import` | Element Plus 自动导入 |
| `unplugin-vue-components` | Element Plus 组件自动注册 |

### 路径别名

| 别名 | 路径 |
|------|------|
| `@` | `src/` |

---

## 5. 应用入口 (`main.js` + `App.vue`)

### main.js 初始化流程

```
1. 创建 Vue 应用
2. 注册 Element Plus 图标组件（全局）
3. 注册 v-chart 组件（全局）
4. 配置 Element Plus（中文语言包）
5. 安装 Pinia
6. 安装 Router
7. 初始化主题 Store
8. 挂载应用
```

### ECharts 按需注册

| 类型 | 组件 |
|------|------|
| 渲染器 | CanvasRenderer |
| 图表 | Line, Bar, Pie, Scatter, Heatmap, Custom |
| 组件 | Grid, Tooltip, Legend, Title, DataZoom, VisualMap |

### App.vue

极简根组件，仅渲染 `MainLayout`。全局样式设置 body margin 和 font-family。

---

## 6. 项目配置文件

### package.json

**项目信息**: `chessdb-frontend` v1.0.0, ESM 模块 (`"type": "module"`)

**脚本**:

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务器 (vite) |
| `npm run build` | 生产构建 (vite build) |
| `npm run preview` | 预览构建产物 (vite preview) |

**运行时依赖**:

| 包 | 版本 | 用途 |
|----|------|------|
| `vue` | ^3.4.0 | 核心框架 |
| `vue-router` | ^4.3.0 | 路由管理 |
| `pinia` | ^2.1.0 | 状态管理 |
| `element-plus` | ^2.6.0 | UI 组件库 |
| `@element-plus/icons-vue` | ^2.3.0 | Element Plus 图标 |
| `axios` | ^1.6.0 | HTTP 客户端 |
| `echarts` | ^5.5.0 | 图表库 |
| `vue-echarts` | ^6.6.0 | ECharts Vue 封装 |
| `chess.js` | ^1.0.0-beta.8 | 国际象棋逻辑 |

**开发依赖**:

| 包 | 版本 | 用途 |
|----|------|------|
| `vite` | ^5.2.0 | 构建工具 |
| `@vitejs/plugin-vue` | ^5.0.0 | Vue SFC 支持 |
| `sass` | ^1.99.0 | SCSS 编译 |
| `unplugin-auto-import` | ^0.17.0 | Element Plus 自动导入 |
| `unplugin-vue-components` | ^0.26.0 | 组件自动注册 |

---

### 环境变量

#### .env（开发环境）

| 变量 | 值 | 说明 |
|------|-----|------|
| `VITE_API_BASE_URL` | `/api` | API 基础路径（由 Vite 代理转发） |
| `VITE_APP_TITLE` | ChessDB - 国际象棋数据管理系统 | 应用标题 |

#### .env.production（生产环境）

与开发环境相同，`VITE_API_BASE_URL` 为 `/api`，生产环境需通过 Nginx 反向代理。

**访问方式**: `import.meta.env.VITE_XXX`

---

### index.html

应用 HTML 入口，关键配置：

| 配置 | 值 | 说明 |
|------|-----|------|
| `lang` | zh-CN | 中文语言 |
| `viewport` | width=device-width, initial-scale=1.0 | 响应式 |
| `title` | ChessDB - 国际象棋数据管理系统 | 页面标题 |
| Element Plus CSS | CDN 引入 (jsdelivr 2.14.0) | 全局样式 |
| 入口脚本 | `/src/main.js` (type=module) | Vite 入口 |
