#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务模型
"""

from models.user import db
from datetime import datetime
import json

class Task(db.Model):
    """任务模型"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)  # 'synthesis' | 'quality' | 'masking'
    task_name = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
    config = db.Column(db.Text)  # JSON 格式
    result_path = db.Column(db.String(500))
    error_message = db.Column(db.Text)
    progress = db.Column(db.Integer, default=0)  # 0-100
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def set_config(self, config_dict):
        """设置配置（字典转JSON）"""
        self.config = json.dumps(config_dict, ensure_ascii=False)
    
    def get_config(self):
        """获取配置（JSON转字典）"""
        if self.config:
            return json.loads(self.config)
        return {}
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': f'task_{self.id}',
            'user_id': self.user_id,
            'task_type': self.task_type,  # 添加task_type字段
            'type': self.task_type,  # 保持向后兼容
            'task_name': self.task_name,  # 添加task_name字段
            'name': self.task_name,  # 保持向后兼容
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'config': self.get_config(),  # 添加config字段
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

