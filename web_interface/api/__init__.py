#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API路由包
=========

导出所有API蓝图
"""

from .auth import auth_bp
from .user import user_bp
from .data_sources import data_bp
from .model_configs import model_bp
from .admin import admin_bp

__all__ = [
    'auth_bp',
    'user_bp',
    'data_bp',
    'model_bp',
    'admin_bp'
]

