# -*- coding: utf-8 -*-
"""拉勾网职位源"""

import logging
import time
import random
from typing import List, Dict, Any

import requests
from bs4 import BeautifulSoup

from .base import BaseJobSource, normalize_job, extract_requirements

logger = logging.getLogger(__name__)


class LagouSource(BaseJobSource):
    """拉勾网（页面结构可能随站点改版变化，需适时调整选择器）"""

    source_id = 'lagou'
    source_name = '拉勾网'

    def __init__(self, timeout: int = 15, max_per_page: int = 20):
        super().__init__(timeout, max_per_page)
        # 使用Session保持会话
        self.session = requests.Session()
        # 更真实的浏览器headers
        self.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        })
        # 初始化时先访问首页获取必要cookie
        try:
            self.session.get('https://www.lagou.com', headers=self.headers, timeout=self.timeout)
            logger.debug("[拉勾网] 已获取初始cookie")
        except Exception as e:
            logger.warning("[拉勾网] 初始化cookie失败: %s", e)

    def test_connection(self) -> bool:
        """测试拉勾网连接状态"""
        try:
            response = self.session.get('https://www.lagou.com', 
                                      headers=self.headers, 
                                      timeout=self.timeout)
            # 检查是否返回验证码页面
            if '滑动验证' in response.text or 'nocaptcha' in response.text:
                logger.debug("[拉勾网] 连接测试: 触发验证码")
                return False
            return response.status_code == 200
        except Exception as e:
            logger.debug("[拉勾网] 连接测试失败: %s", e)
            return False
    
    def is_available(self) -> dict:
        """获取拉勾网的详细可用性状态"""
        try:
            is_conn_ok = self.test_connection()
            if not is_conn_ok:
                return {
                    'available': False,
                    'message': '触发反爬虫验证机制',
                    'last_checked': None
                }
            return {
                'available': True,
                'message': '连接正常',
                'last_checked': None
            }
        except Exception as e:
            return {
                'available': False,
                'message': f'检查失败: {str(e)}',
                'last_checked': None
            }
    
    def search(self, keyword: str, city: str = '全国', page: int = 1) -> List[Dict[str, Any]]:
        jobs = []
        url = f"https://www.lagou.com/jobs/list_{keyword}"
        params = {'city': city, 'pn': page}
        
        # 添加随机延迟避免频繁请求
        time.sleep(random.uniform(1, 3))
        
        # 使用session发送请求
        try:
            response = self.session.get(url, params=params, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            html = response.text
        except Exception as e:
            logger.warning("[拉勾网] 请求失败: %s", e)
            return jobs
            
        # 检查是否被重定向到验证码页面
        if '滑动验证' in html or 'nocaptcha' in html:
            logger.warning("[拉勾网] 触发反爬验证机制，建议使用浏览器自动化或代理")
            return jobs
            
        if not html:
            return jobs
        try:
            soup = BeautifulSoup(html, 'html.parser')
            job_list = soup.find_all('div', class_='job-item')
            for job in job_list[: self.max_per_page]:
                title_elem = job.find('h3', class_='position-name')
                company_elem = job.find('div', class_='company')
                salary_elem = job.find('span', class_='salary')
                desc_elem = job.find('div', class_='job-detail')
                if not title_elem or not salary_elem:
                    continue
                desc_text = desc_elem.get_text(strip=True) if desc_elem else ''
                jobs.append(normalize_job(
                    title=title_elem.get_text(strip=True),
                    company=company_elem.get_text(strip=True) if company_elem else '未知公司',
                    salary=salary_elem.get_text(strip=True),
                    description=desc_text,
                    source_id=self.source_id,
                    source_name=self.source_name,
                    requirements=extract_requirements(desc_text)
                ))
        except Exception as e:
            logger.error("[拉勾网] 解析失败: %s", e)
        return jobs
