# CareerSync AI

智能职业匹配与简历优化系统：支持职位搜索、简历与职位匹配、基于目标岗位的简历优化建议与改写。

---

## 功能概览

- **职位搜索**：按关键词、城市搜索职位（当前支持拉勾网数据源）
- **简历匹配**：上传简历内容，与目标职位列表进行匹配并显示匹配度
- **简历优化**：结合目标职位描述，生成优化建议并由千问大模型输出改写后的简历（可选）

---

## 环境要求

- **Python**：3.10 或 3.12+（推荐 3.12）
- 建议使用 **Conda** 或 **venv** 创建独立虚拟环境

---

## 安装

### 1. 进入项目目录

```bash
cd careersync-ai
```

### 2. 创建并激活虚拟环境

**方式 A：Conda**

```bash
conda create -n careersync_env python=3.12 -y
conda activate careersync_env
```

**方式 B：venv**

```bash
python3 -m venv careersync_env
# Windows:
careersync_env\Scripts\activate
# macOS / Linux:
source careersync_env/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置千问 API（可选）

需要「简历优化」中的 AI 改写与智能建议时，请配置阿里云百炼（千问）API Key：

```bash
# macOS / Linux
export DASHSCOPE_API_KEY="你的API_Key"

# Windows (PowerShell)
$env:DASHSCOPE_API_KEY="你的API_Key"
```

- API Key 获取： [阿里云百炼控制台](https://bailian.console.aliyun.com/) → API-KEY 管理  
- 不配置时，简历优化将使用规则引擎兜底，仍可得到基础建议

---

## 运行与启动

### 方式一：直接运行主程序（推荐）

```bash
# 确保已激活虚拟环境
python3 app.py
```

### 方式二：使用启动脚本（venv 时）

若使用 venv 且虚拟环境位于项目下的 `careersync_env`：

```bash
chmod +x start_server.sh
./start_server.sh
```

脚本会激活 `careersync_env` 并执行 `python3 app.py`。

### 配置文件

项目根目录下的 **`config.json`** 用于设置端口、监听地址等，优先于默认值；环境变量可再覆盖配置文件。

示例：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000
  },
  "debug": true,
  "qwen": {
    "model": "qwen-turbo"
  }
}
```

- 修改 `server.port` 即可更换端口，保存后重启服务生效。
- 若不存在 `config.json`，程序使用内置默认值（端口 5000）。

### 启动参数（环境变量）

