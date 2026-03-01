# -*- coding: utf-8 -*-
"""字节跳动官网职位源"""

import logging
import json
import time
import random
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

from .base import BaseJobSource, normalize_job, extract_requirements
from ..proxy_manager import proxy_manager

logger = logging.getLogger(__name__)


class BytedanceSource(BaseJobSource):
    """字节跳动官网职位源"""
    
    source_id = 'bytedance'
    source_name = '字节跳动'
    
    def __init__(self, timeout: int = 15, max_per_page: int = 20):
        super().__init__(timeout, max_per_page)
        # 使用Session保持会话
        self.session = requests.Session()
        
        # 配置代理
        self.proxies = proxy_manager.get_session_proxies()
        if self.proxies:
            self.session.proxies.update(self.proxies)
            logger.info("[字节跳动] 已配置代理: %s", self.proxies)
        else:
            logger.info("[字节跳动] 代理未启用，使用直连")
        
        # 更真实的浏览器headers
        self.headers.update({
            'Accept': 'application/json, text/plain, */*',
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
        
        # 字节跳动职位搜索API基础URL
        self.base_url = 'https://jobs.bytedance.com/experienced/position'
        self.job_detail_url = 'https://jobs.bytedance.com/experienced/detail/'
    
    def test_connection(self) -> bool:
        """测试字节跳动连接状态"""
        try:
            # 使用更新后的参数格式测试API连接
            test_params = {
                'keywords': '工程师',
                'limit': 1,
                'current': 1,
                'location': '',
                'category': '',
                'project': '',
                'type': '',
                'job_hot_flag': '',
                'functionCategory': '',
                'tag': ''
            }
            response = self.session.get(self.base_url, 
                                      params=test_params, 
                                      headers=self.headers, 
                                      timeout=self.timeout,
                                      proxies=self.proxies)
            return response.status_code == 200
        except Exception as e:
            logger.debug("[字节跳动] 连接测试失败: %s", e)
            return False
    
    def is_available(self) -> dict:
        """获取字节跳动的详细可用性状态"""
        try:
            is_conn_ok = self.test_connection()
            if not is_conn_ok:
                return {
                    'available': False,
                    'message': '连接失败或触发反爬虫机制',
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
        
        # 添加随机延迟避免频繁请求
        time.sleep(random.uniform(1, 3))
        
        try:
            # 构造API请求参数（根据实际URL结构调整）
            params = {
                'keywords': keyword,
                'location': city if city != '全国' else '',
                'current': page,
                'limit': self.max_per_page,
                'category': '',
                'project': '',
                'type': '',
                'job_hot_flag': '',
                'functionCategory': '',
                'tag': ''
            }
            
            logger.info("[字节跳动] 搜索职位: %s (城市: %s, 页码: %d)", keyword, city, page)
            
            # 发送请求
            response = self.session.get(self.base_url, 
                                      params=params, 
                                      headers=self.headers, 
                                      timeout=self.timeout,
                                      proxies=self.proxies)
            
            if response.status_code != 200:
                logger.warning("[字节跳动] 请求失败，状态码: %d", response.status_code)
                return jobs
            
            # 调试：打印响应内容前几字符
            response_text = response.text
            logger.debug("[字节跳动] 响应状态: %d, 响应长度: %d", response.status_code, len(response_text))
            logger.debug("[字节跳动] 响应前200字符: %s", response_text[:200] if response_text else "空响应")
            
            # 保存原始响应用于分析
            if len(response_text) > 0 and not response_text.startswith('{'):
                # 如果不是JSON格式，保存前1000字符用于分析
                logger.debug("[字节跳动] 响应可能不是JSON格式，前1000字符: %s", response_text[:1000])
            
            # 解析JSON响应
            try:
                data = response.json()
                # 根据实际API响应结构调整数据提取逻辑
                job_posts = []
                
                # 尝试多种可能的数据结构
                if isinstance(data, dict):
                    # 情况1: 直接包含职位列表
                    if 'data' in data:
                        job_posts = data['data'].get('list', []) or data['data'].get('positions', []) or []
                    # 情况2: 包含分页信息
                    elif 'positions' in data:
                        job_posts = data['positions']
                    elif 'list' in data:
                        job_posts = data['list']
                    else:
                        # 尝试直接使用整个响应作为职位列表
                        job_posts = [data] if data else []
                elif isinstance(data, list):
                    # 情况3: 响应本身就是职位列表
                    job_posts = data
                
                logger.debug("[字节跳动] 解析到 %d 个职位", len(job_posts))
                
                for job_data in job_posts[:self.max_per_page]:
                    try:
                        job = self._parse_job_data(job_data)
                        if job:
                            jobs.append(job)
                    except Exception as e:
                        logger.warning("[字节跳动] 解析单个职位失败: %s", e)
                        continue
                        
            except json.JSONDecodeError as e:
                logger.error("[字节跳动] JSON解析失败: %s", e)
                # 尝试解析HTML页面（备选方案）
                jobs = self._parse_html_fallback(response.text, keyword)
                
        except Exception as e:
            logger.error("[字节跳动] 搜索失败: %s", e)
        
        logger.info("[字节跳动] 成功获取 %d 个职位", len(jobs))
        return jobs
    
    def _parse_job_data(self, job_data: dict) -> Dict[str, Any]:
        """解析职位数据（适应多种可能的字段名）"""
        try:
            # 提取基本信息（尝试多种字段名）
            title = (job_data.get('title') or 
                    job_data.get('name') or 
                    job_data.get('positionName') or 
                    job_data.get('jobTitle') or '')
            
            company = '字节跳动'
            
            # 薪资信息（多种字段名）
            salary = (job_data.get('salary') or 
                     job_data.get('salaryRange') or 
                     job_data.get('compensation') or 
                     self._format_salary(
                         job_data.get('min_salary'), 
                         job_data.get('max_salary'), 
                         job_data.get('salary_unit')
                     ) or '面议')
            
            # 职位描述和要求
            description = (job_data.get('description') or 
                          job_data.get('jobDescription') or 
                          job_data.get('detail') or '')
            requirements = (job_data.get('requirement') or 
                           job_data.get('requirements') or 
                           job_data.get('jobRequirement') or '')
            full_description = f"{description}\n{requirements}".strip()
            
            # 工作地点
            city = (job_data.get('city') or 
                   job_data.get('location') or 
                   job_data.get('workLocation') or '全国')
            job_category = job_data.get('category', '')
            
            # 职位ID和链接
            job_id = (job_data.get('id') or 
                     job_data.get('jobId') or 
                     job_data.get('positionId') or '')
            job_url = f"{self.job_detail_url}{job_id}" if job_id else ''
            
            # 提取技能要求
            tech_requirements = extract_requirements(full_description)
            
            return normalize_job(
                title=title,
                company=company,
                salary=salary,
                description=full_description,
                source_id=self.source_id,
                source_name=self.source_name,
                requirements=tech_requirements,
                url=job_url
            )
            
        except Exception as e:
            logger.debug("[字节跳动] 解析职位数据失败: %s", e)
            return None
    
    def _format_salary(self, min_salary: int, max_salary: int, unit: str) -> str:
        """格式化薪资显示"""
        if not min_salary and not max_salary:
            return '面议'
        
        unit_map = {
            'MONTH': 'K/月',
            'YEAR': 'K/年',
            'DAY': 'K/天'
        }
        salary_unit = unit_map.get(unit, 'K')
        
        if min_salary and max_salary:
            return f"{min_salary}-{max_salary}{salary_unit}"
        elif min_salary:
            return f"{min_salary}+{salary_unit}"
        elif max_salary:
            return f"Up to {max_salary}{salary_unit}"
        else:
            return '面议'
    
    def _parse_html_fallback(self, html_content: str, keyword: str) -> List[Dict[str, Any]]:
        """HTML页面解析备选方案"""
        jobs = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找职位卡片元素（根据实际页面结构调整选择器）
            job_cards = soup.find_all('div', class_='job-card') or \
                       soup.find_all('li', class_='job-item') or \
                       soup.select('[data-job-id]')
            
            logger.debug("[字节跳动] HTML解析找到 %d 个职位元素", len(job_cards))
            
            for card in job_cards[:self.max_per_page]:
                try:
                    job = self._extract_job_from_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.warning("[字节跳动] HTML解析单个职位失败: %s", e)
                    continue
                    
        except Exception as e:
            logger.error("[字节跳动] HTML备选解析失败: %s", e)
        
        return jobs
    
    def _extract_job_from_card(self, card_element) -> Dict[str, Any]:
        """从职位卡片元素提取信息"""
        try:
            # 尝试多种选择器提取信息
            title_elem = (card_element.find('h3') or 
                         card_element.find('a', class_='job-title') or
                         card_element.find(attrs={'data-title': True}))
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # 薪资信息
            salary_elem = (card_element.find('span', class_='salary') or
                          card_element.find(attrs={'data-salary': True}))
            salary = salary_elem.get_text(strip=True) if salary_elem else "面议"
            
            # 地点信息
            location_elem = (card_element.find('span', class_='location') or
                            card_element.find(attrs={'data-city': True}))
            location = location_elem.get_text(strip=True) if location_elem else "全国"
            
            # 描述信息
            desc_elem = (card_element.find('p', class_='description') or
                        card_element.find('div', class_='job-desc'))
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # 职位链接
            link_elem = card_element.find('a')
            job_url = link_elem.get('href', '') if link_elem else ''
            if job_url and not job_url.startswith('http'):
                job_url = f"https://jobs.bytedance.com{job_url}"
            
            if not title:
                return None
            
            return normalize_job(
                title=title,
                company='字节跳动',
                salary=salary,
                description=description,
                source_id=self.source_id,
                source_name=self.source_name,
                requirements=extract_requirements(description),
                url=job_url
            )
            
        except Exception as e:
            logger.debug("[字节跳动] 提取卡片信息失败: %s", e)
            return None