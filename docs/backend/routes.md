# 后端API路由层 (`backend/app/routes/`)

## 概述

路由层基于 Flask Blueprint 模式实现，每个业务模块对应一个 Blueprint 文件。所有 API 统一注册到 `/api/` 前缀下，支持 JWT 认证、限流保护和 Swagger 文档生成。路由层负责参数校验、调用服务层/模型层、返回 JSON 响应。

## 文件结构

```
routes/
├── __init__.py      # Blueprint注册、首页路由、错误处理
├── auth.py          # 认证模块 /api/auth
├── games.py         # 棋谱管理 /api/games
├── players.py       # 棋手管理 /api/players
├── openings.py      # 开局管理 /api/openings
├── analysis.py      # 分析管理 /api/analysis
├── collections.py   # 收藏管理 /api/collections
├── practice.py      # 练习管理 /api/practice
└── browsing.py      # 浏览历史 /api/browsing
```

## 路由注册机制 (`__init__.py`)

### 核心函数

| 函数 | 说明 |
|------|------|
| `register_blueprints(app)` | 注册所有 Blueprint 到 Flask 应用 |
| `register_index_route(app)` | 注册首页路由 `/`，返回系统状态和 API 列表 |
| `register_error_handlers(app)` | 注册全局错误处理器（400/401/403/404/405/500） |

### Blueprint 注册表

| Blueprint | URL前缀 | 模块 |
|-----------|---------|------|
| `games_bp` | `/api/games` | 棋谱管理 |
| `players_bp` | `/api/players` | 棋手管理 |
| `analysis_bp` | `/api/analysis` | 分析管理 |
| `openings_bp` | `/api/openings` | 开局管理 |
| `auth_bp` | `/api/auth` | 认证管理 |
| `collections_bp` | `/api/collections` | 收藏管理 |
| `practice_bp` | `/api/practice` | 练习管理 |
| `browsing_bp` | `/api/browsing` | 浏览历史 |

### 全局错误处理

所有错误统一返回 JSON 格式：`{"error": "错误类型", "detail": "详细信息"}`。500 错误自动执行 `db.session.rollback()` 防止数据库会话污染。

---

## 模块详解

### 1. auth.py — 认证模块 `/api/auth`

| 端点 | 方法 | 认证 | 限流 | 说明 |
|------|------|------|------|------|
| `/register` | POST | 无 | 5次/分钟 | 用户注册 |
| `/login` | POST | 无 | 10次/分钟 | 用户登录 |
| `/logout` | POST | JWT | 无 | 用户登出 |
| `/profile` | GET | JWT | 无 | 获取用户资料 |
| `/profile` | PUT | JWT | 无 | 更新用户资料 |

**核心逻辑**:
- **注册**: 校验用户名(3-80字符)、邮箱格式、密码(>=6字符)，检查唯一性，创建用户并返回 JWT
- **登录**: 验证用户名密码，返回 JWT 和用户信息
- **更新资料**: 支持修改用户名、邮箱、密码（需验证旧密码）

---

### 2. games.py — 棋谱管理 `/api/games`

| 端点 | 方法 | 认证 | 限流 | 说明 |
|------|------|------|------|------|
| `/filters` | GET | 无 | 无 | 获取筛选选项（ECO代码、结果） |
| `` | GET | 无 | 无 | 获取棋谱列表（分页+筛选+排序） |
| `/<id>` | GET | 无 | 无 | 获取棋谱详情（含PGN和着法） |
| `/upload` | POST | 无 | 10次/分钟 | 上传PGN文件导入 |
| `/upload-pgn` | POST | 无 | 10次/分钟 | PGN文本导入 |
| `/<id>` | PUT | JWT | 无 | 更新棋谱信息 |
| `/<id>` | DELETE | JWT | 无 | 删除棋谱（级联删除分析） |
| `/<id>/moves` | GET | 无 | 无 | 获取着法列表 |
| `/<id>/analysis` | GET | 无 | 无 | 获取分析结果 |
| `/<id>/analyze` | POST | JWT | 无 | 同步分析棋谱 |

**核心逻辑**:
- **列表查询**: 支持 player/eco/result/date_from/date_to/search 筛选，支持 created_at/date/elo/moves 排序
- **上传**: 支持多文件上传，自动解析 PGN、创建棋手、识别开局，UTF-8/Latin-1 双编码兼容
- **同步分析**: 调用 StockfishAnalyzer，深度上限 20，分析完成后保存 Analysis 记录

---