环境变量可覆盖配置文件中的同名字段：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SERVER_HOST` | 监听地址 | 见 config.json 或 `0.0.0.0` |
| `SERVER_PORT` | 监听端口 | 见 config.json 或 `5000` |
| `FLASK_DEBUG` | 是否开启调试 | 见 config.json 或 `true` |
| `QWEN_MODEL` | 千问模型名 | 见 config.json 或 `qwen-turbo` |

示例：通过配置文件改端口时，直接编辑 `config.json` 中的 `server.port`；或临时用环境变量指定端口：

```bash
SERVER_PORT=8080 python3 app.py
```

启动成功后，终端会打印接口列表；浏览器访问 **http://localhost:端口/** 即可使用前端页面。

---

## 使用指导

### 1. 打开前端页面

服务启动后，在浏览器中访问：

- 本机：**http://localhost:5000/**
- 局域网访问：**http://\<你的本机IP\>:5000/**

页面包含三个 Tab：**职位搜索**、**简历匹配**、**简历优化**。

### 2. 职位搜索

1. 在「职位搜索」Tab 中输入 **职位关键词**（如：Python、前端、产品经理）。
2. 可选填写 **城市**（默认「全国」）。
3. 点击 **「搜索职位」**，下方会展示职位列表（标题、公司、薪资、描述摘要）。

### 3. 简历匹配

1. 切换到「简历匹配」Tab。
2. 在文本框中 **粘贴简历正文**。
3. 填写 **目标职位关键词** 和 **城市**。
4. 点击 **「开始匹配」**，系统会拉取相关职位并计算匹配度，展示带匹配百分比的职位列表。

### 4. 简历优化

1. 切换到「简历优化」Tab。
2. 在文本框中 **粘贴当前简历正文**。
3. 填写 **目标职位关键词** 和 **城市**（用于获取目标岗位描述）。
4. 点击 **「获取优化建议」**：
   - 若已配置 `DASHSCOPE_API_KEY`：会得到千问生成的优化建议与改写后的简历正文。
   - 未配置时：仍会得到基于规则的优化建议。

---

## API 接口（供二次开发或联调）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 前端页面 |
| GET | `/api/health` | 健康检查 |
| GET | `/api/system_info` | 系统信息（含版本、是否启用千问等） |
| POST | `/api/search_jobs` | 职位搜索，Body: `{ "keyword", "city?", "page?", "sources?" }`（sources 指定招聘源如 `["lagou"]`） |
| POST | `/api/match_resume` | 简历匹配，Body: `{ "resume", "keyword", "city?" }` |
| POST | `/api/optimize_resume` | 简历优化，Body: `{ "resume", "keyword", "city?" }` |
| GET  | `/api/job_sources` | 可用招聘源 id 列表及当前启用列表 |

请求体均为 JSON；缺失的 `city` 默认为「全国」，`page` 默认为 1。

**招聘源配置**：`config.json` 中 `job_sources` 指定启用的站点（如 `["lagou"]`）；不配置则使用全部已注册源。请求时可传 `sources` 覆盖本次使用的源。

---

## 扩展新招聘站

1. 在 `services/sources/` 下新建模块（如 `xxx.py`）。
2. 继承 `BaseJobSource`，实现 `source_id`、`source_name` 和 `search(keyword, city, page)`，返回 `normalize_job(...)` 构造的职位列表。
3. 在 `services/sources/__init__.py` 的 `SOURCE_REGISTRY` 中注册该源。
4. 在 `config.json` 的 `job_sources` 中加入对应 `source_id`（或留空使用全部）。

---

## 项目结构（简要）

```
careersync-ai/
├── app.py              # 主程序入口，启动服务
├── config.py           # 配置加载（config.json + 环境变量）
├── config.json         # 配置文件（端口、host、debug、qwen 模型等）
├── routes.py           # 路由注册（API + 前端页面）
├── requirements.txt
├── README.md
├── start_server.sh     # 启动脚本（venv）
├── static/             # 前端静态资源
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
└── services/           # 业务逻辑
    ├── career_sync.py  # 主系统编排
    ├── crawler.py      # 多招聘源聚合爬虫
    ├── matcher.py      # 简历-职位匹配
    ├── optimizer.py    # 简历优化（千问 + 规则）
    ├── qwen_client.py  # 千问 API 客户端
    └── sources/        # 可扩展招聘源（每站一个模块）
        ├── base.py     # 基类与统一职位格式
        ├── lagou.py    # 拉勾网
        ├── boss.py     # BOSS直聘（占位）
        └── zhaopin.py  # 智联招聘（占位）
```

---

## 常见问题

- **ImportError: cannot import name 'ComplexWarning' from 'numpy.core.numeric'**  
  多为 NumPy 2.x 与旧版 scikit-learn 不兼容。请确保已执行 `pip install -r requirements.txt`（已使用 `scikit-learn>=1.4.0`）。

- **前端能打开但接口报错**  
  确认后端已启动且浏览器访问的地址与 `SERVER_HOST` / `SERVER_PORT` 一致（默认即本机 5000 端口）。

- **简历优化没有 AI 改写**  
  检查是否已设置环境变量 `DASHSCOPE_API_KEY`；未设置时仅使用规则建议，功能仍可用。

---

## 许可证

本项目仅供学习与个人使用；使用爬虫与第三方 API 时请遵守相关网站与平台的服务条款与法律法规。
