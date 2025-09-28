#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDG多账号控制系统主应用
=====================

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

# 导入配置
from config import get_config

# 创建Flask应用
app = Flask(__name__)

# 加载配置
config_class = get_config()
app.config.from_object(config_class)

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
cors = CORS()

# 初始化应用
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)
cors.init_app(app)

# 配置登录管理器
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    from models.user import User
    return User.query.get(int(user_id))

def register_blueprints(app):
    """注册所有蓝图"""
    from api.auth import auth_bp
    from api.user import user_bp
    from api.data_sources import data_bp
    from api.model_configs import model_bp
    from api.admin import admin_bp
    # from api.synthetic import synthetic_bp
    # from api.quality import quality_bp
    # from api.sensitive import sensitive_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(data_bp, url_prefix='/api/data-sources')
    app.register_blueprint(model_bp, url_prefix='/api/model-configs')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    # app.register_blueprint(synthetic_bp, url_prefix='/api/synthetic')
    # app.register_blueprint(quality_bp, url_prefix='/api/quality')
    # app.register_blueprint(sensitive_bp, url_prefix='/api/sensitive')

def setup_logging(app):
    """设置日志"""
    if not app.debug and not app.testing:
        # 确保日志目录存在
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        os.makedirs(log_dir, exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=getattr(logging, app.config['LOG_LEVEL']),
            format='%(asctime)s %(levelname)s %(name)s %(message)s',
            handlers=[
                logging.FileHandler(app.config['LOG_FILE']),
                logging.StreamHandler()
            ]
        )

def create_app():
    """创建应用实例"""
    # 设置日志
    setup_logging(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 数据库初始化
    with app.app_context():
        db.create_all()
        
        # 创建默认管理员用户（如果不存在）
        create_default_admin()
    
    return app

def create_default_admin():
    """创建默认管理员用户"""
    from models.user import User, UserRole, UserStatus
    
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@sdg.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
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
        app.logger.info(f"创建默认管理员用户: {admin_email}")

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
    </ul>
    '''

@app.route('/health')
def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'environment': app.config.get('ENV', 'development')
    }

@app.route('/api/status')
def api_status():
    """API状态"""
    from models.user import User
    from models.data_source import DataSource
    
    stats = {
        'users_count': User.query.count(),
        'data_sources_count': DataSource.query.count(),
        'active_users': User.query.filter_by(status='active').count()
    }
    
    return {
        'success': True,
        'stats': stats,
        'timestamp': datetime.now().isoformat()
    }

if __name__ == '__main__':
    # 创建应用
    app = create_app()
    
    print("🚀 启动SDG多账号控制系统...")
    print("📱 访问地址: http://localhost:5000")
    print("🔐 认证功能:")
    print("   - 注册: http://localhost:5000/auth/register")
    print("   - 登录: http://localhost:5000/auth/login")
    print("   - 用户资料: http://localhost:5000/api/user/profile")
    print("   - 数据源管理: http://localhost:5000/api/data-sources")
    print("")
    print("💡 默认管理员账号: admin@sdg.com / admin123")
    print("💡 按Ctrl+C停止服务")
    print("")
    
    # 运行应用
    app.run(debug=True, host='0.0.0.0', port=5000)
