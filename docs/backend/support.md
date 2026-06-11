# 后端辅助基础设施 (`backend/data/` + `backend/scripts/` + `backend/tests/` + `backend/migrations/` + 根级工具文件)

## 概述

辅助基础设施包含数据文件、运维脚本、测试套件、数据库迁移和根级工具文件，为应用提供数据支撑、批量操作、质量保障和数据库版本管理能力。

## 文件结构

```
backend/
├── data/
│   └── openings_standard.json     # 标准开局库数据
├── scripts/
│   ├── import_openings.py         # 开局库导入脚本
│   └── match_openings.py          # 棋谱开局匹配脚本
├── tests/
│   ├── __init__.py                # 测试包初始化
│   ├── test_api.py                # API 接口测试
│   ├── test_ai_player.py          # AI 对弈逻辑测试
│   ├── test_fen_utils.py          # FEN 工具测试
│   ├── test_pgn_parser.py         # PGN 解析测试
│   └── test_practice.py           # 练习模块测试
├── migrations/
│   ├── README                     # Alembic 说明
│   ├── alembic.ini                # Alembic 配置
│   ├── env.py                     # 迁移环境配置
│   ├── script.py.mako             # 迁移脚本模板
│   └── versions/                  # 迁移版本文件
│       ├── 4c0f851ac9b1_initial_chess_database_models.py
│       ├── a1b2c3d4e5f6_add_puzzles_table_and_practice_games_fk.py
│       └── 15dd6a7e3374_add_opening_model.py
├── run.py                         # 应用启动入口 + CLI 命令
├── init_db.py                     # 数据库初始化 + 种子数据
├── import_openings.py             # 开局库批量导入（含统计）
├── import_pgn.py                  # PGN 文件批量导入
├── requirements.txt               # Python 依赖
├── .env.example                   # 环境变量示例
└── .env                           # 环境变量（不入库）
```

---

## 1. 数据文件 (`data/`)

### openings_standard.json

**格式**: JSON 对象，键为 ECO 编码，值为开局信息。

```json
{
  "A00": {
    "name": "Polish Opening",
    "variation": "1.b4",
    "moves": ["b4"],
    "description": "也称索科尔斯基开局，侧翼起步的非常规开局"
  },
  "C42": {
    "name": "Petrov's Defense",
    "variation": "1.e4 e5 2.Nf3 Nf6",
    "moves": ["e4", "e5", "Nf3", "Nf6"],
    "description": "俄罗斯防御，以反击代替防守"
  }
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 开局名称 |
| `variation` | string | 变例描述 |
| `moves` | string[] | 走法序列（SAN 格式） |
| `description` | string | 开局说明 |

**用途**: 由 `scripts/import_openings.py` 和根级 `import_openings.py` 读取并导入数据库 `openings` 表。

---

## 2. 运维脚本 (`scripts/`)

### 2.1 import_openings.py — 开局库导入

**用法**: `python scripts/import_openings.py data/openings.json`

**功能**: 读取 JSON 开局数据，新增或更新到 `openings` 表。

**逻辑**:

```
1. 创建 Flask 应用上下文
2. 读取 JSON 文件
3. 遍历每个 ECO 编码：
   ├── 已存在 → 更新 name/variation/moves/category/description
   └── 不存在 → 新建 Opening 记录
4. 每 100 条提交一次
5. 最终提交并打印统计（新增数/更新数）
```

**设计要点**: 使用 `eco_code[0]` 推断 `category`（A/B/C/D/E 类）。

---

### 2.2 match_openings.py — 棋谱开局匹配

**用法**: `python scripts/match_openings.py`

**功能**: 为缺少 `eco_code` 的棋谱自动识别并填充开局信息。

**逻辑**:

```
1. 查询所有 eco_code 为空或 NULL 的 Game
2. 对每局棋：
   ├── 提取 SAN 走法序列
   ├── 调用 OpeningRecognizer.identify_opening() 识别
   └── 匹配成功 → 更新 eco_code 和 opening_name
