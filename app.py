from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import time
import threading
import os
from datetime import datetime
import logging

# 千问 API（阿里云百炼 / DashScope，兼容 OpenAI 接口）
QWEN_API_KEY = os.getenv('DASHSCOPE_API_KEY') or os.getenv('QWEN_API_KEY')
QWEN_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-turbo')

def get_qwen_client():
    """获取千问 API 客户端（OpenAI 兼容接口），未配置 API Key 时返回 None"""
    if not QWEN_API_KEY:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)
    except Exception as e:
        logger.warning(f"千问客户端初始化失败: {e}")
        return None

app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobCrawler:
    """CareerSync AI 职位爬虫引擎"""
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
        """爬取拉勾网职位 - CareerSync AI 专用接口"""
        jobs = []
        try:
            # 模拟搜索请求
            url = f"https://www.lagou.com/jobs/list_{keyword}?city={city}&pn={page}"
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 解析职位信息（简化版）
            job_list = soup.find_all('div', class_='job-item')
            
            for job in job_list[:5]:  # 限制数量
                title_elem = job.find('h3', class_='position-name')
                company_elem = job.find('div', class_='company')
                salary_elem = job.find('span', class_='salary')
                desc_elem = job.find('div', class_='job-detail')
                
                if title_elem and salary_elem:
                    job_data = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True) if company_elem else '未知公司',
                        'salary': salary_elem.get_text(strip=True),
                        'description': desc_elem.get_text(strip=True) if desc_elem else '',
                        'source': '拉勾网',
                        'requirements': self.extract_requirements(desc_elem.get_text(strip=True) if desc_elem else ''),
                        'sync_score': 0  # CareerSync 评分
                    }
                    jobs.append(job_data)
                    
        except Exception as e:
            logger.error(f"CareerSync AI 爬取拉勾网职位失败: {str(e)}")
        
        return jobs
    
    def extract_requirements(self, description):
        """提取职位要求关键词 - CareerSync AI 智能分析"""
        # 简化的技能提取逻辑
        tech_keywords = [
            'Python', 'Java', 'JavaScript', 'React', 'Vue', 'Node.js', 
            'SQL', 'MySQL', 'MongoDB', 'Docker', 'Kubernetes', 
            'Linux', 'Git', 'CSS', 'HTML', 'Spring', 'Django'
        ]
        
        found_skills = []
        for skill in tech_keywords:
            if skill.lower() in description.lower():
                found_skills.append(skill)
        
        return found_skills

