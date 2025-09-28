#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证API路由
============

处理用户认证相关的API接口
"""

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user

from services.auth_service import AuthService
from utils.decorators import json_required, validate_json

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    try:
        data = request.get_json()
        user = AuthService.register_user(
            email=data['email'],
            username=data['username'],
            password=data['password']
        )
        return jsonify({
            'success': True, 
            'message': '注册成功，请查收验证邮件',
            'user': user.to_dict()
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': '注册失败'}), 500

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    try:
        data = request.get_json()
        user = AuthService.login_user(data['email'], data['password'])
        return jsonify({
            'success': True, 
            'message': '登录成功',
            'user': user.to_dict()
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': '登录失败'}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    try:
        AuthService.logout_user()
        return jsonify({'success': True, 'message': '登出成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': '登出失败'}), 500

@auth_bp.route('/verify-email', methods=['POST'])
@json_required
@validate_json('token')
def verify_email():
    """邮箱验证"""
    try:
        data = request.get_json()
        success = AuthService.verify_email(data['token'])
        if success:
            return jsonify({'success': True, 'message': '邮箱验证成功'})
        else:
            return jsonify({'success': False, 'message': '邮箱验证失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': '验证失败'}), 500

@auth_bp.route('/resend-verification', methods=['POST'])
@json_required
@validate_json('email')
def resend_verification():
    """重发验证邮件"""
    try:
        data = request.get_json()
        success = AuthService.resend_verification_email(data['email'])
        if success:
            return jsonify({'success': True, 'message': '验证邮件已重发'})
        else:
            return jsonify({'success': False, 'message': '重发失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': '重发失败'}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
@json_required
@validate_json('email')
def forgot_password():
    """忘记密码"""
    try:
        data = request.get_json()
        success = AuthService.forgot_password(data['email'])
        if success:
            return jsonify({'success': True, 'message': '密码重置邮件已发送'})
        else:
            return jsonify({'success': False, 'message': '邮箱不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': '发送失败'}), 500

@auth_bp.route('/reset-password', methods=['POST'])
@json_required
@validate_json('token', 'new_password')
def reset_password():
    """重置密码"""
    try:
        data = request.get_json()
        success = AuthService.reset_password(data['token'], data['new_password'])
        if success:
            return jsonify({'success': True, 'message': '密码重置成功'})
        else:
            return jsonify({'success': False, 'message': '密码重置失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': '重置失败'}), 500

@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    """检查认证状态"""
    try:
        if current_user.is_authenticated:
            return jsonify({
                'success': True,
                'authenticated': True,
                'user': current_user.to_dict()
            })
        else:
            return jsonify({
                'success': True,
                'authenticated': False
            })
    except Exception as e:
        return jsonify({'success': False, 'message': '检查失败'}), 500

