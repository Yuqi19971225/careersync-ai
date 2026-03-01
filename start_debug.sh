#!/bin/bash

# CareerSync AI Debug Mode 启动脚本
# 用途: 以调试模式启动CareerSync AI项目

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录（假设脚本在项目根目录运行）
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"

echo -e "${BLUE}🚀 CareerSync AI Debug Mode 启动脚本${NC}"
echo "========================================"

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}⚠️  虚拟环境未找到，正在创建...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✅ 虚拟环境创建完成${NC}"
fi

# 激活虚拟环境
echo -e "${BLUE}🔄 激活虚拟环境...${NC}"
source "$VENV_DIR/bin/activate"

# 检查依赖
echo -e "${BLUE}📦 检查依赖包...${NC}"
if [ -f "${PROJECT_DIR}/requirements.txt" ]; then
    pip install -r "${PROJECT_DIR}/requirements.txt" >/dev/null 2>&1
    echo -e "${GREEN}✅ 依赖包检查完成${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt 未找到${NC}"
fi

# 设置调试环境变量
export FLASK_DEBUG=1
export DEBUG=1
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH:-}"

echo -e "${BLUE}🔧 设置调试环境变量:${NC}"
echo "   FLASK_DEBUG=1"
echo "   DEBUG=1"
echo "   PYTHONPATH=${PROJECT_DIR}"

# 检查端口占用
PORT=8443
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 ${PORT} 已被占用${NC}"
    echo -e "${BLUE}   占用进程信息:${NC}"
    lsof -Pi :$PORT -sTCP:LISTEN
    echo ""
    read -p "是否终止占用进程? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lsof -ti :$PORT | xargs kill -9
        echo -e "${GREEN}✅ 已终止占用进程${NC}"
        sleep 2
    else
        echo -e "${YELLOW}⚠️  请手动释放端口或修改配置${NC}"
        exit 1
    fi
fi

# 启动服务
echo -e "${GREEN}🎯 启动 CareerSync AI 服务 (Debug Mode)...${NC}"
echo "========================================"

cd "$PROJECT_DIR"
python3 app.py

# 脚本结束处理
deactivate
echo -e "${BLUE}👋 服务已停止${NC}"