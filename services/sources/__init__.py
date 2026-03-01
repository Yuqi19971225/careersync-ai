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


def get_source_status(source_id: str) -> dict:
    """获取指定招聘源的状态信息"""
    if source_id not in SOURCE_REGISTRY:
        return {
            'available': False,
            'message': f'未知的招聘源: {source_id}',
            'last_checked': None
        }
    
    source = SOURCE_REGISTRY[source_id]
    
    # 检查源是否实现
    if hasattr(source, 'is_available'):
        try:
            return source.is_available()
        except Exception as e:
            logger.warning("检查源 %s 可用性时出错: %s", source_id, e)
            return {
                'available': False,
                'message': f'检查失败: {str(e)}',
                'last_checked': None
            }
    
    # 默认状态检查逻辑
    try:
        # 对于占位实现，标记为不可用
        if source_id in ['boss', 'zhaopin']:
            return {
                'available': False,
                'message': '暂未实现爬取逻辑',
                'last_checked': None
            }
        
        # 对于已实现的源，进行简单测试
        if hasattr(source, 'test_connection'):
            is_available = source.test_connection()
            return {
                'available': is_available,
                'message': '连接正常' if is_available else '连接失败',
                'last_checked': None
            }
        
        # 默认认为已实现的源是可用的
        return {
            'available': True,
            'message': '源已实现',
            'last_checked': None
        }
        
    except Exception as e:
        logger.warning("检查源 %s 状态时出错: %s", source_id, e)
        return {
            'available': False,
            'message': f'状态检查异常: {str(e)}',
            'last_checked': None
        }
