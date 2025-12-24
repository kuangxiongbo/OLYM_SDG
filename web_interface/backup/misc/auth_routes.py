#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证路由
=============

处理用户注册、登录、邮箱验证等认证相关的路由
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from datetime import datetime, timedelta
import re
from typing import Dict, Any

from models import User, UserSession, EmailVerification, PasswordReset, PasswordUtils, TokenUtils
from database import auth_db
from email_service import email_service

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 邮箱验证正则表达式
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# 用户名验证正则表达式（3-20位字母数字下划线）
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_]{3,20}$')

def validate_email(email: str) -> Dict[str, Any]:
    """验证邮箱格式"""
    result = {'valid': True, 'message': ''}
    
    if not email:
        result['valid'] = False
        result['message'] = '邮箱地址不能为空'
    elif not EMAIL_REGEX.match(email):
        result['valid'] = False
        result['message'] = '邮箱地址格式不正确'
    
    return result

def validate_username(username: str) -> Dict[str, Any]:
    """验证用户名格式"""
    result = {'valid': True, 'message': ''}
    
    if not username:
        result['valid'] = False
        result['message'] = '用户名不能为空'
    elif len(username) < 3:
        result['valid'] = False
        result['message'] = '用户名长度至少3位'
    elif len(username) > 20:
        result['valid'] = False
        result['message'] = '用户名长度不能超过20位'
    elif not USERNAME_REGEX.match(username):
        result['valid'] = False
        result['message'] = '用户名只能包含字母、数字和下划线'
    
    return result