3. 每 100 条提交一次
4. 打印处理统计
```

**依赖**: `OpeningRecognizer` 服务（见 services.md）。

---

## 3. 测试套件 (`tests/`)

### 3.1 test_api.py — API 接口测试

**测试类**: 3 个，共 14 个测试用例。

#### TestAuthAPI (7 用例)

| 测试 | 说明 |
|------|------|
| `test_register` | 正常注册 → 201 + token |
| `test_register_missing_fields` | 缺少字段 → 400 |
| `test_register_duplicate_username` | 重复用户名 → 409 |
| `test_login` | 正常登录 → 200 + token |
| `test_login_wrong_password` | 错误密码 → 401 |
| `test_get_profile` | 带 Token 获取资料 → 200 |
| `test_get_profile_unauthorized` | 无 Token → 401 |

#### TestGamesAPI (6 用例)

| 测试 | 说明 |
|------|------|
| `test_get_games` | 获取棋谱列表 → 200 + 分页数据 |
| `test_get_game_detail` | 获取棋谱详情 → 200 |
| `test_get_game_not_found` | 不存在的 ID → 404 |
| `test_get_games_with_search` | 搜索棋手名 → 过滤结果 |
| `test_get_games_with_eco_filter` | ECO 过滤 → 匹配结果 |
| `test_get_games_with_result_filter` | 结果过滤 → 匹配结果 |

#### TestPlayersAPI (3 用例)

| 测试 | 说明 |
|------|------|
| `test_get_players` | 获取棋手列表 → 200 |
| `test_get_player_detail` | 获取棋手详情 → 200 |
| `test_get_player_not_found` | 不存在的 ID → 404 |

**测试配置**: 使用 `TestingConfig`，SQLite 内存数据库 `test_chess.db`，每个测试类独立 `setUp`/`tearDown`。

---

### 3.2 test_ai_player.py — AI 对弈逻辑测试

**测试类**: 7 个，共 27 个测试用例。

#### TestDifficultyConfig (3 用例)

| 测试 | 说明 |
|------|------|
| `test_all_difficulties_exist` | 5 档难度配置完整性 |
| `test_difficulty_ordering` | 深度递增排序 |
| `test_rates_sum_less_than_one` | 随机率+失误率 ≤ 1.0 |

#### TestAIPlayerMock (4 用例)

| 测试 | 说明 |
|------|------|
| `test_get_move_returns_legal` | Mock 模式返回合法着法 |
| `test_get_move_no_legal_moves` | 无合法着法返回 None |
| `test_get_hint_returns_dict` | 提示返回 hint_move/score/win_rate |
| `test_close_no_error` | 关闭无异常 |

#### TestAIPlayerMoveSelection (4 用例)

| 测试 | 说明 |
|------|------|
| `test_blunder_rate_selects_third_candidate` | 低 random 值 → 选第3候选 |
| `test_random_rate_selects_second_candidate` | 中 random 值 → 选第2候选 |
| `test_best_move_selected_normally` | 高 random 值 → 选最佳着法 |
| `test_fewer_candidates` | 候选不足时选最后一个 |

#### TestPracticeSessionBasic (12 用例)

| 测试 | 说明 |
|------|------|
| `test_start_from_fen_white` | 白方开局 |
| `test_start_from_fen_black_ai_moves_first` | 黑方开局 → AI 先走 |
| `test_user_move_normal` | 正常走子 → AI 回应 |
| `test_user_move_invalid` | 无效着法 → PracticeError |
| `test_undo_two_moves` | 悔棋回退两步（用户+AI） |
| `test_undo_one_move_only_user` | 仅回退用户一步 |
| `test_undo_no_moves_error` | 无步可悔 → PracticeError |
| `test_get_hint` | 获取提示 → hint_move |
| `test_get_hint_increments_counter` | 提示计数递增 |
| `test_resign` | 认输 → 0-1 |
| `test_resign_as_black` | 黑方认输 → 1-0 |
| `test_resign_game_over_error` | 已结束再认输 → PracticeError |

#### TestPracticeSessionCheckmate (1 用例)

| 测试 | 说明 |
|------|------|
| `test_scholars_mate` | 学者将杀 → is_checkmate + 1-0 |

#### TestPracticeSessionUndoRebuild (1 用例)

| 测试 | 说明 |
|------|------|
| `test_undo_rebuilds_board_from_start_fen` | 多步悔棋后从初始 FEN 重建棋盘 |

#### TestPracticeSessionNoActive (3 用例)

| 测试 | 说明 |
|------|------|
| `test_user_move_no_session` | 无会话走子 → PracticeError |
| `test_get_status_no_session` | 无会话状态 → active=False |
| `test_to_dict_no_session` | 无会话序列化 → active=False |

**Mock 策略**: 使用 `unittest.mock.patch` 和 `MagicMock` 替代真实 Stockfish 引擎，隔离外部依赖。

---

### 3.3 test_fen_utils.py — FEN 工具测试

**测试类**: 2 个，共 19 个测试用例。

#### TestSquareConversion (6 用例)

| 测试 | 说明 |
|------|------|
| `test_square_to_coords` | 格子名→坐标 (a1→(0,0), h8→(7,7)) |
| `test_square_to_coords_invalid` | 非法格子→ValueError |
| `test_coords_to_square` | 坐标→格子名 |
| `test_coords_to_square_invalid` | 越界坐标→ValueError |
| `test_get_square_color` | 格子颜色判断 (a1=dark, a2=light) |

#### TestFENUtils (13 用例)

| 测试 | 说明 |
|------|------|
| `test_is_valid_fen_initial` | 初始 FEN 有效 |
| `test_is_valid_fen_invalid` | 多种无效 FEN → False |
| `test_parse_fen` | 解析初始 FEN 各字段 |
| `test_fen_to_board_array` | FEN→8×8 数组 |
| `test_get_piece_at` | 获取指定格子棋子 |
| `test_make_move_san` | SAN 走法 → 新 FEN |
| `test_make_move_uci` | UCI 走法 → 新 FEN |
| `test_make_move_invalid` | 无效走法 → ValueError |
| `test_get_legal_moves` | 初始局面 20 个合法着法 |
| `test_is_checkmate` | 将杀检测 |
| `test_is_stalemate` | 逼和检测 |
| `test_is_check` | 将军检测 |
| `test_board_to_fen` | 数组→FEN 反向转换 |
| `test_get_king_square` | 获取王的位置 |
| `test_board_to_unicode` | Unicode 棋盘渲染 |
| `test_parse_fen_after_moves` | 走子后 FEN 解析 |

---

### 3.4 test_pgn_parser.py — PGN 解析测试

**测试类**: 1 个，共 11 个测试用例。

| 测试 | 说明 |
|------|------|
| `test_parse_simple_game` | 解析基本 PGN → 正确的 game_info + moves |
| `test_parse_game_with_eco` | 解析含 ECO/Opening 的 PGN |
| `test_parse_game_with_elo` | 解析含等级分的 PGN |
| `test_parse_invalid_pgn` | 无效 PGN → total_moves=0 |
| `test_parse_empty_content` | 空 PGN → PGNParsingError |
| `test_parse_multiple_games` | 多局 PGN → 2 个结果 |
| `test_moves_structure` | 着法结构验证 (move_number/white/black) |
| `test_to_fen_list` | FEN 序列生成（含初始 FEN） |
| `test_pgn_to_dict_static` | 静态方法 pgn_to_dict |
| `test_get_moves_list_before_parse` | 未解析前 → [] |
| `test_to_fen_list_before_parse` | 未解析前 → [] |

---

### 3.5 test_practice.py — 练习模块测试

**测试类**: 3 个，共 17 个测试用例。

#### TestPuzzleLibrary (11 用例)

| 测试 | 说明 |
|------|------|
| `test_puzzle_library_has_10_entries` | 预设残局数量 = 10 |
| `test_all_puzzles_have_required_fields` | 必填字段完整性 |
| `test_all_fens_are_valid` | 所有 FEN 合法（chess.Board 验证） |
| `test_all_difficulties_are_valid` | 难度值在 {beginner,easy,medium,hard} 内 |
| `test_all_categories_are_valid` | 分类在 {残局,战术,开局,将杀} 内 |
| `test_get_all_puzzles` | 获取全部残局 |
| `test_get_puzzles_by_category` | 按分类筛选 |
| `test_get_puzzles_by_difficulty` | 按难度筛选 |
| `test_get_puzzle_exists` | 获取指定残局 |
| `test_get_puzzle_not_exists` | 不存在 → None |
| `test_specific_puzzles_exist` | 10 个预设 ID 存在性 |

#### TestPracticeGameModel (4 用例)

| 测试 | 说明 |
|------|------|
| `test_to_dict_returns_required_fields` | 序列化字段完整性 |
| `test_moves_json_parsed_correctly` | JSON 着法解析 |
| `test_invalid_moves_json_returns_empty_list` | 无效 JSON → [] |
| `test_empty_moves_json` | 空字符串 → [] |

#### TestPracticeAPIEndpoints (4 用例)

| 测试 | 说明 |
|------|------|
| `test_puzzle_library_imports` | PUZZLE_LIBRARY 可导入 |
| `test_practice_session_imports` | PracticeSession/PracticeError 可导入 |
| `test_practice_model_imports` | PracticeGame.to_dict 存在 |
| `test_practice_route_imports` | practice_bp.name == 'practice' |

---

### 测试运行

```bash
# 运行全部测试
cd backend
python -m pytest tests/ -v

