#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证服务单元测试
"""

import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService
from models import User, UserStatus, UserRole
from utils.validators import validate_email, validate_password


class TestAuthService(unittest.TestCase):
    """认证服务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_email = 'test@example.com'
        self.test_username = 'testuser'
        self.test_password = 'Test123456'
    
    def test_validate_username(self):
        """测试用户名验证"""
        # 有效用户名
        self.assertTrue(AuthService._validate_username('testuser'))
        self.assertTrue(AuthService._validate_username('user123'))
        self.assertTrue(AuthService._validate_username('test_user'))
        
        # 无效用户名
        self.assertFalse(AuthService._validate_username('ab'))  # 太短
        self.assertFalse(AuthService._validate_username('a' * 21))  # 太长
        self.assertFalse(AuthService._validate_username('test-user'))  # 包含连字符
        self.assertFalse(AuthService._validate_username('test user'))  # 包含空格
        self.assertFalse(AuthService._validate_username(''))  # 空字符串
    
    def test_validate_email_helper(self):
        """测试邮箱验证辅助函数"""
        # 有效邮箱
        self.assertTrue(validate_email('test@example.com'))
        self.assertTrue(validate_email('user.name@example.co.uk'))
        
        # 无效邮箱
        self.assertFalse(validate_email('invalid'))
        self.assertFalse(validate_email('invalid@'))
        self.assertFalse(validate_email('@example.com'))
    
    def test_validate_password_helper(self):
        """测试密码验证辅助函数"""
        # 有效密码
        self.assertTrue(validate_password('Test123456'))
        self.assertTrue(validate_password('Password1'))
        
        # 无效密码（需要根据实际验证规则调整）
        # 如果密码验证要求最小长度，测试短密码
        # self.assertFalse(validate_password('short'))
    
    @patch('services.auth_service.User')
    @patch('services.auth_service.db')
    @patch('services.auth_service.validate_email')
    @patch('services.auth_service.validate_password')
    def test_register_user_success(self, mock_validate_password, mock_validate_email, mock_db, mock_user):
        """测试用户注册成功"""
        # 设置mock
        mock_validate_email.return_value = True
        mock_validate_password.return_value = True
        mock_user.query.filter_by.return_value.first.return_value = None  # 用户不存在
        
        # 创建mock用户对象
        mock_user_instance = Mock()
        mock_user_instance.set_password = Mock()
        mock_user.return_value = mock_user_instance
        
        # 执行注册
        user = AuthService.register_user(self.test_email, self.test_username, self.test_password)
        
        # 验证
        self.assertIsNotNone(user)
        mock_validate_email.assert_called_once_with(self.test_email)
        mock_validate_password.assert_called_once_with(self.test_password)
        mock_user_instance.set_password.assert_called_once_with(self.test_password)
    
    @patch('services.auth_service.User')
    @patch('services.auth_service.validate_email')
    def test_register_user_invalid_email(self, mock_validate_email, mock_user):
        """测试注册时邮箱格式无效"""
        mock_validate_email.return_value = False
        
        with self.assertRaises(ValueError) as context:
            AuthService.register_user(self.test_email, self.test_username, self.test_password)
        
        self.assertIn('无效的邮箱格式', str(context.exception))
    
    @patch('services.auth_service.User')
    @patch('services.auth_service.validate_email')
    @patch('services.auth_service.validate_password')
    def test_register_user_invalid_password(self, mock_validate_password, mock_validate_email, mock_user):
        """测试注册时密码强度不足"""
        mock_validate_email.return_value = True
        mock_validate_password.return_value = False
        
        with self.assertRaises(ValueError) as context:
            AuthService.register_user(self.test_email, self.test_username, self.test_password)
        
        self.assertIn('密码强度不足', str(context.exception))
    
    @patch('services.auth_service.User')
    @patch('services.auth_service.validate_email')
    @patch('services.auth_service.validate_password')
    def test_register_user_duplicate_email(self, mock_validate_password, mock_validate_email, mock_user):
        """测试注册时邮箱已存在"""
        mock_validate_email.return_value = True
        mock_validate_password.return_value = True
        
        # 模拟用户已存在
        existing_user = Mock()
        mock_user.query.filter_by.return_value.first.return_value = existing_user
        
        with self.assertRaises(ValueError) as context:
            AuthService.register_user(self.test_email, self.test_username, self.test_password)
        
        self.assertIn('邮箱已被注册', str(context.exception))
    
    @patch('services.auth_service.User')
    @patch('services.auth_service.login_user')
    def test_login_user_success(self, mock_login_user, mock_user):
        """测试用户登录成功"""
        # 创建mock用户
        mock_user_instance = Mock()
        mock_user_instance.check_password.return_value = True
        mock_user_instance.status = UserStatus.ACTIVE
        mock_user_instance.email_verified = True
        mock_user_instance.reset_login_attempts = Mock()
        
        mock_user.query.filter_by.return_value.first.return_value = mock_user_instance
        
        # 执行登录
        user = AuthService.login_user(self.test_email, self.test_password)
        
        # 验证
        self.assertIsNotNone(user)
        mock_user_instance.check_password.assert_called_once_with(self.test_password)
        mock_user_instance.reset_login_attempts.assert_called_once()
        mock_login_user.assert_called_once_with(mock_user_instance)
    
    @patch('services.auth_service.User')
    def test_login_user_wrong_password(self, mock_user):
        """测试登录时密码错误"""
        # 创建mock用户
        mock_user_instance = Mock()
        mock_user_instance.check_password.return_value = False
        mock_user_instance.increment_login_attempts = Mock()
        
        mock_user.query.filter_by.return_value.first.return_value = mock_user_instance
        
        # 执行登录
        with self.assertRaises(ValueError) as context:
            AuthService.login_user(self.test_email, 'wrong_password')
        
        self.assertIn('邮箱或密码错误', str(context.exception))
        mock_user_instance.increment_login_attempts.assert_called_once()
    
    @patch('services.auth_service.User')
    def test_login_user_banned(self, mock_user):
        """测试登录时账号被禁用"""
        # 创建mock用户
        mock_user_instance = Mock()
        mock_user_instance.check_password.return_value = True
        mock_user_instance.status = UserStatus.BANNED
        
        mock_user.query.filter_by.return_value.first.return_value = mock_user_instance
        
        # 执行登录
        with self.assertRaises(ValueError) as context:
            AuthService.login_user(self.test_email, self.test_password)
        
        self.assertIn('账号已被禁用', str(context.exception))
    
    @patch('services.auth_service.User')
    def test_login_user_not_verified(self, mock_user):
        """测试登录时邮箱未验证"""
        # 创建mock用户
        mock_user_instance = Mock()
        mock_user_instance.check_password.return_value = True
        mock_user_instance.status = UserStatus.ACTIVE
        mock_user_instance.email_verified = False
        
        mock_user.query.filter_by.return_value.first.return_value = mock_user_instance
        
        # 执行登录
        with self.assertRaises(ValueError) as context:
            AuthService.login_user(self.test_email, self.test_password)
        
        self.assertIn('请先验证邮箱', str(context.exception))
    
    @patch('services.auth_service.User')
    @patch('services.auth_service.db')
    def test_verify_email_success(self, mock_db, mock_user):
        """测试邮箱验证成功"""
        # 创建mock用户
        mock_user_instance = Mock()
        mock_user_instance.email_verified = False
        
        mock_user.query.filter_by.return_value.first.return_value = mock_user_instance
        
        # 执行验证
        result = AuthService.verify_email(self.test_email)
        
        # 验证
        self.assertTrue(result)
        self.assertTrue(mock_user_instance.email_verified)
        mock_db.session.commit.assert_called_once()
    
    @patch('services.auth_service.User')
    def test_verify_email_user_not_found(self, mock_user):
        """测试邮箱验证时用户不存在"""
        mock_user.query.filter_by.return_value.first.return_value = None
        
        # 执行验证
        result = AuthService.verify_email(self.test_email)
        
        # 验证
        self.assertFalse(result)
    
    @patch('services.auth_service.User')
    @patch('services.auth_service.AuthService._send_verification_email')
    def test_resend_verification_email_success(self, mock_send_email, mock_user):
        """测试重发验证邮件成功"""
        # 创建mock用户
        mock_user_instance = Mock()
        mock_user_instance.email_verified = False
        
        mock_user.query.filter_by.return_value.first.return_value = mock_user_instance
        
        # 执行重发
        result = AuthService.resend_verification_email(self.test_email)
        
        # 验证
        self.assertTrue(result)
        mock_send_email.assert_called_once_with(mock_user_instance)
    
    @patch('services.auth_service.User')
    def test_resend_verification_email_user_not_found(self, mock_user):
        """测试重发验证邮件时用户不存在"""
        mock_user.query.filter_by.return_value.first.return_value = None
        
        # 执行重发
        result = AuthService.resend_verification_email(self.test_email)
        
        # 验证
        self.assertFalse(result)
    
    @patch('services.auth_service.User')
    @patch('services.auth_service.validate_password')
    @patch('services.auth_service.db')
    def test_reset_password_success(self, mock_db, mock_validate_password, mock_user):
        """测试重置密码成功"""
        mock_validate_password.return_value = True
        
        # 创建mock用户
        mock_user_instance = Mock()
        mock_user_instance.set_password = Mock()
        
        mock_user.query.filter_by.return_value.first.return_value = mock_user_instance
        
        # 执行重置
        result = AuthService.reset_password(self.test_email, 'NewPassword123')
        
        # 验证
        self.assertTrue(result)
        mock_validate_password.assert_called_once_with('NewPassword123')
        mock_user_instance.set_password.assert_called_once_with('NewPassword123')
        mock_db.session.commit.assert_called_once()
    
    @patch('services.auth_service.validate_password')
    def test_reset_password_invalid_password(self, mock_validate_password):
        """测试重置密码时密码无效"""
        mock_validate_password.return_value = False
        
        # 执行重置
        result = AuthService.reset_password(self.test_email, 'weak')
        
        # 验证
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()

