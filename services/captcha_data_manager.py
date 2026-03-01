#!/usr/bin/env python3
"""
滑动验证码AI训练数据管理工具
"""

import os
import json
import cv2
import numpy as np
from typing import List, Tuple, Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CaptchaDataManager:
    """验证码数据管理器"""
    
    def __init__(self, data_dir: str = "captcha_training_data"):
        self.data_dir = data_dir
        self.images_dir = os.path.join(data_dir, "images")
        self.labels_dir = os.path.join(data_dir, "labels")
        self.metadata_file = os.path.join(data_dir, "metadata.json")
        
        # 创建目录结构
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.labels_dir, exist_ok=True)
        
        # 加载元数据
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """加载元数据"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载元数据失败: {e}")
        return {"samples": [], "stats": {}}
    
    def save_metadata(self):
        """保存元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
    
    def add_sample(self, image_path: str, target_position: Tuple[int, int], 
                   captcha_type: str = "slide", source: str = "unknown") -> str:
        """
        添加训练样本
        
        Args:
            image_path: 验证码图片路径
            target_position: 目标位置 (x, y)
            captcha_type: 验证码类型
            source: 数据来源
            
        Returns:
            样本ID
        """
        try:
            # 生成唯一ID
            sample_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.metadata['samples'])}"
            
            # 复制图片到训练目录
            filename = f"{sample_id}.png"
            target_image_path = os.path.join(self.images_dir, filename)
            
            # 读取并保存图片
            img = cv2.imread(image_path)
            if img is not None:
                cv2.imwrite(target_image_path, img)
            else:
                raise ValueError("无法读取图片")
            
            # 创建标签文件
            label_data = {
                "id": sample_id,
                "target_x": target_position[0],
                "target_y": target_position[1],
                "type": captcha_type,
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "image_filename": filename
            }
            
            label_file = os.path.join(self.labels_dir, f"{sample_id}.json")
            with open(label_file, 'w', encoding='utf-8') as f:
                json.dump(label_data, f, indent=2)
            
            # 更新元数据
            self.metadata["samples"].append({
                "id": sample_id,
                "type": captcha_type,
                "source": source,
                "timestamp": label_data["timestamp"]
            })
            
            self._update_stats()
            self.save_metadata()
            
            logger.info(f"✅ 添加训练样本: {sample_id}")
            return sample_id
            
        except Exception as e:
            logger.error(f"添加样本失败: {e}")
            raise
    
    def _update_stats(self):
        """更新统计数据"""
        samples = self.metadata["samples"]
        stats = {
            "total_samples": len(samples),
            "by_type": {},
            "by_source": {},
            "latest_timestamp": max([s.get("timestamp", "") for s in samples]) if samples else ""
        }
        
        # 按类型统计
        for sample in samples:
            captcha_type = sample.get("type", "unknown")
            stats["by_type"][captcha_type] = stats["by_type"].get(captcha_type, 0) + 1
        
        # 按来源统计
        for sample in samples:
            source = sample.get("source", "unknown")
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
        
        self.metadata["stats"] = stats
    
    def get_training_data(self) -> List[Tuple[str, Tuple[int, int]]]:
        """
        获取训练数据
        
        Returns:
            [(图片路径, (x, y)), ...]
        """
        training_data = []
        
        for sample in self.metadata["samples"]:
            sample_id = sample["id"]
            
            # 读取标签
            label_file = os.path.join(self.labels_dir, f"{sample_id}.json")
            if not os.path.exists(label_file):
                continue
                
            try:
                with open(label_file, 'r', encoding='utf-8') as f:
                    label_data = json.load(f)
                
                image_path = os.path.join(self.images_dir, label_data["image_filename"])
                target_pos = (label_data["target_x"], label_data["target_y"])
                
                if os.path.exists(image_path):
                    training_data.append((image_path, target_pos))
                    
            except Exception as e:
                logger.warning(f"读取样本 {sample_id} 失败: {e}")
                continue
        
        logger.info(f"📊 获取到 {len(training_data)} 个训练样本")
        return training_data
    
    def analyze_dataset(self) -> Dict:
        """分析数据集质量"""
        stats = self.metadata.get("stats", {})
        
        analysis = {
            "总样本数": stats.get("total_samples", 0),
            "类型分布": stats.get("by_type", {}),
            "来源分布": stats.get("by_source", {}),
            "数据完整性": self._check_data_integrity()
        }
        
        return analysis
    
    def _check_data_integrity(self) -> Dict:
        """检查数据完整性"""
        missing_images = []
        missing_labels = []
        corrupted_images = []
        
        for sample in self.metadata["samples"]:
            sample_id = sample["id"]
            
            # 检查标签文件
            label_file = os.path.join(self.labels_dir, f"{sample_id}.json")
            if not os.path.exists(label_file):
                missing_labels.append(sample_id)
                continue
            
            # 检查图片文件
            try:
                with open(label_file, 'r', encoding='utf-8') as f:
                    label_data = json.load(f)
                
                image_path = os.path.join(self.images_dir, label_data["image_filename"])
                if not os.path.exists(image_path):
                    missing_images.append(sample_id)
                else:
                    # 检查图片是否可读
                    img = cv2.imread(image_path)
                    if img is None:
                        corrupted_images.append(sample_id)
                        
            except Exception as e:
                logger.warning(f"检查样本 {sample_id} 时出错: {e}")
        
        return {
            "missing_images": missing_images,
            "missing_labels": missing_labels,
            "corrupted_images": corrupted_images,
            "healthy_samples": len(self.metadata["samples"]) - len(missing_images) - len(missing_labels) - len(corrupted_images)
        }

