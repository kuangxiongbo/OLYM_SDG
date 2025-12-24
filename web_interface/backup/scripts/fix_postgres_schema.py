#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复PostgreSQL数据库表结构：添加phone列
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.user import db
from sqlalchemy import inspect, text

def fix_postgres_users_table():
    """修复PostgreSQL users表结构"""
    app = create_app()
    
    with app.app_context():
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        
        # 检查是否是PostgreSQL
        if 'postgresql' not in db_uri.lower() and 'postgres' not in db_uri.lower():
            print(f"当前数据库不是PostgreSQL: {db_uri}")
            print("如果错误仍然存在，请检查环境变量DATABASE_URL")
            return
        
        print(f"检测到PostgreSQL数据库连接")
        print(f"正在修复users表结构...")
        
        try:
            inspector = inspect(db.engine)
            
            # 检查users表是否存在
            if not inspector.has_table('users'):
                print("❌ users表不存在，正在创建...")
                db.create_all()
                print("✅ users表创建成功")
                return
            
            # 获取现有列
            existing_columns = {col['name'] for col in inspector.get_columns('users')}
            print(f"现有列: {sorted(existing_columns)}")
            
            # 检查phone列
            if 'phone' not in existing_columns:
                print("⚠️ phone列不存在，正在添加...")
                with db.engine.connect() as conn:
                    try:
                        # 使用事务
                        trans = conn.begin()
                        conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)"))
                        trans.commit()
                        print("✅ phone列添加成功")
                    except Exception as e:
                        trans.rollback()
                        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                            print("ℹ️ phone列已存在")
                        else:
                            print(f"❌ 添加phone列失败: {e}")
                            print("\n请手动执行以下SQL:")
                            print("ALTER TABLE users ADD COLUMN phone VARCHAR(20);")
                            raise
            else:
                print("✅ phone列已存在")
            
            # 检查其他可能缺失的列
            required_columns = {
                'id', 'email', 'password_hash', 'phone', 'name', 'role', 
                'status', 'activation_code', 'activation_expires_at', 
                'created_at', 'updated_at', 'last_login_at'
            }
            
            missing_columns = required_columns - existing_columns
            
            if missing_columns:
                print(f"\n⚠️ 发现其他缺失的列: {missing_columns}")
                with db.engine.connect() as conn:
                    trans = conn.begin()
                    try:
                        for col_name in missing_columns:
                            if col_name == 'name':
                                conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR(100)"))
                            elif col_name == 'role':
                                conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL"))
                            elif col_name == 'status':
                                conn.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'pending' NOT NULL"))
                            elif col_name == 'activation_code':
                                conn.execute(text("ALTER TABLE users ADD COLUMN activation_code VARCHAR(100)"))
                            elif col_name == 'activation_expires_at':
                                conn.execute(text("ALTER TABLE users ADD COLUMN activation_expires_at TIMESTAMP"))
                            elif col_name == 'created_at':
                                conn.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                            elif col_name == 'updated_at':
                                conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                            elif col_name == 'last_login_at':
                                conn.execute(text("ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP"))
                            print(f"✅ 已添加列: {col_name}")
                        trans.commit()
                    except Exception as e:
                        trans.rollback()
                        print(f"❌ 添加列失败: {e}")
                        raise
            
            print("\n✅ PostgreSQL数据库表结构修复完成")
            
        except Exception as e:
            print(f"❌ 修复失败: {e}")
            import traceback
            traceback.print_exc()
            print("\n如果自动修复失败，请手动执行以下SQL:")
            print("ALTER TABLE users ADD COLUMN phone VARCHAR(20);")
            print("ALTER TABLE users ADD COLUMN name VARCHAR(100);")
            print("-- 其他缺失的列...")

if __name__ == '__main__':
    fix_postgres_users_table()






