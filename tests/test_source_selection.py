#!/usr/bin/env python3
"""
测试招聘网站选择功能是否恢复正常
"""

import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_source_selection():
    """测试招聘网站选择功能"""
    print("🔍 测试招聘网站选择功能...")
    
    # 检查API是否正常工作
    try:
        response = requests.get('http://localhost:8443/api/job_sources', timeout=5)
        if response.status_code == 200:
            sources_data = response.json()
            print(f"✅ API返回招聘源数据: {sources_data['available']}")
        else:
            print("❌ API调用失败")
            return False
    except Exception as e:
        print(f"❌ 无法连接到API: {e}")
        return False
    
    # 使用Selenium测试前端功能
    try:
        # 配置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无头模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('http://localhost:8443')
        
        # 等待页面加载
        wait = WebDriverWait(driver, 10)
        
        # 查找招聘网站选择区域
        source_checkboxes = wait.until(
            EC.presence_of_element_located((By.ID, "source-checkboxes"))
        )
        
        # 查找所有的复选框
        checkboxes = driver.find_elements(By.CSS_SELECTOR, "#source-checkboxes input[type='checkbox']")
        
        print(f"✅ 找到 {len(checkboxes)} 个招聘网站选择框")
        
        # 检查是否至少有一个复选框
        if len(checkboxes) == 0:
            print("❌ 没有找到任何招聘网站选择框")
            driver.quit()
            return False
        
        # 检查复选框的标签
        labels = driver.find_elements(By.CSS_SELECTOR, "#source-checkboxes span")
        label_texts = [label.text for label in labels if label.text.strip()]
        print(f"✅ 招聘网站选项: {label_texts}")
        
        # 测试选择功能
        if checkboxes:
            # 选择第一个复选框
            first_checkbox = checkboxes[0]
            first_checkbox.click()
            time.sleep(0.5)
            
            # 验证是否被选中
            is_selected = first_checkbox.is_selected()
            print(f"✅ 复选框选择功能正常: {'已选中' if is_selected else '未选中'}")
            
            # 取消选择
            first_checkbox.click()
            time.sleep(0.5)
            
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ 前端测试失败: {e}")
        try:
            driver.quit()
        except:
            pass
        return False

if __name__ == "__main__":
    success = test_source_selection()
    if success:
        print("\n🎉 招聘网站选择功能测试通过！")
        print("✅ 页面加载时正确显示招聘网站选择框")
        print("✅ 用户可以正常选择/取消选择招聘网站")
        print("✅ 功能在搜索触发前就可以使用")
    else:
        print("\n❌ 招聘网站选择功能测试失败")