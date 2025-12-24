#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库表结构：确保users表包含所有必需的列
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.user import db
from sqlalchemy import inspect, text

def fix_users_table():
    """修复users表结构"""
    app = create_app()
    
    with app.app_context():
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
            print(f"现有列: {existing_columns}")
            
            # 必需的列
            required_columns = {
                'id', 'email', 'password_hash', 'phone', 'name', 'role', 
                'status', 'activation_code', 'activation_expires_at', 
                'created_at', 'updated_at', 'last_login_at'
            }
            
            # 检查缺失的列
            missing_columns = required_columns - existing_columns
            
            if not missing_columns:
                print("✅ users表结构完整，所有必需的列都存在")
                return
            
            print(f"⚠️ 发现缺失的列: {missing_columns}")
            
            # 添加缺失的列
            with db.engine.connect() as conn:
                for col_name in missing_columns:
                    try:
                        if col_name == 'phone':
                            sql = text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
                        elif col_name == 'name':
                            sql = text("ALTER TABLE users ADD COLUMN name VARCHAR(100)")
                        elif col_name == 'role':
                            sql = text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL")
                        elif col_name == 'status':
                            sql = text("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'pending' NOT NULL")
                        elif col_name == 'activation_code':
                            sql = text("ALTER TABLE users ADD COLUMN activation_code VARCHAR(100)")
                        elif col_name == 'activation_expires_at':
                            sql = text("ALTER TABLE users ADD COLUMN activation_expires_at TIMESTAMP")
                        elif col_name == 'created_at':
                            sql = text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                        elif col_name == 'updated_at':
                            sql = text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                        elif col_name == 'last_login_at':
                            sql = text("ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP")
                        else:
                            print(f"⚠️ 跳过未知列: {col_name}")
                            continue
                        
                        conn.execute(sql)
                        conn.commit()
                        print(f"✅ 已添加列: {col_name}")
                    except Exception as e:
                        # 如果列已存在或其他错误
                        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                            print(f"ℹ️ 列 {col_name} 已存在，跳过")
                        else:
                            print(f"❌ 添加列 {col_name} 失败: {e}")
                            # 打印SQL以便手动执行
                            print(f"   请手动执行: ALTER TABLE users ADD COLUMN {col_name} ...")
            
            print("\n✅ 数据库表结构修复完成")
            
        except Exception as e:
            print(f"❌ 修复失败: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    fix_users_table()






