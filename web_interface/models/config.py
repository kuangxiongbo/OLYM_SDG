#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置模型
"""

from models.user import db
from datetime import datetime
import json

class SystemConfig(db.Model):
    """系统配置模型"""
    __tablename__ = 'system_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    config_value = db.Column(db.Text)  # JSON 格式
    config_type = db.Column(db.String(50))  # 'ai_model' | 'email' | 'other'
    description = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_value(self, value_dict):
        """设置配置值（字典转JSON）"""
        self.config_value = json.dumps(value_dict, ensure_ascii=False)
    
    def get_value(self):
        """获取配置值（JSON转字典）"""
        if self.config_value:
            return json.loads(self.config_value)
        return {}
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.get_value(),
            'config_type': self.config_type,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

