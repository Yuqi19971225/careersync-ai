# -*- coding: utf-8 -*-
"""BOSS 直聘职位源（占位，可后续按站点实现）"""

import logging
from typing import List, Dict, Any

from .base import BaseJobSource

logger = logging.getLogger(__name__)


class BossSource(BaseJobSource):
    """BOSS 直聘（zhipin.com）— 当前为占位实现，站点有强反爬需单独适配。"""

    source_id = 'boss'
    source_name = 'BOSS直聘'

    def search(self, keyword: str, city: str = '全国', page: int = 1) -> List[Dict[str, Any]]:
        # BOSS 直聘多为前端渲染或接口加密，需分析接口或使用浏览器自动化
        logger.debug("[BOSS直聘] 暂未实现爬取逻辑，返回空列表")
        return []
    
    def is_available(self) -> dict:
        """BOSS直聘当前不可用"""
        return {
            'available': False,
            'message': '暂未实现爬取逻辑，站点有强反爬需单独适配',
            'last_checked': None
        }