class InteractiveLabelingTool:
    """交互式标注工具"""
    
    def __init__(self, data_manager: CaptchaDataManager):
        self.data_manager = data_manager
        self.current_image = None
        self.current_sample_id = None
    
    def label_image_interactively(self, image_path: str, source: str = "manual"):
        """
        交互式标注图片
        
        Args:
            image_path: 待标注的图片路径
            source: 数据来源标识
        """
        try:
            # 显示图片
            img = cv2.imread(image_path)
            if img is None:
                print("❌ 无法读取图片")
                return
            
            # 创建窗口显示图片
            window_name = "验证码标注工具 - 点击缺口位置"
            cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
            
            # 设置鼠标回调
            cv2.setMouseCallback(window_name, self._mouse_callback)
            
            # 显示图片
            display_img = img.copy()
            cv2.imshow(window_name, display_img)
            
            print("🔧 交互式标注指南:")
            print("1. 在图片上点击缺口的中心位置")
            print("2. 按 'Enter' 确认标注")
            print("3. 按 'Esc' 取消标注")
            print("4. 按 'r' 重新选择位置")
            
            self.current_image = img
            selected_point = None
            
            while True:
                key = cv2.waitKey(1) & 0xFF
                
                if key == 13:  # Enter键
                    if selected_point:
                        # 保存标注
                        sample_id = self.data_manager.add_sample(
                            image_path, selected_point, "slide", source
                        )
                        print(f"✅ 标注完成，样本ID: {sample_id}")
                        break
                    else:
                        print("⚠️ 请先点击选择位置")
                
                elif key == 27:  # Esc键
                    print("❌ 取消标注")
                    break
                
                elif key == ord('r'):  # r键重新选择
                    selected_point = None
                    cv2.imshow(window_name, img.copy())
                    print("🔄 重新选择位置")
            
            cv2.destroyAllWindows()
            
        except Exception as e:
            print(f"❌ 标注过程出错: {e}")
            cv2.destroyAllWindows()
    
    def _mouse_callback(self, event, x, y, flags, param):
        """鼠标回调函数"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # 在图片上标记选择的位置
            display_img = self.current_image.copy()
            cv2.circle(display_img, (x, y), 5, (0, 255, 0), -1)
            cv2.circle(display_img, (x, y), 15, (0, 255, 0), 2)
            cv2.imshow("验证码标注工具 - 点击缺口位置", display_img)
            
            self.current_sample_id = (x, y)
            print(f"📍 选择位置: ({x}, {y})")

def demo_data_management():
    """演示数据管理功能"""
    print("📊 验证码数据管理演示")
    print("=" * 40)
    
    # 创建数据管理器
    data_manager = CaptchaDataManager()
    
    # 分析现有数据集
    analysis = data_manager.analyze_dataset()
    print("\n📈 数据集分析:")
    for key, value in analysis.items():
        print(f"  {key}: {value}")
    
    # 创建交互式标注工具
    labeling_tool = InteractiveLabelingTool(data_manager)
    
    # 获取训练数据
    training_data = data_manager.get_training_data()
    print(f"\n📊 当前训练数据: {len(training_data)} 个样本")
    
    return data_manager

if __name__ == "__main__":
    demo_data_management()