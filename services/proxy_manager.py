# -*- coding: utf-8 -*-
"""代理管理器：支持单代理和代理池模式"""

import logging
import random
from typing import Dict, List, Optional
from itertools import cycle

from config import PROXY_ENABLED, PROXY_HTTP, PROXY_HTTPS, PROXY_POOL, PROXY_ROTATE

logger = logging.getLogger(__name__)


class ProxyManager:
    """代理管理器，支持单代理和代理池模式"""
    
    def __init__(self):
        self.enabled = PROXY_ENABLED
        self.single_proxy = {
            'http': PROXY_HTTP,
            'https': PROXY_HTTPS
        } if PROXY_ENABLED else None
        
        self.proxy_pool = PROXY_POOL if PROXY_POOL else []
        self.rotate_mode = PROXY_ROTATE and len(self.proxy_pool) > 0
        
        # 创建循环迭代器用于轮换
        self.pool_iterator = cycle(self.proxy_pool) if self.proxy_pool else None
        
        self._log_init_status()
    
    def _log_init_status(self):
        """记录初始化状态"""
        if not self.enabled:
            logger.info("🌐 代理管理器: 代理功能已禁用")
            return
            
        if self.rotate_mode:
            logger.info("🌐 代理管理器: 启用代理池轮换模式，共 %d 个代理", len(self.proxy_pool))
            for i, proxy in enumerate(self.proxy_pool):
                logger.debug("  代理 %d: %s", i+1, proxy)
        else:
            logger.info("🌐 代理管理器: 启用单代理模式")
            logger.debug("  HTTP代理: %s", self.single_proxy.get('http', 'N/A'))
            logger.debug("  HTTPS代理: %s", self.single_proxy.get('https', 'N/A'))
    
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """获取当前代理配置"""
        if not self.enabled:
            return None
            
        if self.rotate_mode and self.proxy_pool:
            # 轮换模式：返回下一个代理
            proxy = next(self.pool_iterator)
            logger.debug("🔄 使用代理池中的代理: %s", proxy)
            return proxy
        elif self.single_proxy:
            # 单代理模式
            logger.debug("🔗 使用单代理: %s", self.single_proxy)
            return self.single_proxy
        else:
            logger.warning("⚠️ 代理已启用但未配置有效代理")
            return None
    
    def get_session_proxies(self) -> Optional[Dict[str, str]]:
        """获取适用于requests.Session的代理配置"""
        proxy = self.get_proxy()
        return proxy  # requests.Session.proxies可以直接使用这个格式
    
    def test_proxy_connectivity(self, proxy_config: Dict[str, str]) -> bool:
        """测试代理连通性"""
        import requests
        
        try:
            # 测试HTTP连接
            response = requests.get('http://httpbin.org/ip', 
                                  proxies=proxy_config, 
                                  timeout=10)
            if response.status_code == 200:
                logger.debug("✅ 代理测试成功: %s", response.json().get('origin', 'Unknown'))
                return True
        except Exception as e:
            logger.debug("❌ 代理测试失败: %s", e)
            return False
        return False
    
    def get_all_working_proxies(self) -> List[Dict[str, str]]:
        """获取所有工作正常的代理（仅在代理池模式下有效）"""
        if not self.proxy_pool:
            return [self.single_proxy] if self.single_proxy else []
        
        working_proxies = []
        for proxy in self.proxy_pool:
            if self.test_proxy_connectivity(proxy):
                working_proxies.append(proxy)
        
        logger.info("🔍 代理健康检查完成，%d/%d 个代理工作正常", 
                   len(working_proxies), len(self.proxy_pool))
        return working_proxies


# 创建全局代理管理器实例
proxy_manager = ProxyManager()


def get_current_proxy() -> Optional[Dict[str, str]]:
    """获取当前代理配置的便捷函数"""
    return proxy_manager.get_proxy()


def get_session_proxies() -> Optional[Dict[str, str]]:
    """获取会话代理配置的便捷函数"""
    return proxy_manager.get_session_proxies()