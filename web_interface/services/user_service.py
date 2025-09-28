#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户服务
========

处理用户管理相关的业务逻辑
"""

from datetime import datetime
from typing import Dict, Any, List

from models import db, User, UserRole, UserStatus
from utils.validators import validate_email, validate_password

class UserService:
    """用户服务类"""
    
    @staticmethod
    def get_user_profile(user_id: int) -> User:
        """获取用户个人信息"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        return user
    
    @staticmethod
    def update_user_profile(user_id: int, profile_data: Dict[str, Any]) -> User:
        """更新用户个人信息"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        # 更新允许的字段
        allowed_fields = ['username']
        for field in allowed_fields:
            if field in profile_data:
                if field == 'username' and not UserService._validate_username(profile_data[field]):
                    raise ValueError("用户名格式不正确")
                setattr(user, field, profile_data[field])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return user
    
    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        if not user.check_password(old_password):
            raise ValueError("原密码错误")
        
        if not validate_password(new_password):
            raise ValueError("新密码强度不足")
        
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True
    
    @staticmethod
    def change_email(user_id: int, new_email: str, password: str) -> User:
        """修改邮箱"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        if not user.check_password(password):
            raise ValueError("密码错误")
        
        if not validate_email(new_email):
            raise ValueError("无效的邮箱格式")
        
        # 检查新邮箱是否已被使用
        existing_user = User.query.filter_by(email=new_email).first()
        if existing_user and existing_user.id != user_id:
            raise ValueError("邮箱已被使用")
        
        user.email = new_email
        user.email_verified = False  # 需要重新验证
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 发送验证邮件
        from .auth_service import AuthService
        AuthService._send_verification_email(user)
        
        return user
    
    @staticmethod
    def get_user_stats(user_id: int) -> Dict[str, Any]:
        """获取用户统计信息"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        stats = {
            'data_sources_count': user.data_sources.count(),
            'model_configs_count': user.model_configs.count(),
            'synthetic_tasks_count': user.synthetic_tasks.count(),
            'quality_tasks_count': user.quality_tasks.count(),
            'sensitive_tasks_count': user.sensitive_tasks.count(),
            'completed_synthetic_tasks': user.synthetic_tasks.filter_by(status='completed').count(),
            'completed_quality_tasks': user.quality_tasks.filter_by(status='completed').count(),
            'completed_sensitive_tasks': user.sensitive_tasks.filter_by(status='completed').count()
        }
        
        return stats
    
    @staticmethod
    def _validate_username(username: str) -> bool:
        """验证用户名格式"""
        if not username or len(username) < 3 or len(username) > 20:
            return False
        import re
        return re.match(r'^[a-zA-Z0-9_]+$', username) is not None

