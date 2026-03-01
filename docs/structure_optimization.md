# 📁 CareerSync AI 项目结构优化说明

## 🎯 优化目标

本次优化旨在建立更加清晰、规范和可维护的项目结构，提升团队协作效率和代码质量。

## 🔧 主要变更

### 1. 目录重组
```
📁 旧结构                    📁 新结构
├── demo_*.py               ├── scripts/
├── test_*.py               ├── tests/
├── captcha_training_data/  ├── data/training/
└── 杂乱的根目录文件         └── 按功能分类存放
```

### 2. 新增目录说明

| 目录 | 用途 | 内容 |
|------|------|------|
| `scripts/` | 工具脚本 | 演示程序、辅助工具 |
| `tests/` | 测试文件 | 单元测试、集成测试 |
| `data/` | 数据管理 | 训练数据、运行时数据 |
| `models/` | AI模型 | 预训练模型、模型权重 |
| `logs/` | 日志文件 | 运行日志、错误日志 |

### 3. 文件迁移清单

✅ **已迁移文件**:
- `demo_captcha.py` → `scripts/demo_captcha.py`
- `demo_slide_captcha.py` → `scripts/demo_slide_captcha.py`
- `captcha_training_data/` → `data/training/`

✅ **新增文件**:
- `docs/project_structure.md` - 项目结构文档
- `tests/__init__.py` - 测试包初始化

## 🎨 结构优势

### 1. 职责清晰
- **业务逻辑**: `services/` 集中管理
- **前端资源**: `static/` 统一存放
- **配置管理**: `config.py` + `config.json`
- **入口文件**: `app.py` 专注应用启动

### 2. 便于维护
- 相关文件按功能分组
- 测试文件集中管理
- 演示代码独立存放
- 数据文件统一管理

### 3. 团队友好
- 新成员容易理解项目结构
- 代码审查更有针对性
- 部署和运维更规范

## 🚀 使用指南

### 开发流程
```bash
# 运行演示程序
python scripts/demo_captcha.py

# 执行测试
python -m pytest tests/

# 启动服务
./start_server.sh
```

### 目录使用规范

1. **新增功能**: 在 `services/` 对应模块中开发
2. **编写测试**: 在 `tests/` 创建对应测试文件
3. **添加演示**: 在 `scripts/` 创建演示脚本
4. **存储数据**: 使用 `data/` 目录管理数据文件

## 📋 后续建议

### 短期目标
- [ ] 完善单元测试覆盖率
- [ ] 规范代码注释和文档
- [ ] 建立CI/CD流程

### 长期规划
- [ ] 微服务架构拆分
- [ ] Docker容器化部署
- [ ] Kubernetes集群管理

---

*本次优化保持了向后兼容性，现有功能不受影响*