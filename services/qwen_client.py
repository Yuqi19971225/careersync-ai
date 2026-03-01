# -*- coding: utf-8 -*-
"""千问 API 客户端（阿里云百炼 / DashScope，OpenAI 兼容接口）"""

import logging

from config import QWEN_API_KEY, QWEN_BASE_URL

logger = logging.getLogger(__name__)


def get_qwen_client():
    """获取千问 API 客户端，未配置 API Key 时返回 None"""
    if not QWEN_API_KEY:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)
    except Exception as e:
        logger.warning("千问客户端初始化失败: %s", e)
        return None