# 运行单个测试文件
python -m pytest tests/test_api.py -v

# 运行单个测试类
python -m pytest tests/test_ai_player.py::TestAIPlayerMock -v
```

---

## 4. 数据库迁移 (`migrations/`)

### 迁移链

```
4c0f851ac9b1 (初始) → a1b2c3d4e5f6 → 15dd6a7e3374 (最新)
```

### 4.1 初始迁移 — `4c0f851ac9b1_initial_chess_database_models.py`

**创建表**: openings, players, tournaments, users, games, analyses, collections

**索引**:

| 表 | 索引字段 |
|----|----------|
| openings | eco_code, category |
| players | name, country, elo_rating |
| tournaments | name |
| users | username(UNIQUE), email(UNIQUE) |
| games | white/black_player_id, tournament_id, date, eco_code |
| analyses | game_id(UNIQUE) |
| collections | user_id, game_id, (user_id+game_id) UNIQUE |

### 4.2 残局表迁移 — `a1b2c3d4e5f6_add_puzzles_table_and_practice_games_fk.py`

**操作**:
- 创建 `puzzles` 表（含 source_game_id/created_by 外键）
- 修改 `practice_games.puzzle_id` 类型从 String(50) → Integer
- 添加 `practice_games.puzzle_id` 外键指向 `puzzles.id`
- 创建索引: puzzles.source_game_id, created_by, is_preset; practice_games.puzzle_id

### 4.3 开局模型增强 — `15dd6a7e3374_add_opening_model.py`

**操作**:
- openings 表添加字段: popularity(Integer), white_win_rate(Float), black_win_rate(Float), draw_rate(Float)
- openings.name: String(200) → String(100)
- openings.variation: String(200) → String(100)
- openings.category: String(50) → String(1)
- openings.eco_code 索引: 非唯一 → 唯一
- games 表添加 game_number 唯一索引
- puzzles 表添加 puzzle_number 唯一索引

### 迁移命令

```bash
# 生成新迁移
flask db migrate -m "description"

