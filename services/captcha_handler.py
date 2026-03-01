# -*- coding: utf-8 -*-
"""验证码识别服务：集成第三方识别API和人工辅助验证"""

import logging
import base64
import io
import time
from typing import Optional, Dict, Any, Tuple
from abc import ABC, abstractmethod

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException

logger = logging.getLogger(__name__)

# AI支持检测
try:
    from .ai_captcha_handler import EnhancedSlideCaptchaHandler
    AI_SUPPORT_AVAILABLE = True
    logger.info("✅ AI验证码支持可用")
except ImportError as e:
    AI_SUPPORT_AVAILABLE = False
    logger.info(f"ℹ️ AI验证码支持不可用: {e}")

# 千问大模型支持检测
try:
    from .qwen_captcha_handler import get_qwen_captcha_processor, enhance_captcha_with_qwen
    QWEN_SUPPORT_AVAILABLE = True
    logger.info("✅ 千问验证码支持可用")
except ImportError as e:
    QWEN_SUPPORT_AVAILABLE = False
    logger.info(f"ℹ️ 千问验证码支持不可用: {e}")


class CaptchaSolver(ABC):
    """验证码解决器抽象基类"""
    
    @abstractmethod
    def solve_captcha(self, driver: WebDriver, captcha_element) -> bool:
        """解决验证码"""
        pass
    
    @abstractmethod
    def is_supported(self, captcha_type: str) -> bool:
        """检查是否支持某种验证码类型"""
        pass