### 3. players.py — 棋手管理 `/api/players`

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/filters` | GET | 无 | 获取筛选选项（头衔、国家） |
| `` | GET | 无 | 获取棋手列表（分页+筛选+排序） |
| `/<id>` | GET | 无 | 获取棋手详情（含统计） |
| `/<id>/games` | GET | 无 | 获取棋手对局列表（支持颜色/结果筛选） |
| `/<id>/stats` | GET | 无 | 获取棋手统计（含ECO分类统计） |

**核心逻辑**:
- **列表查询**: 支持 search/country/title/min_elo/max_elo 筛选
- **统计**: `get_stats()` 计算胜负和统计，`/stats` 额外计算 ECO 分类统计

---

### 4. openings.py — 开局管理 `/api/openings`

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `` | GET | 无 | 获取开局列表（分页+筛选+排序） |
| `/<eco>` | GET | 无 | 获取开局详情（含示例棋谱） |
| `/identify` | POST | 无 | 识别开局（传入着法列表） |
| `/tree` | GET | 无 | 获取开局分类树 |

**核心逻辑**:
- **识别开局**: 调用 `OpeningRecognizer.identify_opening()`，返回 ECO 代码、置信度、相似开局
- **开局树**: 合并数据库开局和识别器内置开局数据
- **详情**: 优先查数据库，fallback 到识别器内置数据，附加最近6局示例棋谱

---

### 5. analysis.py — 分析管理 `/api/analysis`

| 端点 | 方法 | 认证 | 限流 | 说明 |
|------|------|------|------|------|
| `/game/<id>/start` | POST | JWT | 5次/分钟 | 启动异步分析任务 |
| `/game/<id>/status` | GET | JWT | 无 | 获取棋谱分析状态 |
| `/tasks/<task_id>` | GET | 无 | 无 | 获取任务状态 |
| `/tasks` | GET | 无 | 无 | 获取所有任务列表 |
| `/tasks/<task_id>` | DELETE | 无 | 无 | 取消分析任务 |
| `/engines` | GET | 无 | 无 | 获取引擎配置信息 |

**核心逻辑**:
- **异步分析**: 使用 `threading.Thread` 在后台执行分析，通过内存字典 `_analysis_tasks` 跟踪任务状态
- **任务状态**: pending → running → completed/failed/cancelled
- **进度回调**: `progress_callback` 实时更新分析进度
- **取消支持**: 通过设置 `task['status'] = 'cancelled'` 和 `InterruptedError` 实现

---

### 6. collections.py — 收藏管理 `/api/collections`

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `` | GET | JWT | 获取收藏列表（含棋谱摘要） |
| `` | POST | JWT | 添加收藏（含备注） |
| `/<id>` | DELETE | JWT | 删除收藏 |
| `/check/<game_id>` | GET | JWT | 检查是否已收藏 |
| `/<id>` | PUT | JWT | 更新收藏备注 |

**核心逻辑**: 所有操作需 JWT 认证，通过 `get_jwt_identity()` 获取用户ID，确保只能操作自己的收藏。

---

### 7. practice.py — 练习管理 `/api/practice`

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/puzzles` | GET | 无 | 获取残局列表 |
| `/puzzles/<id>` | GET | 无 | 获取残局详情 |
| `/puzzles` | POST | JWT | 创建残局 |
| `/puzzles/<id>` | DELETE | JWT | 删除残局 |
| `/search_games` | GET | 无 | 搜索棋谱（用于"从棋谱开始"） |
| `/start` | POST | JWT(optional) | 开始练习对局 |
| `/move` | POST | 无 | 走子 |
| `/undo` | POST | 无 | 悔棋 |
| `/hint` | POST | 无 | 获取提示 |
| `/resign` | POST | 无 | 认输 |
| `/status/<session_id>` | GET | 无 | 获取对局状态 |
| `/history` | GET | JWT(optional) | 获取练习历史 |
| `/history/<id>` | GET | JWT(optional) | 获取练习详情 |
| `/analyze/<id>` | POST | JWT(optional) | 启动练习复盘分析 |
| `/analyze/<id>/status` | GET | JWT(optional) | 获取复盘分析状态 |
| `/analyze/<id>/result` | GET | JWT(optional) | 获取复盘分析结果 |

**核心逻辑**:
- **会话管理**: 使用内存字典 `sessions` 存储活跃对局会话，key 为 UUID
- **三种模式**: puzzle（残局）、from_game（从棋谱）、custom（自定义FEN）
- **AI对弈**: 用户走子后 AI 自动应着，对局结束自动保存到数据库
- **会话过期**: 返回 410 状态码和 `session_expired` 错误码
- **复盘分析**: 异步分析练习对局的走法，使用独立的 `_practice_analysis_tasks` 字典

---

### 8. browsing.py — 浏览历史 `/api/browsing`

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `` | GET | JWT | 获取浏览历史 |
| `` | POST | JWT | 记录浏览（重复浏览更新时间） |
| `/<game_id>` | DELETE | JWT | 删除单条记录 |
| `/clear` | POST | JWT | 清空所有浏览历史 |

**核心逻辑**: 重复浏览同一棋谱时更新 `viewed_at` 而非创建新记录，利用 `UniqueConstraint` 实现。

---

## 通用设计模式

### 1. 分页查询模式

```python
page = request.args.get('page', 1, type=int)
per_page = request.args.get('per_page', 20, type=int)
per_page = min(per_page, 100)  # 上限保护
pagination = query.paginate(page=page, per_page=per_page, error_out=False)
return jsonify({'items': [...], 'total': pagination.total, 'page': page, 'per_page': per_page})
```

### 2. 排序模式

```python
sort_map = {'created_at': Model.created_at, 'date': Model.date, ...}
sort_col = sort_map.get(sort, Model.created_at)
query = query.order_by(sort_col.desc() if order == 'desc' else sort_col.asc())
```

### 3. JWT 认证模式

- 必须认证: `@jwt_required()`
- 可选认证: `@jwt_required(optional=True)` — 游客也可访问，但功能受限
- 获取用户: `get_jwt_identity()` 返回用户ID字符串

### 4. 限流模式

- 注册: `@limiter.limit("5 per minute")`
- 登录: `@limiter.limit("10 per minute")`
- 上传: `@limiter.limit("10 per minute")`
- 分析: `@limiter.limit("5 per minute")`

### 5. 错误处理模式

```python
try:
    db.session.commit()
except Exception as e:
    db.session.rollback()
    logger.error("Operation error: %s", e)
    return jsonify({'error': 'Failed to ...'}), 500
```