# 应用迁移
flask db upgrade

# 回滚迁移
flask db downgrade

# 查看迁移历史
flask db history
```

---

## 5. 根级工具文件

### 5.1 run.py — 应用启动入口

**功能**: Flask 应用启动 + CLI 管理命令。

**启动配置**:

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `FLASK_HOST` | 0.0.0.0 | 监听地址 |
| `FLASK_PORT` | 5000 | 监听端口 |
| `FLASK_DEBUG` | true | 调试模式 |
| `FLASK_ENV` | default | 配置环境 |

**CLI 命令**:

| 命令 | 说明 |
|------|------|
| `flask init-db` | 创建所有数据库表 |
| `flask reset-db` | 删除并重建所有表 |
| `flask seed-data` | 导入种子数据（调用 init_db.py） |
| `flask create-admin` | 交互式创建管理员用户 |

**日志配置**: INFO 级别，格式 `YYYY-MM-DD HH:MM:SS [LEVEL] name: message`。

---

### 5.2 init_db.py — 数据库初始化 + 种子数据

**功能**: 创建表结构并导入预设数据。

**种子数据**:

| 数据类型 | 数量 | 说明 |
|----------|------|------|
| 开局 | 23 条 | 覆盖 A~E 五大类，含西西里/西班牙/后翼弃兵等主流开局 |
| 棋手 | 13 条 | 卡尔森/卡斯帕罗夫/费舍尔/丁立人等传奇棋手 |
| 赛事 | 4 条 | 1972/1985 世界冠军赛、Tata Steel 2023、候选人赛 2024 |
| 棋谱 | 5 条 | 经典对局（费舍尔-斯帕斯基、卡斯帕罗夫-卡尔波夫等） |
| 管理员 | 1 条 | admin/admin123 |

**种子函数**:

| 函数 | 说明 |
|------|------|
| `seed_openings()` | 导入 23 条开局（跳过已存在） |
| `seed_players()` | 导入 13 位棋手（跳过已存在） |
| `seed_tournaments()` | 导入 4 项赛事（跳过已存在） |
| `seed_games()` | 导入 5 局棋谱（关联棋手和赛事） |
| `seed_admin()` | 创建默认管理员 |
| `seed_data()` | 执行全部种子导入 |
| `init_db()` | 创建所有表 |
| `reset_db()` | 删除并重建所有表 |

**运行**: `python init_db.py` 或 `flask seed-data`

---

### 5.3 import_openings.py — 开局库批量导入（含统计）

**用法**: `python import_openings.py`

**与 scripts/import_openings.py 的区别**:

| 特性 | 根级 import_openings.py | scripts/import_openings.py |
|------|------------------------|---------------------------|
| 数据源 | 自动定位 `data/openings_standard.json` | 命令行参数指定 |
| 导入策略 | 先清空再全量导入 | 增量更新（新增/更新） |
| 统计功能 | 从棋谱数据计算胜率 | 无 |
| 输出信息 | 导入数 + 统计更新数 + 总数 | 新增数 + 更新数 |

**统计逻辑**: 导入后查询 `games` 表按 `eco_code` 分组，计算每个开局的:
- `popularity` = 使用该开局的棋谱总数
- `white_win_rate` = 白方胜率(%)
- `black_win_rate` = 黑方胜率(%)
- `draw_rate` = 和棋率(%)

---

### 5.4 import_pgn.py — PGN 文件批量导入

**用法**: `python import_pgn.py --file <path> [--max-games N] [--batch-size N] [--min-elo N]`

**选项**:

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--file` | 必填 | PGN 文件路径（.pgn 或 .pgn.zst） |
| `--max-games` | 0(无限制) | 最大导入局数 |
| `--batch-size` | 500 | 批量提交大小 |
| `--min-elo` | 0 | 最低等级分过滤 |

