# 后端业务服务层 (`backend/app/services/`)

## 概述

服务层封装了系统的核心业务逻辑，包括引擎分析、AI对弈、PGN解析、开局识别、FEN工具和残局库管理。服务层被路由层调用，与模型层交互，是系统的"大脑"。

## 文件结构

```
services/
├── __init__.py            # 空初始化
├── stockfish_analyzer.py  # Stockfish引擎分析器
├── ai_player.py           # AI对弈引擎 + 练习会话管理
├── pgn_parser.py          # PGN解析器
├── opening_recognizer.py  # 开局识别器
├── fen_utils.py           # FEN工具集
└── puzzle_library.py      # 预设残局库
```

---

## 服务详解

### 1. StockfishAnalyzer — Stockfish引擎分析器

**文件**: `stockfish_analyzer.py`

#### 类: `StockfishAnalyzer`

**职责**: 封装 Stockfish UCI 引擎，提供棋谱逐着分析和局面评估功能。

**初始化参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `stockfish_path` | str | "stockfish" | Stockfish 可执行文件路径 |
| `depth` | int | 20 | 分析深度 |
| `threads` | int | 4 | 引擎线程数 |
| `hash_size` | int | 256 | 哈希表大小(MB) |

**降级机制**: 引擎初始化失败时自动切换到 Mock 模式（`_is_mock = True`），使用随机数生成模拟分析结果，确保系统在无 Stockfish 环境下仍可运行。

#### 核心方法

| 方法 | 说明 |
|------|------|
| `analyze_game(game_id, pgn_moves, callback)` | 分析完整棋谱，返回逐着评价数据 |
| `analyze_position(fen, multi_pv=3)` | 分析单个局面，返回多PV结果 |
| `get_engine_info()` | 获取引擎信息（名称、版本、配置） |
| `close()` | 关闭引擎进程 |

#### 分析流程 (`analyze_game`)

```
1. 解析 PGN → chess.pgn.Game 对象
2. 遍历主变着法：
   a. 获取当前局面 FEN
   b. 调用 _analyze_single_position() 获取多PV分析
   c. 调用 _evaluate_actual_move() 评价实际着法
   d. 计算胜率、评分差、着法评价
   e. 触发进度回调 callback(progress, move_data)
3. 返回完整分析结果
```

#### 着法评价算法 (`_evaluate_actual_move`)

通过比较实际着法与引擎最佳着法的评分差异来评价：

| 评分差(兵) | 评价 | NAG | 含义 |
|-----------|------|-----|------|
| < 0.05 (且是最佳) | `!!` | 3 | 妙手 |
| < 0.05 | `""` | None | 正常 |
| 0.05-0.20 | `!` | 1 | 好着 |
| 0.20-0.50 | `!?` | 5 | 有趣 |
| 0.50-1.00 | `?!` | 6 | 不精确 |
| 1.00-2.00 | `?` | 2 | 失误 |
| > 2.00 | `??` | 4 | 严重失误 |

#### 胜率转换 (`_cp_to_win_rate`)

```python
k = 0.004
win_prob = 1.0 / (1.0 + pow(10, -cp * k))
```

使用 Logistic 函数将厘兵值(centipawn)转换为白方胜率百分比。

#### 引擎重启机制

`_restart_engine()`: 捕获 `EngineTerminatedError` 后尝试重新启动引擎，重启失败则切换到 Mock 模式。

---

### 2. AIPlayer + PracticeSession — AI对弈引擎

**文件**: `ai_player.py`

#### 难度配置 (`DIFFICULTY_CONFIG`)

| 难度 | 深度 | 随机率 | 失误率 | 标签 |
|------|------|--------|--------|------|
| beginner | 5 | 25% | 10% | 入门 |
| easy | 8 | 15% | 5% | 初级 |
| medium | 12 | 8% | 2% | 中级 |
| hard | 18 | 3% | 0% | 高级 |
| expert | 22 | 0% | 0% | 专家 |

#### 类: `AIPlayer`

**职责**: 根据难度等级选择走法，模拟不同水平的AI对手。

**核心方法**:

| 方法 | 说明 |
|------|------|
| `get_move(board)` | 根据难度选择走法 |
| `get_hint(board)` | 获取提示（最佳着法+评分+胜率） |
| `close()` | 关闭引擎 |

**走法选择策略** (`get_move`):

```
1. 获取多PV分析结果（multipv=5）
2. 特殊情况直接返回最佳：
   - 被将军时
   - 吃子且评分优势 > 150cp
3. 根据难度概率选择：
   - blunder_rate 概率 → 选择第3-5候选着法
   - random_rate 概率 → 选择第2候选着法
   - 否则 → 选择最佳着法
```

