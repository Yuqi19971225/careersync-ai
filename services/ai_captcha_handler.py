#!/usr/bin/env python3
"""
AI增强的滑动验证码识别系统
"""

import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Flatten, Dropout
from tensorflow.keras.optimizers import Adam
import random
import math
from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)

class AISlideCaptchaRecognizer:
    """AI驱动的滑动验证码识别器"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化AI识别器
        
        Args:
            model_path: 预训练模型路径，如果没有则创建新模型
        """
        self.model = None
        self.is_trained = False
        
        if model_path and tf.io.gfile.exists(model_path):
            try:
                self.model = load_model(model_path)
                self.is_trained = True
                logger.info("✅ 加载预训练模型成功")
            except Exception as e:
                logger.warning(f"❌ 加载模型失败: {e}，创建新模型")
                self._create_model()
        else:
            self._create_model()
    
    def _create_model(self):
        """创建CNN模型用于滑块位置识别"""
        self.model = Sequential([
            # 卷积层1
            Conv2D(32, (3, 3), activation='relu', input_shape=(100, 300, 3)),
            MaxPooling2D(2, 2),
            
            # 卷积层2
            Conv2D(64, (3, 3), activation='relu'),
            MaxPooling2D(2, 2),
            
            # 卷积层3
            Conv2D(128, (3, 3), activation='relu'),
            MaxPooling2D(2, 2),
            
            # 全连接层
            Flatten(),
            Dense(512, activation='relu'),
            Dropout(0.5),
            Dense(256, activation='relu'),
            Dropout(0.3),
            Dense(2, activation='linear')  # 输出x,y坐标
        ])
        
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        logger.info("✅ CNN模型创建完成")
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        预处理验证码图片
        
        Args:
            image_path: 图片路径
            
        Returns:
            处理后的numpy数组
        """
        try:
            # 读取图片
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError("无法读取图片")
            
            # 转换为RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # 调整大小
            img = cv2.resize(img, (300, 100))
            
            # 归一化
            img = img.astype(np.float32) / 255.0
            
            return np.expand_dims(img, axis=0)
            
        except Exception as e:
            logger.error(f"图片预处理失败: {e}")
            raise
    
    def predict_slider_position(self, background_image: str, slider_image: str = None) -> Tuple[int, int]:
        """
        预测滑块应该移动到的位置
        
        Args:
            background_image: 背景图片路径
            slider_image: 滑块图片路径（可选）
            
        Returns:
            (x, y) 坐标元组
        """
        if not self.is_trained:
            logger.warning("⚠️ 模型未训练，使用传统方法")
            return self._traditional_detection(background_image)
        
        try:
            # 预处理图片
            processed_img = self.preprocess_image(background_image)
            
            # 预测坐标
            prediction = self.model.predict(processed_img, verbose=0)[0]
            
            # 转换为实际像素坐标
            x = int(prediction[0] * 300)  # 转换回原始尺寸
            y = int(prediction[1] * 100)
            
            logger.info(f"🤖 AI预测滑块位置: ({x}, {y})")
            return (x, y)
            
        except Exception as e:
            logger.error(f"AI预测失败: {e}")
            return self._traditional_detection(background_image)
    
    def _traditional_detection(self, background_image: str) -> Tuple[int, int]:
        """
        传统的图像处理方法作为备选
        
        Args:
            background_image: 背景图片路径
            
        Returns:
            (x, y) 坐标元组
        """
        try:
            img = cv2.imread(background_image, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return (100, 50)  # 默认值
            
            # 边缘检测
            edges = cv2.Canny(img, 50, 150)
            
            # 查找轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 寻找最可能的缺口位置
            best_match = None
            min_diff = float('inf')
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # 过滤条件：合理的尺寸范围
                if 30 < w < 80 and 30 < h < 80:
                    # 计算与期望位置的差异
                    expected_x = img.shape[1] // 2
                    diff = abs(x - expected_x)
                    if diff < min_diff:
                        min_diff = diff
                        best_match = (x + w//2, y + h//2)
            
            if best_match:
                logger.info(f"🔍 传统方法检测到位置: {best_match}")
                return best_match
            else:
                # 返回默认位置
                return (img.shape[1] // 2, img.shape[0] // 2)
                
        except Exception as e:
            logger.error(f"传统检测方法失败: {e}")
            return (100, 50)
    
    def generate_human_like_trajectory(self, start_pos: Tuple[int, int], 
                                     end_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        生成类似人类的滑动轨迹
        
        Args:
            start_pos: 起始位置 (x, y)
            end_pos: 结束位置 (x, y)
            
        Returns:
            轨迹点列表 [(x, y), ...]
        """
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # 计算距离
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # 根据距离确定点的数量（模拟人类操作）
        num_points = max(20, int(distance / 3))
        
        trajectory = []
        
        for i in range(num_points + 1):
            # 时间参数 (0 to 1)
            t = i / num_points
            
            # 使用easeOutCubic缓动函数模拟人类操作
            eased_t = 1 - pow(1 - t, 3)
            
            # 计算当前位置
            current_x = int(x1 + (x2 - x1) * eased_t)
            current_y = int(y1 + (y2 - y1) * eased_t)
            
            # 添加轻微随机扰动模拟手抖
            jitter_x = random.randint(-2, 2)
            jitter_y = random.randint(-1, 1)
            
            current_x = max(0, min(300, current_x + jitter_x))
            current_y = max(0, min(100, current_y + jitter_y))
            
            trajectory.append((current_x, current_y))
        
        logger.info(f"🎯 生成 {len(trajectory)} 个轨迹点")
        return trajectory
    
    def train_model(self, training_data: List[Tuple[str, Tuple[int, int]]], 
                   epochs: int = 50, batch_size: int = 32):
        """
        训练模型
        
        Args:
            training_data: 训练数据 [(图片路径, (x, y)), ...]
            epochs: 训练轮数
            batch_size: 批次大小
        """
        logger.info("🧠 开始训练AI模型...")
        
        # 准备训练数据
        X_train = []
        y_train = []
        
        for image_path, (target_x, target_y) in training_data:
            try:
                # 预处理图片
                processed_img = self.preprocess_image(image_path)
                X_train.append(processed_img[0])  # 移除批次维度
                
                # 标准化坐标 (转换为0-1范围)
                normalized_x = target_x / 300.0
                normalized_y = target_y / 100.0
                y_train.append([normalized_x, normalized_y])
                
            except Exception as e:
                logger.warning(f"跳过训练样本 {image_path}: {e}")
                continue
        
        if len(X_train) == 0:
            logger.error("❌ 没有有效的训练数据")
            return
        
        # 转换为numpy数组
        X_train = np.array(X_train)
        y_train = np.array(y_train)
        
        # 训练模型
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=1
        )
        
        self.is_trained = True
        logger.info("✅ 模型训练完成")
        
        return history

