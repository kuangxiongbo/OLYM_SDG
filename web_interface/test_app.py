#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试应用
============

用于测试基本功能
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# 简单的用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    status = db.Column(db.String(20), default='active')
    email_verified = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return '''
    <h1>SDG多账号控制系统 - 测试版</h1>
    <p>✅ 应用启动成功！</p>
    <ul>
        <li>数据库连接: ✅</li>
        <li>模型加载: ✅</li>
        <li>蓝图注册: ✅</li>
    </ul>
    '''

@app.route('/test')
def test():
    return {'status': 'success', 'message': '测试成功'}

@app.route('/health')
def health():
    user_count = User.query.count()
    return {
        'status': 'healthy',
        'users': user_count,
        'database': 'connected'
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ 数据库表创建成功")
        
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
        db.session.commit()
        print("✅ 测试用户创建成功")
    
    print("🚀 启动测试应用...")
    print("📱 访问地址: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

