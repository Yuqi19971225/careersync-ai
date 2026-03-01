# -*- coding: utf-8 -*-
"""多招聘源注册与获取，便于扩展新站点"""

import logging
from typing import List, Optional

from .base import BaseJobSource
from .lagou import LagouSource
from .boss import BossSource
from .zhaopin import ZhaopinSource

logger = logging.getLogger(__name__)

# 所有已实现的招聘源：source_id -> 实例
SOURCE_REGISTRY = {
    LagouSource.source_id: LagouSource(),
    BossSource.source_id: BossSource(),
    ZhaopinSource.source_id: ZhaopinSource(),
}


def get_sources(source_ids: Optional[List[str]] = None) -> List[BaseJobSource]:
    """
    按 source_id 列表返回招聘源实例；不传或空则返回全部。
    若某 id 未注册则跳过并打日志。
    """
    if not source_ids:
        return list(SOURCE_REGISTRY.values())
    sources = []
    for sid in source_ids:
        if sid in SOURCE_REGISTRY:
            sources.append(SOURCE_REGISTRY[sid])
        else:
            logger.warning("未知招聘源 id: %s，已忽略", sid)
    return sources


def list_source_ids() -> List[str]:
    """返回当前已注册的 source_id 列表。"""
    return list(SOURCE_REGISTRY.keys())
