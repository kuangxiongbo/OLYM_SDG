#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
"""

import os
from datetime import timedelta

# 加载环境变量（从 .env 文件）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果 python-dotenv 未安装，跳过（依赖项中已包含）
    pass

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ai_data_platform.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session 配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json'}
    
    # 结果文件存储
    RESULTS_FOLDER = os.path.join(os.path.dirname(__file__), 'results')
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.qq.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 465)
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'true').lower() == 'true'
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # 激活码配置
    ACTIVATION_CODE_EXPIRES_HOURS = 24
    
    # SDGX 配置
    SDGX_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'synthetic-data-generator')
    
    # 任务配置
    TASK_TIMEOUT_SECONDS = 3600  # 1小时
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 创建必要的目录
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.RESULTS_FOLDER, exist_ok=True)
