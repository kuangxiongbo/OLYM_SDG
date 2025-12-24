#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化默认管理员账号
"""

from app import create_app
from models.user import db, User

def create_default_admin():
    """创建默认管理员账号"""
    app = create_app()
    with app.app_context():
        # 检查是否已存在管理员
        admin = User.query.filter_by(email='admin@example.com').first()
        if admin:
            print(f"管理员账号已存在: admin@example.com")
            print(f"密码: admin123")
            return
        
        # 创建默认管理员
        # 生成username（使用邮箱前缀）
        email = 'admin@example.com'
        username = email.split('@')[0]
        
        admin = User(
            email=email,
            username=username,  # 设置username字段
            name='系统管理员',
            role='admin',
            status='active'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        print("=" * 50)
        print("✅ 默认管理员账号创建成功！")
        print("=" * 50)
        print("邮箱: admin@example.com")
        print("密码: admin123")
        print("=" * 50)
        print("\n请使用以上账号登录系统")
        print("登录后请及时修改密码！")

if __name__ == '__main__':
    create_default_admin()



