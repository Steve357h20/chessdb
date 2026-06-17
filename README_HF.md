---
title: ChessDB
emoji: ♟️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# ChessDB - 国际象棋对局分析平台

基于 Stockfish 引擎的国际象棋对局分析、棋谱管理与学习平台。

## 功能

- PGN 棋谱上传与管理
- Stockfish 引擎深度分析
- 用户系统与权限管理
- 开局库与棋手信息
- API 文档 (Flasgger)

## 部署说明

本 Space 使用 Docker SDK 部署，单容器包含：
- Nginx (端口 7860，前端静态文件 + 反向代理)
- Gunicorn (Flask 后端，2 workers)
- Stockfish (apt 安装，2 threads, 512MB hash)

### 数据持久化

HF Spaces 的文件系统是临时的，重启后数据会丢失。
如需持久化数据，请在 Space Settings 中配置持久存储 (Persistent Storage)。

### 环境变量

在 Space Settings → Repository secrets 中设置：

- `SECRET_KEY`: Flask 密钥（自动生成或手动设置）
- `JWT_SECRET_KEY`: JWT 密钥（自动生成或手动设置）
