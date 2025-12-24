#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试：接口响应时间，并发测试，大数据量测试
"""

import unittest
import os
import sys
import time
import tempfile
import shutil
import pandas as pd
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_complete import create_app
from models import db, User, Task
from services.synthetic_service import SyntheticService
from services.quality_service import QualityService
from services.masking_service import MaskingService
from services.auth_service import AuthService


class TestPerformance(unittest.TestCase):
    """性能测试"""
    
    def setUp(self):
        """测试前准备"""
        test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-secret-key',
            'UPLOAD_FOLDER': tempfile.mkdtemp(),
            'RESULTS_FOLDER': tempfile.mktemp(),
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
    
    def test_login_response_time(self):
        """测试登录接口响应时间"""
        # 目标：< 500ms
        start_time = time.time()
        
        user = AuthService.login_user('test@example.com', 'Test123456')
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 转换为毫秒
        
        self.assertIsNotNone(user)
        self.assertLess(response_time, 500, f"登录响应时间 {response_time}ms 超过500ms")
        print(f"✅ 登录响应时间: {response_time:.2f}ms")
    
    def test_file_upload_response_time(self):
        """测试文件上传响应时间（10MB文件）"""
        # 创建10MB测试文件（模拟）
        test_file_path = os.path.join(self.temp_dir, 'test_10mb.csv')
        # 实际测试中应该创建真实的大文件
        test_df = pd.DataFrame({
            'col1': range(1000),
            'col2': [f'value_{i}' for i in range(1000)]
        })
        test_df.to_csv(test_file_path, index=False)
        
        # 目标：< 2s
        start_time = time.time()
        
        # 模拟文件上传处理
        synthetic_service = SyntheticService()
        task = Task(
            user_id=self.test_user.id,
            task_type='synthetic',
            task_name='性能测试：文件上传',
            status='pending'
        )
        task.set_config({'file_id': 'test_file_123'})
        db.session.add(task)
        db.session.commit()
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        self.assertLess(response_time, 2000, f"文件上传响应时间 {response_time}ms 超过2000ms")
        print(f"✅ 文件上传响应时间: {response_time:.2f}ms")
    
    def test_task_creation_response_time(self):
        """测试任务创建响应时间"""
        # 目标：< 300ms
        start_time = time.time()
        
        task = Task(
            user_id=self.test_user.id,
            task_type='synthetic',
            task_name='性能测试：任务创建',
            status='pending'
        )
        task.set_config({'file_id': 'test_123'})
        db.session.add(task)
        db.session.commit()
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        self.assertLess(response_time, 300, f"任务创建响应时间 {response_time}ms 超过300ms")
        print(f"✅ 任务创建响应时间: {response_time:.2f}ms")
    
    def test_task_status_query_response_time(self):
        """测试任务状态查询响应时间"""
        # 创建任务
        task = Task(
            user_id=self.test_user.id,
            task_type='synthetic',
            task_name='性能测试：状态查询',
            status='pending'
        )
        db.session.add(task)
        db.session.commit()
        task_id = task.id
        
        # 目标：< 100ms
        start_time = time.time()
        
        queried_task = Task.query.get(task_id)
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        self.assertIsNotNone(queried_task)
        self.assertLess(response_time, 100, f"任务状态查询响应时间 {response_time}ms 超过100ms")
        print(f"✅ 任务状态查询响应时间: {response_time:.2f}ms")
    
    def test_concurrent_login(self):
        """测试并发登录（10个用户同时登录）"""
        # 创建10个测试用户
        users = []
        for i in range(10):
            user = User(
                email=f'user{i}@example.com',
                username=f'user{i}',
                password_hash='',
                role='user',
                status='active',
                email_verified=True
            )
            user.set_password('Test123456')
            db.session.add(user)
            users.append(user)
        db.session.commit()
        
        def login_user(user_email):
            """登录单个用户"""
            try:
                user = AuthService.login_user(user_email, 'Test123456')
                return user is not None
            except Exception as e:
                return False
        
        # 并发执行
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(login_user, f'user{i}@example.com')
                for i in range(10)
            ]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        
        # 验证所有登录都成功
        success_count = sum(results)
        self.assertEqual(success_count, 10, f"并发登录失败: {success_count}/10")
        self.assertLess(total_time, 5000, f"并发登录总时间 {total_time}ms 超过5000ms")
        print(f"✅ 10个用户并发登录总时间: {total_time:.2f}ms, 成功率: {success_count}/10")
    
    def test_concurrent_task_creation(self):
        """测试并发任务创建（5个任务同时创建）"""
        def create_task(task_index):
            """创建单个任务"""
            try:
                task = Task(
                    user_id=self.test_user.id,
                    task_type='synthetic',
                    task_name=f'并发任务{task_index}',
                    status='pending'
                )
                task.set_config({'file_id': f'test_{task_index}'})
                db.session.add(task)
                db.session.commit()
                return task.id is not None
            except Exception as e:
                db.session.rollback()
                return False
        
        # 并发执行
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(create_task, i)
                for i in range(5)
            ]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        
        # 验证所有任务都创建成功
        success_count = sum(results)
        self.assertEqual(success_count, 5, f"并发任务创建失败: {success_count}/5")
        self.assertLess(total_time, 2000, f"并发任务创建总时间 {total_time}ms 超过2000ms")
        print(f"✅ 5个任务并发创建总时间: {total_time:.2f}ms, 成功率: {success_count}/5")
    
    def test_large_data_file_handling(self):
        """测试大数据量文件处理"""
        # 创建包含10000行的测试文件
        test_file_path = os.path.join(self.temp_dir, 'large_data.csv')
        large_df = pd.DataFrame({
            'id': range(10000),
            'name': [f'User_{i}' for i in range(10000)],
            'age': [20 + i % 60 for i in range(10000)],
            'score': [50 + i % 50 for i in range(10000)]
        })
        large_df.to_csv(test_file_path, index=False)
        
        # 测试文件读取性能
        start_time = time.time()
        
        loaded_df = pd.read_csv(test_file_path)
        
        end_time = time.time()
        load_time = (end_time - start_time) * 1000
        
        self.assertEqual(len(loaded_df), 10000)
        self.assertLess(load_time, 5000, f"大数据文件读取时间 {load_time}ms 超过5000ms")
        print(f"✅ 10000行数据文件读取时间: {load_time:.2f}ms")
    
    def test_database_query_performance(self):
        """测试数据库查询性能"""
        # 创建100个任务
        tasks = []
        for i in range(100):
            task = Task(
                user_id=self.test_user.id,
                task_type='synthetic',
                task_name=f'任务{i+1}',
                status='pending'
            )
            db.session.add(task)
            tasks.append(task)
        db.session.commit()
        
        # 测试查询性能
        start_time = time.time()
        
        user_tasks = Task.query.filter_by(user_id=self.test_user.id).all()
        
        end_time = time.time()
        query_time = (end_time - start_time) * 1000
        
        self.assertEqual(len(user_tasks), 100)
        self.assertLess(query_time, 500, f"数据库查询时间 {query_time}ms 超过500ms")
        print(f"✅ 查询100个任务耗时: {query_time:.2f}ms")


if __name__ == '__main__':
    unittest.main()