class EnhancedSlideCaptchaHandler:
    """增强版滑动验证码处理器"""
    
    def __init__(self, ai_model_path: Optional[str] = None):
        self.ai_recognizer = AISlideCaptchaRecognizer(ai_model_path)
        self.tracking_data = []  # 用于收集训练数据
    
    def handle_with_ai(self, background_image_path: str, 
                      slider_element_location: Tuple[int, int],
                      driver = None) -> bool:
        """
        使用AI处理滑动验证码
        
        Args:
            background_image_path: 背景图片路径
            slider_element_location: 滑块元素在页面中的位置
            driver: Selenium WebDriver实例
            
        Returns:
            处理是否成功
        """
        try:
            logger.info("🤖 启动AI滑动验证码处理...")
            
            # 1. AI识别滑块目标位置
            target_x, target_y = self.ai_recognizer.predict_slider_position(background_image_path)
            
            # 2. 生成人类化轨迹
            start_pos = (0, slider_element_location[1])  # 从滑块起始位置开始
            end_pos = (target_x, target_y)
            trajectory = self.ai_recognizer.generate_human_like_trajectory(start_pos, end_pos)
            
            # 3. 执行滑动操作
            if driver:
                success = self._execute_slide_with_selenium(
                    driver, slider_element_location, trajectory
                )
            else:
                success = self._simulate_slide_actions(trajectory)
            
            # 4. 收集数据用于模型优化
            if success:
                self._collect_training_data(background_image_path, (target_x, target_y))
                logger.info("✅ AI滑动验证码处理成功")
            else:
                logger.warning("❌ AI滑动验证码处理失败")
            
            return success
            
        except Exception as e:
            logger.error(f"AI滑动验证码处理出错: {e}")
            return False
    
    def _execute_slide_with_selenium(self, driver, slider_location: Tuple[int, int], 
                                   trajectory: List[Tuple[int, int]]) -> bool:
        """使用Selenium执行滑动操作"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            # 找到滑块元素
            slider = driver.find_element("xpath", "//div[contains(@class, 'slider')]")  # 需要根据实际调整
            
            # 执行滑动
            actions = ActionChains(driver)
            actions.move_to_element_with_offset(slider, 0, 0)
            actions.click_and_hold()
            
            # 按轨迹移动
            for point in trajectory[1:]:  # 跳过起始点
                actions.move_by_offset(point[0] - trajectory[0][0], 0)  # 只移动X轴
                actions.pause(0.01)  # 小暂停模拟人类操作
            
            actions.release()
            actions.perform()
            
            return True
            
        except Exception as e:
            logger.error(f"Selenium滑动执行失败: {e}")
            return False
    
    def _simulate_slide_actions(self, trajectory: List[Tuple[int, int]]) -> bool:
        """模拟滑动动作（用于测试）"""
        logger.info("🧪 模拟滑动轨迹执行...")
        for i, (x, y) in enumerate(trajectory):
            logger.debug(f"  步骤 {i+1}: 移动到 ({x}, {y})")
        return True
    
    def _collect_training_data(self, image_path: str, target_position: Tuple[int, int]):
        """收集训练数据"""
        self.tracking_data.append((image_path, target_position))
        logger.debug(f"📊 收集训练数据: {image_path} -> {target_position}")
        
        # 当积累足够数据时触发增量训练
        if len(self.tracking_data) >= 100:  # 阈值可调整
            logger.info("🔄 触发增量训练...")
            self.ai_recognizer.train_model(self.tracking_data[-50:])  # 使用最近的数据
    
    def save_model(self, model_path: str):
        """保存训练好的模型"""
        if self.ai_recognizer.model:
            self.ai_recognizer.model.save(model_path)
            logger.info(f"💾 模型已保存到: {model_path}")

# 使用示例
def demo_ai_captcha():
    """演示AI滑动验证码处理"""
    print("🤖 AI滑动验证码处理演示")
    print("=" * 40)
    
    # 创建处理器
    handler = EnhancedSlideCaptchaHandler()
    
    # 模拟处理过程
    background_image = "captcha_background.png"  # 实际路径
    slider_location = (50, 200)  # 滑块在页面中的位置
    
    # 处理验证码
    success = handler.handle_with_ai(background_image, slider_location)
    
    if success:
        print("✅ AI成功处理滑动验证码")
    else:
        print("❌ AI处理失败")

if __name__ == "__main__":
    demo_ai_captcha()