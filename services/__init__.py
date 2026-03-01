# -*- coding: utf-8 -*-
"""CareerSync AI 业务服务层"""

from .career_sync import CareerSyncAI
from .crawler import JobCrawler
from .optimizer import AIOptimizer
from .matcher import ResumeMatcher
from .proxy_manager import proxy_manager, get_current_proxy, get_session_proxies
from .browser_automation import browser_manager, get_browser_manager, get_page_with_browser

__all__ = ['CareerSyncAI', 'JobCrawler', 'AIOptimizer', 'ResumeMatcher', 
           'proxy_manager', 'get_current_proxy', 'get_session_proxies',
           'browser_manager', 'get_browser_manager', 'get_page_with_browser']