#### 类: `PracticeSession`

**职责**: 管理一次完整的AI对弈练习会话，包括初始化、走子、悔棋、提示、认输等操作。

**核心方法**:

| 方法 | 说明 |
|------|------|
| `start_from_fen(fen, user_color, difficulty)` | 从FEN开始对局 |
| `start_from_game(game_id, move_number, user_color, difficulty)` | 从棋谱某步开始 |
| `user_move(san)` | 用户走子（AI自动应着） |
| `undo_move()` | 悔棋（撤回用户+AI两步） |
| `get_hint()` | 获取提示 |
| `resign()` | 认输 |
| `get_status()` | 获取对局状态 |
| `to_dict()` | 序列化会话数据 |
| `close()` | 关闭AI引擎 |

**对局结束判定** (`_check_game_over`):
- 将杀 (checkmate)
- 逼和 (stalemate)
- 子力不足 (insufficient_material)
- 50步规则 (fifty_moves)
- 三次重复 (threefold_repetition)

**异常类**: `PracticeError` — 练习过程中的业务异常

---

### 3. PGNParser — PGN解析器

**文件**: `pgn_parser.py`

#### 类: `PGNParser`

**职责**: 解析 PGN 格式棋谱，提取对局信息和着法列表。

**核心方法**:

| 方法 | 说明 |
|------|------|
| `parse_file(file_path)` | 解析PGN文件（支持UTF-8/Latin-1） |
| `parse_content(pgn_string)` | 解析PGN文本 |
| `parse_multiple_games(pgn_string)` | 静态方法，解析包含多局的PGN |
| `get_moves_list()` | 获取解析后的着法列表 |
| `get_game_info()` | 获取对局信息 |
| `to_fen_list()` | 获取FEN序列 |

**解析结果格式**:

```python
{
    "game_info": {
        "event": "...", "site": "...", "date": "...",
        "white": "Carlsen", "black": "Nakamura",
        "result": "1-0", "eco": "B90", "opening": "Sicilian",
        "white_elo": 2863, "black_elo": 2768,
        ...
    },
    "moves": [
        {"move_number": 1, "white": "e4", "black": "c5",
         "white_fen": "...", "black_fen": "...",
         "white_comment": "", "black_comment": "",
         "white_nags": [], "black_nags": []},
        ...
    ],
    "final_fen": "...",
    "total_moves": 42
}
```

**设计要点**:
- 基于 `chess.pgn.read_game()` 实现，支持注释和 NAG 标记
- `parse_multiple_games()` 循环读取直到 `read_game()` 返回 None
- 双编码兼容：UTF-8 失败后尝试 Latin-1

**异常类**: `PGNParsingError` — PGN 解析错误

---

### 4. OpeningRecognizer — 开局识别器

**文件**: `opening_recognizer.py`

#### 类: `OpeningRecognizer`

**职责**: 根据着法序列识别开局，提供开局信息查询和相似开局推荐。

**数据来源**:
1. 优先从数据库 `Opening` 表加载
2. 数据库为空时使用内置的 `_FALLBACK_OPENINGS` 字典（约30个常见开局）

**ECO分类** (`CATEGORY_NAMES`):

| 分类 | 名称 |
|------|------|
| A | Flank Openings（侧翼开局） |
| B | Semi-Open Games（半开放对局） |
| C | Open Games（开放对局） |
| D | Closed & Semi-Closed Games（封闭/半封闭对局） |
| E | Indian Defenses（印度防御） |

**核心方法**:

| 方法 | 说明 |
|------|------|
| `identify_opening(pgn_moves)` | 识别开局（返回ECO代码、名称、置信度） |
| `get_eco_info(eco_code)` | 根据ECO代码获取开局信息 |
| `find_similar_openings(moves, top_k=3)` | 查找相似开局 |
| `get_opening_tree()` | 获取开局分类树 |

**识别算法** (`identify_opening`):

```
1. 标准化着法（去除+#!?符号）
2. 遍历所有已知开局，计算匹配着法数
3. 选择匹配数最多的开局
4. 置信度计算：
   - 基础: matched_count / total_opening_moves
   - 部分匹配: × 0.7
   - 匹配 >= 4步: 最低 0.8
   - 匹配 >= 2步: 最低 0.5
```

**前缀索引** (`_build_move_prefixes`): 构建着法前缀到 ECO 代码的映射，用于快速查找候选开局。

---

### 5. FENUtils — FEN工具集

