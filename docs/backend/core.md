# 后端核心层 (`backend/app/` + `backend/config.py` + `backend/app/admin.py` + `backend/app/utils/`)

## 概述

核心层包含应用工厂、配置管理、后台管理和工具函数，是整个后端应用的骨架和基础设施。

## 文件结构

```
backend/
├── config.py              # 应用配置（多环境）
├── app/
│   ├── __init__.py        # 应用工厂 + 扩展初始化
│   ├── admin.py           # Flask-Admin 后台管理
│   ├── swagger_config.py  # Swagger API 文档配置
│   └── utils/
│       ├── __init__.py    # 空初始化
│       └── validators.py  # 验证器（空文件，预留）
```

---

## 1. 应用工厂 (`app/__init__.py`)

### `create_app(config_name='default')`

Flask 应用工厂模式，负责创建和配置 Flask 应用实例。

**初始化流程**:

```
1. 创建 Flask 应用实例
2. 加载配置（根据 config_name 选择配置类）
3. 初始化扩展：
   ├── SQLAlchemy (db)     — ORM 数据库
   ├── Migrate (migrate)   — 数据库迁移
   ├── CORS                — 跨域支持
   ├── JWTManager (jwt)    — JWT 认证
   └── Limiter (limiter)   — API 限流
4. 注册 Blueprint 和错误处理器
5. 配置 Swagger API 文档
6. 配置 Flask-Admin 后台
7. 创建数据库表 + 初始化预设残局
```

### 全局扩展实例

| 实例 | 说明 | 默认配置 |
|------|------|----------|
| `db` | SQLAlchemy ORM | pool_recycle=3600, pool_pre_ping=True |
| `migrate` | Flask-Migrate | 绑定 db 实例 |
| `jwt` | JWT 认证 | 过期时间 86400秒(24小时) |
| `limiter` | API 限流 | 2000次/天, 500次/小时, memory存储 |

### CORS 配置

```python
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

仅对 `/api/` 路径启用 CORS，允许所有来源访问。

---

## 2. 配置管理 (`config.py`)

### 配置类层次

```
Config (基类)
├── DevelopmentConfig  — 开发环境
├── ProductionConfig   — 生产环境
└── TestingConfig      — 测试环境
```

### 基类配置 (`Config`)

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Flask 密钥（环境变量覆盖） |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | False | 关闭修改追踪 |
| `JWT_SECRET_KEY` | `jwt-dev-secret-key` | JWT 密钥（环境变量覆盖） |
| `JWT_ACCESS_TOKEN_EXPIRES` | 86400 | JWT 有效期(秒) |
| `STOCKFISH_PATH` | `backend/stockfish/stockfish/stockfish-windows-x86-64-avx2.exe` | Stockfish 路径 |
| `ANALYSIS_DEPTH` | 20 | 分析深度 |
| `ANALYSIS_TIMEOUT` | 300 | 分析超时(秒) |
| `ANALYSIS_THREADS` | 1 | 分析线程数 |
| `ANALYSIS_HASH` | 256 | 分析哈希表(MB) |
| `UPLOAD_FOLDER` | `backend/uploads` | 上传目录 |
| `MAX_CONTENT_LENGTH` | 16MB | 上传文件大小限制 |

### 环境差异

| 配置项 | Development | Production | Testing |
|--------|-------------|------------|---------|
| `DEBUG` | True | False | - |
| `TESTING` | - | - | True |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///chessdb.db` | `sqlite:///chessdb.db` | `sqlite:///test_chess.db` |
| `WTF_CSRF_ENABLED` | - | - | False |

### 配置选择

```python
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
```

通过 `create_app(config_name)` 参数或 `FLASK_ENV` 环境变量选择配置。

---

## 3. 后台管理 (`app/admin.py`)

### Flask-Admin 配置

**访问路径**: `/admin/`

### 管理视图

| 视图类 | 模型 | 名称 | 特殊配置 |
|--------|------|------|----------|
| `UserAdmin` | User | 用户 | form: username/email/is_admin; 列表: id/username/email/is_admin/created_at |
| `GameAdmin` | Game | 棋谱 | 过滤: result/eco_code/date; 搜索: opening_name |
| `PlayerAdmin` | Player | 棋手 | 搜索: name |
| `OpeningAdmin` | Opening | 开局库 | 搜索: name/eco_code |
| `SecureModelView` | Analysis | 分析 | 默认配置 |
| `SecureModelView` | Puzzle | 残局 | 默认配置 |
| `SecureModelView` | PracticeGame | 练习历史 | 默认配置 |
| `SecureModelView` | Collection | 收藏 | 默认配置 |
| `SecureModelView` | BrowsingHistory | 浏览历史 | 默认配置 |

### 基类 `SecureModelView`

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `column_display_pk` | True | 显示主键 |
| `column_hide_backrefs` | False | 显示反向引用 |
| `page_size` | 20 | 每页数量 |
| `can_export` | True | 允许导出 |

**设计要点**: 当前未实现管理员认证保护，生产环境需添加 `is_accessible()` 方法限制访问。

---

## 4. Swagger API 文档 (`app/swagger_config.py`)

### 配置

```python
swagger_template = {
    "info": {
        "title": "Chess Data Management API",
        "description": "国际象棋数据管理系统API文档",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header"
        }
    }
}
```

**访问路径**: `/apidocs/` 或 `/flasgger/`

**设计要点**: 所有路由函数的 docstring 遵循 Swagger/OpenAPI 规范格式，Flasgger 自动提取生成文档。

---

## 5. 工具函数 (`app/utils/`)

### validators.py

当前为空文件，预留用于未来添加：
- PGN 格式验证器
- FEN 字符串验证器
- 用户输入校验器
- 文件类型验证器

当前验证逻辑分散在路由层（如 `auth.py` 中的邮箱正则验证、用户名长度校验）。

---

## 应用启动流程

```
1. create_app(config_name)
2. ├── 加载配置
3. ├── 初始化扩展 (db, migrate, CORS, jwt, limiter)
4. ├── 注册 Blueprint (8个API模块)
5. ├── 注册错误处理器 (6种HTTP错误)
6. ├── 配置 Swagger
7. ├── 配置 Flask-Admin
8. └── 应用上下文:
     ├── 导入所有模型 (确保表创建)
     ├── db.create_all() (创建表)
     └── init_system_puzzles() (初始化预设残局)
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SECRET_KEY` | Flask 密钥 | `dev-secret-key-change-in-production` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | `jwt-dev-secret-key` |
| `DATABASE_URI` | 数据库连接字符串 | `sqlite:///chessdb.db` |
| `STOCKFISH_PATH` | Stockfish 可执行文件路径 | 项目内置路径 |
| `ANALYSIS_DEPTH` | 分析深度 | 20 |
| `ANALYSIS_TIMEOUT` | 分析超时 | 300 |
| `ANALYSIS_THREADS` | 分析线程数 | 1 |
| `ANALYSIS_HASH` | 分析哈希表大小 | 256 |
| `UPLOAD_FOLDER` | 上传目录 | `backend/uploads` |
| `FLASK_ENV` | 运行环境 | development |
