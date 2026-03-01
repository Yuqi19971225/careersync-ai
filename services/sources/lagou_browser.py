# -*- coding: utf-8 -*-
"""基于浏览器自动化的拉勾网职位爬虫"""

import logging
import time
import random
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from .base import BaseJobSource, normalize_job, extract_requirements
from services.browser_automation import get_browser_manager

logger = logging.getLogger(__name__)


class LagouBrowserSource(BaseJobSource):
    """基于浏览器自动化的拉勾网职位源"""
    
    source_id = 'lagou_browser'
    source_name = '拉勾网(浏览器)'
    
    def __init__(self, timeout: int = 30, max_per_page: int = 20, headless: bool = True):
        super().__init__(timeout, max_per_page)
        self.headless = headless
        # 延迟初始化浏览器管理器，只在实际需要时创建
        self._browser_manager = None
        logger.info("[拉勾网-浏览器] 初始化完成")
    
    @property
    def browser_manager(self):
        """延迟获取浏览器管理器实例"""
        if self._browser_manager is None:
            self._browser_manager = get_browser_manager(headless=self.headless)
        return self._browser_manager
    
    def search(self, keyword: str, city: str = '全国', page: int = 1) -> List[Dict[str, Any]]:
        """使用浏览器自动化搜索职位"""
        jobs = []
        url = f"https://www.lagou.com/jobs/list_{keyword}?city={city}&pn={page}"
        
        try:
            logger.info("[拉勾网-浏览器] 开始搜索: %s (城市: %s, 页码: %d)", keyword, city, page)
            
            # 使用浏览器获取页面源码
            page_source = self.browser_manager.get_page_source(
                url, 
                wait_for_element=".job-list-box"  # 等待职位列表加载
            )
            
            if not page_source:
                logger.warning("[拉勾网-浏览器] 无法获取页面内容")
                return jobs
            
            # 解析页面内容
            jobs = self._parse_job_list(page_source)
            
            logger.info("[拉勾网-浏览器] 成功获取 %d 个职位", len(jobs))
            return jobs
            
        except Exception as e:
            logger.error("[拉勾网-浏览器] 搜索失败: %s", e)
            return jobs
    
    def _parse_job_list(self, html: str) -> List[Dict[str, Any]]:
        """解析职位列表"""
        jobs = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找职位项（根据拉勾网实际页面结构调整选择器）
            job_items = soup.find_all('div', class_='job-list-item') or \
                       soup.find_all('li', class_='con_list_item') or \
                       soup.select('.job-list-box .item') or \
                       soup.find_all('div', attrs={'data-positionid': True})
            
            logger.debug("[拉勾网-浏览器] 找到 %d 个职位项", len(job_items))
            
            for job_item in job_items[:self.max_per_page]:
                try:
                    job_data = self._extract_job_info(job_item)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.warning("[拉勾网-浏览器] 解析单个职位失败: %s", e)
                    continue
                    
        except Exception as e:
            logger.error("[拉勾网-浏览器] 解析职位列表失败: %s", e)
        
        return jobs
    
    def _extract_job_info(self, job_item) -> Optional[Dict[str, Any]]:
        """提取单个职位信息"""
        try:
            # 尝试多种可能的选择器
            
            # 职位标题
            title_elem = (job_item.find('h3') or 
                         job_item.find('a', class_='position_link') or
                         job_item.find('div', class_='position-name') or
                         job_item.find(attrs={'data-positionname': True}))
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # 公司名称
            company_elem = (job_item.find('div', class_='company_name') or
                           job_item.find('a', class_='company_link') or
                           job_item.find('div', class_='company') or
                           job_item.find(attrs={'data-company': True}))
            company = company_elem.get_text(strip=True) if company_elem else "未知公司"
            
            # 薪资
            salary_elem = (job_item.find('span', class_='salary') or
                          job_item.find('div', class_='salary') or
                          job_item.find(attrs={'data-salary': True}))
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # 职位描述
            desc_elem = (job_item.find('div', class_='job-desc') or
                        job_item.find('p', class_='detail') or
                        job_item.find('div', class_='position-desc'))
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # 如果基本信息都不完整，跳过这个职位
            if not title or not salary:
                return None
            
            return normalize_job(
                title=title,
                company=company,
                salary=salary,
                description=description,
                source_id=self.source_id,
                source_name=self.source_name,
                requirements=extract_requirements(description)
            )
            
        except Exception as e:
            logger.debug("[拉勾网-浏览器] 提取职位信息失败: %s", e)
            return None
    
    def is_available(self) -> dict:
        """检查浏览器源的可用性"""
        try:
            # 测试能否访问拉勾网首页
            test_url = "https://www.lagou.com"
            page_source = self.browser_manager.get_page_source(test_url, "body")
            
            if page_source and len(page_source) > 1000:
                # 检查是否触发验证码
                if '滑动验证' in page_source or 'nocaptcha' in page_source.lower():
                    return {
                        'available': True,
                        'message': '浏览器自动化可用，但可能遇到验证码',
                        'requires_manual': True
                    }
                return {
                    'available': True,
                    'message': '浏览器自动化正常工作',
                    'requires_manual': False
                }
            else:
                return {
                    'available': False,
                    'message': '无法获取有效页面内容',
                    'requires_manual': False
                }
                
        except Exception as e:
            return {
                'available': False,
                'message': f'浏览器检查失败: {str(e)}',
                'requires_manual': False
            }


# 为了向后兼容，也可以创建一个混合模式的源
class LagouHybridSource(LagouBrowserSource):
    """混合模式拉勾网源：优先使用浏览器，失败时降级到普通请求"""
    
    source_id = 'lagou_hybrid'
    source_name = '拉勾网(混合模式)'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 导入普通的拉勾网源用于降级
        from .lagou import LagouSource
        self.fallback_source = LagouSource(*args, **kwargs)
        # 延迟初始化浏览器管理器
        self._browser_manager = None
    
    def search(self, keyword: str, city: str = '全国', page: int = 1) -> List[Dict[str, Any]]:
        """混合搜索：先尝试浏览器，失败则使用普通方式"""
        # 首先尝试浏览器方式
        jobs = super().search(keyword, city, page)
        
        if jobs:  # 浏览器方式成功
            logger.info("[拉勾网-混合] 浏览器方式成功获取 %d 个职位", len(jobs))
            return jobs
        
        # 浏览器方式失败，降级到普通方式
        logger.warning("[拉勾网-混合] 浏览器方式失败，降级到普通请求")
        return self.fallback_source.search(keyword, city, page)
    
    def is_available(self) -> dict:
        """混合源的可用性检查"""
        browser_status = super().is_available()
        fallback_status = self.fallback_source.is_available()
        
        if browser_status['available']:
            return {
                **browser_status,
                'message': f"浏览器模式: {browser_status['message']}"
            }
        elif fallback_status['available']:
            return {
                'available': True,
                'message': f"降级模式可用: {fallback_status['message']}",
                'fallback_mode': True
            }
        else:
            return {
                'available': False,
                'message': '所有模式均不可用'
            }