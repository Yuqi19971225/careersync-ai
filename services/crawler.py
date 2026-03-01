# -*- coding: utf-8 -*-
"""CareerSync AI 职位爬虫：多招聘源聚合，可扩展"""

import logging
from typing import List, Optional

from .sources import get_sources

logger = logging.getLogger(__name__)


class JobCrawler:
    """
    多站点职位爬虫聚合器。
    通过 sources 包注册各招聘源，此处按配置或参数选择源并合并结果。
    """

    def __init__(self, default_source_ids: Optional[List[str]] = None):
        """
        :param default_source_ids: 默认启用的招聘源 id 列表，如 ['lagou']；
                                   为 None 时使用全部已注册源。
        """
        self.default_source_ids = default_source_ids

    def crawl_jobs(
        self,
        keyword: str,
        city: str = '全国',
        page: int = 1,
        source_ids: Optional[List[str]] = None
    ) -> List[dict]:
        """
        从多个招聘源拉取职位并合并为统一格式列表。
        :param keyword: 职位关键词
        :param city: 城市
        :param page: 页码
        :param source_ids: 指定本次使用的招聘源 id；不传则用初始化时的 default_source_ids（再否则全部）
        :return: 职位列表，每条含 title, company, salary, description, source, source_id, requirements, sync_score 等
        """
        ids = source_ids if source_ids is not None else self.default_source_ids
        sources = get_sources(ids)
        if not sources:
            logger.warning("未选择任何招聘源，返回空列表")
            return []

        all_jobs = []
        for src in sources:
            try:
                jobs = src.search(keyword, city=city, page=page)
                all_jobs.extend(jobs)
                if jobs:
                    logger.debug("[%s] 获取 %d 条", src.source_id, len(jobs))
            except Exception as e:
                logger.exception("[%s] 爬取异常: %s", src.source_id, e)
        return all_jobs
