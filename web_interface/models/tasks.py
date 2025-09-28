#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务模型
========

基于SQLAlchemy的任务数据模型
"""

from .user import db
from datetime import datetime
import enum

class TaskStatus(enum.Enum):
    """任务状态枚举"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class SyntheticTask(db.Model):
    """合成数据任务模型"""
    __tablename__ = 'synthetic_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'), nullable=False)
    model_config_id = db.Column(db.Integer, db.ForeignKey('model_configurations.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    model_config = db.Column(db.JSON, nullable=False)
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.PENDING)
    progress = db.Column(db.Integer, default=0)
    result_config = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def is_completed(self):
        """检查任务是否完成"""
        return self.status == TaskStatus.COMPLETED
    
    def is_failed(self):
        """检查任务是否失败"""
        return self.status == TaskStatus.FAILED
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'data_source_id': self.data_source_id,
            'model_config_id': self.model_config_id,
            'name': self.name,
            'model_config': self.model_config,
            'status': self.status.value,
            'progress': self.progress,
            'result_config': self.result_config,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class QualityTask(db.Model):
    """质量评估任务模型"""
    __tablename__ = 'quality_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    original_data_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'))
    synthetic_data_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'))
    task_name = db.Column(db.String(100), nullable=False)
    metrics_config = db.Column(db.JSON, nullable=False)
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.PENDING)
    progress = db.Column(db.Integer, default=0)
    results = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # 关系
    synthetic_data_source = db.relationship('DataSource', foreign_keys=[synthetic_data_id], backref='quality_tasks_synthetic')
    
    def is_completed(self):
        """检查任务是否完成"""
        return self.status == TaskStatus.COMPLETED
    
    def is_failed(self):
        """检查任务是否失败"""
        return self.status == TaskStatus.FAILED
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'original_data_id': self.original_data_id,
            'synthetic_data_id': self.synthetic_data_id,
            'task_name': self.task_name,
            'metrics_config': self.metrics_config,
            'status': self.status.value,
            'progress': self.progress,
            'results': self.results,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class SensitiveTask(db.Model):
    """敏感字段检测任务模型"""
    __tablename__ = 'sensitive_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'), nullable=False)
    task_name = db.Column(db.String(100), nullable=False)
    detection_config = db.Column(db.JSON, nullable=False)
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.PENDING)
    progress = db.Column(db.Integer, default=0)
    results = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def is_completed(self):
        """检查任务是否完成"""
        return self.status == TaskStatus.COMPLETED
    
    def is_failed(self):
        """检查任务是否失败"""
        return self.status == TaskStatus.FAILED
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'data_source_id': self.data_source_id,
            'task_name': self.task_name,
            'detection_config': self.detection_config,
            'status': self.status.value,
            'progress': self.progress,
            'results': self.results,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
