# -*- coding: utf-8 -*-
"""API 路由注册"""

import logging
from datetime import datetime

from flask import request, jsonify, send_from_directory

logger = logging.getLogger(__name__)


def register_routes(app, career_sync_ai):
    """将 API 路由注册到 Flask 应用"""

    @app.route('/')
    def index():
        """前端页面"""
        return send_from_directory(app.static_folder or 'static', 'index.html')

    @app.route('/api/search_jobs', methods=['POST'])
    def search_jobs():
        data = request.json or {}
        keyword = data.get('keyword', '')
        city = data.get('city', '全国')
        page = data.get('page', 1)
        source_ids = data.get('sources')  # 可选：指定招聘源，如 ["lagou", "boss"]
        
        if not keyword:
            return jsonify({'error': 'CareerSync AI: 缺少搜索关键词'}), 400
            
        if not source_ids or len(source_ids) == 0:
            return jsonify({'error': 'CareerSync AI: 请至少选择一个招聘网站'}), 400
        
        try:
            # 检查所选源的可用性
            from services.sources import get_source_status
            unavailable_sources = []
            source_messages = {}
            
            for source_id in source_ids:
                try:
                    status_info = get_source_status(source_id)
                    if not status_info.get('available', True):
                        unavailable_sources.append(source_id)
                        source_messages[source_id] = status_info.get('message', '源不可用')
                except Exception as e:
                    unavailable_sources.append(source_id)
                    source_messages[source_id] = f'状态检查失败: {str(e)}'
                    logger.warning("检查源 %s 状态时出错: %s", source_id, e)
            
            # 执行搜索
            jobs = career_sync_ai.search_jobs(keyword, city, page, source_ids=source_ids)
            
            response_data = {
                'success': True,
                'system': 'CareerSync AI',
                'jobs': jobs,
                'total': len(jobs),
                'selected_sources': source_ids
            }
            
            # 添加源状态信息
            if unavailable_sources:
                response_data['warnings'] = {
                    'unavailable_sources': unavailable_sources,
                    'messages': source_messages
                }
                logger.warning("以下源不可用: %s", ', '.join(unavailable_sources))
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.exception("搜索职位失败")
            return jsonify({'error': f'CareerSync AI: 搜索职位失败 - {str(e)}'}), 500

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

    @app.route('/api/job_sources', methods=['GET'])
    def job_sources():
        """返回已注册的招聘源 id 列表及当前启用的源"""
        from services.sources import list_source_ids, get_source_status
        available_sources = list_source_ids()
        
        # 获取每个源的状态信息
        source_statuses = {}
        for source_id in available_sources:
            try:
                status_info = get_source_status(source_id)
                source_statuses[source_id] = status_info
            except Exception as e:
                logger.warning("获取源 %s 状态失败: %s", source_id, e)
                source_statuses[source_id] = {
                    'available': False,
                    'message': '状态检查失败'
                }
        
        return jsonify({
            'available': available_sources,
            'enabled': career_sync_ai.system_info.get('job_sources'),
            'statuses': source_statuses
        })

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'system': 'CareerSync AI',
            'version': career_sync_ai.system_info['version'],
            'timestamp': datetime.now().isoformat()
        })
