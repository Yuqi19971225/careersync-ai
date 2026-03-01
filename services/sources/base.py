# -*- coding: utf-8 -*-
"""招聘源抽象基类：统一接口与公共能力"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

import requests

logger = logging.getLogger(__name__)

# 统一职位信息字段（各站点解析后需映射到此结构）
JOB_FIELDS = ('title', 'company', 'salary', 'description', 'source', 'source_id', 'requirements', 'url', 'sync_score')

# 公共技能关键词，用于从描述中提取
DEFAULT_TECH_KEYWORDS = [
    'Python', 'Java', 'JavaScript', 'React', 'Vue', 'Node.js',
    'SQL', 'MySQL', 'MongoDB', 'Docker', 'Kubernetes',
    'Linux', 'Git', 'CSS', 'HTML', 'Spring', 'Django', 'Go', 'Rust'
]


def normalize_job(
    title: str,
    company: str,
    salary: str,
    description: str,
    source_id: str,
    source_name: str,
    requirements: List[str] = None,
    url: str = None
) -> Dict[str, Any]:
    """构造统一职位字典，供下游匹配与展示使用。"""
    return {
        'title': title or '',
        'company': company or '未知公司',
        'salary': salary or '',
        'description': description or '',
        'source': source_name,
        'source_id': source_id,
        'requirements': requirements or [],
        'url': url or '',
        'sync_score': 0
    }


def extract_requirements(description: str, keywords: List[str] = None) -> List[str]:
    """从职位描述中提取技术关键词。"""
    keywords = keywords or DEFAULT_TECH_KEYWORDS
    desc = (description or '').lower()
    return [k for k in keywords if k.lower() in desc]


class BaseJobSource(ABC):
    """招聘站点抽象基类，扩展新站点时继承此类并实现 search。"""

    source_id: str = ''   # 唯一标识，如 lagou / boss / zhaopin
    source_name: str = '' # 展示名称，如 拉勾网 / BOSS直聘 / 智联招聘

    def __init__(self, timeout: int = 15, max_per_page: int = 20):
        self.timeout = timeout
        self.max_per_page = max_per_page
        self.headers = {
            'User-Agent': 'CareerSync-AI-Bot/1.0 (compatible; CareerSync AI System)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }

    def fetch(self, url: str, params: dict = None) -> str:
        """发起 GET 请求并返回响应文本，失败返回空字符串。"""
        try:
            r = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:
            logger.warning("[%s] 请求失败 %s: %s", self.source_id, url, e)
            return ''

    @abstractmethod
    def search(self, keyword: str, city: str = '全国', page: int = 1) -> List[Dict[str, Any]]:
        """
        搜索职位，返回统一格式的职位列表。
        每条职位需包含: title, company, salary, description, source, source_id, requirements, sync_score, url(可选)
        """
        pass
