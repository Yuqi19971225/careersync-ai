# -*- coding: utf-8 -*-
"""CareerSync AI 简历-职位匹配引擎"""

import logging

import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class ResumeMatcher:
    """基于 TF-IDF + 余弦相似度的匹配"""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(tokenizer=jieba.cut, stop_words=None)

    def calculate_match_score(self, resume_text, job_description):
        """计算简历与职位描述的匹配度，返回 0～100"""
        try:
            corpus = [resume_text, job_description]
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            score = similarity[0][0] * 100
            return min(int(score), 100)
        except Exception as e:
            logger.debug("匹配分数计算异常，使用默认分: %s", e)
            return 50
