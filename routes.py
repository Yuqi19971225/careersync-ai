# -*- coding: utf-8 -*-
"""API 路由注册"""

import logging
from datetime import datetime

from flask import request, jsonify, send_from_directory
from services.captcha_handler import get_captcha_manager

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
        """返回已注册的招聘源 id 列表及当前启用的源（合并拉勾网相关源）"""
        from services.sources import list_source_ids, get_source_status
        available_sources = list_source_ids()
        
        # 过滤并合并拉勾网相关源
        filtered_sources = []
        has_lagou = False
        
        for source_id in available_sources:
            if source_id.startswith('lagou'):
                if not has_lagou:
                    filtered_sources.append('lagou')  # 只保留一个拉勾网选项
                    has_lagou = True
            else:
                filtered_sources.append(source_id)
        
        # 获取每个源的状态信息
        source_statuses = {}
        for source_id in filtered_sources:
            try:
                # 对于合并后的拉勾网源，获取最佳状态
                if source_id == 'lagou':
                    # 检查所有拉勾网相关源的状态，返回最优的那个
                    lagou_source_ids = [sid for sid in available_sources if sid.startswith('lagou')]
                    best_status = None
                    for lagou_sid in lagou_source_ids:
                        status_info = get_source_status(lagou_sid)
                        if status_info.get('available', False):
                            best_status = status_info
                            break
                    if not best_status:
                        best_status = get_source_status(lagou_source_ids[0]) if lagou_source_ids else {'available': False, 'message': '未知状态'}
                    source_statuses[source_id] = best_status
                else:
                    status_info = get_source_status(source_id)
                    source_statuses[source_id] = status_info
            except Exception as e:
                logger.warning("获取源 %s 状态失败: %s", source_id, e)
                source_statuses[source_id] = {
                    'available': False,
                    'message': '状态检查失败'
                }
        
        return jsonify({
            'available': filtered_sources,
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
    
    @app.route('/api/captcha/pending', methods=['GET'])
    def get_pending_captchas():
        """获取待处理的验证码任务"""
        try:
            captcha_manager = get_captcha_manager()
            pending_captchas = captcha_manager.get_pending_captchas()
            
            # 转换为前端友好的格式
            captcha_list = []
            for captcha_id, task in pending_captchas.items():
                captcha_list.append({
                    'id': captcha_id,
                    'type': task.get('type', 'unknown'),
                    'image': task.get('image', ''),
                    'timestamp': task.get('timestamp', 0)
                })
            
            return jsonify({
                'pending_captchas': captcha_list,
                'count': len(captcha_list)
            })
        
        except Exception as e:
            logger.error("获取待处理验证码失败: %s", e)
            return jsonify({'error': '获取验证码任务失败'}), 500
    
    @app.route('/api/captcha/submit', methods=['POST'])
    def submit_captcha_solution():
        """提交验证码解决方案"""
        try:
            data = request.json or {}
            captcha_id = data.get('captcha_id')
            solution = data.get('solution')
            
            if not captcha_id or not solution:
                return jsonify({'error': '缺少验证码ID或解决方案'}), 400
            
            captcha_manager = get_captcha_manager()
            success = captcha_manager.submit_captcha_solution(captcha_id, solution)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '验证码解决方案已提交'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '验证码解决方案提交失败'
                }), 400
                
        except Exception as e:
            logger.error("提交验证码解决方案失败: %s", e)
            return jsonify({'error': '提交验证码解决方案失败'}), 500
