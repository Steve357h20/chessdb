# ChessDB API 文档

Base URL: `http://localhost:5000/api`

所有接口返回 JSON 格式数据。

## 认证方式

除公开接口外，需要在请求头中携带 JWT Token：

```
Authorization: Bearer <access_token>
```

Token 有效期为 24 小时（86400 秒），过期后需重新登录获取。

部分接口使用 `@jwt_required(optional=True)`，表示认证可选：携带 Token 时关联用户，未携带时以匿名身份访问。

---

## 目录

- [认证模块 `/api/auth`](#认证模块-apiauth)
- [棋谱模块 `/api/games`](#棋谱模块-apigames)
- [棋手模块 `/api/players`](#棋手模块-apiplayers)
- [开局模块 `/api/openings`](#开局模块-apiopenings)
- [分析模块 `/api/analysis`](#分析模块-apianalysis)
- [练习模块 `/api/practice`](#练习模块-apipractice)
- [收藏模块 `/api/collections`](#收藏模块-apicollections)
- [浏览历史模块 `/api/browsing`](#浏览历史模块-apibrowsing)
- [通用错误响应](#通用错误响应)
- [限流规则](#限流规则)

---

## 认证模块 `/api/auth`

### POST /auth/register

注册新用户。限流：5次/分钟。

**请求体：**
```json
{
  "username": "string (3-80字符)",
  "email": "string (有效邮箱格式)",
  "password": "string (最少6字符)"
}
```

**响应 201：**
```json
{
  "message": "Registration successful",
  "user": {
    "id": 1,
    "username": "player1",
    "email": "player1@example.com",
    "is_admin": false,
    "created_at": "2024-01-15T10:30:00"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | No data provided | 请求体为空 |
| 400 | Username, email and password are required | 缺少必填字段 |
| 400 | Username must be between 3 and 80 characters | 用户名长度不符 |
| 400 | Password must be at least 6 characters | 密码过短 |
| 400 | Invalid email format | 邮箱格式错误 |
| 409 | Username already exists | 用户名已存在 |
| 409 | Email already exists | 邮箱已注册 |
| 500 | Registration failed | 注册失败（数据库错误） |

### POST /auth/login

用户登录。限流：10次/分钟。

**请求体：**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应 200：**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "player1",
    "email": "player1@example.com",
    "is_admin": false,
    "created_at": "2024-01-15T10:30:00"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | No data provided | 请求体为空 |
| 400 | Username and password are required | 缺少用户名或密码 |
| 401 | Invalid username or password | 用户名或密码错误 |

### POST /auth/logout

退出登录。需要 JWT Token。

**Headers:** `Authorization: Bearer <token>`

**响应 200：**
```json
{
  "message": "Logout successful"
}
```

### GET /auth/profile

获取当前用户信息。需要 JWT Token。

**Headers:** `Authorization: Bearer <token>`

**响应 200：**
```json
{
  "id": 1,
  "username": "player1",
  "email": "player1@example.com",
  "is_admin": false,
  "created_at": "2024-01-15T10:30:00",
  "collection_count": 3
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | User not found | 用户不存在 |

### PUT /auth/profile

更新用户资料。需要 JWT Token。

**Headers:** `Authorization: Bearer <token>`

**请求体（所有字段可选）：**
```json
{
  "username": "string (3-80字符)",
  "email": "string (有效邮箱)",
  "old_password": "string (当前密码，修改密码时必填)",
  "new_password": "string (最少6字符，修改密码时必填)"
}
```

**响应 200：**
```json
{
  "message": "Profile updated",
  "user": {
    "id": 1,
    "username": "player1",
    "email": "newemail@example.com",
    "is_admin": false,
    "created_at": "2024-01-15T10:30:00"
  }
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | No data provided | 请求体为空 |
| 400 | Username must be between 3 and 80 characters | 用户名长度不符 |
| 400 | Invalid email format | 邮箱格式错误 |
| 400 | Current password is incorrect | 当前密码错误 |
| 400 | New password must be at least 6 characters | 新密码过短 |
| 404 | User not found | 用户不存在 |
| 409 | Username already in use | 用户名已被占用 |
| 409 | Email already in use | 邮箱已被占用 |
| 500 | Update failed | 更新失败（数据库错误） |

---

## 棋谱模块 `/api/games`

### GET /games/filters

获取棋谱筛选器选项（可用的 ECO 编码和结果类型）。无需认证。

**响应 200：**
```json
{
  "eco_codes": ["A00", "B20", "B90", "C42", "D02", "E60"],
  "results": ["1-0", "0-1", "1/2-1/2"]
}
```

### GET /games

获取棋谱列表（分页）。无需认证。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| per_page | int | 20 | 每页数量，最大 100 |
| player | string | - | 棋手名（模糊搜索白方或黑方） |
| date_from | string | - | 起始日期 |
| date_to | string | - | 结束日期 |
| eco | string | - | ECO 开局编码（前缀匹配） |
| result | string | - | 比赛结果 (1-0 / 0-1 / 1/2-1/2) |
| search | string | - | 通用搜索（棋手名/开局名/ECO编码） |
| sort | string | created_at | 排序字段 (created_at/date/white_elo/black_elo/total_moves/eco_code) |
| order | string | desc | 排序方向 (asc/desc) |

**响应 200：**
```json
{
  "items": [
    {
      "id": 1,
      "game_number": 1,
      "white_player_id": 1,
      "black_player_id": 2,
      "white_player_name": "Carlsen",
      "black_player_name": "Nakamura",
      "white_elo": 2860,
      "black_elo": 2780,
      "tournament_id": null,
      "tournament_name": "",
      "date": "2024.01.15",
      "result": "1-0",
      "eco_code": "B90",
      "opening_name": "Sicilian Najdorf",
      "total_moves": 45,
      "final_fen": "rnb... w - - 0 1",
      "termination": "Normal",
      "time_control": "600+5",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 20
}
```

### GET /games/:id

获取棋谱详情，包含 PGN 内容、着法列表和分析结果。无需认证。

**响应 200：**
```json
{
  "id": 1,
  "game_number": 1,
  "white_player_name": "Carlsen",
  "black_player_name": "Nakamura",
  "white_elo": 2860,
  "black_elo": 2780,
  "date": "2024.01.15",
  "result": "1-0",
  "eco_code": "B90",
  "opening_name": "Sicilian Najdorf",
  "total_moves": 45,
  "pgn_content": "1. e4 c5 2. Nf3 d6 ...",
  "moves": [
    {
      "move_number": 1,
      "san": "e4",
      "uci": "e2e4",
      "fen_before": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
      "fen_after": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
      "color": "w"
    }
  ],
  "has_analysis": true,
  "analysis": {
    "id": 1,
    "game_id": 1,
    "opening_eco": "B90",
    "key_moves": [
      {
        "move_number": 12,
        "san": "Nxe4",
        "evaluation": "!!",
        "score_diff": 2.5
      }
    ],
    "win_rate_curve": [
      { "move_number": 1, "white_win_rate": 52.3 }
    ],
    "analysis_data": { "..." : "完整分析数据" },
    "created_at": "2024-01-15T11:00:00"
  }
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Game not found | 棋谱不存在 |

### POST /games/upload

上传 PGN 文件。限流：10次/分钟。无需认证。

**请求：** `multipart/form-data`

| 字段 | 类型 | 说明 |
|------|------|------|
| files | File[] | PGN 文件（支持多个，扩展名 .pgn 或 .txt，最大 16MB） |

**响应 200：**
```json
{
  "uploaded": 5,
  "skipped": 1,
  "errors": [
    { "file": "broken.pgn", "error": "No valid game found" }
  ]
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | No files provided | 未提供文件 |

### POST /games/upload-pgn

通过文本内容上传 PGN。限流：10次/分钟。无需认证。

**请求体：**
```json
{
  "pgn": "1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6"
}
```

**响应 200：**
```json
{
  "imported": 1
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | No PGN content provided | PGN 内容为空 |
| 400 | Failed to parse PGN | PGN 解析失败 |

### PUT /games/:id

更新棋谱信息。需要 JWT Token。

**Headers:** `Authorization: Bearer <token>`

**请求体（所有字段可选）：**
```json
{
  "date": "2024.01.15",
  "result": "1-0",
  "eco_code": "B90",
  "opening_name": "Sicilian Najdorf",
  "tournament_id": 1
}
```

**响应 200：** 返回更新后的棋谱信息。

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Game not found | 棋谱不存在 |

### DELETE /games/:id

删除棋谱及其分析数据。需要 JWT Token。

**Headers:** `Authorization: Bearer <token>`

**响应 200：**
```json
{
  "message": "Game deleted"
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Game not found | 棋谱不存在 |

### GET /games/:id/moves

获取棋谱着法列表。无需认证。

**响应 200：**
```json
{
  "game_id": 1,
  "total_moves": 45,
  "moves": [
    {
      "move_number": 1,
      "san": "e4",
      "uci": "e2e4",
      "fen_before": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
      "fen_after": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
      "color": "w"
    }
  ]
}
```

### GET /games/:id/analysis

获取棋谱分析结果。无需认证。

**响应 200：** 返回分析详情，包含 `analysis_data`、`key_moves`、`win_rate_curve` 等。

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | No analysis found for this game | 该棋谱尚未分析 |

### POST /games/:id/analyze

同步分析棋谱。需要 JWT Token。若已有分析结果则返回缓存。

**Headers:** `Authorization: Bearer <token>`

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| depth | int | 20 | 分析深度，最大 20 |

**响应 200（新分析）：**
```json
{
  "message": "Analysis complete",
  "analysis_id": 1,
  "total_moves_analyzed": 45,
  "key_moves_count": 5
}
```

**缓存响应：**
```json
{
  "message": "Analysis already exists",
  "analysis_id": 1,
  "cached": true
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Game not found | 棋谱不存在 |
| 500 | Analysis failed | 分析失败 |

### GET /games/stats/elo-vs-moves

获取 ELO 与步数关系统计数据。无需认证。

**响应 200：**
```json
{
  "buckets": [
    {
      "avg_elo": 2200,
      "avg_moves": 42.5,
      "game_count": 150
    }
  ],
  "scatter": [
    {
      "avg_elo": 2350,
      "total_moves": 38,
      "result": "1-0",
      "elo_gap": 120
    }
  ],
  "density_grid": [[2200, 40, 25]],
  "distribution": [
    {
      "elo_bucket": 2000,
      "count": 300,
      "min": 15,
      "max": 120,
      "mean": 42.5,
      "std": 15.3
    }
  ],
  "total_games": 1500
}
```

### GET /games/stats/openings

获取开局统计数据。无需认证。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| category | string | - | 开局分类过滤 (A/B/C/D/E) |

**响应 200：**
```json
{
  "openings": [
    {
      "eco_code": "B90",
      "name": "Sicilian Najdorf",
      "total": 150,
      "white_win_rate": 52.3,
      "black_win_rate": 30.1,
      "draw_rate": 17.6,
      "avg_moves": 42.5,
      "avg_elo": 2350
    }
  ],
  "categories": [
    { "category": "B", "name": "半开放开局", "total": 500 }
  ],
  "elo_openings": [
    { "category": "B", "elo_bucket": 2000, "total": 120 }
  ],
  "total_games": 1500
}
```

---

## 棋手模块 `/api/players`

### GET /players/filters

获取棋手筛选器选项（可用的头衔和国家）。无需认证。

**响应 200：**
```json
{
  "titles": ["GM", "IM", "FM", "WGM"],
  "countries": ["China", "USA", "Russia"]
}
```

### GET /players

获取棋手列表（分页）。无需认证。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| per_page | int | 20 | 每页数量，最大 100 |
| search | string | - | 搜索棋手名（模糊匹配） |
| country | string | - | 国家（模糊匹配） |
| title | string | - | 棋手头衔（精确匹配） |
| min_elo | int | 0 | 最低 ELO |
| max_elo | int | 0 | 最高 ELO |
| sort | string | elo_rating | 排序字段 (name/elo_rating/created_at) |
| order | string | desc | 排序方向 (asc/desc) |

**响应 200：**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Carlsen",
      "title": "GM",
      "country": "Norway",
      "elo_rating": 2860,
      "birth_date": "1990-11-30",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 500,
  "page": 1,
  "per_page": 20
}
```

### GET /players/:id

获取棋手详情（含统计数据）。无需认证。

**响应 200：**
```json
{
  "id": 1,
  "name": "Carlsen",
  "title": "GM",
  "country": "Norway",
  "elo_rating": 2860,
  "birth_date": "1990-11-30",
  "stats": {
    "total_games": 150,
    "wins": 80,
    "losses": 40,
    "draws": 30,
    "win_rate": 53.3,
    "as_white": { "wins": 50, "losses": 20, "draws": 15 },
    "as_black": { "wins": 30, "losses": 20, "draws": 15 }
  }
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Player not found | 棋手不存在 |

### GET /players/:id/games

获取棋手对局列表（分页）。无需认证。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| per_page | int | 20 | 每页数量，最大 100 |
| color | string | - | 颜色过滤 (white/black) |
| result | string | - | 结果过滤 (1-0/0-1/1/2-1/2) |

**响应 200：**
```json
{
  "items": [
    {
      "id": 1,
      "white_player_name": "Carlsen",
      "black_player_name": "Nakamura",
      "result": "1-0",
      "date": "2024.01.15",
      "eco_code": "B90",
      "opening_name": "Sicilian Najdorf",
      "total_moves": 45
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 20
}
```

### GET /players/:id/stats

获取棋手详细统计数据（含 ECO 分类统计）。无需认证。

**响应 200：**
```json
{
  "total_games": 150,
  "wins": 80,
  "losses": 40,
  "draws": 30,
  "win_rate": 53.3,
  "as_white": { "wins": 50, "losses": 20, "draws": 15 },
  "as_black": { "wins": 30, "losses": 20, "draws": 15 },
  "eco_stats": {
    "B": { "total": 50, "wins": 30, "losses": 10, "draws": 10 },
    "C": { "total": 40, "wins": 20, "losses": 15, "draws": 5 }
  }
}
```

---

## 开局模块 `/api/openings`

### GET /openings

获取开局列表（分页）。无需认证。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| per_page | int | 20 | 每页数量，最大 100 |
| category | string | - | 分类过滤 (A/B/C/D/E) |
| search | string | - | 搜索开局名称/ECO编码/变体名 |
| eco | string | - | ECO 编码（前缀匹配） |
| sort | string | eco_code | 排序字段 (eco_code/name/white_win_rate/black_win_rate/draw_rate/popularity) |
| order | string | asc | 排序方向 (asc/desc) |

**响应 200：**
```json
{
  "items": [
    {
      "eco_code": "B90",
      "name": "Sicilian Najdorf",
      "variation": "6. Bg5",
      "moves": ["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6", "Bg5"],
      "category": "B",
      "description": "The Najdorf Variation is the most popular and combative...",
      "popularity": 95,
      "white_win_rate": 52.3,
      "black_win_rate": 30.1,
      "draw_rate": 17.6
    }
  ],
  "total": 500,
  "page": 1,
  "per_page": 20
}
```

### GET /openings/:eco

获取开局详情（ECO 编码）。无需认证。

**路径参数：** `eco` - ECO 编码（如 B90），不区分大小写

**响应 200：**
```json
{
  "eco_code": "B90",
  "name": "Sicilian Najdorf",
  "variation": "6. Bg5",
  "moves": ["e4", "c5", "..."],
  "category": "B",
  "description": "...",
  "popularity": 95,
  "white_win_rate": 52.3,
  "black_win_rate": 30.1,
  "draw_rate": 17.6,
  "recognizer_info": {
    "code": "B90",
    "name": "Sicilian Najdorf",
    "moves": ["e4", "c5", "..."]
  },
  "example_games": [
    {
      "id": 1,
      "white_player_name": "Carlsen",
      "black_player_name": "Nakamura",
      "white_elo": 2860,
      "black_elo": 2780,
      "result": "1-0",
      "date": "2024.01.15",
      "eco_code": "B90",
      "opening_name": "Sicilian Najdorf"
    }
  ]
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Opening not found | 开局不存在 |

### POST /openings/identify

识别开局。无需认证。

**请求体：**
```json
{
  "moves": ["e4", "c5", "Nf3", "d6"]
}
```

**响应 200：**
```json
{
  "eco_code": "B90",
  "name": "Sicilian Najdorf",
  "variation": "6. Bg5",
  "moves_matched": 4,
  "similar_openings": [
    {
      "eco_code": "B80",
      "name": "Sicilian Scheveningen",
      "similarity": 0.85
    }
  ]
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | No moves provided | 着法列表为空 |

### GET /openings/tree

获取开局树结构。无需认证。

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| eco | string | ECO 编码过滤 |

**响应 200：** 返回按分类（A-E）组织的开局树结构，包含数据库中的开局信息和识别器信息。

---

## 分析模块 `/api/analysis`

### POST /analysis/game/:game_id/start

异步启动棋谱分析任务。需要 JWT Token。限流：5次/分钟。

若已有分析结果则返回缓存，若已有进行中的任务则返回任务信息。

**Headers:** `Authorization: Bearer <token>`

**响应 200（新任务）：**
```json
{
  "message": "Analysis started",
  "task_id": "uuid-string",
  "game_id": 1
}
```

**缓存响应：**
```json
{
  "message": "Analysis already exists",
  "analysis_id": 1,
  "game_id": 1,
  "cached": true
}
```

**进行中响应：**
```json
{
  "message": "Analysis already in progress",
  "task_id": "uuid-string",
  "game_id": 1
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Game not found | 棋谱不存在 |

### GET /analysis/game/:game_id/status

获取棋谱分析状态。需要 JWT Token。

**Headers:** `Authorization: Bearer <token>`

**响应 200（进行中）：**
```json
{
  "task_id": "uuid-string",
  "game_id": 1,
  "status": "running",
  "progress": 0.45,
  "result": null,
  "error": null
}
```

**响应 200（已完成-缓存）：**
```json
{
  "game_id": 1,
  "status": "completed",
  "progress": 1.0,
  "analysis_id": 1,
  "cached": true
}
```

**响应 200（无任务）：**
```json
{
  "game_id": 1,
  "status": "none",
  "progress": 0.0
}
```

**status 取值：** `pending` / `running` / `completed` / `failed` / `none`

### GET /analysis/game/:game_id

获取棋谱分析结果。需要 JWT Token。

**Headers:** `Authorization: Bearer <token>`

**响应 200：** 返回完整分析数据。

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | No analysis found for this game | 分析结果不存在 |

### GET /analysis/game/:game_id/move/:move_number

获取指定着法的分析数据。需要 JWT Token。

**Headers:** `Authorization: Bearer <token>`

**路径参数：**
- `game_id` - 棋谱 ID
- `move_number` - 着法序号

**响应 200：** 返回该着法的详细分析数据。

### GET /analysis/tasks/:task_id

获取分析任务状态。需要 JWT Token。

**Headers:** `Authorization: Bearer <token>`

**响应 200：**
```json
{
  "task_id": "uuid-string",
  "status": "completed",
  "progress": 1.0,
  "game_id": 1,
  "result": {
    "analysis_id": 1,
    "total_moves": 45,
    "key_moves_count": 5
  },
  "error": null
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Task not found | 任务不存在 |

### GET /analysis/tasks

获取所有分析任务列表。需要 JWT Token。

**Headers:** `Authorization: Bearer <token>`

**响应 200：**
```json
{
  "tasks": [
    {
      "task_id": "uuid-string",
      "game_id": 1,
      "status": "running",
      "progress": 0.45,
      "started_at": "2024-01-15T11:00:00"
    }
  ],
  "total": 3
}
```

### DELETE /analysis/tasks/:task_id

取消分析任务。需要 JWT Token。

**Headers:** `Authorization: Bearer <token>`

**响应 200：**
```json
{
  "message": "Task cancelled"
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Task not found | 任务不存在 |
| 400 | Task already completed | 任务已完成，无法取消 |

### GET /analysis/engines

获取引擎信息。无需认证。

**响应 200：**
```json
{
  "engine": {
    "name": "Stockfish",
    "version": "Stockfish 16.1",
    "is_mock": false,
    "depth": 20,
    "threads": 1,
    "hash_size": 256
  },
  "config": {
    "depth": 20,
    "threads": 1,
    "hash_size": 256,
    "timeout": 300
  }
}
```

> 当 Stockfish 引擎不可用时，`is_mock` 为 `true`，分析将使用 Mock 模式生成随机数据。

---

## 练习模块 `/api/practice`

### GET /practice/puzzles

获取残局题列表。无需认证。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| per_page | int | 50 | 每页数量，最大 100 |
| category | string | - | 分类过滤 (endgame/tactics/mate) |
| difficulty | string | - | 难度过滤 (beginner/easy/medium/hard/expert) |
| source_game_id | int | - | 来源棋谱 ID |

**响应 200：**
```json
{
  "puzzles": [
    {
      "id": 1,
      "puzzle_number": 1,
      "name": "王兵残局",
      "category": "endgame",
      "difficulty": "beginner",
      "description": "白方王和兵对抗黑方王",
      "hint": "用王保护兵前进",
      "fen": "8/8/8/8/4k3/8/4P3/4K3 w - - 0 1",
      "source_game_id": null,
      "from_move": null,
      "created_by": null,
      "is_preset": true,
      "practice_count": 25,
      "solve_count": 18,
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 30,
  "page": 1,
  "per_page": 50,
  "pages": 1
}
```

### GET /practice/puzzles/:puzzle_id

获取残局题详情（含练习记录）。无需认证。

**响应 200：**
```json
{
  "id": 1,
  "puzzle_number": 1,
  "name": "王兵残局",
  "category": "endgame",
  "difficulty": "beginner",
  "fen": "8/8/8/8/4k3/8/4P3/4K3 w - - 0 1",
  "source_game": {
    "id": 5,
    "white_player_name": "Carlsen",
    "black_player_name": "Nakamura",
    "result": "1-0",
    "date": "2024.01.15"
  },
  "practice_records": [
    {
      "id": 10,
      "user_id": 1,
      "mode": "puzzle",
      "result": "1-0",
      "total_moves": 15,
      "created_at": "2024-01-16T08:00:00"
    }
  ]
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Puzzle not found | 残局题不存在 |

### POST /practice/puzzles

创建残局题。需要 JWT Token。

**Headers:** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "name": "string (必填)",
  "fen": "string (必填，合法 FEN)",
  "category": "string (默认 endgame)",
  "difficulty": "string (默认 medium)",
  "description": "string (可选)",
  "hint": "string (可选)",
  "source_game_id": "int (可选)",
  "from_move": "int (可选)"
}
```

**响应 201：** 返回创建的残局题详情。

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | Name and FEN are required | 缺少必填字段 |
| 400 | Invalid FEN | FEN 格式不合法 |
| 404 | Source game not found | 来源棋谱不存在 |

### DELETE /practice/puzzles/:puzzle_id

删除残局题。需要 JWT Token。仅创建者或管理员可删除，预设题不可删除。

**Headers:** `Authorization: Bearer <token>`

**响应 200：**
```json
{
  "message": "Puzzle deleted"
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 403 | Cannot delete preset puzzle | 预设题不可删除 |
| 403 | Not authorized to delete this puzzle | 无权删除 |
| 404 | Puzzle not found | 残局题不存在 |

### GET /practice/search_games

搜索棋谱（用于从棋谱开始练习）。无需认证。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| q | string | - | 搜索关键词（棋手名/开局名） |
| limit | int | 20 | 返回数量，最大 100 |

**响应 200：**
```json
{
  "games": [
    {
      "id": 1,
      "white_player_name": "Carlsen",
      "black_player_name": "Nakamura",
      "white_elo": 2860,
      "black_elo": 2780,
      "date": "2024.01.15",
      "result": "1-0",
      "eco_code": "B90",
      "opening_name": "Sicilian Najdorf",
      "total_moves": 45
    }
  ],
  "total": 5
}
```

### POST /practice/start

开始练习会话。支持可选 JWT Token（匿名用户也可练习）。

**请求体：**
```json
{
  "mode": "string (custom/puzzle/from_game)",
  "user_color": "string (white/black，默认 white)",
  "difficulty": "string (beginner/easy/medium/hard/expert，默认 medium)",
  "puzzle_id": "int (puzzle 模式必填)",
  "game_id": "int (from_game 模式必填)",
  "from_move": "int (from_game 模式可选，从第几步开始)",
  "custom_fen": "string (custom 模式可选，自定义起始 FEN)"
}
```

**响应 200：**
```json
{
  "session_id": "uuid-string",
  "mode": "custom",
  "puzzle_id": null,
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "start_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "is_user_turn": true,
  "user_color": "white",
  "difficulty": "medium"
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | Invalid mode | 无效模式 |
| 400 | puzzle_id is required for puzzle mode | puzzle 模式缺少 puzzle_id |
| 400 | game_id is required for from_game mode | from_game 模式缺少 game_id |
| 400 | Invalid FEN | FEN 格式不合法 |
| 404 | Puzzle not found | 残局题不存在 |
| 404 | Game not found | 棋谱不存在 |

### POST /practice/move

玩家走棋。支持可选 JWT Token。

**请求体：**
```json
{
  "session_id": "string (必填)",
  "move": "string (必填，SAN 格式如 e4, Nf3, O-O)"
}
```

**响应 200（AI 应答）：**
```json
{
  "fen": "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
  "user_fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
  "is_user_turn": true,
  "is_game_over": false,
  "ai_move": "c5"
}
```

**游戏结束响应：**
```json
{
  "fen": "...",
  "is_user_turn": false,
  "is_game_over": true,
  "result": "1-0"
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | session_id and move are required | 缺少必填字段 |
| 400 | Illegal move | 非法着法 |
| 400 | Invalid session | 无效会话 |
| 410 | Session expired | 会话已过期 |

### POST /practice/undo

悔棋。撤销玩家和 AI 的一对着法。支持可选 JWT Token。

**请求体：**
```json
{
  "session_id": "string (必填)"
}
```

**响应 200：**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | session_id is required | 缺少 session_id |
| 400 | Cannot undo | 无法悔棋（着法不足） |
| 400 | Invalid session | 无效会话 |
| 410 | Session expired | 会话已过期 |

### POST /practice/hint

获取提示（最佳着法）。支持可选 JWT Token。

**请求体：**
```json
{
  "session_id": "string (必填)"
}
```

**响应 200：**
```json
{
  "hint": "Nf3",
  "message": "建议走 Nf3"
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | session_id is required | 缺少 session_id |
| 400 | Invalid session | 无效会话 |
| 410 | Session expired | 会话已过期 |

### POST /practice/resign

认输。支持可选 JWT Token。

**请求体：**
```json
{
  "session_id": "string (必填)"
}
```

**响应 200：**
```json
{
  "result": "0-1",
  "message": "You resigned"
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | session_id is required | 缺少 session_id |
| 400 | Invalid session | 无效会话 |
| 410 | Session expired | 会话已过期 |

### GET /practice/status/:session_id

获取练习会话状态。支持可选 JWT Token。

**响应 200：** 返回当前会话状态信息。

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 410 | Session expired | 会话已过期 |

### GET /practice/history

获取练习历史记录。支持可选 JWT Token（登录用户返回自己的记录，匿名返回空）。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| per_page | int | 20 | 每页数量，最大 100 |
| difficulty | string | - | 难度过滤 |
| mode | string | - | 模式过滤 (puzzle/from_game/custom) |
| result | string | - | 结果过滤 (win/lose/draw) |
| sort | string | created_at | 排序字段 (created_at/difficulty/total_moves/hints_used) |
| order | string | desc | 排序方向 (asc/desc) |

**响应 200：**
```json
{
  "history": [
    {
      "id": 1,
      "user_id": 1,
      "username": "player1",
      "mode": "custom",
      "puzzle_id": null,
      "source_game_id": null,
      "user_color": "w",
      "difficulty": "medium",
      "moves": [{ "san": "e4", "color": "w" }],
      "result": "1-0",
      "total_moves": 30,
      "hints_used": 2,
      "undo_count": 1,
      "has_analysis": true,
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

### GET /practice/history/:practice_id

获取练习记录详情。支持可选 JWT Token。

**响应 200：** 返回练习记录详情，包含着法列表。

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Practice game not found | 练习记录不存在 |

### POST /practice/analyze/:practice_id

异步启动练习复盘分析。支持可选 JWT Token。

**响应 200：**
```json
{
  "message": "Analysis started",
  "task_id": "uuid-string",
  "practice_id": 1
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Practice game not found | 练习记录不存在 |
| 400 | Analysis already in progress | 分析已在进行中 |

### GET /practice/analyze/:practice_id/status

获取练习分析状态。支持可选 JWT Token。

**响应 200（进行中）：**
```json
{
  "task_id": "uuid-string",
  "practice_id": 1,
  "status": "running",
  "progress": 0.35,
  "result": null,
  "error": null
}
```

**响应 200（已完成-缓存）：**
```json
{
  "practice_id": 1,
  "status": "completed",
  "progress": 1.0,
  "cached": true
}
```

**响应 200（无任务）：**
```json
{
  "practice_id": 1,
  "status": "none",
  "progress": 0.0
}
```

### GET /practice/analyze/:practice_id/result

获取练习分析结果。支持可选 JWT Token。

**响应 200：**
```json
{
  "practice_id": 1,
  "analysis": {
    "total_moves": 30,
    "moves": [
      {
        "move_number": 1,
        "color": "w",
        "san": "e4",
        "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "score": 0.35,
        "white_win_rate": 52.3,
        "mate_in": null,
        "evaluation": "",
        "best_moves": [
          {
            "move": "e4",
            "score": 0.35,
            "win_rate": 52.3,
            "pv": ["e4", "c5", "Nf3"],
            "depth": 20
          }
        ],
        "score_diff": 0.0,
        "delta": 0.0,
        "nag": null
      }
    ],
    "final_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
  }
}
```

**分析数据字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| score | float | 白方视角分数（正=白优，负=黑优），将杀编码为 ±(100+距离) |
| white_win_rate | float | 白方胜率 (0.1-99.9) |
| mate_in | int/null | 将杀距离，null 表示非将杀局面 |
| evaluation | string | 着法评价标记：`!!`妙手 / `!`好着 / `!?`有趣 / `?!`不精确 / `?`失误 / `??`严重失误 |
| best_moves | array | 最佳着法列表（最多3个），含 PV 变化线 |
| score_diff | float | 与最佳着法的分数差距绝对值 |
| delta | float | 与最佳着法的分数差距（正=失误，负=对手失误） |
| nag | string/null | 数字标注（对应 evaluation 的数字编码） |

**将杀分数编码规则：**
- 白方将杀：`100 + mate_distance`（如 +M3 = 103.0）
- 黑方将杀：`-(100 + mate_distance)`（如 -M5 = -105.0）
- 前端显示时：`mateDist = Math.abs(score) - 100`，若 `mateDist <= 0` 显示为 ±M1

**着法评价阈值：**

| 差距 (兵) | 标记 | 含义 |
|-----------|------|------|
| < 0.05 且为最佳 | `!!` | 妙手 |
| 0.05 - 0.20 | `!` | 好着 |
| 0.20 - 0.50 | `!?` | 有趣 |
| 0.50 - 1.00 | `?!` | 不精确 |
| 1.00 - 2.00 | `?` | 失误 |
| > 2.00 | `??` | 严重失误 |

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Practice game not found | 练习记录不存在 |
| 404 | No analysis available | 分析结果不存在 |
| 500 | Invalid analysis data | 分析数据损坏 |

---

## 收藏模块 `/api/collections`

所有接口需要 JWT Token。

### GET /collections

获取收藏列表（分页）。

**Headers:** `Authorization: Bearer <token>`

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| per_page | int | 20 | 每页数量，最大 100 |

**响应 200：**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "game_id": 5,
      "note": "精彩对局",
      "created_at": "2024-01-15T10:30:00",
      "white_player_name": "Carlsen",
      "black_player_name": "Nakamura",
      "result": "1-0",
      "eco_code": "B90",
      "opening_name": "Sicilian Najdorf",
      "date": "2024.01.15"
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 20
}
```

### POST /collections

添加收藏。

**Headers:** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "game_id": 5,
  "note": "精彩对局"
}
```

**响应 201：**
```json
{
  "id": 1,
  "user_id": 1,
  "game_id": 5,
  "note": "精彩对局",
  "created_at": "2024-01-15T10:30:00"
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | game_id is required | 缺少 game_id |
| 404 | Game not found | 棋谱不存在 |
| 409 | Already in collection | 已收藏 |

### DELETE /collections/:collection_id

移除收藏。

**Headers:** `Authorization: Bearer <token>`

**响应 200：**
```json
{
  "message": "Removed from collection"
}
```

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Collection not found | 收藏记录不存在 |

### GET /collections/check/:game_id

检查棋谱是否已收藏。

**Headers:** `Authorization: Bearer <token>`

**响应 200（已收藏）：**
```json
{
  "is_collected": true,
  "collection": {
    "id": 1,
    "user_id": 1,
    "game_id": 5,
    "note": "精彩对局",
    "created_at": "2024-01-15T10:30:00"
  }
}
```

**响应 200（未收藏）：**
```json
{
  "is_collected": false
}
```

### PUT /collections/:collection_id

更新收藏备注。

**Headers:** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "note": "新的备注内容"
}
```

**响应 200：** 返回更新后的收藏信息。

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 404 | Collection not found | 收藏记录不存在 |

---

## 浏览历史模块 `/api/browsing`

所有接口需要 JWT Token。

### GET /browsing

获取浏览历史（分页）。

**Headers:** `Authorization: Bearer <token>`

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| per_page | int | 20 | 每页数量，最大 100 |

**响应 200：**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "game_id": 5,
      "viewed_at": "2024-01-15T10:30:00",
      "white_player_name": "Carlsen",
      "black_player_name": "Nakamura",
      "result": "1-0",
      "eco_code": "B90",
      "opening_name": "Sicilian Najdorf",
      "date": "2024.01.15"
    }
  ],
  "total": 30,
  "page": 1,
  "per_page": 20
}
```

### POST /browsing

记录浏览历史（若已存在则更新时间）。

**Headers:** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "game_id": 5
}
```

**响应 201：** 返回浏览记录信息。

**错误响应：**

| 状态码 | error 字段 | 说明 |
|--------|-----------|------|
| 400 | game_id is required | 缺少 game_id |
| 404 | Game not found | 棋谱不存在 |

### DELETE /browsing/:game_id

删除指定浏览记录。

**Headers:** `Authorization: Bearer <token>`

**响应 200：**
```json
{
  "message": "Deleted"
}
```

### POST /browsing/clear

清空所有浏览历史。

**Headers:** `Authorization: Bearer <token>`

**响应 200：**
```json
{
  "message": "Cleared"
}
```

---

## 通用错误响应

所有接口在出错时返回统一格式：

```json
{
  "error": "Error type",
  "detail": "Detailed message"
}
```

> 部分接口仅返回 `error` 字段，不含 `detail`。

| 状态码 | 说明 | 前端处理 |
|--------|------|----------|
| 400 | 请求参数错误 | 显示错误消息 |
| 401 | 未认证 / Token 过期 | 清除 Token，跳转登录页 |
| 403 | 无权限 | 显示"没有操作权限" |
| 404 | 资源不存在 | 显示"请求的资源不存在" |
| 409 | 资源冲突（如用户名已存在、已收藏） | 显示具体冲突信息 |
| 410 | 会话已过期（练习对弈会话） | 标记 `_sessionExpired`，结束练习 |
| 422 | 数据验证失败 | 显示验证错误 |
| 429 | 请求频率超限 | 显示"请求过于频繁，请稍后再试" |
| 500 | 服务器内部错误 | 显示"服务器内部错误" |

## 限流规则

| 接口 | 限制 | 说明 |
|------|------|------|
| POST /auth/register | 5次/分钟 | 防止批量注册 |
| POST /auth/login | 10次/分钟 | 防止暴力破解 |
| POST /games/upload | 10次/分钟 | 防止大量文件上传 |
| POST /games/upload-pgn | 10次/分钟 | 防止大量文本导入 |
| POST /analysis/game/:id/start | 5次/分钟 | 防止分析资源滥用 |
| 全局默认 | 2000次/天，500次/小时 | 通用保护 |

超出限流时返回 429 状态码。

## 接口总览

| 模块 | 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|------|
| 认证 | POST | /auth/register | 无 | 注册 |
| 认证 | POST | /auth/login | 无 | 登录 |
| 认证 | POST | /auth/logout | JWT | 登出 |
| 认证 | GET | /auth/profile | JWT | 获取用户信息 |
| 认证 | PUT | /auth/profile | JWT | 更新用户资料 |
| 棋谱 | GET | /games/filters | 无 | 获取筛选选项 |
| 棋谱 | GET | /games | 无 | 棋谱列表 |
| 棋谱 | GET | /games/:id | 无 | 棋谱详情 |
| 棋谱 | POST | /games/upload | 无 | 上传 PGN 文件 |
| 棋谱 | POST | /games/upload-pgn | 无 | 文本导入 PGN |
| 棋谱 | PUT | /games/:id | JWT | 更新棋谱 |
| 棋谱 | DELETE | /games/:id | JWT | 删除棋谱 |
| 棋谱 | GET | /games/:id/moves | 无 | 获取着法列表 |
| 棋谱 | GET | /games/:id/analysis | 无 | 获取分析结果 |
| 棋谱 | POST | /games/:id/analyze | JWT | 同步分析 |
| 棋谱 | GET | /games/stats/elo-vs-moves | 无 | ELO-步数统计 |
| 棋谱 | GET | /games/stats/openings | 无 | 开局统计 |
| 棋手 | GET | /players/filters | 无 | 获取筛选选项 |
| 棋手 | GET | /players | 无 | 棋手列表 |
| 棋手 | GET | /players/:id | 无 | 棋手详情 |
| 棋手 | GET | /players/:id/games | 无 | 棋手对局列表 |
| 棋手 | GET | /players/:id/stats | 无 | 棋手统计 |
| 开局 | GET | /openings | 无 | 开局列表 |
| 开局 | GET | /openings/:eco | 无 | 开局详情 |
| 开局 | POST | /openings/identify | 无 | 识别开局 |
| 开局 | GET | /openings/tree | 无 | 开局树 |
| 分析 | POST | /analysis/game/:id/start | JWT | 启动异步分析 |
| 分析 | GET | /analysis/game/:id/status | JWT | 分析状态 |
| 分析 | GET | /analysis/game/:id | JWT | 分析结果 |
| 分析 | GET | /analysis/game/:id/move/:n | JWT | 单着分析 |
| 分析 | GET | /analysis/tasks/:id | JWT | 任务状态 |
| 分析 | GET | /analysis/tasks | JWT | 任务列表 |
| 分析 | DELETE | /analysis/tasks/:id | JWT | 取消任务 |
| 分析 | GET | /analysis/engines | 无 | 引擎信息 |
| 练习 | GET | /practice/puzzles | 无 | 残局题列表 |
| 练习 | GET | /practice/puzzles/:id | 无 | 残局题详情 |
| 练习 | POST | /practice/puzzles | JWT | 创建残局题 |
| 练习 | DELETE | /practice/puzzles/:id | JWT | 删除残局题 |
| 练习 | GET | /practice/search_games | 无 | 搜索棋谱 |
| 练习 | POST | /practice/start | 可选 | 开始练习 |
| 练习 | POST | /practice/move | 可选 | 走棋 |
| 练习 | POST | /practice/undo | 可选 | 悔棋 |
| 练习 | POST | /practice/hint | 可选 | 获取提示 |
| 练习 | POST | /practice/resign | 可选 | 认输 |
| 练习 | GET | /practice/status/:id | 可选 | 会话状态 |
| 练习 | GET | /practice/history | 可选 | 练习历史 |
| 练习 | GET | /practice/history/:id | 可选 | 练习详情 |
| 练习 | POST | /practice/analyze/:id | 可选 | 启动复盘分析 |
| 练习 | GET | /practice/analyze/:id/status | 可选 | 复盘分析状态 |
| 练习 | GET | /practice/analyze/:id/result | 可选 | 复盘分析结果 |
| 收藏 | GET | /collections | JWT | 收藏列表 |
| 收藏 | POST | /collections | JWT | 添加收藏 |
| 收藏 | DELETE | /collections/:id | JWT | 移除收藏 |
| 收藏 | GET | /collections/check/:id | JWT | 检查收藏状态 |
| 收藏 | PUT | /collections/:id | JWT | 更新收藏备注 |
| 浏览 | GET | /browsing | JWT | 浏览历史 |
| 浏览 | POST | /browsing | JWT | 记录浏览 |
| 浏览 | DELETE | /browsing/:id | JWT | 删除浏览记录 |
| 浏览 | POST | /browsing/clear | JWT | 清空浏览历史 |