class ManualCaptchaSolver(CaptchaSolver):
    """人工验证码解决器"""
    
    def __init__(self):
        self.pending_captchas = {}  # 存储待处理的验证码任务
    
    def solve_captcha(self, driver: WebDriver, captcha_element) -> bool:
        """解决验证码 - 先尝试千问AI，再尝试传统AI，最后人工处理"""
        captcha_id = f"captcha_{int(time.time() * 1000)}"
        
        # 获取验证码图片和类型
        try:
            captcha_image = self._extract_captcha_image(captcha_element)
            captcha_type = self._detect_captcha_type(captcha_element)
            
            if not captcha_image:
                logger.warning("无法提取验证码图片")
                return False
                
            logger.info(f"🔄 开始处理 {captcha_type} 类型验证码 (ID: {captcha_id})")
            
            # 1. 首先尝试千问大模型处理
            if QWEN_SUPPORT_AVAILABLE:
                logger.info("🤖 尝试使用千问大模型处理验证码...")
                qwen_result = self._try_qwen_processing(captcha_type, captcha_image, driver, captcha_element)
                if qwen_result:
                    logger.info("✅ 千问大模型处理成功")
                    return True
                else:
                    logger.info("❌ 千问大模型处理失败，尝试其他方法")
            
            # 2. 尝试传统AI处理（仅限滑动验证码）
            if AI_SUPPORT_AVAILABLE and captcha_type == 'slide':
                logger.info("🧠 尝试使用传统AI处理滑动验证码...")
                ai_result = self._try_ai_processing(driver, captcha_element, captcha_image)
                if ai_result:
                    logger.info("✅ 传统AI处理成功")
                    return True
                else:
                    logger.info("❌ 传统AI处理失败，转人工处理")
            
            # 3. 最后转人工处理
            logger.info("👤 转入人工处理流程")
            return self._handle_manual_processing(driver, captcha_element, captcha_image, captcha_type, captcha_id)
            
        except Exception as e:
            logger.error(f"验证码处理流程出错: {e}")
            return False
    
    def _extract_captcha_image(self, captcha_element) -> Optional[str]:
        """提取验证码图片（整个验证码区域）"""
        try:
            # 获取验证码容器元素（不仅仅是滑块）
            captcha_container = self._find_captcha_container(captcha_element)
            
            if captcha_container:
                # 截图整个验证码容器
                screenshot = captcha_container.screenshot_as_base64
                logger.debug("已截图整个验证码容器")
                return screenshot
            else:
                # 降级到原始元素截图
                screenshot = captcha_element.screenshot_as_base64
                logger.debug("截图原始验证码元素")
                return screenshot
            
        except Exception as e:
            logger.warning("提取验证码图片失败: %s", e)
            return None
    
    def _try_qwen_processing(self, captcha_type: str, image_data: str, 
                           driver: WebDriver, element) -> bool:
        """尝试使用千问大模型处理验证码"""
        try:
            # 使用千问处理器
            result = enhance_captcha_with_qwen(captcha_type, image_data)
            
            if result is None:
                return False
            
            # 根据不同类型应用结果
            if captcha_type == 'slide' and isinstance(result, int):
                # 滑动验证码：执行滑动操作
                return self._execute_slide_action(driver, element, result)
            elif captcha_type == 'image_text' and isinstance(result, str):
                # 图片文字验证码：输入识别结果
                return self._solve_image_text_captcha(driver, element, result)
            elif captcha_type == 'click' and isinstance(result, list):
                # 点选验证码：执行点击操作
                return self._solve_click_captcha(driver, element, ';'.join([f"{x},{y}" for x, y in result]))
            else:
                logger.warning(f"千问处理结果类型不匹配: {type(result)}")
                return False
                
        except Exception as e:
            logger.error(f"千问验证码处理失败: {e}")
            return False
    
    def _try_ai_processing(self, driver: WebDriver, element, image_data: str) -> bool:
        """尝试使用传统AI处理滑动验证码"""
        try:
            # 这里可以集成原有的AI处理逻辑
            # 暂时返回False，让人工处理
            return False
        except Exception as e:
            logger.error(f"传统AI处理失败: {e}")
            return False
    
    def _handle_manual_processing(self, driver: WebDriver, element, 
                                image_data: str, captcha_type: str, captcha_id: str) -> bool:
        """处理人工验证码流程"""
        try:
            # 存储验证码任务供人工处理
            self.pending_captchas[captcha_id] = {
                'driver': driver,
                'element': element,
                'image': image_data,
                'type': captcha_type,
                'timestamp': time.time()
            }
            
            logger.info(f"👤 验证码需要人工处理，ID: {captcha_id}")
            return False  # 需要人工干预
            
        except Exception as e:
            logger.error(f"人工处理流程设置失败: {e}")
            return False
    
    def _execute_slide_action(self, driver: WebDriver, element, distance: int) -> bool:
        """执行滑动操作"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            import random
            
            # 找到滑块元素
            slider = element.find_element(By.CLASS_NAME, 'nc-lang-cnt')
            if not slider:
                return False
            
            # 模拟拖拽动作
            action = ActionChains(driver)
            action.click_and_hold(slider)
            
            # 分段滑动模拟人工
            steps = 15
            for i in range(steps):
                vertical_move = random.randint(-2, 2)
                action.move_by_offset(distance // steps, vertical_move)
                action.pause(random.uniform(0.02, 0.08))
            
            action.release()
            action.perform()
            
            time.sleep(2)  # 等待验证结果
            return True
            
        except Exception as e:
            logger.error(f"滑动操作执行失败: {e}")
            return False
    
    def _find_captcha_container(self, slider_element):
        """查找包含整个验证码的容器元素"""
        try:
            from selenium.webdriver.common.by import By
            
            # 方法1: 查找父级容器
            parent = slider_element.find_element(By.XPATH, "./../..")
            
            # 检查是否包含典型的验证码容器特征
            container_classes = parent.get_attribute('class') or ''
            if ('nc-container' in container_classes or 
                'captcha' in container_classes or 
                'verify' in container_classes):
                return parent
            
            # 方法2: 查找兄弟元素中的背景图片容器
            siblings = parent.find_elements(By.XPATH, "./div")
            for sibling in siblings:
                style = sibling.get_attribute('style') or ''
                if 'background-image' in style and ('url(' in style):
                    return sibling
            
            # 方法3: 查找具有特定尺寸的祖先元素
            ancestor = parent
            for _ in range(3):  # 最多向上查找3层
                size = ancestor.size
                # 验证码容器通常有一定尺寸范围
                if 200 <= size['width'] <= 600 and 100 <= size['height'] <= 300:
                    return ancestor
                try:
                    ancestor = ancestor.find_element(By.XPATH, "./..")
                except:
                    break
            
            return parent  # 返回最合适的容器
            
        except Exception as e:
            logger.debug("查找验证码容器失败: %s", e)
            return None
    
    def _detect_captcha_type(self, captcha_element) -> str:
        """检测验证码类型"""
        try:
            classes = captcha_element.get_attribute('class') or ''
            element_tag = captcha_element.tag_name.lower()
            
            # 滑动验证码检测
            if ('nc-container' in classes or 
                'slidetounlock' in classes or 
                'slider' in classes or
                'drag' in classes):
                return 'slide'
            
            # 极验验证码检测
            elif 'geetest' in classes:
                return 'geetest'
            
            # 点选验证码检测
            elif ('click' in classes or 
                  'point' in classes or 
                  'select' in classes):
                return 'click'
            
            # 图片数字验证码检测
            elif ('captcha' in classes or 
                  'verify' in classes or 
                  'image-captcha' in classes or
                  captcha_element.find_elements(By.TAG_NAME, 'img')):
                return 'image_text'
            
            # 文本输入验证码
            elif element_tag == 'input' and ('captcha' in element_tag or 'verify' in element_tag):
                return 'text_input'
            
            else:
                return 'unknown'
                
        except Exception as e:
            logger.debug("验证码类型检测失败: %s", e)
            return 'unknown'
    
    def is_supported(self, captcha_type: str) -> bool:
        """人工解决器支持所有类型"""
        return True
    
    def get_pending_captchas(self) -> Dict[str, Any]:
        """获取待处理的验证码任务（包含额外的验证码信息）"""
        # 清理过期的任务（超过5分钟）
        current_time = time.time()
        expired_keys = [
            key for key, task in self.pending_captchas.items()
            if current_time - task['timestamp'] > 300
        ]
        for key in expired_keys:
            del self.pending_captchas[key]
        
        # 添加存储的验证码详细信息
        enhanced_captchas = self.pending_captchas.copy()
        
        # 如果有存储的验证码信息，合并到任务中
        if hasattr(self, '_captcha_storage'):
            for captcha_id, storage_info in self._captcha_storage.items():
                if captcha_id in enhanced_captchas:
                    # 合并详细信息
                    enhanced_captchas[captcha_id].update({
                        'captcha_images': storage_info.get('images', {}),
                        'captcha_solution': storage_info.get('solution', ''),
                        'enhanced_type': 'slide_with_images' if storage_info.get('type') == 'slide' else storage_info.get('type')
                    })
        
        return enhanced_captchas
    
    def submit_captcha_solution(self, captcha_id: str, solution: str) -> bool:
        """提交验证码解决方案"""
        if captcha_id not in self.pending_captchas:
            logger.warning("验证码任务不存在: %s", captcha_id)
            return False
        
        task = self.pending_captchas[captcha_id]
        try:
            # 根据验证码类型执行不同的操作
            if task['type'] == 'slide':
                return self._solve_slide_captcha(task['driver'], task['element'], solution)
            elif task['type'] == 'click':
                return self._solve_click_captcha(task['driver'], task['element'], solution)
            elif task['type'] == 'image_text':
                return self._solve_image_text_captcha(task['driver'], task['element'], solution)
            elif task['type'] == 'text_input':
                return self._solve_text_captcha(task['driver'], task['element'], solution)
            else:
                # 默认作为文本验证码处理
                return self._solve_text_captcha(task['driver'], task['element'], solution)
                
        except Exception as e:
            logger.error("提交验证码解决方案失败: %s", e)
            return False
        finally:
            # 删除已完成的任务
            if captcha_id in self.pending_captchas:
                del self.pending_captchas[captcha_id]
    
    def _solve_text_captcha(self, driver: WebDriver, element, solution: str) -> bool:
        """解决文本验证码"""
        try:
            element.clear()
            element.send_keys(solution)
            return True
        except Exception as e:
            logger.error("文本验证码输入失败: %s", e)
            return False
    
    def _solve_image_text_captcha(self, driver: WebDriver, element, solution: str) -> bool:
        """解决图片数字验证码"""
        try:
            # 查找验证码输入框
            input_field = None
            
            # 方法1: 查找相邻的输入框
            try:
                input_field = element.find_element(By.XPATH, "./following-sibling::input[@type='text']")
            except:
                pass
            
            # 方法2: 查找父元素下的输入框
            if not input_field:
                try:
                    parent = element.find_element(By.XPATH, "./..")
                    input_field = parent.find_element(By.TAG_NAME, "input")
                except:
                    pass
            
            # 方法3: 查找附近的输入框
            if not input_field:
                try:
                    input_fields = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                    # 选择距离最近的输入框
                    if input_fields:
                        input_field = input_fields[0]
                except:
                    pass
            
            if input_field:
                input_field.clear()
                input_field.send_keys(solution)
                logger.info("✅ 图片验证码答案已输入: %s", solution)
                return True
            else:
                logger.warning("❌ 未找到图片验证码对应的输入框")
                return False
                
        except Exception as e:
            logger.error("图片验证码处理失败: %s", e)
            return False
    
    def _solve_slide_captcha(self, driver: WebDriver, element, solution: str) -> bool:
        """解决滑动验证码（模拟人工滑动）"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            # 获取整个验证码容器用于前端展示
            captcha_container = self._find_captcha_container(element)
            container_element = captcha_container if captcha_container else element
            
            # 提取验证码背景图片和滑块图片
            captcha_data = self._extract_captcha_images(container_element)
            
            # 找到滑块元素
            slider = element.find_element(By.CLASS_NAME, 'nc-lang-cnt')
            if not slider:
                return False
            
            # 存储验证码信息供前端使用
            self._store_captcha_info(element, captcha_data, solution)
            
            # 模拟拖拽动作
            action = ActionChains(driver)
            action.click_and_hold(slider)
            
            # 根据solution值计算滑动距离
            distance = int(solution) if solution.isdigit() else 300
            
            # 分段滑动模拟人工
            steps = 15  # 增加步数使滑动更自然
            for i in range(steps):
                # 添加轻微的垂直抖动模拟真人操作
                vertical_move = random.randint(-2, 2)
                action.move_by_offset(distance // steps, vertical_move)
                action.pause(random.uniform(0.02, 0.08))
            
            action.release()
            action.perform()
            
            time.sleep(2)  # 等待验证结果
            return True
            
        except Exception as e:
            logger.error("滑动验证码解决失败: %s", e)
            return False
    
    def _extract_captcha_images(self, container_element) -> dict:
        """提取验证码的背景图片和滑块图片"""
        try:
            images = {}
            
            # 提取背景图片
            bg_style = container_element.value_of_css_property('background-image')
            if bg_style and 'url(' in bg_style:
                # 提取背景图片URL
                bg_url = bg_style.split('url("')[1].split('")')[0]
                images['background'] = bg_url
            
            # 查找滑块元素并提取其图片
            try:
                slider = container_element.find_element(By.CLASS_NAME, 'nc-lang-cnt')
                slider_bg = slider.value_of_css_property('background-image')
                if slider_bg and 'url(' in slider_bg:
                    slider_url = slider_bg.split('url("')[1].split('")')[0]
                    images['slider'] = slider_url
            except:
                pass
            
            # 截取整个容器图片
            images['full_captcha'] = container_element.screenshot_as_base64
            
            return images
            
        except Exception as e:
            logger.debug("提取验证码图片信息失败: %s", e)
            return {}
    
    def _store_captcha_info(self, element, captcha_data: dict, solution: str):
        """存储验证码信息供前端使用"""
        try:
            # 生成唯一ID
            captcha_id = f"slide_captcha_{int(time.time() * 1000)}"
            
            # 存储到全局存储中（实际项目中应该使用数据库或缓存）
            if not hasattr(self, '_captcha_storage'):
                self._captcha_storage = {}
            
            self._captcha_storage[captcha_id] = {
                'type': 'slide',
                'element': element,
                'images': captcha_data,
                'solution': solution,
                'timestamp': time.time()
            }
            
            logger.debug("已存储滑动验证码信息，ID: %s", captcha_id)
            
        except Exception as e:
            logger.debug("存储验证码信息失败: %s", e)
    
    def _solve_click_captcha(self, driver: WebDriver, element, solution: str) -> bool:
        """解决点选验证码"""
        try:
            # 解析坐标点 (格式: "x1,y1;x2,y2")
            points = solution.split(';')
            from selenium.webdriver.common.action_chains import ActionChains
            
            action = ActionChains(driver)
            
            for point_str in points:
                coords = point_str.split(',')
                if len(coords) == 2:
                    x, y = int(coords[0]), int(coords[1])
                    action.move_to_element_with_offset(element, x, y).click()
                    action.pause(0.5)
            
            action.perform()
            return True
            
        except Exception as e:
            logger.error("点选验证码解决失败: %s", e)
            return False


class ThirdPartyCaptchaSolver(CaptchaSolver):
    """第三方验证码识别服务"""
    
    def __init__(self, api_key: str = None, service: str = 'custom'):
        self.api_key = api_key
        self.service = service
        self.supported_types = ['text', 'click']  # 滑动验证码通常需要人工
        
    def solve_captcha(self, driver: WebDriver, captcha_element) -> bool:
        """使用第三方服务解决验证码"""
        try:
            captcha_type = self._detect_captcha_type(captcha_element)
            
            if not self.is_supported(captcha_type):
                logger.debug("第三方服务不支持此验证码类型: %s", captcha_type)
                return False
            
            # 提取验证码图片
            image_data = self._extract_captcha_image(captcha_element)
            if not image_data:
                return False
            
            # 调用第三方API识别
            solution = self._call_third_party_api(image_data, captcha_type)
            if not solution:
                return False
            
            # 应用解决方案
            return self._apply_solution(driver, captcha_element, solution, captcha_type)
            
        except Exception as e:
            logger.error("第三方验证码识别失败: %s", e)
            return False
    
    def _extract_captcha_image(self, captcha_element) -> Optional[str]:
        """提取验证码图片数据"""
        try:
            # 截图验证码元素
            screenshot = captcha_element.screenshot_as_base64
            return screenshot
        except Exception as e:
            logger.warning("提取验证码图片失败: %s", e)
            return None
    
    def _detect_captcha_type(self, captcha_element) -> str:
        """检测验证码类型"""
        try:
            classes = captcha_element.get_attribute('class') or ''
            if 'nc-container' in classes:
                return 'slide'
            elif 'geetest' in classes:
                return 'geetest'
            else:
                return 'text'  # 默认文本验证码
        except Exception:
            return 'text'
    
    def _call_third_party_api(self, image_data: str, captcha_type: str) -> Optional[str]:
        """调用第三方验证码识别API"""
        # 这里可以集成具体的第三方服务
        # 如：打码平台、云打码等
        
        logger.debug("调用第三方验证码识别API，类型: %s", captcha_type)
        
        # 根据验证码类型调用不同的识别方法
        if captcha_type in ['text_input', 'image_text']:
            # OCR文字识别
            return self._ocr_recognition(image_data)
        elif captcha_type == 'click':
            # 图像识别，返回坐标
            return self._image_recognition(image_data)
        elif captcha_type == 'slide':
            # 滑动距离计算
            return self._slide_distance_calculation(image_data)
        
        return None  # 不支持的类型
    
    def _ocr_recognition(self, image_data: str) -> Optional[str]:
        """OCR文字识别"""
        # 模拟OCR识别结果
        import random
        fake_results = ['abcd', '1234', 'xyz9', 'hello', '5678', 'test']
        result = random.choice(fake_results)
        logger.debug("OCR识别结果: %s", result)
        return result
    
    def _image_recognition(self, image_data: str) -> Optional[str]:
        """图像识别（返回点击坐标）"""
        # 模拟图像识别结果（返回坐标格式："x1,y1;x2,y2"）
        import random
        x1, y1 = random.randint(50, 150), random.randint(50, 150)
        x2, y2 = random.randint(200, 300), random.randint(200, 300)
        result = f"{x1},{y1};{x2},{y2}"
        logger.debug("图像识别结果: %s", result)
        return result
    
    def _slide_distance_calculation(self, image_data: str) -> Optional[str]:
        """滑动距离计算"""
        # 模拟滑动距离计算结果
        import random
        distance = random.randint(200, 400)
        result = str(distance)
        logger.debug("滑动距离计算结果: %s", result)
        return result
    
    def _apply_solution(self, driver: WebDriver, element, solution: str, captcha_type: str) -> bool:
        """应用验证码解决方案"""
        try:
            if captcha_type == 'text':
                element.clear()
                element.send_keys(solution)
                return True
            else:
                # 其他类型需要特殊处理
                return False
        except Exception as e:
            logger.error("应用验证码解决方案失败: %s", e)
            return False
    
    def is_supported(self, captcha_type: str) -> bool:
        """检查是否支持该验证码类型"""
        return captcha_type in self.supported_types


class CaptchaManager:
    """验证码管理器"""
    
    def __init__(self):
        self.manual_solver = ManualCaptchaSolver()
        self.third_party_solver = None
        self.use_third_party = False
        
    def enable_third_party(self, api_key: str, service: str = 'custom'):
        """启用第三方验证码识别服务"""
        self.third_party_solver = ThirdPartyCaptchaSolver(api_key, service)
        self.use_third_party = True
        logger.info("已启用第三方验证码识别服务: %s", service)
    
    def disable_third_party(self):
        """禁用第三方验证码识别服务"""
        self.third_party_solver = None
        self.use_third_party = False
        logger.info("已禁用第三方验证码识别服务")
    
    def handle_captcha(self, driver: WebDriver) -> bool:
        """处理页面上的验证码"""
        try:
            # 检测并处理各种类型的验证码
            captcha_handlers = [
                self._handle_slide_captcha,
                self._handle_text_captcha,
                self._handle_geetest_captcha,
                self._handle_click_captcha
            ]
            
            for handler in captcha_handlers:
                if handler(driver):
                    return True
                    
            return False  # 未发现验证码或处理失败
            
        except Exception as e:
            logger.error("验证码处理出错: %s", e)
            return False
    
    def _handle_slide_captcha(self, driver: WebDriver) -> bool:
        """处理滑动验证码"""
        try:
            slide_elements = driver.find_elements(By.CLASS_NAME, "nc-container")
            if not slide_elements:
                return False
            
            for element in slide_elements:
                # 优先使用第三方服务
                if (self.use_third_party and self.third_party_solver and
                    self.third_party_solver.solve_captcha(driver, element)):
                    logger.info("✅ 第三方服务成功解决滑动验证码")
                    return True
                
                # 降级到人工处理
                if not self.manual_solver.solve_captcha(driver, element):
                    logger.info("🔄 滑动验证码需要人工处理")
                    return True  # 返回True表示已检测到验证码
                    
            return False
            
        except Exception as e:
            logger.debug("滑动验证码处理失败: %s", e)
            return False
    
    def _handle_text_captcha(self, driver: WebDriver) -> bool:
        """处理文本验证码"""
        try:
            # 查找常见的文本验证码元素
            selectors = [
                'input[placeholder*="验证码"]',
                '.captcha-input',
                '#captcha',
                '[name*="captcha"]'
            ]
            
            for selector in selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        # 优先使用第三方服务
                        if (self.use_third_party and self.third_party_solver and
                            self.third_party_solver.solve_captcha(driver, element)):
                            logger.info("✅ 第三方服务成功解决文本验证码")
                            return True
                        
                        # 降级到人工处理
                        if not self.manual_solver.solve_captcha(driver, element):
                            logger.info("🔄 文本验证码需要人工处理")
                            return True
            
            return False
            
        except Exception as e:
            logger.debug("文本验证码处理失败: %s", e)
            return False
    
    def _handle_geetest_captcha(self, driver: WebDriver) -> bool:
        """处理极验验证码"""
        try:
            geetest_elements = driver.find_elements(By.CLASS_NAME, "geetest_panel")
            if not geetest_elements:
                return False
            
            for element in geetest_elements:
                if not self.manual_solver.solve_captcha(driver, element):
                    logger.info("🔄 极验验证码需要人工处理")
                    return True
                    
            return False
            
        except Exception as e:
            logger.debug("极验验证码处理失败: %s", e)
            return False
    
    def _handle_click_captcha(self, driver: WebDriver) -> bool:
        """处理点选验证码"""
        try:
            click_elements = driver.find_elements(By.CLASS_NAME, "click-captcha")
            if not click_elements:
                return False
            
            for element in click_elements:
                if not self.manual_solver.solve_captcha(driver, element):
                    logger.info("🔄 点选验证码需要人工处理")
                    return True
                    
            return False
            
        except Exception as e:
            logger.debug("点选验证码处理失败: %s", e)
            return False
    
    def get_pending_captchas(self) -> Dict[str, Any]:
        """获取待处理的验证码任务"""
        return self.manual_solver.get_pending_captchas()
    
    def submit_captcha_solution(self, captcha_id: str, solution: str) -> bool:
        """提交验证码解决方案"""
        return self.manual_solver.submit_captcha_solution(captcha_id, solution)


# 全局验证码管理器实例
captcha_manager = CaptchaManager()


# AI增强验证码处理功能
class AICaptchaEnhancement:
    """AI验证码增强处理"""
    
    def __init__(self):
        self.ai_handler = None
        self.ai_available = False
        self._init_ai_support()
    
    def _init_ai_support(self):
        """初始化AI支持"""
        try:
            if AI_SUPPORT_AVAILABLE:
                from .ai_captcha_handler import EnhancedSlideCaptchaHandler
                self.ai_handler = EnhancedSlideCaptchaHandler()
                self.ai_available = True
                logger.info("✅ AI验证码支持已启用")
            else:
                logger.info("ℹ️ AI验证码支持不可用")
        except Exception as e:
            logger.warning(f"AI验证码初始化失败: {e}")
            self.ai_available = False
    
    def enhance_slide_captcha_processing(self, driver: WebDriver, 
                                       captcha_element, 
                                       background_image_path: str) -> bool:
        """
        使用AI增强滑动验证码处理
        
        Args:
            driver: WebDriver实例
            captcha_element: 验证码元素
            background_image_path: 背景图片路径
            
        Returns:
            处理是否成功
        """
        if not self.ai_available or not self.ai_handler:
            logger.info("🤖 AI支持不可用，使用传统方法")
            return False
        
        try:
            logger.info("🤖 启动AI滑动验证码处理...")
            
            # 获取滑块元素位置
            slider_location = (captcha_element.location['x'], captcha_element.location['y'])
            
            # 使用AI处理
            success = self.ai_handler.handle_with_ai(
                background_image_path, 
                slider_location, 
                driver
            )
            
            if success:
                logger.info("✅ AI滑动验证码处理成功")
                return True
            else:
                logger.warning("❌ AI滑动验证码处理失败，回退到人工处理")
                return False
                
        except Exception as e:
            logger.error(f"AI滑动验证码处理出错: {e}")
            return False
    
    def collect_training_data(self, image_path: str, target_position: Tuple[int, int]):
        """收集训练数据"""
        if self.ai_available and self.ai_handler:
            try:
                self.ai_handler._collect_training_data(image_path, target_position)
                logger.debug(f"📊 收集训练数据: {image_path} -> {target_position}")
            except Exception as e:
                logger.warning(f"收集训练数据失败: {e}")


# 全局AI增强实例
ai_enhancement = AICaptchaEnhancement()


def get_ai_enhancement() -> AICaptchaEnhancement:
    """获取AI增强实例"""
    return ai_enhancement


def enhance_captcha_with_ai(driver: WebDriver, captcha_element, 
                          background_image_path: str) -> bool:
    """
    便捷函数：使用AI增强验证码处理
    
    Args:
        driver: WebDriver实例
        captcha_element: 验证码元素
        background_image_path: 背景图片路径
        
    Returns:
        处理是否成功
    """
    return ai_enhancement.enhance_slide_captcha_processing(
        driver, captcha_element, background_image_path
    )


# 全局验证码管理器实例
captcha_manager = CaptchaManager()


def get_captcha_manager() -> CaptchaManager:
    """获取验证码管理器实例"""
    return captcha_manager