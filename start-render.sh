#!/bin/bash
# Render 容器启动脚本
# 在 gunicorn 启动前自动初始化数据库和种子数据

set -e

echo "[ChessDB] 启动初始化..."

# 初始化数据库表结构（db.create_all 在 app/__init__.py 中已自动执行）
# 灌入种子数据（幂等，不会重复插入）
echo "[ChessDB] 灌入种子数据..."
python -c "
from run import app
from init_db import seed_data
with app.app_context():
    seed_data()
" 2>&1 || echo "警告: 种子数据灌入失败，可能已存在"

echo "[ChessDB] 初始化完成，启动 gunicorn..."

# 启动 gunicorn
exec gunicorn -w 1 -b 0.0.0.0:5000 --timeout 300 --preload run:app