**支持格式**:
- `.pgn` — 标准 PGN 文本文件
- `.pgn.zst` — Zstandard 压缩的 PGN 文件（自动解压）

**导入流程**:

```
1. 打开文件（自动检测压缩格式）
2. 逐局读取（chess.pgn.read_game）
3. 对每局棋：
   ├── 解析头部信息（棋手/等级分/结果/ECO/赛事等）
   ├── 等级分过滤（min-elo）
   ├── get_or_create_player() — 自动创建棋手
   ├── get_or_create_tournament() — 自动创建赛事
   ├── 导出 PGN 字符串
   ├── 计算总步数 + 最终 FEN
   └── 创建 Game 记录
4. 每 batch_size 条提交一次
5. 打印统计（导入数/跳过数/错误数/速度）
```

**性能**: 批量提交 + 流式读取，适合百万级 PGN 文件导入。

---

### 5.5 requirements.txt — Python 依赖

| 包 | 版本要求 | 用途 |
|----|----------|------|
| Flask | ≥3.0.0 | Web 框架 |
| Flask-SQLAlchemy | ≥3.1.0 | ORM |
| Flask-CORS | ≥4.0.0 | 跨域支持 |
| Flask-JWT-Extended | ≥4.6.0 | JWT 认证 |
| Flask-Migrate | ≥4.0.0 | 数据库迁移 |
| Flask-Limiter | ≥3.5.0 | API 限流 |
| python-dotenv | ≥1.0.0 | 环境变量 |
| python-chess | ≥1.999.0 | 国际象棋逻辑 |
| zstandard | ≥0.20.0 | Zstandard 解压 |
| Werkzeug | ≥3.0.0 | WSGI 工具 + 密码哈希 |
| Flask-Admin | ≥1.6.0 | 后台管理 |
| flasgger | ≥0.9.7 | Swagger API 文档 |

---

### 5.6 .env.example — 环境变量示例

| 变量 | 示例值 | 说明 |
|------|--------|------|
| `SECRET_KEY` | your-secret-key-here | Flask 密钥 |
| `FLASK_ENV` | development | 运行环境 |
| `DATABASE_URI` | mysql+pymysql://... | 数据库连接（生产环境） |
| `JWT_SECRET_KEY` | your-jwt-secret-key-here | JWT 签名密钥 |
| `STOCKFISH_PATH` | stockfish | Stockfish 路径 |
| `ANALYSIS_DEPTH` | 20 | 分析深度 |
| `ANALYSIS_TIMEOUT` | 300 | 分析超时(秒) |
| `ANALYSIS_THREADS` | 1 | 分析线程数 |
| `ANALYSIS_HASH` | 256 | 哈希表大小(MB) |
| `UPLOAD_FOLDER` | ./uploads | 上传目录 |

**注意**: `.env` 文件包含实际密钥，不应提交到版本控制。

---

## 工具文件使用场景

| 场景 | 命令 |
|------|------|
| 首次部署 | `flask init-db && flask seed-data` |
| 重置数据库 | `flask reset-db && flask seed-data` |
| 创建管理员 | `flask create-admin` |
| 导入开局库 | `python import_openings.py` |
| 批量导入 PGN | `python import_pgn.py --file data.pgn --batch-size 1000` |
| 导入压缩 PGN | `python import_pgn.py --file data.pgn.zst --min-elo 2400` |
| 匹配开局 | `python scripts/match_openings.py` |
| 运行测试 | `python -m pytest tests/ -v` |
| 数据库迁移 | `flask db upgrade` |
