#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型配置模型
============

基于SQLAlchemy的模型配置数据模型
"""

from .user import db
from datetime import datetime
import enum

class ModelType(enum.Enum):
    """模型类型枚举"""
    CTGAN = 'ctgan'
    TVAE = 'tvae'
    GAUSSIAN_COPULA = 'gaussian_copula'
    CUSTOM = 'custom'

class ModelStatus(enum.Enum):
    """模型状态枚举"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'

class ModelConfig(db.Model):
    """模型配置模型"""
    __tablename__ = 'model_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    model_type = db.Column(db.Enum(ModelType), nullable=False)
    config = db.Column(db.JSON, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum(ModelStatus), default=ModelStatus.ACTIVE)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    synthetic_tasks = db.relationship('SyntheticTask', backref='model_config_ref', lazy='dynamic', cascade='all, delete-orphan')
    
    def is_active(self):
        """检查模型配置是否激活"""
        return self.status == ModelStatus.ACTIVE
    
    def get_default_config(self):
        """获取默认配置"""
        default_configs = {
            ModelType.CTGAN: {
                'epochs': 300,
                'batch_size': 500,
                'generator_lr': 2e-4,
                'discriminator_lr': 2e-4
            },
            ModelType.TVAE: {
                'epochs': 300,
                'batch_size': 500,
                'l2norm': 1e-5
            },
            ModelType.GAUSSIAN_COPULA: {
                'default_distribution': 'gaussian'
            }
        }
        return default_configs.get(self.model_type, {})
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'model_type': self.model_type.value,
            'config': self.config,
            'is_default': self.is_default,
            'status': self.status.value,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ModelConfig {self.name} ({self.model_type.value})>'
