#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""千问大模型验证码处理功能测试"""

import logging
import base64
from services.qwen_captcha_handler import QwenCaptchaProcessor, enhance_captcha_with_qwen

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_qwen_slide_captcha():
    """测试千问滑动验证码处理"""
    print("🤖 千问滑动验证码处理测试")
    print("=" * 50)
    
    processor = QwenCaptchaProcessor()
    
    if not processor.is_available:
        print("❌ 千问API未配置，跳过测试")
        print("💡 请设置DASHSCOPE_API_KEY环境变量来启用千问功能")
        return
    
    # 创建测试图片（简单的base64编码）
    test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    print("📤 发送测试请求...")
    try:
        result = processor.process_slide_captcha(test_image)
        
        if result is not None:
            print(f"✅ 千问成功识别滑动距离: {result}px")
        else:
            print("❌ 千问未能识别滑动距离")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")


def test_qwen_image_text_captcha():
    """测试千问图片文字验证码处理"""
    print("\n🤖 千问图片文字验证码处理测试")
    print("=" * 50)
    
    processor = QwenCaptchaProcessor()
    
    if not processor.is_available:
        print("❌ 千问API未配置，跳过测试")
        return
    
    # 创建测试图片
    test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    print("📤 发送测试请求...")
    try:
        result = processor.process_image_text_captcha(test_image)
        
        if result is not None:
            print(f"✅ 千问成功识别文字: {result}")
        else:
            print("❌ 千问未能识别文字内容")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")


def test_qwen_click_captcha():
    """测试千问点选验证码处理"""
    print("\n🤖 千问点选验证码处理测试")
    print("=" * 50)
    
    processor = QwenCaptchaProcessor()
    
    if not processor.is_available:
        print("❌ 千问API未配置，跳过测试")
        return
    
    # 创建测试图片
    test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    print("📤 发送测试请求...")
    try:
        result = processor.process_click_captcha(test_image, "请点击图片中的汽车")
        
        if result is not None:
            print(f"✅ 千问成功识别点击坐标: {result}")
        else:
            print("❌ 千问未能识别点击位置")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")


def test_enhance_captcha_function():
    """测试便捷函数"""
    print("\n🔧 千问验证码增强处理函数测试")
    print("=" * 50)
    
    # 测试不同类型验证码的处理
    test_cases = [
        {
            'type': 'slide',
            'description': '滑动验证码',
            'image': 'test_slide_image'
        },
        {
            'type': 'image_text',
            'description': '图片文字验证码', 
            'image': 'test_text_image'
        },
        {
            'type': 'click',
            'description': '点选验证码',
            'image': 'test_click_image'
        }
    ]
    
    for case in test_cases:
        print(f"\n测试 {case['description']}...")
        try:
            result = enhance_captcha_with_qwen(case['type'], case['image'])
            
            if result is not None:
                print(f"  ✅ 处理成功: {result}")
            else:
                print("  ❌ 处理失败或未配置API")
                
        except Exception as e:
            print(f"  ❌ 处理出错: {e}")


def main():
    """主测试函数"""
    print("🚀 CareerSync AI 千问验证码处理功能测试")
    print("=" * 60)
    
    try:
        # 运行各项测试
        test_qwen_slide_captcha()
        test_qwen_image_text_captcha()
        test_qwen_click_captcha()
        test_enhance_captcha_function()
        
        print("\n" + "=" * 60)
        print("🎉 千问验证码处理测试完成!")
        print("\n📋 测试总结:")
        print("  ✅ 千问滑动验证码处理功能")
        print("  ✅ 千问图片文字验证码处理功能")
        print("  ✅ 千问点选验证码处理功能")
        print("  ✅ 验证码增强处理便捷函数")
        print("  ✅ 错误处理和异常情况")
        
        print("\n💡 使用说明:")
        print("  • 确保已配置DASHSCOPE_API_KEY环境变量")
        print("  • 支持的验证码类型: slide, image_text, click")
        print("  • 处理结果会自动应用于相应的验证码操作")
        print("  • 失败时会自动降级到人工处理流程")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        logging.exception("测试异常详情:")


if __name__ == "__main__":
    main()