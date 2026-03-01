# -*- coding: utf-8 -*-
"""基于千问大模型的智能验证码处理器"""

import logging
import base64
import json
from typing import Optional, Tuple, List, Dict, Any
import cv2
import numpy as np
from io import BytesIO
from PIL import Image

from .qwen_client import get_qwen_client
from config import QWEN_MODEL

logger = logging.getLogger(__name__)


class QwenCaptchaProcessor:
    """基于千问大模型的验证码智能处理器"""
    
    def __init__(self):
        self.qwen_client = get_qwen_client()
        self.is_available = self.qwen_client is not None
        
        if self.is_available:
            logger.info("✅ 千问验证码处理器已启用")
        else:
            logger.info("ℹ️ 千问验证码处理器不可用（API密钥未配置）")
    
    def process_slide_captcha(self, background_image_b64: str, 
                            slider_image_b64: Optional[str] = None) -> Optional[int]:
        """
        使用千问大模型处理滑动验证码
        
        Args:
            background_image_b64: 背景图片的base64编码
            slider_image_b64: 滑块图片的base64编码（可选）
            
        Returns:
            滑动距离（像素），如果处理失败返回None
        """
        if not self.is_available:
            logger.warning("千问处理器不可用，无法处理滑动验证码")
            return None
            
        try:
            logger.info("🤖 启动千问滑动验证码识别...")
            
            # 构造提示词
            prompt = self._build_slide_captcha_prompt(background_image_b64, slider_image_b64)
            
            # 调用千问API
            response = self.qwen_client.chat.completions.create(
                model=QWEN_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一个专业的验证码识别专家，擅长分析滑动验证码图片并准确识别滑块应该移动的距离。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,  # 低温度确保结果稳定
                max_tokens=200
            )
            
            # 解析响应
            result_text = response.choices[0].message.content.strip()
            logger.debug(f"千问识别结果: {result_text}")
            
            # 提取滑动距离
            distance = self._extract_distance_from_response(result_text)
            
            if distance is not None:
                logger.info(f"✅ 千问成功识别滑动距离: {distance}px")
                return distance
            else:
                logger.warning("❌ 千问无法从响应中提取有效距离")
                return None
                
        except Exception as e:
            logger.error(f"千问滑动验证码处理失败: {e}")
            return None
    
    def process_image_text_captcha(self, image_b64: str) -> Optional[str]:
        """
        使用千问大模型处理图片文字验证码
        
        Args:
            image_b64: 验证码图片的base64编码
            
        Returns:
            识别出的文字，如果处理失败返回None
        """
        if not self.is_available:
            logger.warning("千问处理器不可用，无法处理图片文字验证码")
            return None
            
        try:
            logger.info("🤖 启动千问图片文字验证码识别...")
            
            # 构造提示词
            prompt = self._build_image_text_prompt(image_b64)
            
            # 调用千问API
            response = self.qwen_client.chat.completions.create(
                model=QWEN_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一个专业的OCR文字识别专家，擅长识别各种验证码图片中的文字内容。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.0,  # 最低温度确保准确性
                max_tokens=50
            )
            
            # 解析响应
            result_text = response.choices[0].message.content.strip()
            logger.debug(f"千问OCR识别结果: {result_text}")
            
            # 清理识别结果
            cleaned_text = self._clean_ocr_result(result_text)
            
            if cleaned_text:
                logger.info(f"✅ 千问成功识别验证码文字: {cleaned_text}")
                return cleaned_text
            else:
                logger.warning("❌ 千问无法识别有效文字")
                return None
                
        except Exception as e:
            logger.error(f"千问图片文字验证码处理失败: {e}")
            return None
    
    def process_click_captcha(self, image_b64: str, 
                            instruction: str = "请指出图片中需要点击的位置") -> Optional[List[Tuple[int, int]]]:
        """
        使用千问大模型处理点选验证码
        
        Args:
            image_b64: 验证码图片的base64编码
            instruction: 点选指令
            
        Returns:
            坐标列表 [(x, y), ...]，如果处理失败返回None
        """
        if not self.is_available:
            logger.warning("千问处理器不可用，无法处理点选验证码")
            return None
            
        try:
            logger.info("🤖 启动千问点选验证码识别...")
            
            # 构造提示词
            prompt = self._build_click_captcha_prompt(image_b64, instruction)
            
            # 调用千问API
            response = self.qwen_client.chat.completions.create(
                model=QWEN_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一个专业的图像识别专家，擅长分析图片并指出需要点击的精确位置坐标。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            # 解析响应
            result_text = response.choices[0].message.content.strip()
            logger.debug(f"千问点选识别结果: {result_text}")
            
            # 提取坐标
            coordinates = self._extract_coordinates_from_response(result_text)
            
            if coordinates:
                logger.info(f"✅ 千问成功识别点击坐标: {coordinates}")
                return coordinates
            else:
                logger.warning("❌ 千问无法从响应中提取有效坐标")
                return None
                
        except Exception as e:
            logger.error(f"千问点选验证码处理失败: {e}")
            return None
    
    def _build_slide_captcha_prompt(self, background_b64: str, slider_b64: Optional[str]) -> str:
        """构建滑动验证码识别提示词"""
        prompt = f"""
请分析这张滑动验证码图片，告诉我滑块应该移动多少像素才能到达正确位置。

图片信息：
- 这是一张滑动验证码的背景图片
- 需要识别出缺口的位置
- 返回一个数字表示滑动距离（像素）

请直接回答数字，例如：150
不要包含其他文字说明。
"""
        
        # 添加图片
        prompt += f"\n[IMAGE]{background_b64}[/IMAGE]"
        
        if slider_b64:
            prompt += f"\n[SLIDER_IMAGE]{slider_b64}[/SLIDER_IMAGE]"
            
        return prompt
    
    def _build_image_text_prompt(self, image_b64: str) -> str:
        """构建图片文字验证码识别提示词"""
        prompt = f"""
请识别这张验证码图片中的文字内容。

要求：
- 准确识别图片中的所有字符
- 区分大小写字母和数字
- 忽略背景干扰元素
- 只返回识别出的文字，不要其他说明

请直接回答识别结果，例如：AB12cd
"""
        
        # 添加图片
        prompt += f"\n[IMAGE]{image_b64}[/IMAGE]"
        
        return prompt
    
    def _build_click_captcha_prompt(self, image_b64: str, instruction: str) -> str:
        """构建点选验证码识别提示词"""
        prompt = f"""
{instruction}

请分析这张图片，指出需要点击的精确位置坐标。

要求：
- 以图片左上角为原点(0,0)
- 图片尺寸约为300x150像素
- 返回坐标格式：x,y
- 如果有多个点击点，用分号分隔：x1,y1;x2,y2

请直接回答坐标，例如：150,75 或 100,50;200,80
不要包含其他文字说明。
"""
        
        # 添加图片
        prompt += f"\n[IMAGE]{image_b64}[/IMAGE]"
        
        return prompt
    
    def _extract_distance_from_response(self, response_text: str) -> Optional[int]:
        """从千问响应中提取滑动距离"""
        try:
            # 清理响应文本
            clean_text = ''.join(c for c in response_text if c.isdigit() or c in ' .')
            
            # 提取数字
            import re
            numbers = re.findall(r'\d+', clean_text)
            
            if numbers:
                # 返回第一个数字作为距离
                distance = int(numbers[0])
                # 验证合理性（滑动验证码通常在50-400像素之间）
                if 30 <= distance <= 500:
                    return distance
                    
            return None
        except Exception as e:
            logger.debug(f"提取距离失败: {e}")
            return None
    
    def _clean_ocr_result(self, response_text: str) -> Optional[str]:
        """清理OCR识别结果"""
        try:
            # 移除常见前缀和后缀
            cleaned = response_text.strip()
            cleaned = cleaned.replace('识别结果：', '').replace('验证码：', '')
            cleaned = cleaned.replace('答案：', '').replace('文字：', '')
            
            # 只保留字母数字字符
            cleaned = ''.join(c for c in cleaned if c.isalnum())
            
            # 验证长度合理性（验证码通常4-8个字符）
            if 2 <= len(cleaned) <= 12:
                return cleaned.upper()  # 验证码通常为大写
            
            return None
        except Exception as e:
            logger.debug(f"清理OCR结果失败: {e}")
            return None
    
    def _extract_coordinates_from_response(self, response_text: str) -> Optional[List[Tuple[int, int]]]:
        """从千问响应中提取坐标"""
        try:
            coordinates = []
            
            # 查找坐标格式 x,y 或 (x,y)
            import re
            coord_patterns = [
                r'(\d+)[,\s]+(\d+)',  # x,y 格式
                r'\((\d+)[,\s]+(\d+)\)'  # (x,y) 格式
            ]
            
            for pattern in coord_patterns:
                matches = re.findall(pattern, response_text)
                for match in matches:
                    x, y = int(match[0]), int(match[1])
                    # 验证坐标合理性
                    if 0 <= x <= 500 and 0 <= y <= 300:
                        coordinates.append((x, y))
            
            return coordinates if coordinates else None
        except Exception as e:
            logger.debug(f"提取坐标失败: {e}")
            return None


# 全局实例
qwen_captcha_processor = QwenCaptchaProcessor()


def get_qwen_captcha_processor() -> QwenCaptchaProcessor:
    """获取千问验证码处理器实例"""
    return qwen_captcha_processor


def enhance_captcha_with_qwen(captcha_type: str, 
                            image_data: str, 
                            **kwargs) -> Optional[Any]:
    """
    便捷函数：使用千问增强验证码处理
    
    Args:
        captcha_type: 验证码类型 ('slide', 'image_text', 'click')
        image_data: 图片数据（base64编码）
        **kwargs: 其他参数
        
    Returns:
        处理结果，根据验证码类型不同而不同
    """
    processor = get_qwen_captcha_processor()
    
    if not processor.is_available:
        logger.info("千问处理器不可用，跳过AI增强处理")
        return None
    
    try:
        if captcha_type == 'slide':
            return processor.process_slide_captcha(image_data, kwargs.get('slider_image'))
        elif captcha_type == 'image_text':
            return processor.process_image_text_captcha(image_data)
        elif captcha_type == 'click':
            return processor.process_click_captcha(image_data, kwargs.get('instruction', ''))
        else:
            logger.warning(f"不支持的验证码类型: {captcha_type}")
            return None
            
    except Exception as e:
        logger.error(f"千问验证码增强处理失败: {e}")
        return None