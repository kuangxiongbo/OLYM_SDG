#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDG多账号控制系统主应用 - 修复版
=================================

基于Flask的多账号数据生成平台
提供合成数据生成、质量评估和敏感字段发现三大核心功能
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
import os
import logging
from datetime import datetime

# 创建Flask应用
app = Flask(__name__)

# 基础配置
app.config['SECRET_KEY'] = 'sdg-web-interface-secret-key-2025'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 确保目录存在并设置数据库路径
current_dir = os.path.dirname(os.path.abspath(__file__))
instance_dir = os.path.join(current_dir, 'instance')
db_path = os.path.join(instance_dir, 'database.db')

# 创建instance目录
os.makedirs(instance_dir, exist_ok=True)

# 设置数据库URI - 使用绝对路径
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

# 邮件配置
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None
app.config['MAIL_DEFAULT_SENDER'] = None

# 会话配置
from datetime import timedelta
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# 初始化扩展
db = SQLAlchemy(app)
login_manager = LoginManager(app)
mail = Mail(app)
cors = CORS(app)

# 配置登录管理器
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'info'

# 导入模型
from models.user import User, UserRole, UserStatus
from models.data_source import DataSource
from models.model_config import ModelConfig
from models.tasks import SyntheticTask, QualityTask, SensitiveTask

@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    return User.query.get(int(user_id))

def register_blueprints(app):
    """注册所有蓝图"""
    try:
        from api.auth import auth_bp
        from api.user import user_bp
        from api.data_sources import data_bp
        from api.model_configs import model_bp
        from api.admin import admin_bp
        
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(user_bp, url_prefix='/api/user')
        app.register_blueprint(data_bp, url_prefix='/api/data-sources')
        app.register_blueprint(model_bp, url_prefix='/api/model-configs')
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        
        print("✅ 蓝图注册成功")
    except Exception as e:
        print(f"❌ 蓝图注册失败: {e}")

def create_app():
    """创建应用实例"""
    print("🔧 初始化应用...")
    
    # 注册蓝图
    register_blueprints(app)
    
    # 数据库初始化
    try:
        with app.app_context():
            print("🔧 创建数据库表...")
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 创建默认管理员用户（如果不存在）
            create_default_admin()
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise
    
    return app

def create_default_admin():
    """创建默认管理员用户"""
    try:
        admin_email = 'admin@sdg.com'
        admin_password = 'admin123'
        
        existing_admin = User.query.filter_by(email=admin_email).first()
        if not existing_admin:
            admin = User(
                email=admin_email,
                username='admin',
                password_hash='',
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
                email_verified=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"✅ 创建默认管理员用户: {admin_email}")
        else:
            print(f"ℹ️  管理员用户已存在: {admin_email}")
    except Exception as e:
        print(f"❌ 创建管理员用户失败: {e}")

# 基础路由
@app.route('/')
def index():
    """首页"""
    return '''
    <h1>SDG多账号控制系统</h1>
    <p>欢迎使用SDG多账号控制系统！</p>
    <ul>
        <li><a href="/auth/register">注册</a></li>
        <li><a href="/auth/login">登录</a></li>
        <li><a href="/api/user/profile">用户资料</a></li>
        <li><a href="/api/data-sources">数据源管理</a></li>
        <li><a href="/api/model-configs">模型配置</a></li>
        <li><a href="/api/admin/stats">系统统计</a></li>
    </ul>
    '''

@app.route('/health')
def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0-fixed',
        'database_path': db_path,
        'database_exists': os.path.exists(db_path)
    }

@app.route('/api/status')
def api_status():
    """API状态"""
    try:
        stats = {
            'users_count': User.query.count(),
            'data_sources_count': DataSource.query.count(),
            'model_configs_count': ModelConfig.query.count(),
            'active_users': User.query.filter_by(status=UserStatus.ACTIVE).count()
        }
        
        return {
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == '__main__':
    # 创建应用
    print("🚀 启动SDG多账号控制系统...")
    app = create_app()
    
    print("📱 访问地址: http://localhost:5000")
    print("🔐 认证功能:")
    print("   - 注册: http://localhost:5000/auth/register")
    print("   - 登录: http://localhost:5000/auth/login")
    print("   - 用户资料: http://localhost:5000/api/user/profile")
    print("   - 数据源管理: http://localhost:5000/api/data-sources")
    print("   - 模型配置: http://localhost:5000/api/model-configs")
    print("   - 系统统计: http://localhost:5000/api/admin/stats")
    print("")
    print("💡 默认管理员账号: admin@sdg.com / admin123")
    print("💡 数据库路径:", db_path)
    print("💡 按Ctrl+C停止服务")
    print("")
    
    # 运行应用
    app.run(debug=True, host='0.0.0.0', port=5000)

