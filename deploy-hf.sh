#!/bin/bash
# ChessDB Hugging Face Spaces 部署脚本
# 使用方法: bash deploy-hf.sh
# 需要先设置 HF_TOKEN 环境变量: https://huggingface.co/settings/tokens

set -e

echo "============================================"
echo "  ChessDB Hugging Face Spaces 部署脚本"
echo "============================================"

# ---- 检查依赖 ----
if ! command -v git &> /dev/null; then
    echo "错误: 未安装 git"
    exit 1
fi

# ---- 配置 ----
HF_USER=${HF_USER:-""}
SPACE_NAME=${SPACE_NAME:-"chessdb"}

# 获取 HF 用户名
if [ -z "$HF_USER" ]; then
    if [ -n "$HF_TOKEN" ]; then
        HF_USER=$(curl -s -H "Authorization: Bearer $HF_TOKEN" https://huggingface.co/api/whoami-v2 | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])" 2>/dev/null || echo "")
    fi
    if [ -z "$HF_USER" ]; then
        read -p "请输入你的 Hugging Face 用户名: " HF_USER
    fi
fi

SPACE_URL="https://huggingface.co/spaces/${HF_USER}/${SPACE_NAME}"
GIT_URL="https://huggingface.co/spaces/${HF_USER}/${SPACE_NAME}"

echo ""
echo "目标 Space: $SPACE_URL"

# ---- 检查 HF Token ----
if [ -z "$HF_TOKEN" ]; then
    echo ""
    echo "错误: 未设置 HF_TOKEN 环境变量"
    echo "请访问 https://huggingface.co/settings/tokens 创建 Access Token (write 权限)"
    echo "然后运行: export HF_TOKEN=hf_xxxxx"
    exit 1
fi

# ---- 准备临时目录 ----
TEMP_DIR=$(mktemp -d /tmp/chessdb-hf-XXXXXX)
echo ""
echo "准备部署文件到: $TEMP_DIR"

# 复制项目文件（排除不需要的文件）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 创建目录结构
mkdir -p "$TEMP_DIR/backend" "$TEMP_DIR/frontend" "$TEMP_DIR/hf"

# 复制后端
cp -r "$SCRIPT_DIR/backend/"* "$TEMP_DIR/backend/" 2>/dev/null || true
# 排除 __pycache__, .venv, stockfish 源码
find "$TEMP_DIR/backend" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR/backend" -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR/backend" -type d -name "stockfish" -path "*/stockfish/stockfish/src" -exec rm -rf {} + 2>/dev/null || true

# 复制前端
cp -r "$SCRIPT_DIR/frontend/"* "$TEMP_DIR/frontend/" 2>/dev/null || true
# 排除 node_modules
rm -rf "$TEMP_DIR/frontend/node_modules" 2>/dev/null || true

# 复制 HF 专用配置文件
cp -r "$SCRIPT_DIR/hf/"* "$TEMP_DIR/hf/" 2>/dev/null || true

# 复制启动脚本
cp "$SCRIPT_DIR/start-hf.sh" "$TEMP_DIR/" 2>/dev/null || true

# 复制 Dockerfile.hf 为 Dockerfile
cp "$SCRIPT_DIR/Dockerfile.hf" "$TEMP_DIR/Dockerfile"

# 复制 README_HF.md 为 README.md
cp "$SCRIPT_DIR/README_HF.md" "$TEMP_DIR/README.md"

# 复制示例数据
cp "$SCRIPT_DIR/sample_games.pgn" "$TEMP_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/sample_games_2.pgn" "$TEMP_DIR/" 2>/dev/null || true

echo "文件准备完成"

# ---- 初始化 Git 仓库 ----
cd "$TEMP_DIR"
git init
git config user.email "deploy@chessdb.local"
git config user.name "ChessDB Deploy"

# ---- 推送到 HF Spaces ----
echo ""
echo "推送到 Hugging Face Spaces..."

# 添加 remote
git remote add origin "https://user:$HF_TOKEN@huggingface.co/spaces/${HF_USER}/${SPACE_NAME}"

# 检查 Space 是否已存在
SPACE_EXISTS=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $HF_TOKEN" \
    "https://huggingface.co/api/spaces/${HF_USER}/${SPACE_NAME}")

if [ "$SPACE_EXISTS" = "404" ]; then
    echo "Space 不存在，正在创建..."
    curl -s -X POST "https://huggingface.co/api/repos/create" \
        -H "Authorization: Bearer $HF_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"type\":\"space\",\"name\":\"${SPACE_NAME}\",\"sdk\":\"docker\",\"private\":false}" \
        > /dev/null
    echo "Space 创建完成"
fi

# 提交并推送
git add .
git commit -m "Deploy ChessDB to Hugging Face Spaces"
git push -f origin main || git push -f origin master

# ---- 清理 ----
rm -rf "$TEMP_DIR"

# ---- 完成 ----
echo ""
echo "============================================"
echo "  部署完成!"
echo "============================================"
echo ""
echo "  Space 地址: $SPACE_URL"
echo "  应用地址: https://${HF_USER}-${SPACE_NAME}.hf.space"
echo ""
echo "  首次部署需要等待 5-10 分钟构建镜像"
echo ""
echo "  初始化数据库 (在 Space Logs 页面查看构建进度):"
echo "    构建完成后，访问应用首页会自动初始化"
echo ""
echo "  如需创建管理员:"
echo "    在 HF Space 页面 → Settings → Logs 查看"
echo ""
echo "  数据持久化:"
echo "    HF Spaces 默认不持久化数据，重启后数据库会重置"
echo "    如需持久化: Settings → Persistent Storage → 添加 (免费 20GB)"
echo "============================================"
