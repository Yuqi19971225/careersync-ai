# -*- coding: utf-8 -*-
"""CareerSync AI 配置：环境变量与常量"""

import os
import logging

# 千问 API（阿里云百炼 / DashScope，兼容 OpenAI 接口）
QWEN_API_KEY = os.getenv('DASHSCOPE_API_KEY') or os.getenv('QWEN_API_KEY')
QWEN_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-turbo')

# 服务
SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(os.getenv('SERVER_PORT', '5000'))
DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() in ('1', 'true', 'yes')


def setup_logging(level=logging.INFO):
    """配置全局日志"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
