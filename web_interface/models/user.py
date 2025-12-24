#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户模型
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets
import string

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), nullable=True)  # 兼容数据库中的username字段（如果数据库要求NOT NULL，创建时必须提供）
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user', nullable=False)  # 'user' | 'admin'
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending' | 'active' | 'disabled'
    activation_code = db.Column(db.String(100))
    activation_expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    # 关系
    tasks = db.relationship('Task', backref='user', lazy=True)
    logs = db.relationship('OperationLog', backref='user', lazy=True)
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def generate_activation_code(self, expires_hours=24):
        """生成激活码"""
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        self.activation_code = code
        from datetime import timedelta
        self.activation_expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        return code
    
    def is_active(self):
        """检查账号是否激活"""
        return self.status == 'active'
    
    def is_admin(self):
        """检查是否为管理员"""
        return self.role == 'admin'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'name': self.name,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }



