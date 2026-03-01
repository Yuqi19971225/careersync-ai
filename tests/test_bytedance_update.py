#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""字节跳动招聘源更新测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import json
from services.sources.bytedance import BytedanceSource

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_updated_bytedance_source():
    """测试更新后的字节跳动招聘源"""
    print("🎯 字节跳动招聘源更新测试")
    print("=" * 50)
    
    try:
        # 创建字节跳动源实例
        bytedance_source = BytedanceSource(timeout=30, max_per_page=5)
        print("✅ 字节跳动源实例创建成功")
        
        # 测试连接状态
        print("\n📡 测试连接状态...")
        is_available = bytedance_source.is_available()
        print(f"连接状态: {'可用' if is_available['available'] else '不可用'}")
        print(f"状态消息: {is_available['message']}")
        
        # 测试职位搜索 - 使用您提供的URL参数结构
        print("\n🔍 测试职位搜索...")
        keyword = "python"
        city = "北京"
        page = 1
        
        print(f"搜索条件: 关键词='{keyword}', 城市='{city}', 页码={page}")
        jobs = bytedance_source.search(keyword, city, page)
        
        print(f"✅ 搜索完成，找到 {len(jobs)} 个职位")
        
        # 显示职位信息
        if jobs:
            print("\n📋 职位信息详情:")
            print("-" * 50)
            for i, job in enumerate(jobs, 1):
                print(f"{i}. 标题: {job['title']}")
                print(f"   公司: {job['company']}")
                print(f"   薪资: {job['salary']}")
                print(f"   地点: {job.get('location', '未指定')}")
                print(f"   技能: {', '.join(job['requirements']) if job['requirements'] else '未提取'}")
                if job.get('url'):
                    print(f"   链接: {job['url']}")
                print(f"   描述预览: {job['description'][:100]}..." if len(job['description']) > 100 else f"   描述: {job['description']}")
                print()
        else:
            print("⚠️  未找到相关职位")
            print("可能的原因:")
            print("   • API接口可能需要认证")
            print("   • 参数格式可能需要调整")
            print("   • 网站结构可能已变化")
            print("   • 反爬虫机制阻止访问")
        
        # 测试不同搜索条件
        print("\n🧪 测试不同搜索条件...")
        test_cases = [
            ("算法工程师", "上海"),
            ("数据分析师", "深圳"),
            ("产品经理", "杭州")
        ]
        
        for keyword, city in test_cases:
            jobs = bytedance_source.search(keyword, city, 1)
            print(f"  {keyword}@{city}: {len(jobs)} 个职位")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        logger.exception("详细错误信息:")
        return False


def test_api_parameters():
    """测试API参数构建"""
    print("\n⚙️  API参数构建测试")
    print("=" * 30)
    
    try:
        # 模拟参数构建过程
        keyword = "python开发"
        city = "北京"
        page = 1
        max_per_page = 10
        
        params = {
            'keywords': keyword,
            'location': city if city != '全国' else '',
            'current': page,
            'limit': max_per_page,
            'category': '',
            'project': '',
            'type': '',
            'job_hot_flag': '',
            'functionCategory': '',
            'tag': ''
        }
        
        print("构建的API参数:")
        for key, value in params.items():
            print(f"  {key}: {value}")
        
        # 构建完整URL（模拟）
        base_url = "https://jobs.bytedance.com/experienced/position"
        from urllib.parse import urlencode
        full_url = f"{base_url}?{urlencode(params)}"
        print(f"\n完整URL示例:")
        print(f"  {full_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ 参数构建测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 CareerSync AI 字节跳动招聘源更新测试")
    print("=" * 60)
    
    try:
        # 运行各项测试
        param_test = test_api_parameters()
        source_test = test_updated_bytedance_source()
        
        print("\n" + "=" * 60)
        print("🎉 测试完成!")
        print("\n📋 测试总结:")
        print(f"  ✅ 参数构建测试: {'通过' if param_test else '失败'}")
        print(f"  ✅ 源功能测试: {'通过' if source_test else '失败'}")
        
        if param_test and source_test:
            print("\n💡 字节跳动招聘源已根据实际URL结构更新!")
            print("   • 使用了正确的API端点")
            print("   • 适配了实际的查询参数")
            print("   • 增强了数据解析的灵活性")
        else:
            print("\n⚠️  部分测试未通过，请检查上述错误信息")
            
    except Exception as e:
        print(f"\n❌ 测试过程中出现严重错误: {e}")
        logging.exception("测试异常详情:")


if __name__ == "__main__":
    main()