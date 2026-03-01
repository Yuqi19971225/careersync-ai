# -*- coding: utf-8 -*-
"""浏览器自动化管理器：使用Selenium处理复杂的反爬虫机制"""

import logging
import time
import random
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from services.captcha_handler import get_captcha_manager

logger = logging.getLogger(__name__)


class BrowserAutomationManager:
    """浏览器自动化管理器"""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.is_initialized = False
        self.captcha_manager = get_captcha_manager()
        self._setup_driver()
    
    def _setup_driver(self):
        """设置Chrome驱动"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # 反爬虫相关配置
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 模拟真实用户代理
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 禁用图片加载提高速度（可选）
            # chrome_options.add_argument('--blink-settings=imagesEnabled=false')
            
            # 禁用JavaScript（谨慎使用，可能影响页面功能）
            # chrome_options.add_argument('--disable-javascript')
            
            # 设置窗口大小
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 禁用扩展
            chrome_options.add_argument('--disable-extensions')
            
            # 禁用信息栏
            chrome_options.add_argument('--disable-infobars')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 执行CDP命令隐藏webdriver特征
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    delete navigator.__proto__.webdriver;
                    window.chrome = {runtime: {}};
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                '''
            })
            
            self.driver.implicitly_wait(10)
            self.is_initialized = True
            logger.info("🌐 浏览器自动化已初始化")
            
        except Exception as e:
            logger.error("❌ 浏览器初始化失败: %s", e)
            self.is_initialized = False
    
    @contextmanager
    def get_driver(self):
        """获取浏览器驱动的上下文管理器"""
        if not self.is_initialized:
            self._setup_driver()
        
        if not self.driver:
            raise RuntimeError("浏览器驱动未初始化")
        
        try:
            yield self.driver
        finally:
            # 清理会话数据
            try:
                self.driver.delete_all_cookies()
            except:
                pass
    
    def wait_and_find_element(self, driver, locator, timeout=None):
        """等待并查找元素"""
        wait = WebDriverWait(driver, timeout or self.timeout)
        return wait.until(EC.presence_of_element_located(locator))
    
    def wait_and_find_elements(self, driver, locator, timeout=None):
        """等待并查找多个元素"""
        wait = WebDriverWait(driver, timeout or self.timeout)
        return wait.until(EC.presence_of_all_elements_located(locator))
    
    def human_like_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """模拟人类操作延迟"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def scroll_page(self, driver, scrolls: int = 3):
        """滚动页面模拟用户行为"""
        for i in range(scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.human_like_delay(0.5, 1.5)
            driver.execute_script("window.scrollTo(0, 0);")
            self.human_like_delay(0.5, 1.0)
    
    def handle_captcha_if_present(self, driver) -> bool:
        """处理验证码（集成完整解决方案）"""
        try:
            logger.info("🤖 开始处理页面验证码...")
            captcha_handled = self.captcha_manager.handle_captcha(driver)
            
            if captcha_handled:
                logger.info("✅ 验证码处理完成")
                # 给页面一些时间来验证和加载
                self.human_like_delay(3, 5)
                return True
            else:
                logger.info("ℹ️ 未检测到验证码或无需处理")
                return True
                
        except Exception as e:
            logger.warning("验证码处理出错: %s", e)
            return False
    
    def get_page_source(self, url: str, wait_for_element: Optional[str] = None) -> Optional[str]:
        """获取页面源码"""
        if not self.is_initialized:
            logger.error("浏览器未初始化")
            return None
        
        try:
            with self.get_driver() as driver:
                logger.info("🧭 访问页面: %s", url)
                driver.get(url)
                
                # 模拟人类浏览行为
                self.human_like_delay(2, 4)
                self.scroll_page(driver, 2)
                
                # 等待特定元素加载（如果指定了）
                if wait_for_element:
                    try:
                        self.wait_and_find_element(driver, (By.CSS_SELECTOR, wait_for_element))
                    except TimeoutException:
                        logger.warning("等待元素超时: %s", wait_for_element)
                
                # 处理验证码
                if not self.handle_captcha_if_present(driver):
                    logger.warning("验证码处理失败")
                    return None
                
                # 获取页面源码
                page_source = driver.page_source
                logger.debug("📄 成功获取页面源码，长度: %d", len(page_source))
                return page_source
                
        except WebDriverException as e:
            logger.error("WebDriver错误: %s", e)
            return None
        except Exception as e:
            logger.error("获取页面源码失败: %s", e)
            return None
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🌐 浏览器已关闭")
            except Exception as e:
                logger.warning("关闭浏览器时出错: %s", e)
            finally:
                self.driver = None
                self.is_initialized = False


# 全局浏览器管理器实例
browser_manager = BrowserAutomationManager(headless=True)


def get_browser_manager() -> BrowserAutomationManager:
    """获取浏览器管理器实例"""
    return browser_manager


def get_page_with_browser(url: str, wait_for_element: Optional[str] = None) -> Optional[str]:
    """便捷函数：使用浏览器获取页面"""
    return browser_manager.get_page_source(url, wait_for_element)