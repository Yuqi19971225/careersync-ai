# -*- coding: utf-8 -*-
"""CareerSync AI 配置：配置文件 + 环境变量"""

import json
import logging
import os
from pathlib import Path

# 配置文件路径（项目根目录下的 config.json）
_CONFIG_PATH = Path(__file__).resolve().parent / 'config.json'

def _load_file_config():
    """从 config.json 读取配置，不存在或解析失败返回空字典"""
    if not _CONFIG_PATH.exists():
        return {}
    try:
        with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

_file_config = _load_file_config()

# 千问 API（环境变量优先，其次配置文件不存储密钥）
QWEN_API_KEY = os.getenv('DASHSCOPE_API_KEY') or os.getenv('QWEN_API_KEY')
QWEN_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
QWEN_MODEL = (
    os.getenv('QWEN_MODEL')
    or (_file_config.get('qwen') or {}).get('model')
    or 'qwen-turbo'
)

# 服务：配置文件优先，环境变量可覆盖
_server = _file_config.get('server') or {}
SERVER_HOST = os.getenv('SERVER_HOST') or _server.get('host') or '0.0.0.0'
SERVER_PORT = int(
    os.getenv('SERVER_PORT')
    or _server.get('port')
    or 5000
)
_debug_raw = os.getenv('FLASK_DEBUG')
if _debug_raw is not None:
    DEBUG = _debug_raw.lower() in ('1', 'true', 'yes')
else:
    DEBUG = _file_config.get('debug', True)


def setup_logging(level=logging.INFO):
    """配置全局日志"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
