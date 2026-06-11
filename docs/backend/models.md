# 后端数据模型层 (`backend/app/models/`)

## 概述

数据模型层定义了系统的所有数据库表结构，基于 SQLAlchemy ORM 实现。所有模型继承自 `db.Model`，统一通过 `app/__init__.py` 中的 `db = SQLAlchemy()` 实例管理。模型间通过外键和关系建立关联，支持 JSON 字段存储复杂数据结构。

## 文件结构

```
models/
├── __init__.py          # 模型注册与导出
├── user.py              # 用户模型
├── player.py            # 棋手模型
├── game.py              # 棋谱模型
├── tournament.py        # 赛事模型
├── analysis.py          # 分析结果模型
├── opening.py           # 开局库模型
├── collection.py        # 收藏模型
├── practice.py          # 练习相关模型（PracticeGame + Puzzle）
└── browsing_history.py  # 浏览历史模型
```

## 模型详解

### 1. User — 用户模型

**文件**: `user.py` | **表名**: `users`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, 自增 | 用户ID |
| `username` | String(80) | UNIQUE, NOT NULL, 索引 | 用户名 |
| `password_hash` | String(256) | NOT NULL | 密码哈希（werkzeug） |
| `email` | String(120) | UNIQUE, NOT NULL, 索引 | 邮箱 |
| `is_admin` | Boolean | 默认 False | 是否管理员 |
| `created_at` | DateTime | 默认 utcnow | 创建时间 |

**关系**:
- `collections` → Collection（一对多，dynamic lazy）

**方法**:
- `set_password(password)` — 使用 `generate_password_hash` 设置密码哈希
- `check_password(password)` — 使用 `check_password_hash` 验证密码
- `to_dict()` — 序列化为字典（不含密码哈希）

**设计要点**: 密码不存储明文，使用 werkzeug 的 PBKDF2 哈希算法。`is_admin` 字段用于 Flask-Admin 后台权限控制。

---

### 2. Player — 棋手模型

**文件**: `player.py` | **表名**: `players`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, 自增 | 棋手ID |
| `name` | String(200) | NOT NULL, 索引 | 棋手姓名 |
| `title` | String(10) | 默认 '' | 头衔（GM/IM/FM/WGM等） |
| `country` | String(100) | 默认 '', 索引 | 国家 |
| `elo_rating` | Integer | 默认 0, 索引 | 等级分 |
| `birth_date` | String(20) | 默认 '' | 出生日期 |
| `created_at` | DateTime | 默认 utcnow | 创建时间 |

**关系**:
- `white_games` → Game（白方对局，foreign_keys='Game.white_player_id'）
- `black_games` → Game（黑方对局，foreign_keys='Game.black_player_id'）

**方法**:
- `to_dict()` — 序列化
- `get_stats()` — 计算胜/负/和统计，分白方/黑方统计

**设计要点**: 一个棋手可参与多场对局，通过 `foreign_keys` 参数区分白方和黑方关系。`get_stats()` 实时查询计算统计数据。

---

### 3. Game — 棋谱模型

