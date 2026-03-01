# CareerSync AI 项目结构说明

## 📁 优化后的目录结构

```
careersync-ai/
├── app.py                 # 应用主入口
├── config.py             # 配置管理
├── config.json           # 配置文件
├── requirements.txt      # 依赖包列表
├── routes.py             # API路由定义
├── README.md             # 项目说明文档
├── .gitignore            # Git忽略文件
├── start_server.sh       # 服务启动脚本
│
├── services/             # 核心业务服务层
│   ├── __init__.py
│   ├── career_sync.py    # 主服务协调器
│   ├── crawler.py        # 爬虫基础服务
│   ├── matcher.py        # 简历匹配服务
│   ├── optimizer.py      # 简历优化服务
│   ├── proxy_manager.py  # 代理管理服务
│   ├── browser_automation.py  # 浏览器自动化
│   ├── qwen_client.py    # 千问API客户端
│   ├── captcha_handler.py     # 验证码处理主服务
│   ├── qwen_captcha_handler.py # 千问验证码处理器
│   ├── ai_captcha_handler.py   # AI验证码处理器
│   ├── captcha_data_manager.py # 验证码数据管理
│   └── sources/          # 招聘网站源
│       ├── __init__.py
│       ├── base.py       # 基础源接口
│       ├── boss.py       # BOSS直聘源
│       ├── lagou.py      # 拉勾网源
│       ├── lagou_browser.py # 拉勾网浏览器源
│       └── zhaopin.py    # 智联招聘源
│
├── static/               # 静态资源
│   ├── index.html        # 前端主页面
│   ├── css/              # 样式文件
│   │   └── style.css
│   └── js/               # JavaScript文件
│       └── app.js
│
├── data/                 # 数据目录
│   └── training/         # 验证码训练数据
│       ├── images/       # 训练图片
│       └── labels/       # 标签数据
│
├── models/               # AI模型文件
│   └── (预留目录)
│
├── logs/                 # 日志文件目录
│   └── (运行时生成)
│
├── scripts/              # 工具脚本和演示程序
│   ├── demo_captcha.py          # 验证码功能演示
│   └── demo_slide_captcha.py    # 滑动验证码演示
│
├── tests/                # 测试文件
│   ├── __init__.py
│   ├── test_captcha.py          # 验证码功能测试
│   ├── test_qwen_captcha.py     # 千问验证码测试
│   ├── test_slider_detection.py # 滑块检测测试
│   └── test_merge.html          # 合并功能测试
│
└── docs/                 # 文档目录
    ├── project_structure.md     # 项目结构说明
    └── qwen_captcha_guide.md    # 千问验证码使用指南
```

## 🎯 结构优化说明

### 1. 分层清晰
- **核心服务层** (`services/`): 包含所有业务逻辑
- **静态资源层** (`static/`): 前端文件集中管理
- **数据管理层** (`data/`): 训练数据和运行时数据
- **工具脚本层** (`scripts/`): 演示和辅助脚本
- **测试层** (`tests/`): 所有测试文件集中存放

### 2. 职责分离
- `app.py`: 仅负责应用启动和基本配置
- `routes.py`: 专门处理API路由
- `config.py`: 统一配置管理
- `services/`: 按功能模块划分服务

### 3. 命名规范化
- 使用复数形式命名目录 (如 `services`, `scripts`, `tests`)
- 保持一致的命名约定
- 清晰的文件用途标识

### 4. 可扩展性
- `models/`: 为AI模型预留空间
- `logs/`: 为日志文件预留目录
- `data/`: 统一数据管理入口

## 🚀 使用建议

### 开发环境
```bash
# 启动服务
./start_server.sh

# 运行测试
python -m pytest tests/

# 查看演示
python scripts/demo_captcha.py
```

### 生产部署
- 确保 `logs/` 目录有写权限
- 配置 `config.json` 中的生产环境参数
- 使用 `models/` 目录存放训练好的模型文件

### 团队协作
- 新功能开发在对应的服务模块中
- 测试文件与功能代码保持对应关系
- 文档及时更新维护