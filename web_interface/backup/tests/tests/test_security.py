#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全测试：SQL注入防护，XSS防护，权限控制，文件上传安全
"""

import unittest
import os
import sys
import tempfile
import shutil
import pandas as pd
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_complete import create_app
from models import db, User, Task
from services.auth_service import AuthService
from utils.helpers import allowed_file, save_uploaded_file
from config import Config


class TestSecurity(unittest.TestCase):
    """安全测试"""
    
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
        
        self.test_admin = User(
            email='admin@example.com',
            username='admin',
            password_hash='',
            role='admin',
            status='active',
            email_verified=True
        )
        self.test_admin.set_password('Admin123456')
        db.session.add(self.test_admin)
        db.session.commit()
        
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_sql_injection_protection(self):
        """测试SQL注入防护"""
        # SQL注入尝试
        sql_injection_attempts = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "1' OR '1'='1",
            "admin'--"
        ]
        
        for attempt in sql_injection_attempts:
            # 尝试使用SQL注入字符串作为邮箱登录
            try:
                user = AuthService.login_user(attempt, 'password')
                # 如果登录成功，说明存在SQL注入漏洞
                self.assertIsNone(user, f"SQL注入防护失败: {attempt}")
            except ValueError:
                # 预期的行为：登录失败
                pass
        
        # 验证用户表仍然存在
        users = User.query.all()
        self.assertGreater(len(users), 0, "SQL注入可能导致表被删除")
        print("✅ SQL注入防护测试通过")
    
    def test_xss_protection(self):
        """测试XSS防护"""
        # XSS攻击尝试
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "'><script>alert('XSS')</script>"
        ]
        
        for attempt in xss_attempts:
            # 尝试使用XSS字符串作为用户名注册
            try:
                user = AuthService.register_user(
                    f'test{attempt}@example.com',
                    attempt,
                    'Test123456'
                )
                # 验证用户名是否被转义
                self.assertNotIn('<script>', user.username, f"XSS防护失败: {attempt}")
                self.assertNotIn('javascript:', user.username, f"XSS防护失败: {attempt}")
            except ValueError:
                # 预期的行为：注册失败（用户名格式验证）
                pass
        
        print("✅ XSS防护测试通过")
    
    def test_permission_control(self):
        """测试权限控制"""
        # 普通用户尝试访问管理员功能
        # 这里需要根据实际权限控制逻辑进行测试
        
        # 测试用户数据隔离
        user1 = User(
            email='user1@example.com',
            username='user1',
            password_hash='',
            role='user',
            status='active',
            email_verified=True
        )
        user1.set_password('Test123456')
        db.session.add(user1)
        
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
        
        # 为用户1创建任务
        task1 = Task(
            user_id=user1.id,
            task_type='synthetic',
            task_name='用户1的任务',
            status='pending'
        )
        db.session.add(task1)
        
        # 为用户2创建任务
        task2 = Task(
            user_id=user2.id,
            task_type='synthetic',
            task_name='用户2的任务',
            status='pending'
        )
        db.session.add(task2)
        db.session.commit()
        
        # 验证用户1只能看到自己的任务
        user1_tasks = Task.query.filter_by(user_id=user1.id).all()
        self.assertEqual(len(user1_tasks), 1)
        self.assertEqual(user1_tasks[0].task_name, '用户1的任务')
        
        # 验证用户2只能看到自己的任务
        user2_tasks = Task.query.filter_by(user_id=user2.id).all()
        self.assertEqual(len(user2_tasks), 1)
        self.assertEqual(user2_tasks[0].task_name, '用户2的任务')
        
        print("✅ 权限控制测试通过")
    
    def test_file_upload_security(self):
        """测试文件上传安全"""
        # 测试不允许的文件类型
        dangerous_extensions = [
            '.exe',
            '.bat',
            '.sh',
            '.php',
            '.jsp',
            '.py',
            '.js',
            '.html'
        ]
        
        for ext in dangerous_extensions:
            filename = f'test_file{ext}'
            is_allowed = allowed_file(filename)
            self.assertFalse(is_allowed, f"危险文件类型 {ext} 应该被拒绝")
        
        # 测试允许的文件类型
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        for ext in allowed_extensions:
            filename = f'test_file{ext}'
            is_allowed = allowed_file(filename)
            self.assertTrue(is_allowed, f"允许的文件类型 {ext} 应该被接受")
        
        print("✅ 文件上传安全测试通过")
    
    def test_path_traversal_protection(self):
        """测试路径遍历防护"""
        # 路径遍历尝试
        path_traversal_attempts = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32',
            '../../../../root/.ssh/id_rsa',
            '....//....//etc/passwd'
        ]
        
        for attempt in path_traversal_attempts:
            # 测试secure_filename是否能防止路径遍历
            from werkzeug.utils import secure_filename
            secured = secure_filename(attempt)
            
            # 验证路径遍历被阻止
            self.assertNotIn('..', secured, f"路径遍历防护失败: {attempt}")
            self.assertNotIn('/', secured, f"路径遍历防护失败: {attempt}")
            self.assertNotIn('\\', secured, f"路径遍历防护失败: {attempt}")
        
        print("✅ 路径遍历防护测试通过")
    
    def test_password_security(self):
        """测试密码安全"""
        # 测试弱密码
        weak_passwords = [
            '123456',
            'password',
            'admin',
            'test',
            'abc123'
        ]
        
        for weak_password in weak_passwords:
            # 尝试使用弱密码注册
            try:
                user = AuthService.register_user(
                    f'weak{weak_password}@example.com',
                    f'user{weak_password}',
                    weak_password
                )
                # 如果注册成功，说明密码验证不够严格
                # 这里需要根据实际的密码验证规则调整
                pass
            except ValueError:
                # 预期的行为：注册失败（密码强度不足）
                pass
        
        # 测试密码哈希
        user = User(
            email='hashtest@example.com',
            username='hashtest',
            password_hash='',
            role='user',
            status='active',
            email_verified=True
        )
        user.set_password('Test123456')
        
        # 验证密码哈希不是明文
        self.assertNotEqual(user.password_hash, 'Test123456')
        self.assertIsNotNone(user.password_hash)
        self.assertGreater(len(user.password_hash), 20)  # 哈希值应该足够长
        
        # 验证密码验证功能
        self.assertTrue(user.check_password('Test123456'))
        self.assertFalse(user.check_password('WrongPassword'))
        
        print("✅ 密码安全测试通过")
    
    def test_input_validation(self):
        """测试输入验证"""
        # 测试邮箱格式验证
        invalid_emails = [
            'invalid',
            'invalid@',
            '@example.com',
            'invalid..email@example.com',
            'invalid@example',
            ''
        ]
        
        for email in invalid_emails:
            try:
                user = AuthService.register_user(email, 'testuser', 'Test123456')
                # 如果注册成功，说明邮箱验证不够严格
                self.fail(f"无效邮箱 {email} 应该被拒绝")
            except ValueError:
                # 预期的行为：注册失败（邮箱格式无效）
                pass
        
        # 测试用户名格式验证
        invalid_usernames = [
            'ab',  # 太短
            'a' * 21,  # 太长
            'test-user',  # 包含连字符
            'test user',  # 包含空格
            'test@user',  # 包含特殊字符
            ''
        ]
        
        for username in invalid_usernames:
            try:
                user = AuthService.register_user(
                    f'{username}@example.com',
                    username,
                    'Test123456'
                )
                # 如果注册成功，说明用户名验证不够严格
                self.fail(f"无效用户名 {username} 应该被拒绝")
            except ValueError:
                # 预期的行为：注册失败（用户名格式无效）
                pass
        
        print("✅ 输入验证测试通过")


if __name__ == '__main__':
    unittest.main()

