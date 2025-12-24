#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证码生成工具
"""

import random
import string
import io
import base64
from flask import session
from datetime import datetime, timedelta

def generate_captcha_code(length=4):
    """生成验证码字符串（数字和字母）"""
    # 使用数字和大写字母，排除容易混淆的字符
    chars = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
    return ''.join(random.choice(chars) for _ in range(length))

def generate_math_captcha():
    """生成数学验证码（简单算术题）"""
    # 生成两个1-10的随机数
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    operator = random.choice(['+', '-', '*'])
    
    if operator == '+':
        answer = num1 + num2
        question = f"{num1} + {num2}"
    elif operator == '-':
        # 确保结果为正数
        if num1 < num2:
            num1, num2 = num2, num1
        answer = num1 - num2
        question = f"{num1} - {num2}"
    else:  # *
        # 限制乘法，避免结果过大
        num1 = random.randint(1, 5)
        num2 = random.randint(1, 5)
        answer = num1 * num2
        question = f"{num1} × {num2}"
    
    return question, str(answer)

def create_simple_captcha_image(text):
    """创建简单的文本验证码图片（使用ASCII艺术）"""
    # 由于可能没有PIL，我们返回文本验证码
    # 如果需要图片，可以安装Pillow并使用PIL生成
    return text

def verify_captcha(user_input, captcha_code):
    """验证验证码"""
    if not user_input or not captcha_code:
        return False
    
    # 确保都是字符串类型
    if not isinstance(user_input, str) or not isinstance(captcha_code, str):
        return False
    
    # 不区分大小写比较
    return user_input.strip().upper() == captcha_code.upper()

def store_captcha_in_session(captcha_code, expire_minutes=5):
    """将验证码存储到session中"""
    session['captcha_code'] = captcha_code.upper()
    session['captcha_expire'] = (datetime.now() + timedelta(minutes=expire_minutes)).isoformat()

def get_captcha_from_session():
    """从session中获取验证码"""
    captcha_code = session.get('captcha_code')
    expire_str = session.get('captcha_expire')
    
    if not captcha_code or not expire_str:
        return None
    
    try:
        expire_time = datetime.fromisoformat(expire_str)
        if datetime.now() > expire_time:
            # 验证码已过期
            session.pop('captcha_code', None)
            session.pop('captcha_expire', None)
            return None
    except:
        return None
    
    return captcha_code

def clear_captcha_from_session():
    """清除session中的验证码"""
    session.pop('captcha_code', None)
    session.pop('captcha_expire', None)

