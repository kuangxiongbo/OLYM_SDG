#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证工具
========

提供各种验证功能
"""

import re
import pandas as pd
from typing import Tuple

def validate_email(email: str) -> bool:
    """邮箱格式验证"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> bool:
    """密码强度验证"""
    if not password or len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return sum([has_upper, has_lower, has_digit, has_special]) >= 3

def validate_username(username: str) -> bool:
    """用户名格式验证"""
    if not username or len(username) < 3 or len(username) > 20:
        return False
    
    return re.match(r'^[a-zA-Z0-9_]+$', username) is not None

def validate_data_source(file_path: str, data_type: str) -> Tuple[bool, str]:
    """数据源验证"""
    try:
        if data_type == 'csv':
            df = pd.read_csv(file_path, nrows=100)  # 只读前100行验证
        elif data_type == 'json':
            df = pd.read_json(file_path, nrows=100)
        else:
            return True, "支持的数据类型"
        
        # 检查数据质量
        if df.empty:
            return False, "数据文件为空"
        
        if df.shape[1] < 2:
            return False, "数据至少需要2列"
        
        return True, f"数据验证通过，共{df.shape[1]}列"
    
    except Exception as e:
        return False, f"数据验证失败: {str(e)}"