def validate_password(password: str) -> Dict[str, Any]:
    """验证密码强度"""
    return PasswordUtils.validate_password_strength(password)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        # 验证输入
        email_validation = validate_email(email)
        if not email_validation['valid']:
            return jsonify({'success': False, 'message': email_validation['message']})
        
        username_validation = validate_username(username)
        if not username_validation['valid']:
            return jsonify({'success': False, 'message': username_validation['message']})
        
        password_validation = validate_password(password)
        if not password_validation['valid']:
            return jsonify({'success': False, 'message': '密码不符合要求: ' + ', '.join(password_validation['errors'])})
        
        if password != confirm_password:
            return jsonify({'success': False, 'message': '两次输入的密码不一致'})
        
        # 检查邮箱是否已存在
        existing_user = auth_db.users.get_user_by_email(email)
        if existing_user:
            return jsonify({'success': False, 'message': '该邮箱已被注册'})
        
        # 检查用户名是否已存在
        existing_username = auth_db.users.get_user_by_username(username)
        if existing_username:
            return jsonify({'success': False, 'message': '该用户名已被使用'})
        
        # 创建用户
        password_hash = PasswordUtils.hash_password(password)
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            is_verified=False
        )
        
        # 生成邮箱验证令牌
        verification_token = TokenUtils.generate_verification_token()
        user.email_verification_token = verification_token
        
        # 保存用户
        if not auth_db.users.create_user(user):
            return jsonify({'success': False, 'message': '注册失败，请稍后重试'})
        
        # 创建邮箱验证记录
        verification = EmailVerification(email=email, token=verification_token)
        auth_db.verifications.create_verification(verification)
        
        # 发送验证邮件
        email_service.send_verification_email(email, username, verification_token)
        
        return jsonify({
            'success': True,
            'message': '注册成功！请检查您的邮箱并点击验证链接完成注册。'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'})

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    try:
        data = request.get_json() if request.is_json else request.form
        email_or_username = data.get('email_or_username', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        if not email_or_username or not password:
            return jsonify({'success': False, 'message': '请输入邮箱/用户名和密码'})
        
        # 查找用户（支持邮箱或用户名登录）
        user = None
        if '@' in email_or_username:
            user = auth_db.users.get_user_by_email(email_or_username)
        else:
            user = auth_db.users.get_user_by_username(email_or_username)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        # 验证密码
        if not PasswordUtils.verify_password(password, user.password_hash):
            return jsonify({'success': False, 'message': '密码错误'})
        
        # 检查邮箱是否已验证
        if not user.is_verified:
            return jsonify({'success': False, 'message': '请先验证您的邮箱地址'})
        
        # 创建会话
        session_token = TokenUtils.generate_session_token()
        session_expires = datetime.now() + timedelta(days=7 if remember_me else 1)
        
        user_session = UserSession(
            user_id=user.user_id,
            session_token=session_token,
            expires_at=session_expires,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        auth_db.sessions.create_session(user_session)
        
        # 更新用户最后登录时间
        user.last_login = datetime.now()
        auth_db.users.update_user(user)
        
        # 设置会话
        session['user_id'] = user.user_id
        session['session_token'] = session_token
        session['username'] = user.username
        session['email'] = user.email
        session['role'] = user.role
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'})

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用户登出"""
    try:
        session_token = session.get('session_token')
        if session_token:
            auth_db.sessions.delete_session(session_token)
        
        session.clear()
        
        return jsonify({'success': True, 'message': '登出成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'登出失败: {str(e)}'})

@auth_bp.route('/verify_email')
def verify_email():
    """邮箱验证"""
    try:
        token = request.args.get('token')
        if not token:
            flash('验证链接无效', 'error')
            return redirect(url_for('auth.login'))
        
        # 获取验证记录
        verification = auth_db.verifications.get_verification(token)
        if not verification:
            flash('验证链接无效或已过期', 'error')
            return redirect(url_for('auth.login'))
        
        # 获取用户
        user = auth_db.users.get_user_by_email(verification.email)
        if not user:
            flash('用户不存在', 'error')
            return redirect(url_for('auth.login'))
        
        if user.is_verified:
            flash('邮箱已验证，无需重复验证', 'info')
            return redirect(url_for('auth.login'))
        
        # 标记用户为已验证
        user.is_verified = True
        user.email_verification_token = None
        
        if not auth_db.users.update_user(user):
            flash('验证失败，请稍后重试', 'error')
            return redirect(url_for('auth.login'))
        
        # 标记验证为已使用
        auth_db.verifications.mark_verification_used(token)
        
        # 发送欢迎邮件
        email_service.send_welcome_email(user.email, user.username)
        
        flash('邮箱验证成功！欢迎使用我们的服务。', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        flash(f'验证失败: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/resend_verification', methods=['POST'])
def resend_verification():
    """重新发送验证邮件"""
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'success': False, 'message': '请输入邮箱地址'})
        
        # 获取用户
        user = auth_db.users.get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        if user.is_verified:
            return jsonify({'success': False, 'message': '邮箱已验证，无需重复验证'})
        
        # 生成新的验证令牌
        verification_token = TokenUtils.generate_verification_token()
        user.email_verification_token = verification_token
        
        auth_db.users.update_user(user)
        
        # 创建新的验证记录
        verification = EmailVerification(email=email, token=verification_token)
        auth_db.verifications.create_verification(verification)
        
        # 发送验证邮件
        email_service.send_verification_email(email, user.username, verification_token)
        
        return jsonify({'success': True, 'message': '验证邮件已重新发送'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送失败: {str(e)}'})

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """忘记密码"""
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')
    
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        
        email_validation = validate_email(email)
        if not email_validation['valid']:
            return jsonify({'success': False, 'message': email_validation['message']})
        
        # 获取用户
        user = auth_db.users.get_user_by_email(email)
        if not user:
            # 为了安全，不暴露用户是否存在
            return jsonify({'success': True, 'message': '如果该邮箱已注册，密码重置邮件已发送'})
        
        # 生成重置令牌
        reset_token = TokenUtils.generate_verification_token()
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.now() + timedelta(hours=1)
        
        auth_db.users.update_user(user)
        
        # 创建重置记录
        password_reset = PasswordReset(email=email, token=reset_token)
        auth_db.password_resets.create_reset(password_reset)
        
        # 发送重置邮件
        email_service.send_password_reset_email(email, user.username, reset_token)
        
        return jsonify({'success': True, 'message': '如果该邮箱已注册，密码重置邮件已发送'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送失败: {str(e)}'})

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    """重置密码"""
    token = request.args.get('token')
    
    if request.method == 'GET':
        if not token:
            flash('重置链接无效', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        # 验证令牌
        reset_record = auth_db.password_resets.get_reset(token)
        if not reset_record:
            flash('重置链接无效或已过期', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        return render_template('auth/reset_password.html', token=token)
    
    try:
        data = request.get_json() if request.is_json else request.form
        token = data.get('token', '')
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not token:
            return jsonify({'success': False, 'message': '重置令牌无效'})
        
        # 获取重置记录
        reset_record = auth_db.password_resets.get_reset(token)
        if not reset_record:
            return jsonify({'success': False, 'message': '重置令牌无效或已过期'})
        
        # 验证密码
        password_validation = validate_password(password)
        if not password_validation['valid']:
            return jsonify({'success': False, 'message': '密码不符合要求: ' + ', '.join(password_validation['errors'])})
        
        if password != confirm_password:
            return jsonify({'success': False, 'message': '两次输入的密码不一致'})
        
        # 获取用户
        user = auth_db.users.get_user_by_email(reset_record.email)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        # 更新密码
        user.password_hash = PasswordUtils.hash_password(password)
        user.password_reset_token = None
        user.password_reset_expires = None
        
        if not auth_db.users.update_user(user):
            return jsonify({'success': False, 'message': '密码重置失败'})
        
        # 标记重置为已使用
        auth_db.password_resets.mark_reset_used(token)
        
        # 删除用户所有会话（强制重新登录）
        auth_db.sessions.delete_user_sessions(user.user_id)
        
        return jsonify({'success': True, 'message': '密码重置成功，请重新登录'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'重置失败: {str(e)}'})

@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """用户资料"""
    # 检查登录状态
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = auth_db.users.get_user_by_id(user_id)
    
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    if request.method == 'GET':
        return render_template('auth/profile.html', user=user.to_dict())
    
    try:
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        
        # 验证用户名
        username_validation = validate_username(username)
        if not username_validation['valid']:
            return jsonify({'success': False, 'message': username_validation['message']})
        
        # 检查用户名是否被其他用户使用
        existing_user = auth_db.users.get_user_by_username(username)
        if existing_user and existing_user.user_id != user_id:
            return jsonify({'success': False, 'message': '该用户名已被使用'})
        
        # 更新用户名
        user.username = username
        if not auth_db.users.update_user(user):
            return jsonify({'success': False, 'message': '更新失败'})
        
        # 更新会话
        session['username'] = username
        
        return jsonify({'success': True, 'message': '资料更新成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})

@auth_bp.route('/change_password', methods=['POST'])
def change_password():
    """修改密码"""
    # 检查登录状态
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': '请先登录'})
    
    try:
        data = request.get_json() if request.is_json else request.form
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        user_id = session['user_id']
        user = auth_db.users.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        # 验证当前密码
        if not PasswordUtils.verify_password(current_password, user.password_hash):
            return jsonify({'success': False, 'message': '当前密码错误'})
        
        # 验证新密码
        password_validation = validate_password(new_password)
        if not password_validation['valid']:
            return jsonify({'success': False, 'message': '新密码不符合要求: ' + ', '.join(password_validation['errors'])})
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': '两次输入的新密码不一致'})
        
        # 更新密码
        user.password_hash = PasswordUtils.hash_password(new_password)
        
        if not auth_db.users.update_user(user):
            return jsonify({'success': False, 'message': '密码修改失败'})
        
        # 删除用户所有会话（除了当前会话）
        auth_db.sessions.delete_user_sessions(user_id)
        
        return jsonify({'success': True, 'message': '密码修改成功，请重新登录'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'修改失败: {str(e)}'})

# 装饰器：检查用户是否登录
def login_required(f):
    """登录检查装饰器"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            if request.is_json:
                return jsonify({'success': False, 'message': '请先登录'}), 401
            else:
                return redirect(url_for('auth.login'))
        
        # 验证会话
        session_token = session.get('session_token')
        if session_token:
            user_session = auth_db.sessions.get_session(session_token)
            if not user_session:
                session.clear()
                if request.is_json:
                    return jsonify({'success': False, 'message': '会话已过期，请重新登录'}), 401
                else:
                    return redirect(url_for('auth.login'))
            
            # 更新会话活动时间
            user_session.update_activity()
            auth_db.sessions.update_session(user_session)
        
        return f(*args, **kwargs)
    
    return decorated_function

# 装饰器：检查用户角色
def role_required(required_role):
    """角色检查装饰器"""
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                if request.is_json:
                    return jsonify({'success': False, 'message': '请先登录'}), 401
                else:
                    return redirect(url_for('auth.login'))
            
            user_role = session.get('role', 'user')
            
            # 角色权限检查
            role_hierarchy = {'user': 1, 'moderator': 2, 'admin': 3}
            if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
                if request.is_json:
                    return jsonify({'success': False, 'message': '权限不足'}), 403
                else:
                    flash('权限不足', 'error')
                    return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# API路由：获取当前用户信息
@auth_bp.route('/api/me', methods=['GET'])
@login_required
def get_current_user():
    """获取当前用户信息"""
    user_id = session['user_id']
    user = auth_db.users.get_user_by_id(user_id)
    
    if user:
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    else:
        return jsonify({'success': False, 'message': '用户不存在'})

# API路由：检查登录状态
@auth_bp.route('/api/check_auth', methods=['GET'])
def check_auth():
    """检查登录状态"""
    if session.get('user_id'):
        user_id = session['user_id']
        user = auth_db.users.get_user_by_id(user_id)
        
        if user:
            return jsonify({
                'success': True,
                'authenticated': True,
                'user': {
                    'user_id': user.user_id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            })
    
    return jsonify({
        'success': True,
        'authenticated': False
    })

