# -*- coding: utf-8 -*-
"""CareerSync AI 业务服务层"""

from .career_sync import CareerSyncAI
from .crawler import JobCrawler
from .optimizer import AIOptimizer
from .matcher import ResumeMatcher
from .proxy_manager import proxy_manager, get_current_proxy, get_session_proxies
from .browser_automation import get_browser_manager, get_page_with_browser
from .captcha_handler import captcha_manager, get_captcha_manager
from .qwen_captcha_handler import QwenCaptchaProcessor, get_qwen_captcha_processor, enhance_captcha_with_qwen

__all__ = ['CareerSyncAI', 'JobCrawler', 'AIOptimizer', 'ResumeMatcher', 
           'proxy_manager', 'get_current_proxy', 'get_session_proxies',
           'get_browser_manager', 'get_page_with_browser',
           'captcha_manager', 'get_captcha_manager',
           'QwenCaptchaProcessor', 'get_qwen_captcha_processor', 'enhance_captcha_with_qwen']
