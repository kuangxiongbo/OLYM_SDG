#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDG Web界面 - 仅认证功能版本
=============================

不依赖SDG模块的简化版本，专注于用户认证功能
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import os
import uuid
from datetime import datetime
import traceback

# 导入认证相关模块
from models import User, UserSession, EmailVerification, PasswordReset, PasswordUtils, TokenUtils
from database import auth_db
from email_service import email_service

app = Flask(__name__)
app.secret_key = 'sdg_web_interface_secret_key_2025'

# 导入认证蓝图
from auth_routes import auth_bp

# 注册认证蓝图
app.register_blueprint(auth_bp)

# 配置
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# 创建必要的文件夹
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0-auth-only',
        'features': ['user_authentication', 'email_verification', 'password_reset']
    })

@app.route('/dashboard')
def dashboard():
    """用户仪表板"""
    # 检查登录状态
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = auth_db.users.get_user_by_id(user_id)
    
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    return render_template('dashboard.html', user=user.to_dict())

@app.route('/admin')
def admin():
    """管理员页面"""
    # 检查登录状态和权限
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = auth_db.users.get_user_by_id(user_id)
    
    if not user or user.role != 'admin':
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    
    # 获取用户统计信息
    users = auth_db.users.list_users()
    total_users = len(users)
    verified_users = len([u for u in users if u.is_verified])
    
    return render_template('admin.html', 
                         user=user.to_dict(),
                         stats={
                             'total_users': total_users,
                             'verified_users': verified_users,
                             'unverified_users': total_users - verified_users
                         })

@app.route('/api/stats')
def api_stats():
    """获取统计信息API"""
    try:
        users = auth_db.users.list_users()
        total_users = len(users)
        verified_users = len([u for u in users if u.is_verified])
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'verified_users': verified_users,
                'unverified_users': total_users - verified_users,
                'users_by_role': {
                    'user': len([u for u in users if u.role == 'user']),
                    'admin': len([u for u in users if u.role == 'admin']),
                    'moderator': len([u for u in users if u.role == 'moderator'])
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# 清理过期数据的定时任务（简化版）
@app.before_request
def cleanup_expired_data():
    """清理过期数据"""
    try:
        # 每100个请求清理一次，避免频繁清理
        if not hasattr(cleanup_expired_data, 'counter'):
            cleanup_expired_data.counter = 0
        
        cleanup_expired_data.counter += 1
        if cleanup_expired_data.counter % 100 == 0:
            auth_db.cleanup_expired_data()
    except Exception as e:
        # 清理失败不影响主要功能
        pass

if __name__ == '__main__':
    print("🚀 启动SDG Web界面认证系统...")
    print("📱 访问地址: http://localhost:5001")
    print("🔐 认证功能:")
    print("   - 注册: http://localhost:5001/auth/register")
    print("   - 登录: http://localhost:5001/auth/login")
    print("   - 个人资料: http://localhost:5001/auth/profile")
    print("")
    print("💡 这是仅认证功能版本，不包含SDG数据生成功能")
    print("💡 按Ctrl+C停止服务")
    print("")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
