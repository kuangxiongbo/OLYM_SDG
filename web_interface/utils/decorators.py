#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装饰器工具
==========

提供各种装饰器功能
"""

from functools import wraps
from flask import jsonify, request
from flask_login import current_user

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated_function

def json_required(f):
    """JSON请求装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': '请求必须是JSON格式'}), 400
        return f(*args, **kwargs)
    return decorated_function

def validate_json(*required_fields):
    """JSON字段验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({'error': '请求体不能为空'}), 400
            
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'缺少必需字段: {field}'}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def login_required_api(f):
    """API登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': '需要登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

