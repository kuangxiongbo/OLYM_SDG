#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路由模块
"""

from .auth import auth_bp
from .synthetic import synthetic_bp
from .quality import quality_bp
from .masking import masking_bp
from .task import task_bp
from .settings import settings_bp

__all__ = ['auth_bp', 'synthetic_bp', 'quality_bp', 'masking_bp', 'task_bp', 'settings_bp']



