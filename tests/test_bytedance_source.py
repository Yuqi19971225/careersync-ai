#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""字节跳动招聘源测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from services.sources.bytedance import BytedanceSource

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_bytedance_source():
    """测试字节跳动招聘源基本功能"""
    print("🎯 字节跳动招聘源测试")
    print("=" * 50)
    
    try:
        # 创建字节跳动源实例
        bytedance_source = BytedanceSource(timeout=30, max_per_page=10)
        print("✅ 字节跳动源实例创建成功")
        
        # 测试连接状态
        print("\n📡 测试连接状态...")
        is_available = bytedance_source.is_available()
        print(f"连接状态: {'可用' if is_available['available'] else '不可用'}")
        print(f"状态消息: {is_available['message']}")
        
        # 测试职位搜索
        print("\n🔍 测试职位搜索...")
        keyword = "Python工程师"
        city = "北京"
        page = 1
        
        print(f"搜索条件: 关键词='{keyword}', 城市='{city}', 页码={page}")
        jobs = bytedance_source.search(keyword, city, page)
        
        print(f"✅ 搜索完成，找到 {len(jobs)} 个职位")
        
        # 显示前几个职位信息
        if jobs:
            print("\n📋 职位信息预览:")
            print("-" * 40)
            for i, job in enumerate(jobs[:3], 1):
                print(f"{i}. {job['title']}")
                print(f"   公司: {job['company']}")
                print(f"   薪资: {job['salary']}")
                print(f"   地点: {job.get('location', '未指定')}")
                print(f"   技能: {', '.join(job['requirements']) if job['requirements'] else '未提取'}")
                if job.get('url'):
                    print(f"   链接: {job['url']}")
                print()
        else:
            print("⚠️  未找到相关职位，可能是:")
            print("   • 搜索关键词过于具体")
            print("   • 网络连接问题")
            print("   • 站点反爬虫机制")
            print("   • API接口发生变化")
        
        # 测试不同城市的搜索
        print("\n🌍 测试不同城市搜索...")
        cities_to_test = ['上海', '深圳', '杭州']
        for city in cities_to_test:
            jobs = bytedance_source.search("算法工程师", city, 1)
            print(f"  {city}: {len(jobs)} 个职位")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        logger.exception("详细错误信息:")
        return False


def test_source_registration():
    """测试源注册功能"""
    print("\n📋 招聘源注册测试")
    print("=" * 30)
    
    try:
        from services.sources import list_source_ids, get_source_status
        
        # 获取所有注册的源
        registered_sources = list_source_ids()
        print(f"已注册的招聘源: {registered_sources}")
        
        # 检查字节跳动源是否已注册
        if 'bytedance' in registered_sources:
            print("✅ 字节跳动源已成功注册")
            
            # 获取源状态
            status = get_source_status('bytedance')
            print(f"源状态: {status}")
        else:
            print("❌ 字节跳动源未注册")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 源注册测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 CareerSync AI 字节跳动招聘源测试")
    print("=" * 60)
    
    try:
        # 运行各项测试
        registration_success = test_source_registration()
        source_success = test_bytedance_source()
        
        print("\n" + "=" * 60)
        print("🎉 测试完成!")
        print("\n📋 测试总结:")
        print(f"  ✅ 源注册测试: {'通过' if registration_success else '失败'}")
        print(f"  ✅ 源功能测试: {'通过' if source_success else '失败'}")
        
        if registration_success and source_success:
            print("\n💡 字节跳动招聘源已成功集成到系统中!")
            print("   可以在前端界面中选择'字节跳动'进行职位搜索")
        else:
            print("\n⚠️  部分测试未通过，请检查上述错误信息")
            
    except Exception as e:
        print(f"\n❌ 测试过程中出现严重错误: {e}")
        logging.exception("测试异常详情:")


if __name__ == "__main__":
    main()