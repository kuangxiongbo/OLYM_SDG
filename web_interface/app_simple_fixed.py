#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDG多账号控制系统 - 简化修复版
===============================

用于测试基本功能
"""

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from datetime import datetime

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sdg-web-interface-secret-key-2025'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 确保目录存在并设置数据库路径
current_dir = os.path.dirname(os.path.abspath(__file__))
instance_dir = os.path.join(current_dir, 'instance')
db_path = os.path.join(instance_dir, 'database_simple.db')

# 创建instance目录
os.makedirs(instance_dir, exist_ok=True)

# 设置数据库URI
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

# 初始化扩展
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# 简单的用户模型
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    status = db.Column(db.String(20), default='active')
    email_verified = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'role': self.role,
            'status': self.status,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DataSource(db.Model):
    __tablename__ = 'data_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='processing')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'type': self.type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 基础路由
@app.route('/')
def index():
    """首页"""
    return '''
    <h1>SDG多账号控制系统 - 简化版</h1>
    <p>✅ 系统运行正常！</p>
    <ul>
        <li><a href="/health">健康检查</a></li>
        <li><a href="/api/status">API状态</a></li>
        <li><a href="/api/users">用户列表</a></li>
        <li><a href="/api/data-sources">数据源列表</a></li>
    </ul>
    '''

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0-simple',
        'database_path': db_path,
        'database_exists': os.path.exists(db_path)
    })

@app.route('/api/status')
def api_status():
    """API状态"""
    try:
        stats = {
            'users_count': User.query.count(),
            'data_sources_count': DataSource.query.count(),
            'active_users': User.query.filter_by(status='active').count()
        }
        
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/users')
def get_users():
    """获取用户列表"""
    try:
        users = User.query.all()
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/data-sources')
def get_data_sources():
    """获取数据源列表"""
    try:
        data_sources = DataSource.query.all()
        return jsonify({
            'success': True,
            'data_sources': [ds.to_dict() for ds in data_sources]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def create_app():
    """创建应用实例"""
    print("🔧 初始化简化版应用...")
    
    # 数据库初始化
    try:
        with app.app_context():
            print("🔧 创建数据库表...")
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 创建测试数据
            create_test_data()
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise
    
    return app

def create_test_data():
    """创建测试数据"""
    try:
        # 检查是否已有数据
        if User.query.count() == 0:
            # 创建测试用户
            test_user = User(
                email='test@example.com',
                username='testuser',
                password_hash='hashed_password',
                role='user',
                status='active',
                email_verified=True
            )
            db.session.add(test_user)
            
            # 创建管理员用户
            admin_user = User(
                email='admin@sdg.com',
                username='admin',
                password_hash='hashed_password',
                role='super_admin',
                status='active',
                email_verified=True
            )
            db.session.add(admin_user)
            
            db.session.commit()
            print("✅ 测试数据创建成功")
        else:
            print("ℹ️  测试数据已存在")
            
    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")

if __name__ == '__main__':
    # 创建应用
    print("🚀 启动SDG多账号控制系统 - 简化版...")
    app = create_app()
    
    print("📱 访问地址: http://localhost:5000")
    print("💡 数据库路径:", db_path)
    print("💡 按Ctrl+C停止服务")
    print("")
    
    # 运行应用
    app.run(debug=True, host='0.0.0.0', port=5000)

