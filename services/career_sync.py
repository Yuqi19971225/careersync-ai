# -*- coding: utf-8 -*-
"""CareerSync AI 主系统：编排爬虫、匹配、优化"""

from .crawler import JobCrawler
from .optimizer import AIOptimizer
from .matcher import ResumeMatcher

try:
    from config import JOB_SOURCES
except ImportError:
    JOB_SOURCES = None


class CareerSyncAI:
    """统一入口：职位搜索、简历匹配、简历优化"""

    def __init__(self):
        self.crawler = JobCrawler(default_source_ids=JOB_SOURCES)
        self.optimizer = AIOptimizer()
        self.matcher = ResumeMatcher()
        self.cache = {}
        self.system_info = {
            'name': 'CareerSync AI',
            'version': '1.0.0',
            'description': '智能职业匹配与简历优化系统',
            'features': [
                '多平台职位搜索',
                'AI驱动简历优化',
                '智能匹配算法',
                '实时数据分析'
            ],
            'qwen_enabled': bool(self.optimizer._qwen),
            'job_sources': self.crawler.default_source_ids,
        }

    def search_jobs(self, keyword, city='全国', page=1, source_ids=None):
        """搜索职位（带简单缓存）。source_ids 可指定本次使用的招聘源，如 ['lagou']。"""
        cache_key = f"{keyword}_{city}_{page}_{(source_ids or 'default')}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        jobs = self.crawler.crawl_jobs(keyword, city=city, page=page, source_ids=source_ids)
        self.cache[cache_key] = jobs
        return jobs

    def match_resume_to_jobs(self, resume_text, jobs):
        """简历与职位列表匹配并按匹配度排序"""
        matched = []
        for job in jobs:
            score = self.matcher.calculate_match_score(resume_text, job.get('description', ''))
            item = {**job, 'match_score': score, 'sync_score': score}
            matched.append(item)
        matched.sort(key=lambda x: x['match_score'], reverse=True)
        return matched

    def get_resume_optimization(self, resume_text, matched_jobs):
        """基于最佳匹配职位获取简历优化建议"""
        if not matched_jobs:
            return []
        best = matched_jobs[0]
        return self.optimizer.get_optimization_suggestions(resume_text, best.get('description', ''))
