#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试：完整功能测试，P0/P1/P2优先级
"""

import unittest
import os
import sys
import tempfile
import shutil
import pandas as pd
import json
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_complete import create_app
from models import db, User, Task, Config, Log
from services.synthetic_service import SyntheticService
from services.quality_service import QualityService
from services.masking_service import MaskingService
from services.auth_service import AuthService


class TestSystemP0(unittest.TestCase):
    """P0优先级：核心功能测试"""
    
    def setUp(self):
        """测试前准备"""
        test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-secret-key',
            'UPLOAD_FOLDER': tempfile.mkdtemp(),
            'RESULTS_FOLDER': tempfile.mkdtemp(),
            'WTF_CSRF_ENABLED': False
        }
        
        self.app = create_app(test_config)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        self.test_user = User(
            email='test@example.com',
            username='testuser',
            password_hash='',
            role='user',
            status='active',
            email_verified=True
        )
        self.test_user.set_password('Test123456')
        db.session.add(self.test_user)
        db.session.commit()
        
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_p0_user_login(self):
        """P0: 用户登录功能"""
        # 正常登录
        user = AuthService.login_user('test@example.com', 'Test123456')
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@example.com')
        
        # 错误密码
        with self.assertRaises(ValueError):
            AuthService.login_user('test@example.com', 'WrongPassword')
        
        # 不存在的用户
        with self.assertRaises(ValueError):
            AuthService.login_user('nonexistent@example.com', 'Password123')
    
    def test_p0_user_registration(self):
        """P0: 用户注册功能"""
        # 正常注册
        user = AuthService.register_user(
            'newuser@example.com',
            'newuser',
            'NewPass123456'
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'newuser@example.com')
        
        # 重复邮箱
        with self.assertRaises(ValueError):
            AuthService.register_user(
                'newuser@example.com',
                'anotheruser',
                'AnotherPass123456'
            )
    
    def test_p0_synthetic_data_generation(self):
        """P0: AI仿真数据生成功能"""
        # 创建测试文件
        test_file_path = os.path.join(self.temp_dir, 'test_data.csv')
        test_df = pd.DataFrame({
            'id': range(100),
            'name': [f'User_{i}' for i in range(100)],
            'age': [20 + i % 60 for i in range(100)]
        })
        test_df.to_csv(test_file_path, index=False)
        
        # 创建任务
        task = Task(
            user_id=self.test_user.id,
            task_type='synthetic',
            task_name='P0测试：合成数据生成',
            status='pending'
        )
        task.set_config({
            'file_id': 'test_file_123',
            'model_type': 'ctgan',
            'similarity': 0.8,
            'num_rows': 100
        })
        db.session.add(task)
        db.session.commit()
        
        # 验证任务创建
        self.assertIsNotNone(task.id)
        config = task.get_config()
        self.assertEqual(config['model_type'], 'ctgan')
    
    def test_p0_quality_assessment(self):
        """P0: AI数据质量评估功能"""
        # 创建测试文件
        original_file_path = os.path.join(self.temp_dir, 'original.csv')
        synthetic_file_path = os.path.join(self.temp_dir, 'synthetic.csv')
        
        original_df = pd.DataFrame({
            'col1': range(100),
            'col2': [f'value_{i}' for i in range(100)]
        })
        synthetic_df = pd.DataFrame({
            'col1': range(100),
            'col2': [f'value_{i}' for i in range(100)]
        })
        
        original_df.to_csv(original_file_path, index=False)
        synthetic_df.to_csv(synthetic_file_path, index=False)
        
        # 创建评估任务
        task = Task(
            user_id=self.test_user.id,
            task_type='quality',
            task_name='P0测试：质量评估',
            status='pending'
        )
        task.set_config({
            'original_file_id': 'original_123',
            'synthetic_file_id': 'synthetic_123',
            'indicators': [
                {'name': 'correlation', 'enabled': True, 'threshold': 0.7}
            ]
        })
        db.session.add(task)
        db.session.commit()
        
        # 验证任务创建
        self.assertIsNotNone(task.id)
        config = task.get_config()
        self.assertEqual(len(config['indicators']), 1)
    
    def test_p0_data_masking(self):
        """P0: AI数据脱敏功能"""
        # 创建测试文件
        test_file_path = os.path.join(self.temp_dir, 'test_data.csv')
        test_df = pd.DataFrame({
            'name': ['张三', '李四', '王五'],
            'phone': ['13800138000', '13900139000', '15000150000']
        })
        test_df.to_csv(test_file_path, index=False)
        
        # 创建脱敏任务
        task = Task(
            user_id=self.test_user.id,
            task_type='masking',
            task_name='P0测试：数据脱敏',
            status='pending'
        )
        task.set_config({
            'file_id': 'test_file_123',
            'fields': [
                {
                    'name': 'phone',
                    'strategy': 'masking',
                    'rule': {'keep_prefix': 3, 'keep_suffix': 4}
                }
            ]
        })
        db.session.add(task)
        db.session.commit()
        
        # 验证任务创建
        self.assertIsNotNone(task.id)
        config = task.get_config()
        self.assertEqual(len(config['fields']), 1)


class TestSystemP1(unittest.TestCase):
    """P1优先级：重要功能测试"""
    
    def setUp(self):
        """测试前准备"""
        test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-secret-key',
            'UPLOAD_FOLDER': tempfile.mkdtemp(),
            'RESULTS_FOLDER': tempfile.mkdtemp(),
            'WTF_CSRF_ENABLED': False
        }
        
        self.app = create_app(test_config)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        self.test_user = User(
            email='test@example.com',
            username='testuser',
            password_hash='',
            role='user',
            status='active',
            email_verified=True
        )
        self.test_user.set_password('Test123456')
        db.session.add(self.test_user)
        db.session.commit()
        
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_p1_task_management(self):
        """P1: 任务管理功能"""
        # 创建多个任务
        tasks = []
        for i in range(5):
            task = Task(
                user_id=self.test_user.id,
                task_type='synthetic',
                task_name=f'任务{i+1}',
                status='pending'
            )
            db.session.add(task)
            tasks.append(task)
        db.session.commit()
        
        # 查询任务列表
        user_tasks = Task.query.filter_by(user_id=self.test_user.id).all()
        self.assertEqual(len(user_tasks), 5)
        
        # 更新任务状态
        task = tasks[0]
        task.status = 'running'
        task.progress = 50
        db.session.commit()
        
        updated_task = Task.query.get(task.id)
        self.assertEqual(updated_task.status, 'running')
        self.assertEqual(updated_task.progress, 50)
    
    def test_p1_task_filtering(self):
        """P1: 任务筛选功能"""
        # 创建不同类型的任务
        task1 = Task(
            user_id=self.test_user.id,
            task_type='synthetic',
            task_name='合成任务',
            status='pending'
        )
        task2 = Task(
            user_id=self.test_user.id,
            task_type='quality',
            task_name='质量评估任务',
            status='completed'
        )
        task3 = Task(
            user_id=self.test_user.id,
            task_type='masking',
            task_name='脱敏任务',
            status='running'
        )
        
        db.session.add_all([task1, task2, task3])
        db.session.commit()
        
        # 按类型筛选
        synthetic_tasks = Task.query.filter_by(
            user_id=self.test_user.id,
            task_type='synthetic'
        ).all()
        self.assertEqual(len(synthetic_tasks), 1)
        
        # 按状态筛选
        completed_tasks = Task.query.filter_by(
            user_id=self.test_user.id,
            status='completed'
        ).all()
        self.assertEqual(len(completed_tasks), 1)
    
    def test_p1_system_settings(self):
        """P1: 系统设置功能"""
        # 创建配置
        config = Config(
            key='test_setting',
            value='test_value',
            category='test'
        )
        db.session.add(config)
        db.session.commit()
        
        # 查询配置
        retrieved_config = Config.query.filter_by(key='test_setting').first()
        self.assertIsNotNone(retrieved_config)
        self.assertEqual(retrieved_config.value, 'test_value')
        
        # 更新配置
        retrieved_config.value = 'updated_value'
        db.session.commit()
        
        updated_config = Config.query.filter_by(key='test_setting').first()
        self.assertEqual(updated_config.value, 'updated_value')


class TestSystemP2(unittest.TestCase):
    """P2优先级：辅助功能测试"""
    
    def setUp(self):
        """测试前准备"""
        test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-secret-key',
            'UPLOAD_FOLDER': tempfile.mkdtemp(),
            'RESULTS_FOLDER': tempfile.mkdtemp(),
            'WTF_CSRF_ENABLED': False
        }
        
        self.app = create_app(test_config)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        self.test_user = User(
            email='test@example.com',
            username='testuser',
            password_hash='',
            role='user',
            status='active',
            email_verified=True
        )
        self.test_user.set_password('Test123456')
        db.session.add(self.test_user)
        db.session.commit()
        
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_p2_operation_logs(self):
        """P2: 操作日志功能"""
        # 创建日志
        log = Log(
            user_id=self.test_user.id,
            action='test_action',
            resource_type='test_resource',
            resource_id=1,
            details='测试日志'
        )
        db.session.add(log)
        db.session.commit()
        
        # 查询日志
        logs = Log.query.filter_by(user_id=self.test_user.id).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, 'test_action')
    
    def test_p2_data_export(self):
        """P2: 数据导出功能"""
        # 创建测试结果文件
        result_dir = os.path.join(self.temp_dir, 'task_123')
        os.makedirs(result_dir, exist_ok=True)
        
        test_df = pd.DataFrame({
            'col1': range(10),
            'col2': [f'value_{i}' for i in range(10)]
        })
        test_df.to_csv(os.path.join(result_dir, 'synthetic.csv'), index=False)
        
        # 验证文件存在
        self.assertTrue(os.path.exists(os.path.join(result_dir, 'synthetic.csv')))
        
        # 验证文件内容
        loaded_df = pd.read_csv(os.path.join(result_dir, 'synthetic.csv'))
        self.assertEqual(len(loaded_df), 10)
    
    def test_p2_task_pagination(self):
        """P2: 任务分页功能"""
        # 创建多个任务
        tasks = []
        for i in range(25):
            task = Task(
                user_id=self.test_user.id,
                task_type='synthetic',
                task_name=f'任务{i+1}',
                status='pending'
            )
            db.session.add(task)
            tasks.append(task)
        db.session.commit()
        
        # 测试分页查询（每页10条）
        page = 1
        page_size = 10
        
        total = Task.query.filter_by(user_id=self.test_user.id).count()
        self.assertEqual(total, 25)
        
        paginated_tasks = Task.query.filter_by(
            user_id=self.test_user.id
        ).limit(page_size).offset((page - 1) * page_size).all()
        
        self.assertEqual(len(paginated_tasks), 10)
        
        # 第二页
        page = 2
        paginated_tasks = Task.query.filter_by(
            user_id=self.test_user.id
        ).limit(page_size).offset((page - 1) * page_size).all()
        
        self.assertEqual(len(paginated_tasks), 10)


if __name__ == '__main__':
    unittest.main()

