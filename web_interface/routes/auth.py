#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证路由
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from models.user import db, User
from utils.validators import validate_email, validate_password
from services.email_service import EmailService
from utils.captcha import generate_math_captcha, store_captcha_in_session, get_captcha_from_session, verify_captcha, clear_captcha_from_session
from utils.helpers import log_operation_direct, get_client_ip

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/agreement', methods=['GET'])
def agreement_page():
    """用户协议页面"""
    return render_template('agreement.html')

@auth_bp.route('/login', methods=['GET'])
def login_page():
    """显示登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    try:
        return render_template('auth/login_new.html')
    except:
        # 如果模板不存在，返回简单的登录页面
        return '''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>登录 - AI 数据平台</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
                .container { background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); max-width: 400px; width: 100%; padding: 40px; }
                h1 { text-align: center; color: #333; margin-bottom: 30px; }
                .form-group { margin-bottom: 20px; }
                label { display: block; margin-bottom: 8px; color: #666; font-weight: 500; }
                input { width: 100%; padding: 12px; border: 2px solid #e1e5e9; border-radius: 8px; font-size: 16px; }
                input:focus { outline: none; border-color: #667eea; }
                button { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }
                button:hover { transform: translateY(-2px); }
                .links { text-align: center; margin-top: 20px; }
                .links a { color: #667eea; text-decoration: none; }
                .error { color: #e74c3c; margin-top: 10px; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>AI 数据平台</h1>
                <form id="loginForm">
                    <div class="form-group">
                        <label>邮箱</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label>密码</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit">登录</button>
                    <div id="error" class="error"></div>
                </form>
                <div class="links">
                    <a href="/api/auth/register">还没有账号？立即注册</a>
                </div>
            </div>
            <script>
                document.getElementById('loginForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const errorDiv = document.getElementById('error');
                    
                    try {
                        const response = await fetch('/api/auth/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email, password })
                        });
                        const data = await response.json();
                        if (data.success) {
                            window.location.href = '/';
                        } else {
                            errorDiv.textContent = data.error || '登录失败';
                        }
                    } catch (error) {
                        errorDiv.textContent = '网络错误，请重试';
                    }
                });
            </script>
        </body>
        </html>
        ''', 200

@auth_bp.route('/register', methods=['GET'])
def register_page():
    """显示注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    try:
        return render_template('auth/register_new.html')
    except:
        # 如果模板不存在，返回简单的注册页面
        return '''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>注册 - AI 数据平台</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
                .container { background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); max-width: 400px; width: 100%; padding: 40px; }
                h1 { text-align: center; color: #333; margin-bottom: 30px; }
                .form-group { margin-bottom: 20px; }
                label { display: block; margin-bottom: 8px; color: #666; font-weight: 500; }
                input { width: 100%; padding: 12px; border: 2px solid #e1e5e9; border-radius: 8px; font-size: 16px; }
                input:focus { outline: none; border-color: #667eea; }
                button { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }
                button:hover { transform: translateY(-2px); }
                .links { text-align: center; margin-top: 20px; }
                .links a { color: #667eea; text-decoration: none; }
                .error { color: #e74c3c; margin-top: 10px; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>注册账号</h1>
                <form id="registerForm">
                    <div class="form-group">
                        <label>邮箱</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label>密码</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <div class="form-group">
                        <label>确认密码</label>
                        <input type="password" id="confirm_password" name="confirm_password" required>
                    </div>
                    <button type="submit">注册</button>
                    <div id="error" class="error"></div>
                </form>
                <div class="links">
                    <a href="/api/auth/login">已有账号？立即登录</a>
                </div>
            </div>
            <script>
                document.getElementById('registerForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    const confirmPassword = document.getElementById('confirm_password').value;
                    const errorDiv = document.getElementById('error');
                    
                    if (password !== confirmPassword) {
                        errorDiv.textContent = '两次输入的密码不一致';
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/auth/register', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email, password, confirm_password: confirmPassword })
                        });
                        const data = await response.json();
                        if (data.success) {
                            alert('注册成功！激活码已发送至邮箱，请查收。');
                            window.location.href = '/api/auth/activate';
                        } else {
                            errorDiv.textContent = data.error || '注册失败';
                        }
                    } catch (error) {
                        errorDiv.textContent = '网络错误，请重试';
                    }
                });
            </script>
        </body>
        </html>
        ''', 200