class AIOptimizer:
    """CareerSync AI 优化引擎（支持千问 API + 规则兜底）"""
    def __init__(self):
        self._qwen = get_qwen_client()
        if self._qwen:
            logger.info("CareerSync AI: 已接入千问 API，将使用大模型生成优化建议")
        else:
            logger.info("CareerSync AI: 未配置 DASHSCOPE_API_KEY，将使用规则引擎兜底")

    def _get_suggestions_via_qwen(self, resume_text, matched_job_desc):
        """通过千问 API 获取简历优化建议"""
        if not self._qwen:
            return None
        prompt = f"""你是一名专业的简历优化顾问。请根据以下「当前简历」和「目标职位描述」的差异，给出 3～5 条具体、可操作的简历优化建议。
要求：每条建议单独一行，以「建议：」或「CareerSync AI 建议：」开头，语言简洁，针对技能、经历描述、量化成果等给出可执行建议。

【当前简历】
{resume_text[:3000]}

【目标职位描述】
{matched_job_desc[:2000]}

请直接输出建议列表，不要其他开场白。"""

        try:
            resp = self._qwen.chat.completions.create(
                model=QWEN_MODEL,
                messages=[
                    {"role": "system", "content": "你是 CareerSync AI 的简历优化助手，只输出中文建议，每条一行。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            text = (resp.choices[0].message.content or "").strip()
            if not text:
                return None
            # 按行解析，保留像建议的句子
            lines = [s.strip() for s in text.replace("CareerSync AI 建议：", "建议：").split("\n") if s.strip()]
            suggestions = []
            for line in lines:
                if line.startswith("建议："):
                    suggestions.append(f"CareerSync AI 建议: {line[3:].strip()}")
                elif "建议" in line or len(line) > 10:
                    suggestions.append(f"CareerSync AI 建议: {line}")
            return suggestions[:6] if suggestions else None
        except Exception as e:
            logger.warning(f"千问 API 调用失败，将使用规则兜底: {e}")
            return None

    def _get_suggestions_fallback(self, resume_text, matched_job_desc):
        """规则兜底：无千问或调用失败时使用"""
        suggestions = []
        resume_words = set(jieba.cut(resume_text))
        job_words = set(jieba.cut(matched_job_desc))
        missing_skills = job_words - resume_words
        if len(missing_skills) > 0:
            suggestions.append(f"CareerSync AI 建议: 在简历中增加以下技能关键词: {', '.join(list(missing_skills)[:5])}")
        if '年' in resume_text or '月' in resume_text:
            suggestions.append("CareerSync AI 建议: 增加具体的量化成果描述，如'提升效率30%'、'减少成本20%'等")
        suggestions.append("CareerSync AI 建议: 按熟练程度重新组织技能列表，将最擅长的技能放在前面")
        if '项目' in resume_text:
            suggestions.append("CareerSync AI 建议: 在项目经验中突出您的个人贡献和使用的技术栈")
        return suggestions

    def get_optimization_suggestions(self, resume_text, matched_job_desc):
        """获取简历优化建议 - 优先千问 API，否则规则引擎"""
        suggestions = self._get_suggestions_via_qwen(resume_text, matched_job_desc)
        if suggestions:
            return suggestions
        return self._get_suggestions_fallback(resume_text, matched_job_desc)

    def _optimize_resume_via_qwen(self, resume_text, suggestions):
        """通过千问 API 生成优化后的简历正文"""
        if not self._qwen:
            return None
        suggestions_text = "\n".join(suggestions)
        prompt = f"""请根据以下「原始简历」和「优化建议」，直接输出一版修改后的完整简历正文。
要求：只输出简历内容，不要解释；在保留原意的基础上按建议微调表述、补充关键词或量化信息，不要大幅删减经历。

【原始简历】
{resume_text[:3500]}

【优化建议】
{suggestions_text}

【修改后的简历】"""

        try:
            resp = self._qwen.chat.completions.create(
                model=QWEN_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            return (resp.choices[0].message.content or "").strip() or None
        except Exception as e:
            logger.warning(f"千问生成优化简历失败: {e}")
            return None

    def optimize_resume(self, resume_text, suggestions):
        """根据建议优化简历 - 有千问时由千问生成全文，否则仅追加建议中的技能"""
        optimized = self._optimize_resume_via_qwen(resume_text, suggestions)
        if optimized:
            return optimized
        optimized_resume = resume_text
        for suggestion in suggestions:
            if '技能关键词' in suggestion:
                skills = suggestion.split(':')[-1].strip()
                optimized_resume += f"\n\n/* CareerSync AI 建议添加的技能 */\n{skills}"
        return optimized_resume

class ResumeMatcher:
    """CareerSync AI 匹配引擎"""
    def __init__(self):
        self.vectorizer = TfidfVectorizer(tokenizer=jieba.cut, stop_words=None)
    
    def calculate_match_score(self, resume_text, job_description):
        """计算简历与职位的匹配度 - CareerSync AI 算法"""
        try:
            # 使用TF-IDF计算相似度
            corpus = [resume_text, job_description]
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            
            # 计算余弦相似度
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            score = similarity[0][0] * 100
            
            return min(int(score), 100)  # 限制在0-100之间
        except:
            return 50  # 默认分数

class CareerSyncAI:
    """CareerSync AI 主系统"""
    def __init__(self):
        self.crawler = JobCrawler()
        self.optimizer = AIOptimizer()
        self.matcher = ResumeMatcher()
        self.cache = {}  # 简单缓存
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
        }
    
    def search_jobs(self, keyword, city='全国', page=1):
        """搜索职位 - CareerSync AI 引擎"""
        cache_key = f"{keyword}_{city}_{page}"
        
        # 检查缓存
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 爬取职位
        jobs = self.crawler.crawl_lagou_jobs(keyword, city, page)
        
        # 缓存结果（简单实现）
        self.cache[cache_key] = jobs
        
        return jobs
    
    def match_resume_to_jobs(self, resume_text, jobs):
        """匹配简历与职位 - CareerSync AI 算法"""
        matched_jobs = []
        
        for job in jobs:
            score = self.matcher.calculate_match_score(resume_text, job['description'])
            job_with_score = job.copy()
            job_with_score['match_score'] = score
            job_with_score['sync_score'] = score  # CareerSync 特有评分
            matched_jobs.append(job_with_score)
        
        # 按匹配度排序
        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matched_jobs
    
    def get_resume_optimization(self, resume_text, matched_jobs):
        """获取简历优化建议 - CareerSync AI 专属"""
        if not matched_jobs:
            return []
        
        # 使用匹配度最高的职位作为参考
        best_match = matched_jobs[0]
        suggestions = self.optimizer.get_optimization_suggestions(
            resume_text, 
            best_match['description']
        )
        
        return suggestions

# 创建 CareerSync AI 实例
career_sync_ai = CareerSyncAI()

@app.route('/api/search_jobs', methods=['POST'])
def search_jobs():
    """搜索职位接口 - CareerSync AI"""
    data = request.json
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
        logger.error(f"CareerSync AI 搜索职位失败: {str(e)}")
        return jsonify({'error': 'CareerSync AI: 搜索职位失败'}), 500

@app.route('/api/match_resume', methods=['POST'])
def match_resume():
    """简历匹配接口 - CareerSync AI"""
    data = request.json
    resume_text = data.get('resume', '')
    keyword = data.get('keyword', '')
    city = data.get('city', '全国')
    
    if not resume_text or not keyword:
        return jsonify({'error': 'CareerSync AI: 缺少简历内容或搜索关键词'}), 400
    
    try:
        # 获取职位
        jobs = career_sync_ai.search_jobs(keyword, city)
        
        # 匹配简历与职位
        matched_jobs = career_sync_ai.match_resume_to_jobs(resume_text, jobs)
        
        return jsonify({
            'success': True,
            'system': 'CareerSync AI',
            'matched_jobs': matched_jobs
        })
    except Exception as e:
        logger.error(f"CareerSync AI 简历匹配失败: {str(e)}")
        return jsonify({'error': 'CareerSync AI: 简历匹配失败'}), 500

@app.route('/api/optimize_resume', methods=['POST'])
def optimize_resume():
    """简历优化接口 - CareerSync AI"""
    data = request.json
    resume_text = data.get('resume', '')
    keyword = data.get('keyword', '')
    city = data.get('city', '全国')
    
    if not resume_text or not keyword:
        return jsonify({'error': 'CareerSync AI: 缺少简历内容或搜索关键词'}), 400
    
    try:
        # 获取职位
        jobs = career_sync_ai.search_jobs(keyword, city)
        
        # 匹配简历与职位
        matched_jobs = career_sync_ai.match_resume_to_jobs(resume_text, jobs)
        
        # 获取优化建议
        suggestions = career_sync_ai.get_resume_optimization(resume_text, matched_jobs)
        
        # 生成优化后的简历
        optimized_resume = career_sync_ai.optimizer.optimize_resume(resume_text, suggestions)
        
        return jsonify({
            'success': True,
            'system': 'CareerSync AI',
            'original_resume': resume_text,
            'optimized_resume': optimized_resume,
            'suggestions': suggestions,
            'matched_jobs': matched_jobs[:3],  # 返回前3个最佳匹配
            'optimization_confidence': 0.85  # 优化置信度
        })
    except Exception as e:
        logger.error(f"CareerSync AI 简历优化失败: {str(e)}")
        return jsonify({'error': 'CareerSync AI: 简历优化失败'}), 500

@app.route('/api/system_info', methods=['GET'])
def system_info():
    """系统信息接口 - CareerSync AI"""
    return jsonify(career_sync_ai.system_info)

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口 - CareerSync AI"""
    return jsonify({
        'status': 'healthy',
        'system': 'CareerSync AI',
        'version': career_sync_ai.system_info['version'],
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("="*60)
    print("🚀 CareerSync AI - 智能职业匹配与简历优化系统")
    print("="*60)
    print(f"📋 系统版本: {career_sync_ai.system_info['version']}")
    print(f"💡 系统功能: {', '.join(career_sync_ai.system_info['features'])}")
    print("\n🌐 API 接口列表:")
    print("  POST /api/search_jobs   - 职位搜索")
    print("  POST /api/match_resume  - 简历匹配") 
    print("  POST /api/optimize_resume - 简历优化")
    print("  GET  /api/system_info   - 系统信息")
    print("  GET  /api/health        - 健康检查")
    print("\n⚡ 启动 CareerSync AI 服务...")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=5000)
