#!/bin/bash

# 字节跳动招聘源单元测试运行脚本

echo "🚀 运行字节跳动招聘源单元测试"
echo "================================"

# 进入项目目录
cd "$(dirname "$0")" || exit 1

# 激活虚拟环境
source .venv/bin/activate 2>/dev/null || {
    echo "❌ 未找到虚拟环境，请先运行 start_debug.sh 创建环境"
    exit 1
}

# 运行基本测试（不包含覆盖率）
echo "📋 运行基本单元测试..."
python3 -m pytest tests/test_bytedance_unit.py -v

# 检查测试结果
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 所有单元测试通过！"
    echo ""
    echo "📊 测试统计:"
    python3 -m pytest tests/test_bytedance_unit.py --tb=no -q | tail -1
else
    echo ""
    echo "❌ 部分测试失败，请检查错误信息"
    exit 1
fi