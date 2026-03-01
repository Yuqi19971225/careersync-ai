# -*- coding: utf-8 -*-
"""API 路由注册"""

import logging
from datetime import datetime

from flask import request, jsonify

logger = logging.getLogger(__name__)


def register_routes(app, career_sync_ai):
    """将 API 路由注册到 Flask 应用"""

    @app.route('/api/search_jobs', methods=['POST'])
    def search_jobs():
        data = request.json or {}
        keyword = data.get('keyword', '')
        city = data.get('city', '全国')
        page = data.get('page', 1)
        if not keyword:
            return jsonify({'error': 'CareerSync AI: 缺少搜索关键词'}), 400
        try:
            jobs = career_sync_ai.search_jobs(keyword, city, page)
            return jsonify({
                'success': True,
                'system': 'CareerSync AI',
                'jobs': jobs,
                'total': len(jobs)
            })
        except Exception as e:
            logger.exception("搜索职位失败")
            return jsonify({'error': 'CareerSync AI: 搜索职位失败'}), 500

    @app.route('/api/match_resume', methods=['POST'])
    def match_resume():
        data = request.json or {}
        resume_text = data.get('resume', '')
        keyword = data.get('keyword', '')
        city = data.get('city', '全国')
        if not resume_text or not keyword:
            return jsonify({'error': 'CareerSync AI: 缺少简历内容或搜索关键词'}), 400
        try:
            jobs = career_sync_ai.search_jobs(keyword, city)
            matched_jobs = career_sync_ai.match_resume_to_jobs(resume_text, jobs)
            return jsonify({
                'success': True,
                'system': 'CareerSync AI',
                'matched_jobs': matched_jobs
            })
        except Exception as e:
            logger.exception("简历匹配失败")
            return jsonify({'error': 'CareerSync AI: 简历匹配失败'}), 500

    @app.route('/api/optimize_resume', methods=['POST'])
    def optimize_resume():
        data = request.json or {}
        resume_text = data.get('resume', '')
        keyword = data.get('keyword', '')
        city = data.get('city', '全国')
        if not resume_text or not keyword:
            return jsonify({'error': 'CareerSync AI: 缺少简历内容或搜索关键词'}), 400
        try:
            jobs = career_sync_ai.search_jobs(keyword, city)
            matched_jobs = career_sync_ai.match_resume_to_jobs(resume_text, jobs)
            suggestions = career_sync_ai.get_resume_optimization(resume_text, matched_jobs)
            optimized_resume = career_sync_ai.optimizer.optimize_resume(resume_text, suggestions)
            return jsonify({
                'success': True,
                'system': 'CareerSync AI',
                'original_resume': resume_text,
                'optimized_resume': optimized_resume,
                'suggestions': suggestions,
                'matched_jobs': matched_jobs[:3],
                'optimization_confidence': 0.85
            })
        except Exception as e:
            logger.exception("简历优化失败")
            return jsonify({'error': 'CareerSync AI: 简历优化失败'}), 500

    @app.route('/api/system_info', methods=['GET'])
    def system_info():
        return jsonify(career_sync_ai.system_info)

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'system': 'CareerSync AI',
            'version': career_sync_ai.system_info['version'],
            'timestamp': datetime.now().isoformat()
        })
