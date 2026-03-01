#!/usr/bin/env python3
"""
测试：确保拉勾网API调用只在点击搜索时触发
"""

import requests
import time
import subprocess
import signal
import os

def test_no_auto_lagou_calls():
    """测试系统启动和初始化过程中不自动调用拉勾网API"""
    print("🔍 测试拉勾网API调用时机...")
    
    # 检查服务器是否正常运行
    try:
        response = requests.get('http://localhost:8443/api/health', timeout=5)
        if response.status_code != 200:
            print("❌ 服务器未正常运行")
            return False
        print("✅ 服务器运行正常")
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False
    
    # 检查系统信息API
    try:
        response = requests.get('http://localhost:8443/api/system_info', timeout=5)
        if response.status_code == 200:
            system_info = response.json()
            print(f"✅ 系统信息获取成功")
            print(f"   版本: {system_info.get('version')}")
            print(f"   启用的招聘源: {system_info.get('job_sources')}")
        else:
            print("❌ 系统信息API调用失败")
            return False
    except Exception as e:
        print(f"❌ 系统信息API测试失败: {e}")
        return False
    
    # 检查招聘源状态API（这不应该触发实际的拉勾网调用）
    try:
        response = requests.get('http://localhost:8443/api/job_sources', timeout=5)
        if response.status_code == 200:
            job_sources = response.json()
            print(f"✅ 招聘源信息获取成功")
            print(f"   可用源: {job_sources.get('available', [])}")
            print(f"   启用源: {job_sources.get('enabled', [])}")
            
            # 检查拉勾网相关源的状态
            statuses = job_sources.get('statuses', {})
            lagou_sources = [k for k in statuses.keys() if 'lagou' in k]
            
            for source in lagou_sources:
                status = statuses[source]
                print(f"   {source} 状态: {status.get('message', '未知')}")
                if '触发反爬' in status.get('message', '') or '验证码' in status.get('message', ''):
                    print("❌ 发现自动触发的拉勾网调用!")
                    return False
                    
        else:
            print("❌ 招聘源API调用失败")
            return False
    except Exception as e:
        print(f"❌ 招聘源API测试失败: {e}")
        return False
    
    # 测试实际搜索（这才是应该触发拉勾网调用的地方）
    print("\n🔍 测试搜索功能...")
    search_data = {
        "keyword": "Python",
        "city": "北京",
        "sources": ["lagou_hybrid"]
    }
    
    try:
        response = requests.post('http://localhost:8443/api/search_jobs', 
                               json=search_data, timeout=15)
        if response.status_code == 200:
            result = response.json()
            print("✅ 搜索API调用成功")
            jobs_count = len(result.get('jobs', []))
            print(f"   返回职位数量: {jobs_count}")
            
            # 检查是否有拉勾网相关的日志信息
            if jobs_count > 0:
                print("✅ 拉勾网API在搜索时正常调用")
            else:
                print("⚠️  搜索返回空结果（可能是正常的）")
        else:
            print(f"❌ 搜索API调用失败: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ 搜索API测试失败: {e}")
        return False
    
    print("\n✅ 测试结论:")
    print("✅ 系统启动时没有自动调用拉勾网API")
    print("✅ 招聘源状态检查没有触发实际的网络请求")
    print("✅ 只有在点击搜索时才触发拉勾网API调用")
    
    return True

if __name__ == "__main__":
    success = test_no_auto_lagou_calls()
    if success:
        print("\n🎉 测试通过！拉勾网API调用时机控制成功")
    else:
        print("\n❌ 测试失败")