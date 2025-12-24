#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
辅助函数
"""

import os
import uuid
from werkzeug.utils import secure_filename
from flask import request
from config import Config

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def generate_file_id():
    """生成文件ID"""
    return f"file_{uuid.uuid4().hex[:12]}"

def get_client_ip():
    """获取客户端IP地址"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

def save_uploaded_file(file, file_id=None):
    """保存上传的文件"""
    if file_id is None:
        file_id = generate_file_id()
    
    if file and allowed_file(file.filename):
        # 从原始文件名获取扩展名（在secure_filename之前）
        original_filename = file.filename
        if '.' in original_filename:
            ext = original_filename.rsplit('.', 1)[1].lower()
        else:
            return None, None, None
        
        # 确保扩展名在允许列表中
        if ext not in Config.ALLOWED_EXTENSIONS:
            return None, None, None
        
        saved_filename = f"{file_id}.{ext}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, saved_filename)
        
        # 确保目录存在
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        file.save(filepath)
        return file_id, filepath, saved_filename
    return None, None, None

def log_operation_direct(action, resource_type=None, resource_id=None, result='success', 
                        user_id=None, details=None, ip_address=None, user_agent=None):
    """直接记录操作日志（支持未登录用户）"""
    try:
        from models.log import OperationLog, db
        from flask import request
        from flask_login import current_user
        
        # 如果没有提供user_id，尝试从current_user获取
        if user_id is None:
            if current_user.is_authenticated:
                user_id = current_user.id
            else:
                # 未登录用户，使用系统用户ID（0）或查找系统用户
                try:
                    from models.user import User
                    system_user = User.query.filter_by(email='system@sdg.com').first()
                    if system_user:
                        user_id = system_user.id
                    else:
                        # 如果没有系统用户，使用0（需要确保数据库允许）
                        user_id = 0
                except:
                    user_id = 0
        
        # 如果没有提供IP和User-Agent，从request获取
        if ip_address is None:
            ip_address = get_client_ip()
        if user_agent is None:
            user_agent = request.headers.get('User-Agent', '') if request else ''
        
        log = OperationLog(
            user_id=user_id if user_id else 0,  # 如果仍然为None，使用0
            action=action,
            resource_type=resource_type,
            resource_id=resource_id if isinstance(resource_id, int) else None,
            result=result,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # 保存详情
        if details:
            log.set_details(details)
        
        db.session.add(log)
        db.session.commit()
        return log
    except Exception as e:
        # 日志记录失败不应该影响主流程
        try:
            db.session.rollback()
        except:
            pass
        import sys
        print(f"[WARNING] 记录操作日志失败: {e}", file=sys.stderr)
        return None