@auth_bp.route('/captcha', methods=['GET'])
def get_captcha():
    """获取验证码"""
    try:
        # 生成数学验证码
        question, answer = generate_math_captcha()
        
        # 存储到session
        store_captcha_in_session(answer, expire_minutes=5)
        
        return jsonify({
            'success': True,
            'data': {
                'question': question,
                'type': 'math'
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json() or {}
        # 安全地获取并处理数据，防止 None 值
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''
        confirm_password = data.get('confirm_password') or ''
        phone = (data.get('phone') or '').strip()
        captcha = (data.get('captcha') or '').strip()
        
        # 验证验证码
        captcha_code = get_captcha_from_session()
        if not captcha_code:
            return jsonify({
                'success': False,
                'error': '验证码已过期，请刷新验证码',
                'code': 'CAPTCHA_EXPIRED'
            }), 400
        
        if not verify_captcha(captcha, captcha_code):
            return jsonify({
                'success': False,
                'error': '验证码错误，请重新输入',
                'code': 'CAPTCHA_INVALID'
            }), 400
        
        # 验证输入
        if not email or not password:
            return jsonify({
                'success': False,
                'error': '邮箱和密码不能为空',
                'code': 'INVALID_PARAMS'
            }), 400
        
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': '邮箱格式不正确',
                'code': 'INVALID_PARAMS'
            }), 400
        
        if password != confirm_password:
            return jsonify({
                'success': False,
                'error': '两次输入的密码不一致',
                'code': 'INVALID_PARAMS'
            }), 400
        
        is_valid, msg = validate_password(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': msg,
                'code': 'INVALID_PARAMS'
            }), 400
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'error': '该邮箱已被注册',
                'code': 'INVALID_PARAMS'
            }), 400
        
        # 创建用户
        # 生成username（使用邮箱前缀）
        username = email.split('@')[0]
        # 检查username是否已存在，如果存在则添加数字后缀
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User(
            email=email,
            username=username,  # 设置username字段
            phone=phone,
            role='user',
            status='pending'
        )
        user.set_password(password)
        activation_code = user.generate_activation_code()
        db.session.add(user)
        db.session.commit()
        
        # 记录注册日志
        log_operation_direct(
            action='用户注册',
            resource_type='user',
            resource_id=user.id,
            result='success',
            user_id=user.id,
            details={
                'email': email,
                'phone': phone if phone else None,
                'role': 'user',
                'status': 'pending'
            }
        )
        
        # 清除验证码（注册成功后）
        clear_captcha_from_session()
        
        # 发送激活邮件
        email_sent = False
        email_error = None
        try:
            import sys
            email_service = EmailService()
            email_service.send_activation_email(email, activation_code)
            email_sent = True
            
            # 记录发送邮件日志
            log_operation_direct(
                action='发送激活邮件',
                resource_type='email',
                resource_id=user.id,
                result='success',
                user_id=user.id,
                details={
                    'recipient': email,
                    'email_type': 'activation',
                    'activation_code': activation_code
                }
            )
        except Exception as e:
            import sys
            import traceback
            error_detail = traceback.format_exc()
            print(f"[ERROR] 邮件发送失败: {e}", file=sys.stderr)
            print(f"[ERROR] 错误详情: {error_detail}", file=sys.stderr)
            email_error = str(e)
            
            # 记录发送邮件失败日志
            log_operation_direct(
                action='发送激活邮件',
                resource_type='email',
                resource_id=user.id,
                result='failure',
                user_id=user.id,
                details={
                    'recipient': email,
                    'email_type': 'activation',
                    'error': str(e)
                }
            )
        
        # 即使邮件发送失败，也返回成功（用户已创建）
        # 但会在消息中提示邮件发送状态
        if email_sent:
            message = '注册成功，激活码已发送至邮箱'
        else:
            message = f'注册成功，但邮件发送失败: {email_error}。激活码: {activation_code}'
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user.id,
                'email': user.email,
                'message': message,
                'activation_code': activation_code if not email_sent else None,  # 如果邮件发送失败，返回激活码
                'email_sent': email_sent
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/activate', methods=['GET'])
def activate_page():
    """显示激活页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    try:
        return render_template('auth/activation_new.html')
    except:
        return '''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>账号激活 - AI 数据平台</title>
        </head>
        <body>
            <div style="max-width: 520px; margin: 50px auto; padding: 20px;">
                <h2>激活你的账户</h2>
                <p>已向您的邮箱发送激活码，请查收并填写激活码。</p>
                <form id="activateForm">
                    <div style="margin-bottom: 20px;">
                        <label>邮箱</label>
                        <input type="email" id="email" required style="width: 100%; padding: 10px; margin-top: 5px;">
                    </div>
                    <div style="margin-bottom: 20px;">
                        <label>激活码</label>
                        <input type="text" id="activation_code" required style="width: 100%; padding: 10px; margin-top: 5px;">
                    </div>
                    <button type="submit" style="width: 100%; padding: 12px; background: #2563eb; color: white; border: none; border-radius: 8px;">提交激活</button>
                </form>
                <div style="margin-top: 20px;">
                    <button onclick="resendActivation()" style="background: transparent; border: 1px solid #2563eb; color: #2563eb; padding: 10px 20px; border-radius: 8px;">重新发送激活邮件</button>
                </div>
            </div>
            <script>
                document.getElementById('activateForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    const email = document.getElementById('email').value;
                    const code = document.getElementById('activation_code').value;
                    const response = await fetch('/api/auth/activate', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({email, activation_code: code})
                    });
                    const data = await response.json();
                    if (data.success) {
                        alert('激活成功！');
                        window.location.href = '/api/auth/login';
                    } else {
                        alert(data.error || '激活失败');
                    }
                });
                async function resendActivation() {
                    const email = document.getElementById('email').value;
                    if (!email) {
                        alert('请先输入邮箱');
                        return;
                    }
                    const response = await fetch('/api/auth/resend-activation', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({email})
                    });
                    const data = await response.json();
                    alert(data.success ? '激活码已重新发送' : (data.error || '发送失败'));
                }
            </script>
        </body>
        </html>
        ''', 200

@auth_bp.route('/activate', methods=['POST'])
def activate():
    """账号激活"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        activation_code = data.get('activation_code', '').strip().upper()
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'success': False,
                'error': '用户不存在',
                'code': 'RESOURCE_NOT_FOUND'
            }), 404
        
        if user.status == 'active':
            # 记录激活失败日志（账号已激活）
            log_operation_direct(
                action='账号激活',
                resource_type='user',
                resource_id=user.id,
                result='failure',
                user_id=user.id,
                details={
                    'email': email,
                    'error': '账号已激活'
                }
            )
            return jsonify({
                'success': False,
                'error': '账号已激活',
                'code': 'INVALID_PARAMS'
            }), 400
        
        if not user.activation_code or user.activation_code != activation_code:
            # 记录激活失败日志
            log_operation_direct(
                action='账号激活',
                resource_type='user',
                resource_id=user.id,
                result='failure',
                user_id=user.id,
                details={
                    'email': email,
                    'error': '激活码错误'
                }
            )
            return jsonify({
                'success': False,
                'error': '激活码错误',
                'code': 'INVALID_PARAMS'
            }), 400
        
        from datetime import datetime
        if user.activation_expires_at and user.activation_expires_at < datetime.utcnow():
            # 记录激活失败日志
            log_operation_direct(
                action='账号激活',
                resource_type='user',
                resource_id=user.id,
                result='failure',
                user_id=user.id,
                details={
                    'email': email,
                    'error': '激活码已过期'
                }
            )
            return jsonify({
                'success': False,
                'error': '激活码已过期',
                'code': 'INVALID_PARAMS'
            }), 400
        
        # 激活账号
        user.status = 'active'
        user.activation_code = None
        user.activation_expires_at = None
        db.session.commit()
        
        # 记录激活日志
        log_operation_direct(
            action='账号激活',
            resource_type='user',
            resource_id=user.id,
            result='success',
            user_id=user.id,
            details={
                'email': email,
                'status': 'active'
            }
        )
        
        return jsonify({
            'success': True,
            'data': {
                'message': '激活成功'
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        captcha_session_id = data.get('captcha_session_id')
        captcha_code = data.get('captcha_code', '').strip().upper()
        remember = data.get('remember', True)
        
        # 检查登录失败次数（如果存在LoginAttempt模型）
        from datetime import datetime, timedelta
        try:
            from models.log import LoginAttempt
            recent_attempts = LoginAttempt.query.filter(
                LoginAttempt.email == email,
                LoginAttempt.success == False,
                LoginAttempt.created_at > datetime.utcnow() - timedelta(minutes=15)
            ).count()
            
            # 如果失败次数大于等于1，需要验证码
            if recent_attempts >= 1:
                if not captcha_session_id or not captcha_code:
                    return jsonify({
                        'success': False,
                        'error': '登录失败次数过多，需要图形验证码',
                        'code': 'AUTH_FAILED',
                        'require_captcha': True
                    }), 400
                
                # 验证验证码
                try:
                    from models.config import CaptchaSession
                    captcha_session = CaptchaSession.query.filter_by(session_id=captcha_session_id).first()
                    if not captcha_session or not captcha_session.is_valid():
                        return jsonify({
                            'success': False,
                            'error': '验证码已过期，请刷新验证码',
                            'code': 'AUTH_FAILED',
                            'require_captcha': True
                        }), 400
                    
                    if captcha_session.captcha_code.upper() != captcha_code:
                        # 记录登录失败
                        login_attempt = LoginAttempt(
                            email=email,
                            success=False,
                            ip_address=request.remote_addr,
                            user_agent=request.headers.get('User-Agent', '')
                        )
                        db.session.add(login_attempt)
                        db.session.commit()
                        return jsonify({
                            'success': False,
                            'error': '验证码错误',
                            'code': 'AUTH_FAILED',
                            'require_captcha': True
                        }), 400
                    
                    # 验证码正确，标记为已使用
                    captcha_session.use()
                    db.session.commit()
                except ImportError:
                    # 如果模型不存在，跳过验证码验证
                    pass
        except ImportError:
            # 如果LoginAttempt模型不存在，跳过失败次数检查
            pass
        
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            # 记录登录失败
            try:
                from models.log import LoginAttempt
                login_attempt = LoginAttempt(
                    email=email,
                    success=False,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')
                )
                db.session.add(login_attempt)
                db.session.commit()
            except ImportError:
                pass
            
            # 记录登录失败日志
            log_operation_direct(
                action='用户登录',
                resource_type='auth',
                result='failure',
                user_id=user.id if user else None,
                details={
                    'email': email,
                    'error': '邮箱或密码错误'
                }
            )
            
            return jsonify({
                'success': False,
                'error': '邮箱或密码错误',
                'code': 'AUTH_FAILED'
            }), 401
        
        if user.status != 'active':
            return jsonify({
                'success': False,
                'error': '账号未激活，请先激活账号',
                'code': 'AUTH_FAILED'
            }), 403
        
        # 记录登录成功
        try:
            from models.log import LoginAttempt
            login_attempt = LoginAttempt(
                email=email,
                success=True,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            db.session.add(login_attempt)
        except ImportError:
            pass
        
        # 更新最后登录时间
        from datetime import datetime
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        # 登录用户
        login_user(user, remember=remember)
        
        # 记录登录成功日志
        log_operation_direct(
            action='用户登录',
            resource_type='auth',
            result='success',
            user_id=user.id,
            details={
                'email': email,
                'remember': remember
            }
        )
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(),
                'message': '登录成功'
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    """用户登出"""
    from flask import redirect, url_for
    
    # 记录登出日志（在logout_user之前，因为logout后current_user会失效）
    user_id = current_user.id if current_user.is_authenticated else None
    user_email = current_user.email if current_user.is_authenticated else None
    
    logout_user()
    
    # 记录登出日志
    if user_id:
        log_operation_direct(
            action='用户登出',
            resource_type='auth',
            result='success',
            user_id=user_id,
            details={
                'email': user_email
            }
        )
    
    # 如果是GET请求（浏览器访问），重定向到登录页
    if request.method == 'GET':
        return redirect(url_for('auth.login_page'))
    return jsonify({
        'success': True,
        'message': '登出成功'
    }), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """获取当前用户信息"""
    return jsonify({
        'success': True,
        'data': current_user.to_dict()
    }), 200

@auth_bp.route('/resend-activation', methods=['POST'])
def resend_activation():
    """重新发送激活码"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'success': False,
                'error': '用户不存在',
                'code': 'RESOURCE_NOT_FOUND'
            }), 404
        
        if user.status == 'active':
            return jsonify({
                'success': False,
                'error': '账号已激活',
                'code': 'INVALID_PARAMS'
            }), 400
        
        # 重新生成激活码
        activation_code = user.generate_activation_code()
        db.session.commit()
        
        # 发送激活邮件
        email_sent = False
        email_error = None
        try:
            email_service = EmailService()
            email_service.send_activation_email(email, activation_code)
            email_sent = True
            
            # 记录重新发送激活邮件日志
            log_operation_direct(
                action='重新发送激活邮件',
                resource_type='email',
                resource_id=user.id,
                result='success',
                user_id=user.id,
                details={
                    'recipient': email,
                    'email_type': 'activation'
                }
            )
        except Exception as e:
            print(f"邮件发送失败: {e}")
            email_error = str(e)
            
            # 记录重新发送激活邮件失败日志
            log_operation_direct(
                action='重新发送激活邮件',
                resource_type='email',
                resource_id=user.id,
                result='failure',
                user_id=user.id,
                details={
                    'recipient': email,
                    'email_type': 'activation',
                    'error': str(e)
                }
            )
        
        return jsonify({
            'success': True,
            'message': '激活码已重新发送' if email_sent else f'激活码重新发送失败: {email_error}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

