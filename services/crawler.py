# -*- coding: utf-8 -*-
"""CareerSync AI 职位爬虫引擎"""

import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class JobCrawler:
    """多平台职位爬虫"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'CareerSync-AI-Bot/1.0 (compatible; CareerSync AI System)'
        }
        self.job_sources = {
            'lagou': 'https://www.lagou.com/jobs/list_',
            'boss': 'https://www.zhipin.com/job_detail/',
            'zhilian': 'https://sou.zhaopin.com/jobs/searchresult.ashx'
        }

    def crawl_lagou_jobs(self, keyword, city='全国', page=1):
        """爬取拉勾网职位"""
        jobs = []
        try:
            url = f"https://www.lagou.com/jobs/list_{keyword}?city={city}&pn={page}"
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            job_list = soup.find_all('div', class_='job-item')

            for job in job_list[:5]:
                title_elem = job.find('h3', class_='position-name')
                company_elem = job.find('div', class_='company')
                salary_elem = job.find('span', class_='salary')
                desc_elem = job.find('div', class_='job-detail')

                if title_elem and salary_elem:
                    desc_text = desc_elem.get_text(strip=True) if desc_elem else ''
                    job_data = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True) if company_elem else '未知公司',
                        'salary': salary_elem.get_text(strip=True),
                        'description': desc_text,
                        'source': '拉勾网',
                        'requirements': self.extract_requirements(desc_text),
                        'sync_score': 0
                    }
                    jobs.append(job_data)
        except Exception as e:
            logger.error("爬取拉勾网职位失败: %s", e)
        return jobs

    def extract_requirements(self, description):
        """从职位描述中提取技术关键词"""
        tech_keywords = [
            'Python', 'Java', 'JavaScript', 'React', 'Vue', 'Node.js',
            'SQL', 'MySQL', 'MongoDB', 'Docker', 'Kubernetes',
            'Linux', 'Git', 'CSS', 'HTML', 'Spring', 'Django'
        ]
        found = [s for s in tech_keywords if s.lower() in (description or '').lower()]
        return found
