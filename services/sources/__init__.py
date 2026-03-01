# -*- coding: utf-8 -*-
"""多招聘源注册与获取，便于扩展新站点"""

import logging
from typing import List, Optional

from .base import BaseJobSource
from .lagou import LagouSource
from .lagou_browser import LagouBrowserSource, LagouHybridSource
from .boss import BossSource
from .zhaopin import ZhaopinSource

logger = logging.getLogger(__name__)

# 所有已实现的招聘源：source_id -> 类（延迟初始化）
SOURCE_REGISTRY = {
    LagouSource.source_id: LagouSource,
    LagouBrowserSource.source_id: LagouBrowserSource,
    LagouHybridSource.source_id: LagouHybridSource,
    BossSource.source_id: BossSource,
    ZhaopinSource.source_id: ZhaopinSource,
}

# 缓存已创建的实例
_source_instances = {}


def _get_source_instance(source_id: str) -> BaseJobSource:
    """延迟创建并缓存招聘源实例"""
    if source_id not in _source_instances:
        if source_id in SOURCE_REGISTRY:
            source_class = SOURCE_REGISTRY[source_id]
            _source_instances[source_id] = source_class()
        else:
            raise ValueError(f"未知的招聘源: {source_id}")
    return _source_instances[source_id]


def get_sources(source_ids: Optional[List[str]] = None) -> List[BaseJobSource]:
    """
    按 source_id 列表返回招聘源实例；不传或空则返回全部。
    若某 id 未注册则跳过并打日志。
    """
    if not source_ids:
        # 返回所有已注册源的实例（延迟创建）
        return [_get_source_instance(sid) for sid in SOURCE_REGISTRY.keys()]
    sources = []
    for sid in source_ids:
        try:
            sources.append(_get_source_instance(sid))
        except ValueError as e:
            logger.warning("未知招聘源 id: %s，已忽略", sid)
    return sources


def list_source_ids() -> List[str]:
    """返回当前已注册的 source_id 列表。"""
    return list(SOURCE_REGISTRY.keys())


def get_source_status(source_id: str) -> dict:
    """获取指定招聘源的状态信息（不触发实际初始化）"""
    # 检查源是否已注册
    if source_id not in SOURCE_REGISTRY:
        return {
            'available': False,
            'message': f'未知的招聘源: {source_id}',
            'last_checked': None
        }
    
    # 获取源类信息而不创建实例
    source_class = SOURCE_REGISTRY[source_id]
    
    # 返回基础信息，不触发实际初始化
    source_name = getattr(source_class, 'source_name', source_id)
    
    # 根据源类型返回不同的状态信息
    if source_id in ['boss', 'zhaopin']:
        return {
            'available': False,
            'message': '暂未实现爬取逻辑，站点有强反爬需单独适配',
            'last_checked': None
        }
    elif 'lagou' in source_id:
        return {
            'available': True,
            'message': '浏览器自动化可用，但可能遇到验证码',
            'requires_manual': True,
            'last_checked': None
        }
    else:
        return {
            'available': True,
            'message': f'{source_name}: 模块已注册，等待实际调用',
            'last_checked': None
        }