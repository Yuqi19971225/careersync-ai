# -*- coding: utf-8 -*-
"""CareerSync AI 配置：配置文件 + 环境变量"""

import json
import logging
import os
from pathlib import Path

# 配置文件路径（项目根目录下的 config.json）
_CONFIG_PATH = Path(__file__).resolve().parent / 'config.json'

def _load_file_config():
    """从 config.json 读取配置，不存在或解析失败返回空字典"""
    if not _CONFIG_PATH.exists():
        return {}
    try:
        with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

_file_config = _load_file_config()

# 千问 API（环境变量优先，其次配置文件不存储密钥）
QWEN_API_KEY = os.getenv('DASHSCOPE_API_KEY') or os.getenv('QWEN_API_KEY')
QWEN_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
QWEN_MODEL = (
    os.getenv('QWEN_MODEL')
    or (_file_config.get('qwen') or {}).get('model')
    or 'qwen-turbo'
)

# 服务：配置文件优先，环境变量可覆盖
_server = _file_config.get('server') or {}
SERVER_HOST = os.getenv('SERVER_HOST') or _server.get('host') or '0.0.0.0'
SERVER_PORT = int(
    os.getenv('SERVER_PORT')
    or _server.get('port')
    or 5000
)
_debug_raw = os.getenv('FLASK_DEBUG')
if _debug_raw is not None:
    DEBUG = _debug_raw.lower() in ('1', 'true', 'yes')
else:
    DEBUG = _file_config.get('debug', True)

# 招聘源：启用哪些站点（source_id 列表），不配置则使用全部已注册源
_job_sources = _file_config.get('job_sources')
if _job_sources is not None and isinstance(_job_sources, list):
    JOB_SOURCES = [str(x) for x in _job_sources]
else:
    JOB_SOURCES = None  # 表示“全部源"

# 日志配置
_logging_config = _file_config.get('logging') or {}
LOG_FILE = _logging_config.get('log_file', 'app.log')
LOG_LEVEL = _logging_config.get('log_level', 'INFO')
LOG_MAX_BYTES = _logging_config.get('max_bytes', 10485760)  # 10MB
LOG_BACKUP_COUNT = _logging_config.get('backup_count', 5)


def setup_logging(level=logging.INFO, log_file=None, max_bytes=None, backup_count=None):
    """配置全局日志 - 支持文件日志和控制台日志"""
    import logging.handlers
    
    # 清除现有的处理器
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 设置日志级别
    log_level = getattr(logging, LOG_LEVEL.upper()) if isinstance(LOG_LEVEL, str) else LOG_LEVEL
    root_logger.setLevel(log_level)
    
    # 格式化器
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了日志文件）
    if log_file or LOG_FILE:
        log_path = Path(log_file or LOG_FILE)
        # 如果是相对路径，转换为绝对路径（相对于项目根目录）
        if not log_path.is_absolute():
            log_path = Path(__file__).resolve().parent / log_path
        
        # 创建日志目录（如果不存在）
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用 RotatingFileHandler 实现日志轮转
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes or LOG_MAX_BYTES,
            backupCount=backup_count or LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        print(f"📝 日志文件路径: {log_path}")
        print(f"📊 日志级别: {logging.getLevelName(log_level)}")
        print(f"🔄 日志轮转: 每 {max_bytes or LOG_MAX_BYTES} 字节，保留 {backup_count or LOG_BACKUP_COUNT} 个备份")
