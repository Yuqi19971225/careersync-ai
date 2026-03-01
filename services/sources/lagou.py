# -*- coding: utf-8 -*-
"""拉勾网职位源"""

import logging
from typing import List, Dict, Any

from bs4 import BeautifulSoup

from .base import BaseJobSource, normalize_job, extract_requirements

logger = logging.getLogger(__name__)


class LagouSource(BaseJobSource):
    """拉勾网（页面结构可能随站点改版变化，需适时调整选择器）"""

    source_id = 'lagou'
    source_name = '拉勾网'

    def search(self, keyword: str, city: str = '全国', page: int = 1) -> List[Dict[str, Any]]:
        jobs = []
        url = f"https://www.lagou.com/jobs/list_{keyword}"
        params = {'city': city, 'pn': page}
        html = self.fetch(url, params)
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