**文件**: `game.py` | **表名**: `games`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, 自增 | 棋谱ID |
| `game_number` | Integer | UNIQUE, 索引 | 棋谱编号（自动递增） |
| `white_player_id` | Integer | FK→players.id, NOT NULL, 索引 | 白方棋手 |
| `black_player_id` | Integer | FK→players.id, NOT NULL, 索引 | 黑方棋手 |
| `tournament_id` | Integer | FK→tournaments.id, 索引 | 赛事 |
| `date` | String(20) | 默认 '', 索引 | 对局日期 |
| `result` | String(10) | 默认 '*' | 结果（1-0/0-1/1/2-1/2/*） |
| `pgn_content` | Text | 默认 '' | PGN原始内容 |
| `eco_code` | String(10) | 默认 '', 索引 | ECO开局代码 |
| `opening_name` | String(200) | 默认 '' | 开局名称 |
| `total_moves` | Integer | 默认 0 | 总着数 |
| `final_fen` | String(100) | 默认 '' | 最终FEN |
| `white_elo` | Integer | 可空 | 白方等级分 |
| `black_elo` | Integer | 可空 | 黑方等级分 |
| `termination` | String(50) | 默认 '' | 终局方式 |
| `time_control` | String(30) | 默认 '' | 用时规则 |
| `created_at` | DateTime | 默认 utcnow | 创建时间 |

**关系**:
- `analysis` → Analysis（一对一，uselist=False）
- `collections` → Collection（一对多，dynamic）
- `white_player` / `black_player` → Player（由 Player 反向定义）
- `tournament` → Tournament（由 Tournament 反向定义）

**方法**:
- `assign_game_number()` — 自动分配递增编号
- `to_dict()` — 序列化（含棋手名称、赛事名称）
- `get_moves_list()` — 解析 PGN 内容返回着法列表（含 SAN/UCI/FEN）

**设计要点**: `game_number` 独立于 `id`，用于用户可见编号。`get_moves_list()` 使用 `chess.pgn` 实时解析，返回每步的 SAN、UCI、前后 FEN 等详细信息。

---

### 4. Tournament — 赛事模型

**文件**: `tournament.py` | **表名**: `tournaments`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, 自增 | 赛事ID |
| `name` | String(200) | NOT NULL, 索引 | 赛事名称 |
| `start_date` | String(20) | 默认 '' | 开始日期 |
| `end_date` | String(20) | 默认 '' | 结束日期 |
| `location` | String(200) | 默认 '' | 举办地点 |
| `category` | String(50) | 默认 '' | 赛事类别 |
| `created_at` | DateTime | 默认 utcnow | 创建时间 |

**关系**:
- `games` → Game（一对多，dynamic）

**方法**:
- `to_dict()` — 序列化（含对局数量）

**设计要点**: 轻量级模型，仅存储赛事基本信息。日期使用 String 类型兼容 PGN 中的各种日期格式。

---

### 5. Analysis — 分析结果模型

**文件**: `analysis.py` | **表名**: `analyses`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, 自增 | 分析ID |
| `game_id` | Integer | FK→games.id, UNIQUE, NOT NULL, 索引 | 关联棋谱 |
| `analysis_data` | Text | 默认 '{}' | JSON: 完整分析数据 |
| `opening_eco` | String(10) | 默认 '' | 开局ECO代码 |
| `key_moves` | Text | 默认 '[]' | JSON: 关键着法列表 |
| `win_rate_curve` | Text | 默认 '[]' | JSON: 胜率曲线数据 |
| `created_at` | DateTime | 默认 utcnow | 创建时间 |

**关系**:
- `game` → Game（一对一，backref）

**方法**:
- `get_analysis_data()` / `set_analysis_data(data)` — JSON 序列化/反序列化
- `get_key_moves()` / `set_key_moves(moves)` — JSON 序列化/反序列化
- `get_win_rate_curve()` / `set_win_rate_curve(curve)` — JSON 序列化/反序列化
- `to_dict()` — 序列化

**设计要点**: 使用 Text 字段 + JSON 序列化存储复杂分析数据，避免大量关联表。`game_id` 设为 UNIQUE 确保每个棋谱只有一份分析结果。

---

### 6. Opening — 开局库模型

**文件**: `opening.py` | **表名**: `openings`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | 开局ID |
| `eco_code` | String(10) | UNIQUE, NOT NULL, 索引 | ECO代码 |
| `name` | String(100) | NOT NULL | 开局名称 |
| `variation` | String(100) | 默认 '' | 变例名称 |
| `moves` | Text | 默认 '[]' | JSON: 着法序列 |
| `category` | String(1) | 默认 'A', 索引 | ECO分类（A-E） |
| `description` | Text | 默认 '' | 描述 |
| `popularity` | Integer | 默认 0 | 流行度 |
| `white_win_rate` | Float | 默认 50.0 | 白方胜率 |
| `black_win_rate` | Float | 默认 50.0 | 黑方胜率 |
| `draw_rate` | Float | 默认 0.0 | 和棋率 |

**方法**:
- `get_moves_list()` — JSON 反序列化着法序列
- `to_dict()` — 序列化

**设计要点**: ECO 分类 A-E 对应不同开局类型（A-侧翼开局, B-半开放, C-开放, D-封闭/半封闭, E-印度防御）。胜率数据用于开局库统计展示。

---

### 7. Collection — 收藏模型

**文件**: `collection.py` | **表名**: `collections`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, 自增 | 收藏ID |
| `user_id` | Integer | FK→users.id, NOT NULL, 索引 | 用户 |
| `game_id` | Integer | FK→games.id, NOT NULL, 索引 | 棋谱 |
| `note` | Text | 默认 '' | 收藏备注 |
| `created_at` | DateTime | 默认 utcnow | 收藏时间 |

**约束**: `UniqueConstraint('user_id', 'game_id', name='uq_user_game')` — 同一用户不可重复收藏同一棋谱。

**设计要点**: 典型的多对多关联表，附加 `note` 字段支持用户备注。

---

### 8. PracticeGame — 练习对局模型

**文件**: `practice.py` | **表名**: `practice_games`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, 自增 | 练习ID |
| `user_id` | Integer | FK→users.id, 索引 | 用户（可空=游客） |
| `mode` | String(20) | NOT NULL | 模式（puzzle/from_game/custom） |
| `puzzle_id` | Integer | FK→puzzles.id, 索引 | 关联残局 |
| `source_game_id` | Integer | 可空 | 来源棋谱ID |
| `from_move` | Integer | 可空 | 从第N步开始 |
| `start_fen` | Text | 默认 '' | 起始FEN |
| `user_color` | String(1) | 默认 'w' | 用户执子颜色 |
| `difficulty` | String(20) | 默认 'medium' | 难度 |
| `moves_json` | Text | 默认 '[]' | JSON: 走法历史 |
| `final_fen` | Text | 默认 '' | 最终FEN |
| `result` | String(10) | 默认 '*' | 结果 |
| `total_moves` | Integer | 默认 0 | 总着数 |
| `hints_used` | Integer | 默认 0 | 使用提示次数 |
| `undo_count` | Integer | 默认 0 | 悔棋次数 |
| `duration_seconds` | Integer | 可空 | 用时（秒） |
| `analysis_json` | Text | 可空 | JSON: 复盘分析数据 |
| `created_at` | DateTime | 默认 utcnow | 创建时间 |

**设计要点**: `user_id` 可空支持游客练习。`moves_json` 存储完整走法历史用于复盘。`analysis_json` 存储复盘分析结果。

---

### 9. Puzzle — 残局题模型

**文件**: `practice.py` | **表名**: `puzzles`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, 自增 | 残局ID |
| `puzzle_number` | Integer | UNIQUE, 索引 | 残局编号 |
| `name` | String(200) | NOT NULL | 残局名称 |
| `category` | String(50) | 默认 'endgame' | 分类（endgame/tactics/mate） |
| `difficulty` | String(20) | 默认 'medium' | 难度 |
| `description` | Text | 默认 '' | 描述 |
| `hint` | Text | 默认 '' | 提示 |
| `fen` | Text | NOT NULL | FEN局面 |
| `source_game_id` | Integer | FK→games.id, 索引 | 来源棋谱 |
| `from_move` | Integer | 可空 | 从第N步截取 |
| `created_by` | Integer | FK→users.id, 索引 | 创建者 |
| `is_preset` | Boolean | 默认 False, 索引 | 是否预设残局 |
| `practice_count` | Integer | 默认 0 | 练习次数 |
| `solve_count` | Integer | 默认 0 | 解决次数 |
| `created_at` | DateTime | 默认 utcnow | 创建时间 |

**方法**:
- `assign_puzzle_number()` — 预设残局编号 < 1000，用户创建编号 >= 1001
- `to_dict(include_source=False)` — 序列化，可选包含来源棋谱信息

**设计要点**: 预设残局与用户创建残局通过编号区间区分。`practice_count` 和 `solve_count` 用于统计解题率。

---

### 10. BrowsingHistory — 浏览历史模型

**文件**: `browsing_history.py` | **表名**: `browsing_history`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, 自增 | 记录ID |
| `user_id` | Integer | FK→users.id, NOT NULL, 索引 | 用户 |
| `game_id` | Integer | FK→games.id, NOT NULL, 索引 | 棋谱 |
| `viewed_at` | DateTime | 默认 utcnow | 浏览时间 |

**约束**: `UniqueConstraint('user_id', 'game_id', name='uq_user_game_browse')` — 同一用户对同一棋谱只保留一条记录，重复浏览更新时间。

**关系**: `game` → Game（joined eager loading）

**设计要点**: 使用 `lazy='joined'` 预加载关联棋谱，减少列表查询的 N+1 问题。

---

## 模型关系图

```
User ──1:N── Collection ──N:1── Game
User ──1:N── BrowsingHistory ──N:1── Game
User ──1:N── PracticeGame
User ──1:N── Puzzle (created_by)

Game ──1:1── Analysis
Game ──N:1── Player (white_player_id)
Game ──N:1── Player (black_player_id)
Game ──N:1── Tournament
Game ──1:N── Puzzle (source_game_id)

PracticeGame ──N:1── Puzzle

Opening (独立表，通过 eco_code 与 Game.eco_code 逻辑关联)
```

## 通用设计模式

1. **JSON 字段存储**: `Analysis`、`PracticeGame`、`Opening` 使用 Text + JSON 序列化存储复杂嵌套数据，避免过度规范化
2. **to_dict() 序列化**: 所有模型提供 `to_dict()` 方法，统一 API 响应格式
3. **软删除**: 无软删除机制，删除操作直接移除记录
4. **时间字段**: 统一使用 `datetime.utcnow` 作为默认值
5. **索引策略**: 外键字段、查询过滤字段（如 `eco_code`、`date`）均建立索引
