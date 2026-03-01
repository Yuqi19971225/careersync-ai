# -*- coding: utf-8 -*-
"""智联招聘职位源（占位，可后续按站点实现）"""

import logging
from typing import List, Dict, Any

from .base import BaseJobSource

logger = logging.getLogger(__name__)


class ZhaopinSource(BaseJobSource):
    """智联招聘（zhaopin.com）— 当前为占位实现，可按站点接口/页面实现。"""

    source_id = 'zhaopin'
    source_name = '智联招聘'

    def search(self, keyword: str, city: str = '全国', page: int = 1) -> List[Dict[str, Any]]:
        logger.debug("[智联招聘] 暂未实现爬取逻辑，返回空列表")
        return []
