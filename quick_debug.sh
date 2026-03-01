#!/bin/bash

# CareerSync AI 简化调试启动脚本
# 用途: 快速以debug模式启动项目（无交互）

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"

# 激活虚拟环境
source "$VENV_DIR/bin/activate" 2>/dev/null || {
    echo "创建并激活虚拟环境..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
}

# 安装依赖
pip install -r "${PROJECT_DIR}/requirements.txt" >/dev/null 2>&1

# 设置调试环境变量
export FLASK_DEBUG=1
export DEBUG=1
export PYTHONPATH="${PROJECT_DIR}"

# 启动服务
cd "$PROJECT_DIR"
exec python3 app.py