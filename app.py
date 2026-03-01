# -*- coding: utf-8 -*-
"""
CareerSync AI 主程序入口：创建应用并启动服务。
业务逻辑见 config、services、routes 等模块。
"""

from flask import Flask
from flask_cors import CORS

from config import setup_logging, DEBUG, SERVER_HOST, SERVER_PORT
from services import CareerSyncAI
from routes import register_routes

# 日志
setup_logging()
import logging
logger = logging.getLogger(__name__)

# 创建应用
app = Flask(__name__)
CORS(app)

# 创建服务实例并注册路由
career_sync_ai = CareerSyncAI()
register_routes(app, career_sync_ai)


def main():
    """启动 HTTP 服务"""
    print("=" * 60)
    print("🚀 CareerSync AI - 智能职业匹配与简历优化系统")
    print("=" * 60)
    print("📋 系统版本: %s" % career_sync_ai.system_info['version'])
    print("💡 系统功能: %s" % ", ".join(career_sync_ai.system_info['features']))
    print("\n🌐 API 接口列表:")
    print("  POST /api/search_jobs    - 职位搜索")
    print("  POST /api/match_resume   - 简历匹配")
    print("  POST /api/optimize_resume - 简历优化")
    print("  GET  /api/system_info    - 系统信息")
    print("  GET  /api/health         - 健康检查")
    print("\n⚡ 启动 CareerSync AI 服务...")
    print("=" * 60)
    app.run(debug=DEBUG, host=SERVER_HOST, port=SERVER_PORT)


if __name__ == '__main__':
    main()
