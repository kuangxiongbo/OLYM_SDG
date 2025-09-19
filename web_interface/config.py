#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDG Web界面配置文件
==================

包含所有可配置的参数和设置
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sdg_web_interface_secret_key_2025'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    ENV = os.environ.get('FLASK_ENV', 'development')
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))  # 50MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    RESULTS_FOLDER = os.environ.get('RESULTS_FOLDER', 'results')
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    
    # 数据库配置（如果需要）
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///sdg_web.db')
    
    # API配置
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_API_URL = os.environ.get('OPENAI_API_URL', 'https://api.openai.com/v1/')
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
    DEEPSEEK_API_URL = os.environ.get('DEEPSEEK_API_URL', 'http://localhost:8000/v1/')
    
    # 模型默认配置
    DEFAULT_CTGAN_CONFIG = {
        'epochs': 50,
        'batch_size': 500,
        'generator_lr': 2e-4,
        'discriminator_lr': 2e-4,
        'generator_decay': 1e-6,
        'discriminator_decay': 1e-6,
        'generator_dim': '(256, 256)',
        'discriminator_dim': '(256, 256)'
    }
    
    DEFAULT_GPT_CONFIG = {
        'openai_API_key': '',
        'openai_API_url': 'https://api.openai.com/v1/',
        'gpt_model': 'gpt-3.5-turbo',
        'temperature': 0.1,
        'max_tokens': 2000,
        'timeout': 90,
        'query_batch': 10
    }
    
    # 质量评估配置
    QUALITY_THRESHOLDS = {
        'excellent': 80,
        'good': 60,
        'poor': 0
    }
    
    # 生成配置
    MAX_SAMPLES = 10000
    MIN_SAMPLES = 10
    DEFAULT_SAMPLES = 100
    
    # 会话配置
    SESSION_TIMEOUT = 3600  # 1小时
    MAX_SESSIONS = 100
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 创建必要的目录
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.RESULTS_FOLDER, exist_ok=True)
        
        # 设置日志
        import logging
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL),
            format='%(asctime)s %(levelname)s %(name)s %(message)s',
            handlers=[
                logging.FileHandler(Config.LOG_FILE),
                logging.StreamHandler()
            ]
        )

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    
    # 生产环境安全配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    
    # 测试数据库
    DATABASE_URL = 'sqlite:///:memory:'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# 模型配置模板
MODEL_CONFIG_TEMPLATES = {
    'ctgan': {
        'epochs': {
            'type': 'number',
            'default': 50,
            'min': 1,
            'max': 1000,
            'description': '训练轮数，越多训练越充分但耗时越长'
        },
        'batch_size': {
            'type': 'number',
            'default': 500,
            'min': 32,
            'max': 2000,
            'description': '批次大小，影响训练稳定性和速度'
        },
        'generator_lr': {
            'type': 'number',
            'default': 2e-4,
            'min': 1e-6,
            'max': 1e-2,
            'step': 1e-6,
            'description': '生成器学习率，控制生成器学习速度'
        },
        'discriminator_lr': {
            'type': 'number',
            'default': 2e-4,
            'min': 1e-6,
            'max': 1e-2,
            'step': 1e-6,
            'description': '判别器学习率，控制判别器学习速度'
        },
        'generator_decay': {
            'type': 'number',
            'default': 1e-6,
            'min': 0,
            'max': 1e-3,
            'step': 1e-6,
            'description': '生成器权重衰减，防止过拟合'
        },
        'discriminator_decay': {
            'type': 'number',
            'default': 1e-6,
            'min': 0,
            'max': 1e-3,
            'step': 1e-6,
            'description': '判别器权重衰减，防止过拟合'
        },
        'generator_dim': {
            'type': 'text',
            'default': '(256, 256)',
            'description': '生成器网络维度，格式如(256, 256)'
        },
        'discriminator_dim': {
            'type': 'text',
            'default': '(256, 256)',
            'description': '判别器网络维度，格式如(256, 256)'
        }
    },
    
    'gpt': {
        'openai_API_key': {
            'type': 'password',
            'default': '',
            'description': 'OpenAI API密钥，必填'
        },
        'openai_API_url': {
            'type': 'text',
            'default': 'https://api.openai.com/v1/',
            'description': 'API地址，支持自定义端点'
        },
        'gpt_model': {
            'type': 'select',
            'default': 'gpt-3.5-turbo',
            'options': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'],
            'description': 'GPT模型版本，gpt-4效果更好但成本更高'
        },
        'temperature': {
            'type': 'number',
            'default': 0.1,
            'min': 0,
            'max': 2,
            'step': 0.1,
            'description': '创造性参数，0-2之间，越小越保守'
        },
        'max_tokens': {
            'type': 'number',
            'default': 2000,
            'min': 100,
            'max': 8000,
            'description': '最大生成token数，影响生成数据量'
        },
        'timeout': {
            'type': 'number',
            'default': 90,
            'min': 10,
            'max': 300,
            'description': '请求超时时间，网络慢时可增加'
        },
        'query_batch': {
            'type': 'number',
            'default': 10,
            'min': 1,
            'max': 50,
            'description': '批次大小，影响处理效率'
        }
    }
}

# 质量评估配置
QUALITY_METRICS = {
    'statistical_similarity': {
        'name': '统计相似性',
        'weight': 0.4,
        'description': '均值、标准差等统计指标的相似性'
    },
    'distribution_similarity': {
        'name': '分布相似性',
        'weight': 0.3,
        'description': '数据分布的相似性'
    },
    'correlation_similarity': {
        'name': '相关性相似性',
        'weight': 0.2,
        'description': '特征间相关性的相似性'
    },
    'categorical_similarity': {
        'name': '分类相似性',
        'weight': 0.1,
        'description': '分类变量分布的相似性'
    }
}

# 文件类型配置
FILE_TYPE_CONFIG = {
    'csv': {
        'mime_types': ['text/csv', 'application/csv'],
        'extensions': ['.csv'],
        'description': '逗号分隔值文件'
    },
    'excel': {
        'mime_types': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      'application/vnd.ms-excel'],
        'extensions': ['.xlsx', '.xls'],
        'description': 'Excel电子表格文件'
    }
}

# 错误消息配置
ERROR_MESSAGES = {
    'file_too_large': '文件大小超过限制（50MB）',
    'invalid_file_type': '不支持的文件类型',
    'file_upload_failed': '文件上传失败',
    'data_loading_failed': '数据加载失败',
    'model_creation_failed': '模型创建失败',
    'generation_failed': '数据生成失败',
    'evaluation_failed': '质量评估失败',
    'session_expired': '会话已过期',
    'invalid_parameters': '参数配置无效',
    'api_key_required': 'API密钥必填',
    'network_error': '网络连接错误',
    'timeout_error': '请求超时',
    'unknown_error': '未知错误'
}

# 成功消息配置
SUCCESS_MESSAGES = {
    'file_uploaded': '文件上传成功',
    'data_loaded': '数据加载成功',
    'model_created': '模型创建成功',
    'generation_completed': '数据生成完成',
    'evaluation_completed': '质量评估完成',
    'file_downloaded': '文件下载成功'
}
