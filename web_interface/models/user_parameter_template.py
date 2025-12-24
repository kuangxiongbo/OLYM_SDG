#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户参数模板模型
"""

from models.user import db
from datetime import datetime
import json

class UserParameterTemplate(db.Model):
    """用户参数模板模型"""
    __tablename__ = 'user_parameter_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)  # 模板名称
    model_type = db.Column(db.String(50), nullable=False)  # 'ctgan' | 'gaussian_copula' | 'tvae'
    parameters = db.Column(db.Text)  # JSON格式的参数配置
    is_default = db.Column(db.Boolean, default=False)  # 是否为默认模板
    description = db.Column(db.Text)  # 模板描述
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_parameters(self, params_dict):
        """设置参数（字典转JSON）"""
        self.parameters = json.dumps(params_dict, ensure_ascii=False)
    
    def get_parameters(self):
        """获取参数（JSON转字典）"""
        if self.parameters:
            return json.loads(self.parameters)
        return {}
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'model_type': self.model_type,
            'parameters': self.get_parameters(),
            'is_default': self.is_default,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


