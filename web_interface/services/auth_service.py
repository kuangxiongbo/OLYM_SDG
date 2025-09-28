#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证服务
========

处理用户认证相关的业务逻辑
"""

from flask_login import login_user, logout_user
from flask_mail import Message
from datetime import datetime, timedelta
import secrets
import hashlib
import re
from typing import Dict, Any, Optional

from models import db, User, UserStatus, UserRole
from utils.validators import validate_email, validate_password

class AuthService:
    """认证服务类"""
    
    @staticmethod
    def register_user(email: str, username: str, password: str) -> User:
        """用户注册"""
        # 验证输入
        if not validate_email(email):
            raise ValueError("无效的邮箱格式")
        if not validate_password(password):
            raise ValueError("密码强度不足")
        if not AuthService._validate_username(username):
            raise ValueError("用户名格式不正确")
        
        # 检查用户是否已存在
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            raise ValueError("邮箱已被注册")
        
        # 创建用户
        user = User(
            email=email,
            username=username,
            password_hash='',  # 稍后设置
            role=UserRole.USER,
            status=UserStatus.PENDING
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # 发送验证邮件
        AuthService._send_verification_email(user)
        
        return user
    
    @staticmethod
    def login_user(email: str, password: str) -> User:
        """用户登录"""
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.status == UserStatus.BANNED:
                raise ValueError("账号已被禁用")
            
            if not user.email_verified:
                raise ValueError("请先验证邮箱")
            
            # 登录成功
            login_user(user)
            user.reset_login_attempts()
            
            return user
        else:
            # 登录失败
            if user:
                user.increment_login_attempts()
            raise ValueError("邮箱或密码错误")
    
    @staticmethod
    def logout_user():
        """用户登出"""
        logout_user()
    
    @staticmethod
    def verify_email(token: str) -> bool:
        """验证邮箱"""
        # 这里应该实现邮箱验证逻辑
        # 由于当前没有EmailVerification表，简化处理
        user = User.query.filter_by(email=token).first()  # 简化实现
        if user and not user.email_verified:
            user.email_verified = True
            user.status = UserStatus.ACTIVE
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def resend_verification_email(email: str) -> bool:
        """重发验证邮件"""
        user = User.query.filter_by(email=email).first()
        if user and not user.email_verified:
            AuthService._send_verification_email(user)
            return True
        return False
    
    @staticmethod
    def forgot_password(email: str) -> bool:
        """忘记密码"""
        user = User.query.filter_by(email=email).first()
        if user:
            # 这里应该实现密码重置逻辑
            # 发送密码重置邮件
            AuthService._send_password_reset_email(user)
            return True
        return False
    
    @staticmethod
    def reset_password(token: str, new_password: str) -> bool:
        """重置密码"""
        # 这里应该验证token并重置密码
        # 简化实现
        if validate_password(new_password):
            user = User.query.filter_by(email=token).first()  # 简化实现
            if user:
                user.set_password(new_password)
                db.session.commit()
                return True
        return False
    
    @staticmethod
    def _validate_username(username: str) -> bool:
        """验证用户名格式"""
        if not username or len(username) < 3 or len(username) > 20:
            return False
        return re.match(r'^[a-zA-Z0-9_]+$', username) is not None
    
    @staticmethod
    def _send_verification_email(user: User):
        """发送验证邮件"""
        # 这里应该实现邮件发送逻辑
        print(f"发送验证邮件到: {user.email}")
    
    @staticmethod
    def _send_password_reset_email(user: User):
        """发送密码重置邮件"""
        # 这里应该实现邮件发送逻辑
        print(f"发送密码重置邮件到: {user.email}")

