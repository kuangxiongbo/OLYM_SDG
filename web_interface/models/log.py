#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作日志模型
"""

from models.user import db
from datetime import datetime
import json

class OperationLog(db.Model):
    """操作日志模型"""
    __tablename__ = 'operation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)  # 允许None，用于系统操作
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))  # 'task' | 'config' | 'user'
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON 格式
    result = db.Column(db.String(20))  # 'success' | 'failure'
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def set_details(self, details_dict):
        """设置详情（字典转JSON）"""
        self.details = json.dumps(details_dict, ensure_ascii=False)
    
    def get_details(self):
        """获取详情（JSON转字典）"""
        if self.details:
            return json.loads(self.details)
        return {}
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user': {
                'id': self.user.id if self.user else None,
                'email': self.user.email if self.user else None,
                'name': self.user.name if self.user else None
            } if self.user else None,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.get_details(),
            'result': self.result,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

