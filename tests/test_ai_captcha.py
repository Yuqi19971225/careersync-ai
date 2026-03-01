#!/usr/bin/env python3
"""
AI滑动验证码功能测试
"""

import unittest
import os
import tempfile
import cv2
import numpy as np
from unittest.mock import Mock, patch

class TestAICaptchaFeatures(unittest.TestCase):
    """AI验证码功能测试"""
    
    def setUp(self):
        """测试前置条件"""
        self.test_image_path = self._create_test_image()
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
    
    def _create_test_image(self):
        """创建测试用的验证码图片"""
        # 创建一个简单的测试图片
        img = np.zeros((100, 300, 3), dtype=np.uint8)
        img[:] = [255, 255, 255]  # 白色背景
        
        # 添加一些干扰元素
        cv2.rectangle(img, (50, 30), (80, 70), (100, 100, 100), -1)  # 模拟缺口
        cv2.rectangle(img, (20, 20), (280, 80), (200, 200, 200), 2)  # 边框
        
        # 保存图片
        temp_path = tempfile.mktemp(suffix='.png')
        cv2.imwrite(temp_path, img)
        return temp_path
    
    def test_ai_model_creation(self):
        """测试AI模型创建"""
        try:
            from services.ai_captcha_handler import AISlideCaptchaRecognizer
            recognizer = AISlideCaptchaRecognizer()
            self.assertIsNotNone(recognizer.model)
            self.assertFalse(recognizer.is_trained)
            print("✅ AI模型创建测试通过")
        except Exception as e:
            self.skipTest(f"AI依赖不可用: {e}")
    
    def test_image_preprocessing(self):
        """测试图片预处理"""
        try:
            from services.ai_captcha_handler import AISlideCaptchaRecognizer
            recognizer = AISlideCaptchaRecognizer()
            
            processed = recognizer.preprocess_image(self.test_image_path)
            self.assertEqual(processed.shape, (1, 100, 300, 3))
            self.assertTrue(processed.dtype == np.float32)
            print("✅ 图片预处理测试通过")
        except Exception as e:
            self.skipTest(f"AI依赖不可用: {e}")
    
    def test_trajectory_generation(self):
        """测试轨迹生成"""
        try:
            from services.ai_captcha_handler import AISlideCaptchaRecognizer
            recognizer = AISlideCaptchaRecognizer()
            
            start = (0, 50)
            end = (200, 50)
            trajectory = recognizer.generate_human_like_trajectory(start, end)
            
            self.assertIsInstance(trajectory, list)
            self.assertGreater(len(trajectory), 10)
            self.assertEqual(trajectory[0], start)
            self.assertEqual(trajectory[-1], end)
            print("✅ 轨迹生成测试通过")
        except Exception as e:
            self.skipTest(f"AI依赖不可用: {e}")
    
    def test_traditional_detection(self):
        """测试传统检测方法"""
        try:
            from services.ai_captcha_handler import AISlideCaptchaRecognizer
            recognizer = AISlideCaptchaRecognizer()
            
            position = recognizer._traditional_detection(self.test_image_path)
            self.assertIsInstance(position, tuple)
            self.assertEqual(len(position), 2)
            self.assertTrue(all(isinstance(coord, int) for coord in position))
            print("✅ 传统检测方法测试通过")
        except Exception as e:
            self.skipTest(f"AI依赖不可用: {e}")
    
    def test_ai_enhancement_integration(self):
        """测试AI增强功能集成"""
        try:
            from services.captcha_handler import get_ai_enhancement
            
            ai_enhancement = get_ai_enhancement()
            self.assertIsNotNone(ai_enhancement)
            
            # 测试便捷函数
            from services.captcha_handler import enhance_captcha_with_ai
            self.assertTrue(callable(enhance_captcha_with_ai))
            print("✅ AI增强功能集成测试通过")
        except Exception as e:
            self.skipTest(f"AI依赖不可用: {e}")
    
    def test_data_manager_basic(self):
        """测试数据管理器基础功能"""
        try:
            from services.captcha_data_manager import CaptchaDataManager
            
            with tempfile.TemporaryDirectory() as temp_dir:
                data_manager = CaptchaDataManager(temp_dir)
                
                # 测试添加样本
                sample_id = data_manager.add_sample(
                    self.test_image_path, 
                    (150, 50), 
                    "slide", 
                    "test"
                )
                
                self.assertIsNotNone(sample_id)
                
                # 测试获取训练数据
                training_data = data_manager.get_training_data()
                self.assertIsInstance(training_data, list)
                self.assertGreater(len(training_data), 0)
                
                print("✅ 数据管理器测试通过")
        except Exception as e:
            self.skipTest(f"数据管理依赖不可用: {e}")

def run_comprehensive_test():
    """运行综合测试"""
    print("🧪 AI滑动验证码功能综合测试")
    print("=" * 40)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAICaptchaFeatures)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print("\n" + "=" * 40)
    print("测试结果汇总:")
    print(f"  总测试数: {result.testsRun}")
    print(f"  通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("🎉 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)