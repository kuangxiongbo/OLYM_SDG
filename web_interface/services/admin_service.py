#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员服务
==========

处理管理员相关的业务逻辑
"""

from typing import Dict, Any, List
from models import User, DataSource, ModelConfig

class AdminService:
    """管理员服务类"""
    
    @staticmethod
    def get_all_users() -> List[User]:
        """获取所有用户"""
        return User.query.order_by(User.created_at.desc()).all()
    
    @staticmethod
    def get_all_data_sources() -> List[DataSource]:
        """获取所有数据源"""
        return DataSource.query.order_by(DataSource.created_at.desc()).all()
    
    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = {
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(status='active').count(),
            'total_data_sources': DataSource.query.count(),
            'total_model_configs': ModelConfig.query.count()
        }
        return stats

