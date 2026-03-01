# -*- coding: utf-8 -*-
"""CareerSync AI 简历优化引擎（千问 API + 规则兜底）"""

import logging

import jieba

from config import QWEN_MODEL
from services.qwen_client import get_qwen_client

logger = logging.getLogger(__name__)


class AIOptimizer:
    """简历优化：优先千问，失败时规则兜底"""

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
            lines = [s.strip() for s in text.replace("CareerSync AI 建议：", "建议：").split("\n") if s.strip()]
            suggestions = []
            for line in lines:
                if line.startswith("建议："):
                    suggestions.append(f"CareerSync AI 建议: {line[3:].strip()}")
                elif "建议" in line or len(line) > 10:
                    suggestions.append(f"CareerSync AI 建议: {line}")
            return suggestions[:6] if suggestions else None
        except Exception as e:
            logger.warning("千问 API 调用失败，将使用规则兜底: %s", e)
            return None

    def _get_suggestions_fallback(self, resume_text, matched_job_desc):
        """规则兜底"""
        suggestions = []
        resume_words = set(jieba.cut(resume_text))
        job_words = set(jieba.cut(matched_job_desc))
        missing_skills = job_words - resume_words
        if missing_skills:
            suggestions.append(
                f"CareerSync AI 建议: 在简历中增加以下技能关键词: {', '.join(list(missing_skills)[:5])}"
            )
        if '年' in resume_text or '月' in resume_text:
            suggestions.append("CareerSync AI 建议: 增加具体的量化成果描述，如'提升效率30%'、'减少成本20%'等")
        suggestions.append("CareerSync AI 建议: 按熟练程度重新组织技能列表，将最擅长的技能放在前面")
        if '项目' in resume_text:
            suggestions.append("CareerSync AI 建议: 在项目经验中突出您的个人贡献和使用的技术栈")
        return suggestions

    def get_optimization_suggestions(self, resume_text, matched_job_desc):
        """获取简历优化建议"""
        suggestions = self._get_suggestions_via_qwen(resume_text, matched_job_desc)
        if suggestions:
            return suggestions
        return self._get_suggestions_fallback(resume_text, matched_job_desc)

    def _optimize_resume_via_qwen(self, resume_text, suggestions):
        """通过千问生成优化后的简历正文"""
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
            logger.warning("千问生成优化简历失败: %s", e)
            return None

    def optimize_resume(self, resume_text, suggestions):
        """根据建议优化简历：有千问则生成全文，否则仅追加技能建议"""
        optimized = self._optimize_resume_via_qwen(resume_text, suggestions)
        if optimized:
            return optimized
        result = resume_text
        for suggestion in suggestions:
            if '技能关键词' in suggestion:
                skills = suggestion.split(':')[-1].strip()
                result += f"\n\n/* CareerSync AI 建议添加的技能 */\n{skills}"
        return result
