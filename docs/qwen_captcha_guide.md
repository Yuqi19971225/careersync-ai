# 千问大模型验证码处理功能说明

## 📋 功能概述

本系统集成了阿里云千问大模型来智能处理各种类型的验证码，提供比传统OCR更高的识别准确率和更强的适应性。

## 🔧 技术架构

### 处理流程
```
验证码检测 → 千问AI处理 → 成功？ → 自动执行/人工处理
               ↓否
           传统AI处理 → 成功？ → 自动执行/人工处理
                         ↓否
                     人工处理流程
```

### 支持的验证码类型
- **滑动验证码** (`slide`): 识别滑块应移动的距离
- **图片文字验证码** (`image_text`): OCR文字识别
- **点选验证码** (`click`): 识别需要点击的坐标位置

## 🚀 使用方法

### 1. 环境配置
```bash
# 设置千问API密钥
export DASHSCOPE_API_KEY="your-api-key-here"

# 或者在config.json中配置
{
  "qwen": {
    "api_key": "your-api-key-here",
    "model": "qwen-turbo"
  }
}
```

### 2. 代码集成示例

#### 直接使用处理器
```python
from services.qwen_captcha_handler import QwenCaptchaProcessor

# 创建处理器实例
processor = QwenCaptchaProcessor()

# 处理滑动验证码
distance = processor.process_slide_captcha(background_image_b64)
if distance:
    print(f"识别到滑动距离: {distance}px")

# 处理图片文字验证码
text = processor.process_image_text_captcha(image_b64)
if text:
    print(f"识别到文字: {text}")

# 处理点选验证码
coordinates = processor.process_click_captcha(image_b64, "请点击图片中的汽车")
if coordinates:
    print(f"识别到点击坐标: {coordinates}")
```

#### 使用便捷函数
```python
from services.qwen_captcha_handler import enhance_captcha_with_qwen

# 统一接口处理各种验证码
result = enhance_captcha_with_qwen('slide', image_data)
result = enhance_captcha_with_qwen('image_text', image_data)
result = enhance_captcha_with_qwen('click', image_data, instruction="点击汽车")
```

### 3. 在爬虫中使用
```python
from services.captcha_handler import get_captcha_manager

# 系统会自动优先使用千问AI处理
captcha_manager = get_captcha_manager()
success = captcha_manager.handle_captcha(driver)
```

## 🎯 功能特点

### 智能降级机制
- **一级**: 千问大模型处理（最高准确率）
- **二级**: 传统AI处理（备用方案）
- **三级**: 人工处理（兜底保障）

### 错误处理
- 自动检测API密钥配置状态
- 优雅处理网络异常和超时
- 详细的日志记录便于调试

### 性能优化
- 低温度参数确保结果稳定性
- 合理的token限制控制成本
- 缓存机制减少重复请求

## 📊 识别效果示例

### 滑动验证码
```
输入: 滑动验证码背景图片base64
输出: 280 (表示需要滑动280像素)
```

### 图片文字验证码
```
输入: 包含文字的验证码图片
输出: "ABCD1234" (识别出的文字内容)
```

### 点选验证码
```
输入: 需要点选的图片
输出: [(150, 75), (200, 120)] (需要点击的坐标列表)
```

## ⚠️ 注意事项

1. **API费用**: 千问API会产生调用费用，请合理控制使用频率
2. **网络环境**: 确保服务器能访问阿里云API服务
3. **图片质量**: 提供清晰的验证码图片有助于提高识别准确率
4. **隐私安全**: 验证码图片可能包含敏感信息，请注意数据保护

## 🛠️ 故障排除

### 常见问题
1. **"千问处理器不可用"**: 检查API密钥配置
2. **识别准确率低**: 尝试提供更高清的图片
3. **响应超时**: 检查网络连接和API配额

### 调试建议
```python
import logging
logging.basicConfig(level=logging.DEBUG)  # 启用详细日志
```

## 📈 未来发展

- [ ] 支持更多验证码类型
- [ ] 增加本地模型缓存机制
- [ ] 优化提示词工程提升准确率
- [ ] 添加批量处理功能
- [ ] 集成学习机制持续优化

---
*CareerSync AI - 让AI助力你的职业发展*