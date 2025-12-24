#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装饰器
"""

from functools import wraps
from flask import jsonify, request
from flask_login import current_user
from models.user import User
from models.log import OperationLog, db

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'error': '需要登录',
                'code': 'AUTH_REQUIRED'
            }), 401
        if not current_user.is_admin():
            return jsonify({
                'success': False,
                'error': '权限不足',
                'code': 'PERMISSION_DENIED'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def log_operation(action, resource_type=None):
    """操作日志装饰器 - 自动记录操作详情"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request
            from flask_login import current_user
            from models.log import OperationLog, db
            from utils.helpers import get_client_ip
            import json
            
            # 提取资源ID（从kwargs或args中）
            resource_id = None
            if kwargs:
                # 尝试从常见参数名中提取资源ID
                for key in ['model_id', 'admin_id', 'user_id', 'task_id', 'file_id']:
                    if key in kwargs:
                        resource_id = kwargs[key]
                        break
            elif args:
                # 如果第一个参数是ID
                if len(args) > 0 and isinstance(args[0], (int, str)):
                    resource_id = args[0]
            
            # 准备详情信息（不包含敏感信息）
            details = {}
            
            # 从请求中提取关键信息
            if request.is_json:
                try:
                    data = request.get_json() or {}
                    # 提取非敏感信息
                    for key in ['provider', 'enabled', 'model_id', 'action', 'name', 'email']:
                        if key in data:
                            details[key] = data[key]
                    
                    # 对于配置更新，提取配置的关键信息（排除敏感字段）
                    if 'config' in data and isinstance(data['config'], dict):
                        config_info = {}
                        for key in ['smtp_host', 'smtp_port', 'encryption', 'sender_email', 'endpoint']:
                            if key in data['config']:
                                config_info[key] = data['config'][key]
                        if config_info:
                            details['config'] = config_info
                    
                    # 对于模型配置，记录模型ID和启用状态
                    if 'enabled' in data:
                        details['enabled'] = data['enabled']
                    
                except:
                    pass
            
            # 如果没有提取到详情，至少记录资源ID
            if not details and resource_id:
                details['resource_id'] = resource_id
            
            try:
                result = f(*args, **kwargs)
                # 记录成功日志
                if current_user.is_authenticated:
                    try:
                        log = OperationLog(
                            user_id=current_user.id,
                            action=action,
                            resource_type=resource_type,
                            resource_id=resource_id if isinstance(resource_id, int) else None,
                            result='success',
                            ip_address=get_client_ip(),
                            user_agent=request.headers.get('User-Agent', '')
                        )
                        # 保存详情（如果有）
                        if details:
                            log.set_details(details)
                        db.session.add(log)
                        db.session.commit()
                    except Exception as log_error:
                        # 日志记录失败不应该影响主流程
                        db.session.rollback()
                        import sys
                        print(f"[WARNING] 记录操作日志失败: {log_error}", file=sys.stderr)
                return result
            except Exception as e:
                # 记录失败日志
                if current_user.is_authenticated:
                    try:
                        log = OperationLog(
                            user_id=current_user.id,
                            action=action,
                            resource_type=resource_type,
                            resource_id=resource_id if isinstance(resource_id, int) else None,
                            result='failure',
                            ip_address=get_client_ip(),
                            user_agent=request.headers.get('User-Agent', '')
                        )
                        # 保存错误信息和详情
                        error_details = details.copy()
                        error_details['error'] = str(e)
                        log.set_details(error_details)
                        db.session.add(log)
                        db.session.commit()
                    except:
                        db.session.rollback()
                raise
        return decorated_function
    return decorator
