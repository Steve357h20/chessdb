#!/bin/bash
# ChessDB 容器启动脚本
# 在启动 gunicorn 前自动初始化数据库和种子数据

set -e

echo "[ChessDB] 启动初始化..."

# 等待数据库就绪（SQLite 无需等待）
export FLASK_APP=run

# 初始化数据库表结构
echo "[ChessDB] 创建数据库表..."
python -c "
from run import app, db
with app.app_context():
    db.create_all()
    print('数据库表创建完成')
" 2>&1 || echo "警告: 数据库表创建失败，可能已存在"

# 灌入种子数据（棋手、开局、示例棋谱）
echo "[ChessDB] 灌入种子数据..."
python -c "
from run import app
from init_db import seed_data
with app.app_context():
    seed_data()
" 2>&1 || echo "警告: 种子数据灌入失败，可能已存在"

# 初始化系统谜题
echo "[ChessDB] 初始化系统谜题..."
python -c "
from run import app
with app.app_context():
    from app.services.puzzle_library import init_system_puzzles
    init_system_puzzles()
    print('系统谜题初始化完成')
" 2>&1 || echo "警告: 系统谜题初始化失败"

# 创建默认管理员（仅当不存在任何管理员时）
echo "[ChessDB] 检查管理员账户..."
python -c "
from run import app, db
from app.models import User
with app.app_context():
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        import os
        admin_user = os.getenv('ADMIN_USERNAME', 'admin')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@chessdb.local')
        admin_pass = os.getenv('ADMIN_PASSWORD', 'chessdb123')
        existing = User.query.filter_by(username=admin_user).first()
        if not existing:
            admin = User(username=admin_user, email=admin_email, is_admin=True)
            admin.set_password(admin_pass)
            db.session.add(admin)
            db.session.commit()
            print(f'默认管理员已创建: {admin_user} / {admin_pass}')
            print('请尽快登录修改密码!')
        else:
            print(f'用户 {admin_user} 已存在')
    else:
        print('管理员账户已存在')
" 2>&1 || echo "警告: 管理员创建失败"

echo "[ChessDB] 初始化完成，启动服务..."

# 启动 Supervisor (Nginx + Gunicorn)
exec supervisord -n -c /etc/supervisor/supervisord.conf