**文件**: `fen_utils.py`

**职责**: 提供 FEN 字符串的解析、验证、转换和操作工具函数。

**核心方法**:

| 方法 | 说明 |
|------|------|
| `parse_fen(fen)` | 解析FEN为结构化字典（含棋盘数组、易位权等） |
| `fen_to_board_array(fen)` | FEN → 8×8棋盘数组 |
| `get_piece_at(fen, square)` | 获取指定格子的棋子 |
| `make_move(fen, move)` | 在FEN上执行着法，返回新FEN |
| `is_valid_fen(fen)` | 验证FEN格式有效性 |
| `board_to_fen(board_array, ...)` | 棋盘数组 → FEN字符串 |
| `get_legal_moves(fen)` | 获取合法着法列表 |
| `is_checkmate(fen)` | 判断是否将杀 |
| `is_stalemate(fen)` | 判断是否逼和 |
| `is_check(fen)` | 判断是否被将军 |
| `get_king_square(fen, color)` | 获取王的位置 |
| `board_to_unicode(fen)` | 棋盘Unicode字符画 |

**辅助函数**:

| 函数 | 说明 |
|------|------|
| `square_to_coords(square)` | 格子名→坐标 (如 "e4" → (4, 4)) |
| `coords_to_square(file_idx, rank_idx)` | 坐标→格子名 |
| `get_square_color(square)` | 获取格子颜色（light/dark） |

**FEN验证规则** (`is_valid_fen`):
- 必须有6个部分
- 活动方: w 或 b
- 易位权: 仅含 KQkq 或 -
- 吃过路兵: 合法格子或 -
- 半回合计数/回合数: 非负整数
- 棋子排列: 8行，每行8格

**设计要点**: 所有方法均为 `@staticmethod`，基于 `chess.Board` 实现，先验证 FEN 有效性再操作。

---

### 6. puzzle_library — 预设残局库

**文件**: `puzzle_library.py`

**职责**: 管理系统内置的残局题目，提供分类查询和数据库初始化功能。

**预设残局** (`PUZZLE_LIBRARY`):

| 键 | 名称 | 分类 | 难度 |
|----|------|------|------|
| endgame_king_pawn | 王兵残局 | endgame | beginner |
| endgame_rook | 车杀残局 | endgame | easy |
| endgame_queen_vs_rook | 后对车 | endgame | medium |
| tactic_fork | 骑士叉击 | tactics | easy |
| tactic_pin | 牵制战术 | tactics | medium |
| tactic_discovered_attack | 闪击战术 | tactics | hard |
| opening_scholar_mate | 学者将杀 | mate | beginner |
| endgame_bishop_pair | 双象残局 | endgame | hard |
| mate_in_two_1 | 两步将杀 | mate | medium |
| mate_in_two_2 | 后翼将杀 | mate | easy |

**核心函数**:

| 函数 | 说明 |
|------|------|
| `get_all_puzzles()` | 获取所有预设残局 |
| `get_puzzles_by_category(category)` | 按分类筛选 |
| `get_puzzles_by_difficulty(difficulty)` | 按难度筛选 |
| `get_puzzle(puzzle_id)` | 获取单个残局 |
| `init_system_puzzles()` | 初始化预设残局到数据库（幂等操作） |

**初始化逻辑**: `init_system_puzzles()` 检查数据库中是否已有预设残局（`is_preset=True`），若无则批量插入。编号 < 1000 为预设残局保留区间。

---

## 服务间调用关系

```
routes/practice.py
  ├── AIPlayer.get_move()          ← AI走法选择
  ├── PracticeSession              ← 会话管理
  │     └── AIPlayer               ← 内部使用AI引擎
  └── StockfishAnalyzer            ← 复盘分析

routes/games.py
  ├── PGNParser.parse_multiple_games()  ← PGN解析
  ├── OpeningRecognizer.identify_opening() ← 开局识别
  └── StockfishAnalyzer.analyze_game()  ← 棋谱分析

routes/analysis.py
  └── StockfishAnalyzer.analyze_game()  ← 异步分析
```

## 通用设计模式

1. **降级模式**: StockfishAnalyzer 和 AIPlayer 均实现 Mock 降级，引擎不可用时使用随机模拟
2. **资源管理**: 所有引擎封装类提供 `close()` 方法和 `__del__` 析构，确保 UCI 进程正确关闭
3. **异常体系**: `AnalysisError`、`PGNParsingError`、`PracticeError` 分层定义业务异常
4. **回调机制**: `analyze_game()` 支持 `callback(progress, move_data)` 实时进度通知
