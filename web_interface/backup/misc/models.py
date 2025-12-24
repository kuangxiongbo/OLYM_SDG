#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证数据模型
================

定义用户、会话等认证相关的数据模型
"""

from datetime import datetime, timedelta
import hashlib
import secrets
import uuid
from typing import Optional, Dict, Any
import json

class User:
    """用户模型"""
    
    def __init__(self, email: str, username: str, password_hash: str, 
                 is_verified: bool = False, role: str = 'user', 
                 created_at: Optional[datetime] = None, 
                 last_login: Optional[datetime] = None,
                 user_id: Optional[str] = None):
        self.user_id = user_id or str(uuid.uuid4())
        self.email = email.lower().strip()
        self.username = username.strip()
        self.password_hash = password_hash
        self.is_verified = is_verified
        self.role = role  # 'user', 'admin', 'moderator'
        self.created_at = created_at or datetime.now()
        self.last_login = last_login
        self.email_verification_token = None
        self.password_reset_token = None
        self.password_reset_expires = None
        self.profile_data = {}  # 用户个人资料数据
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'username': self.username,
            'is_verified': self.is_verified,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'profile_data': self.profile_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """从字典创建用户对象"""
        user = cls(
            email=data['email'],
            username=data['username'],
            password_hash=data['password_hash'],
            is_verified=data.get('is_verified', False),
            role=data.get('role', 'user'),
            user_id=data['user_id']
        )
        
        if data.get('created_at'):
            user.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('last_login'):
            user.last_login = datetime.fromisoformat(data['last_login'])
        
        user.email_verification_token = data.get('email_verification_token')
        user.password_reset_token = data.get('password_reset_token')
        if data.get('password_reset_expires'):
            user.password_reset_expires = datetime.fromisoformat(data['password_reset_expires'])
        
        user.profile_data = data.get('profile_data', {})
        return user

class UserSession:
    """用户会话模型"""
    
    def __init__(self, user_id: str, session_token: str, 
                 expires_at: Optional[datetime] = None,
                 ip_address: Optional[str] = None,
                 user_agent: Optional[str] = None):
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        self.session_token = session_token
        self.expires_at = expires_at or (datetime.now() + timedelta(days=7))
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.is_active = True
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'session_token': self.session_token,
            'expires_at': self.expires_at.isoformat(),
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSession':
        """从字典创建会话对象"""
        session = cls(
            user_id=data['user_id'],
            session_token=data['session_token'],
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent')
        )
        
        session.session_id = data['session_id']
        session.expires_at = datetime.fromisoformat(data['expires_at'])
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.last_activity = datetime.fromisoformat(data['last_activity'])
        session.is_active = data.get('is_active', True)
        return session
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.now() > self.expires_at
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()

class EmailVerification:
    """邮箱验证模型"""
    
    def __init__(self, email: str, token: str, 
                 expires_at: Optional[datetime] = None):
        self.verification_id = str(uuid.uuid4())
        self.email = email.lower().strip()
        self.token = token
        self.created_at = datetime.now()
        self.expires_at = expires_at or (datetime.now() + timedelta(hours=24))
        self.is_used = False
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'verification_id': self.verification_id,
            'email': self.email,
            'token': self.token,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_used': self.is_used
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailVerification':
        """从字典创建验证对象"""
        verification = cls(
            email=data['email'],
            token=data['token']
        )
        
        verification.verification_id = data['verification_id']
        verification.created_at = datetime.fromisoformat(data['created_at'])
        verification.expires_at = datetime.fromisoformat(data['expires_at'])
        verification.is_used = data.get('is_used', False)
        return verification
    
    def is_expired(self) -> bool:
        """检查验证是否过期"""
        return datetime.now() > self.expires_at

class PasswordReset:
    """密码重置模型"""
    
    def __init__(self, email: str, token: str, 
                 expires_at: Optional[datetime] = None):
        self.reset_id = str(uuid.uuid4())
        self.email = email.lower().strip()
        self.token = token
        self.created_at = datetime.now()
        self.expires_at = expires_at or (datetime.now() + timedelta(hours=1))
        self.is_used = False
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'reset_id': self.reset_id,
            'email': self.email,
            'token': self.token,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_used': self.is_used
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PasswordReset':
        """从字典创建重置对象"""
        reset = cls(
            email=data['email'],
            token=data['token']
        )
        
        reset.reset_id = data['reset_id']
        reset.created_at = datetime.fromisoformat(data['created_at'])
        reset.expires_at = datetime.fromisoformat(data['expires_at'])
        reset.is_used = data.get('is_used', False)
        return reset
    
    def is_expired(self) -> bool:
        """检查重置是否过期"""
        return datetime.now() > self.expires_at

# 密码工具类
class PasswordUtils:
    """密码处理工具类"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', 
                                       password.encode('utf-8'), 
                                       salt.encode('utf-8'), 
                                       100000)
        return salt + pwd_hash.hex()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            salt = password_hash[:32]  # 前32个字符是salt
            stored_hash = password_hash[32:]
            
            pwd_hash = hashlib.pbkdf2_hmac('sha256',
                                          password.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          100000)
            
            return pwd_hash.hex() == stored_hash
        except:
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """验证密码强度"""
        result = {
            'valid': True,
            'errors': [],
            'strength': 'weak'
        }
        
        if len(password) < 8:
            result['valid'] = False
            result['errors'].append('密码长度至少8位')
        
        if not any(c.isupper() for c in password):
            result['valid'] = False
            result['errors'].append('密码必须包含大写字母')
        
        if not any(c.islower() for c in password):
            result['valid'] = False
            result['errors'].append('密码必须包含小写字母')
        
        if not any(c.isdigit() for c in password):
            result['valid'] = False
            result['errors'].append('密码必须包含数字')
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            result['valid'] = False
            result['errors'].append('密码必须包含特殊字符')
        
        # 计算密码强度
        if len(password) >= 12 and result['valid']:
            result['strength'] = 'strong'
        elif len(password) >= 8 and len(result['errors']) <= 1:
            result['strength'] = 'medium'
        
        return result

# 令牌工具类
class TokenUtils:
    """令牌生成工具类"""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """生成随机令牌"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_session_token() -> str:
        """生成会话令牌"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def generate_verification_token() -> str:
        """生成验证令牌"""
        return secrets.token_urlsafe(32)

