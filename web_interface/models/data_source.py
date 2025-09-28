#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源模型
==========

基于SQLAlchemy的数据源模型
"""

from .user import db
from datetime import datetime
import enum

class DataSourceType(enum.Enum):
    """数据源类型枚举"""
    CSV = 'csv'
    JSON = 'json'
    DATABASE = 'database'
    API = 'api'

class DataSourceStatus(enum.Enum):
    """数据源状态枚举"""
    ACTIVE = 'active'
    ERROR = 'error'
    PROCESSING = 'processing'

class DataSource(db.Model):
    """数据源模型"""
    __tablename__ = 'data_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum(DataSourceType), nullable=False)
    file_path = db.Column(db.String(500))
    config = db.Column(db.JSON, nullable=False)
    status = db.Column(db.Enum(DataSourceStatus), default=DataSourceStatus.PROCESSING)
    file_size = db.Column(db.Integer)
    row_count = db.Column(db.Integer)
    column_count = db.Column(db.Integer)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    synthetic_tasks = db.relationship('SyntheticTask', backref='data_source', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='SyntheticTask.data_source_id')
    quality_tasks = db.relationship('QualityTask', backref='original_data_source', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='QualityTask.original_data_id')
    sensitive_tasks = db.relationship('SensitiveTask', backref='data_source', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='SensitiveTask.data_source_id')
    
    def is_active(self):
        """检查数据源是否激活"""
        return self.status == DataSourceStatus.ACTIVE
    
    def get_file_size_mb(self):
        """获取文件大小（MB）"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'type': self.type.value,
            'file_path': self.file_path,
            'config': self.config,
            'status': self.status.value,
            'file_size': self.file_size,
            'file_size_mb': self.get_file_size_mb(),
            'row_count': self.row_count,
            'column_count': self.column_count,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<DataSource {self.name} ({self.type.value})>'
