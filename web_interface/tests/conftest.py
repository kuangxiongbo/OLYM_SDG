#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest配置文件
提供测试fixtures和配置
"""

import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_complete import create_app
from models import db, User, Task, Config, Log
from config import Config as AppConfig


@pytest.fixture(scope='session')
def app():
    """创建Flask应用实例"""
    # 使用测试配置
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'UPLOAD_FOLDER': tempfile.mkdtemp(),
        'RESULTS_FOLDER': tempfile.mkdtemp(),
        'WTF_CSRF_ENABLED': False
    }
    
    app = create_app(test_config)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    # 清理临时目录
    if os.path.exists(test_config['UPLOAD_FOLDER']):
        shutil.rmtree(test_config['UPLOAD_FOLDER'])
    if os.path.exists(test_config['RESULTS_FOLDER']):
        shutil.rmtree(test_config['RESULTS_FOLDER'])


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建CLI运行器"""
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """创建数据库会话"""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        email='test@example.com',
        username='testuser',
        password_hash='',
        role='user',
        status='active',
        email_verified=True
    )
    user.set_password('Test123456')
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture
def test_admin(db_session):
    """创建测试管理员"""
    admin = User(
        email='admin@example.com',
        username='admin',
        password_hash='',
        role='admin',
        status='active',
        email_verified=True
    )
    admin.set_password('Admin123456')
    db_session.session.add(admin)
    db_session.session.commit()
    return admin


@pytest.fixture
def temp_upload_folder():
    """创建临时上传文件夹"""
    folder = tempfile.mkdtemp()
    yield folder
    if os.path.exists(folder):
        shutil.rmtree(folder)


@pytest.fixture
def temp_results_folder():
    """创建临时结果文件夹"""
    folder = tempfile.mkdtemp()
    yield folder
    if os.path.exists(folder):
        shutil.rmtree(folder)

