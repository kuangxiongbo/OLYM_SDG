#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试：模块间交互测试，完整流程测试
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


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试应用
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
        
        # 创建数据库表
        db.create_all()
        
        # 创建测试用户
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
    
    def test_user_registration_to_login_flow(self):
        """测试用户注册到登录的完整流程"""
        # 1. 用户注册
        new_user = AuthService.register_user(
            'newuser@example.com',
            'newuser',
            'NewPass123456'
        )
        
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.email, 'newuser@example.com')
        self.assertEqual(new_user.status, 'pending')
        
        # 2. 邮箱验证
        verified = AuthService.verify_email('newuser@example.com')
        self.assertTrue(verified)
        
        # 验证用户状态已更新
        db.session.refresh(new_user)
        self.assertTrue(new_user.email_verified)
        self.assertEqual(new_user.status, 'active')
        
        # 3. 用户登录
        logged_in_user = AuthService.login_user(
            'newuser@example.com',
            'NewPass123456'
        )
        
        self.assertIsNotNone(logged_in_user)
        self.assertEqual(logged_in_user.email, 'newuser@example.com')
    
    def test_file_upload_to_synthetic_generation_flow(self):
        """测试文件上传到合成数据生成的完整流程"""
        # 1. 创建测试文件
        test_file_path = os.path.join(self.temp_dir, 'test_data.csv')
        test_df = pd.DataFrame({
            'id': range(100),
            'name': [f'User_{i}' for i in range(100)],
            'age': [20 + i % 60 for i in range(100)],
            'score': [50 + i % 50 for i in range(100)]
        })
        test_df.to_csv(test_file_path, index=False)
        
        # 2. 模拟文件上传（创建任务）
        synthetic_service = SyntheticService()
        
        # 模拟任务创建
        task = Task(
            user_id=self.test_user.id,
            task_type='synthetic',
            task_name='测试合成数据生成',
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
        
        # 3. 验证任务已创建
        self.assertIsNotNone(task.id)
        self.assertEqual(task.status, 'pending')
        
        # 4. 验证任务配置
        config = task.get_config()
        self.assertEqual(config['model_type'], 'ctgan')
        self.assertEqual(config['similarity'], 0.8)
    
    def test_quality_assessment_flow(self):
        """测试数据质量评估的完整流程"""
        # 1. 创建原始数据和合成数据文件
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
        
        # 2. 创建评估任务
        quality_service = QualityService()
        
        task = Task(
            user_id=self.test_user.id,
            task_type='quality',
            task_name='测试质量评估',
            status='pending'
        )
        task.set_config({
            'original_file_id': 'original_123',
            'synthetic_file_id': 'synthetic_123',
            'indicators': [
                {'name': 'correlation', 'enabled': True, 'threshold': 0.7},
                {'name': 'distribution_similarity', 'enabled': True, 'threshold': 0.7}
            ]
        })
        db.session.add(task)
        db.session.commit()
        
        # 3. 验证任务配置
        config = task.get_config()
        self.assertEqual(len(config['indicators']), 2)
        self.assertTrue(config['indicators'][0]['enabled'])
    
    def test_masking_flow(self):
        """测试数据脱敏的完整流程"""
        # 1. 创建测试数据文件
        test_file_path = os.path.join(self.temp_dir, 'test_data.csv')
        test_df = pd.DataFrame({
            'name': ['张三', '李四', '王五'],
            'phone': ['13800138000', '13900139000', '15000150000'],
            'email': ['zhang@example.com', 'li@example.com', 'wang@example.com']
        })
        test_df.to_csv(test_file_path, index=False)
        
        # 2. 创建脱敏任务
        masking_service = MaskingService()
        
        task = Task(
            user_id=self.test_user.id,
            task_type='masking',
            task_name='测试数据脱敏',
            status='pending'
        )
        task.set_config({
            'file_id': 'test_file_123',
            'fields': [
                {
                    'name': 'name',
                    'strategy': 'simulation',
                    'rule': {}
                },
                {
                    'name': 'phone',
                    'strategy': 'masking',
                    'rule': {'keep_prefix': 3, 'keep_suffix': 4}
                }
            ]
        })
        db.session.add(task)
        db.session.commit()
        
        # 3. 验证任务配置
        config = task.get_config()
        self.assertEqual(len(config['fields']), 2)
        self.assertEqual(config['fields'][0]['strategy'], 'simulation')
        self.assertEqual(config['fields'][1]['strategy'], 'masking')
    
    def test_task_creation_to_status_update_flow(self):
        """测试任务创建到状态更新的流程"""
        # 1. 创建任务
        task = Task(
            user_id=self.test_user.id,
            task_type='synthetic',
            task_name='测试任务',
            status='pending'
        )
        db.session.add(task)
        db.session.commit()
        
        task_id = task.id
        
        # 2. 更新任务状态
        task.status = 'running'
        task.progress = 50
        db.session.commit()
        
        # 3. 验证状态更新
        updated_task = Task.query.get(task_id)
        self.assertEqual(updated_task.status, 'running')
        self.assertEqual(updated_task.progress, 50)
        
        # 4. 完成任务
        updated_task.status = 'completed'
        updated_task.progress = 100
        updated_task.result_path = '/path/to/results'
        db.session.commit()
        
        # 5. 验证完成状态
        completed_task = Task.query.get(task_id)
        self.assertEqual(completed_task.status, 'completed')
        self.assertEqual(completed_task.progress, 100)
        self.assertIsNotNone(completed_task.result_path)
    
    def test_config_storage_and_retrieval(self):
        """测试配置存储和检索"""
        # 1. 创建任务并设置配置
        task = Task(
            user_id=self.test_user.id,
            task_type='synthetic',
            task_name='测试任务',
            status='pending'
        )
        
        config = {
            'file_id': 'test_123',
            'model_type': 'ctgan',
            'similarity': 0.8,
            'num_rows': 100,
            'nested': {
                'key1': 'value1',
                'key2': [1, 2, 3]
            }
        }
        
        task.set_config(config)
        db.session.add(task)
        db.session.commit()
        
        # 2. 检索配置
        retrieved_config = task.get_config()
        
        # 3. 验证配置
        self.assertEqual(retrieved_config['file_id'], 'test_123')
        self.assertEqual(retrieved_config['model_type'], 'ctgan')
        self.assertEqual(retrieved_config['similarity'], 0.8)
        self.assertEqual(retrieved_config['nested']['key1'], 'value1')
        self.assertEqual(retrieved_config['nested']['key2'], [1, 2, 3])
    
    def test_user_data_isolation(self):
        """测试用户数据隔离"""
        # 1. 创建第二个用户
        user2 = User(
            email='user2@example.com',
            username='user2',
            password_hash='',
            role='user',
            status='active',
            email_verified=True
        )
        user2.set_password('Test123456')
        db.session.add(user2)
        db.session.commit()
        
        # 2. 为两个用户创建任务
        task1 = Task(
            user_id=self.test_user.id,
            task_type='synthetic',
            task_name='用户1的任务',
            status='pending'
        )
        db.session.add(task1)
        
        task2 = Task(
            user_id=user2.id,
            task_type='synthetic',
            task_name='用户2的任务',
            status='pending'
        )
        db.session.add(task2)
        db.session.commit()
        
        # 3. 验证用户1只能看到自己的任务
        user1_tasks = Task.query.filter_by(user_id=self.test_user.id).all()
        self.assertEqual(len(user1_tasks), 1)
        self.assertEqual(user1_tasks[0].task_name, '用户1的任务')
        
        # 4. 验证用户2只能看到自己的任务
        user2_tasks = Task.query.filter_by(user_id=user2.id).all()
        self.assertEqual(len(user2_tasks), 1)
        self.assertEqual(user2_tasks[0].task_name, '用户2的任务')


if __name__ == '__main__':
    unittest.main()

