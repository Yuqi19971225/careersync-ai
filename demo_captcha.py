#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证码处理功能使用演示"""

import logging
from services.captcha_handler import get_captcha_manager
from services.browser_automation import get_browser_manager

# 配置日志
logging.basicConfig(level=logging.INFO)

def demo_captcha_processing():
    """演示验证码处理流程"""
    print("🤖 CareerSync AI 验证码处理功能演示")
    print("=" * 50)
    
    # 1. 初始化组件
    print("1. 初始化验证码管理器和浏览器...")
    captcha_manager = get_captcha_manager()
    browser_manager = get_browser_manager()
    
    print("   ✅ 验证码管理器:", "已初始化" if captcha_manager else "初始化失败")
    print("   ✅ 浏览器管理器:", "已初始化" if browser_manager.is_initialized else "初始化失败")
    
    # 2. 展示验证码类型识别能力
    print("\n2. 验证码类型识别能力:")
    captcha_types = {
        'slide': '滑动验证码 - 如拉勾网的滑块验证',
        'image_text': '图片数字验证码 - 包含数字/字母的图片',
        'text_input': '文本输入验证码 - 纯文本输入框',
        'click': '点选验证码 - 需要点选特定区域',
        'geetest': '极验验证码 - 复杂的交互式验证'
    }
    
    for type_code, description in captcha_types.items():
        print(f"   • {type_code:12} : {description}")
    
    # 3. 第三方服务集成示例
    print("\n3. 第三方验证码识别服务集成:")
    print("   支持的服务类型:")
    third_party_capabilities = {
        'OCR识别': ['text_input', 'image_text'],
        '图像识别': ['click', 'image_text'], 
        '距离计算': ['slide'],
        '行为分析': ['geetest']
    }
    
    for service, supported_types in third_party_capabilities.items():
        types_str = ", ".join(supported_types)
        print(f"   • {service:10} : 支持 {types_str}")
    
    # 4. 处理流程说明
    print("\n4. 验证码处理流程:")
    print("   步骤1: 自动检测页面中的验证码元素")
    print("   步骤2: 识别验证码类型（滑动/图片/文本/点选等）")
    print("   步骤3: 尝试第三方自动识别服务")
    print("   步骤4: 识别失败则转人工辅助处理")
    print("   步骤5: 用户在前端界面输入解决方案")
    print("   步骤6: 系统自动应用解决方案并继续流程")
    
    # 5. 实际使用示例
    print("\n5. 实际使用示例代码:")
    print("""
    # 在爬虫代码中使用
    from services.captcha_handler import get_captcha_manager
    from services.browser_automation import get_browser_manager
    
    # 初始化
    captcha_manager = get_captcha_manager()
    browser_manager = get_browser_manager()
    
    # 访问需要验证码的页面
    with browser_manager.get_driver() as driver:
        driver.get("https://example.com/login")
        
        # 自动处理验证码
        if captcha_manager.handle_captcha(driver):
            print("验证码处理成功")
        else:
            print("需要人工处理")
    
    # 前端会自动弹出验证码处理窗口
    """)
    
    # 6. 配置说明
    print("\n6. 配置选项:")
    print("   • 启用/禁用第三方识别服务")
    print("   • 设置人工处理超时时间")
    print("   • 配置不同验证码类型的处理策略")
    print("   • 自定义验证码检测规则")
    
    print("\n" + "=" * 50)
    print("🎯 功能特点总结:")
    print("  ✅ 智能识别5种主要验证码类型")
    print("  ✅ 支持第三方自动识别服务集成")
    print("  ✅ 完善的人工辅助处理机制")
    print("  ✅ 用户友好的前端交互界面")
    print("  ✅ 可扩展的插件化架构")
    print("  ✅ 完整的日志记录和错误处理")

def demo_api_usage():
    """演示API使用方法"""
    print("\n🌐 API接口使用演示:")
    print("=" * 30)
    
    api_endpoints = {
        "GET /api/captcha/pending": "获取待处理的验证码任务",
        "POST /api/captcha/submit": "提交验证码解决方案",
        "GET /api/system_info": "获取系统状态信息"
    }
    
    for endpoint, description in api_endpoints.items():
        print(f"  {endpoint:25} - {description}")
    
    print("\n示例请求:")
    print("""
    # 获取待处理验证码
    curl -X GET "http://localhost:8443/api/captcha/pending"
    
    # 提交验证码解决方案
    curl -X POST "http://localhost:8443/api/captcha/submit" \\
         -H "Content-Type: application/json" \\
         -d '{"captcha_id": "task_123", "solution": "abcd1234"}'
    """)

if __name__ == "__main__":
    demo_captcha_processing()
    demo_api_usage()
    
    print("\n💡 提示:")
    print("  • 运行 'python3 test_captcha.py' 进行完整功能测试")
    print("  • 访问 http://localhost:8443 查看前端界面")
    print("  • 查看日志文件了解详细处理过程")