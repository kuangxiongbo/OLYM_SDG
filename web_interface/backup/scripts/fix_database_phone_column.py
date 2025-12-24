#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库phone列 - 通用版本
支持SQLite和PostgreSQL
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.user import db
from sqlalchemy import inspect, text

def fix_phone_column():
    """修复phone列"""
    app = create_app()
    
    with app.app_context():
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        print(f"数据库连接: {db_uri.split('@')[-1] if '@' in db_uri else db_uri}")
        
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
                
                # 根据数据库类型选择SQL语句
                if 'postgresql' in db_uri.lower() or 'postgres' in db_uri.lower():
                    # PostgreSQL
                    sql = text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
                else:
                    # SQLite
                    sql = text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
                
                with db.engine.connect() as conn:
                    trans = conn.begin()
                    try:
                        conn.execute(sql)
                        trans.commit()
                        print("✅ phone列添加成功")
                    except Exception as e:
                        trans.rollback()
                        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower() or 'exists' in str(e).lower():
                            print("ℹ️ phone列已存在")
                        else:
                            print(f"❌ 添加phone列失败: {e}")
                            raise
            else:
                print("✅ phone列已存在")
            
            # 验证修复
            inspector = inspect(db.engine)
            columns_after = {col['name'] for col in inspector.get_columns('users')}
            if 'phone' in columns_after:
                print("\n✅ 数据库修复完成，phone列已存在")
            else:
                print("\n⚠️ 警告：修复后phone列仍然不存在")
                
        except Exception as e:
            print(f"❌ 修复失败: {e}")
            import traceback
            traceback.print_exc()
            print("\n请手动执行以下SQL:")
            if 'postgresql' in db_uri.lower() or 'postgres' in db_uri.lower():
                print("ALTER TABLE users ADD COLUMN phone VARCHAR(20);")
            else:
                print("ALTER TABLE users ADD COLUMN phone VARCHAR(20);")

if __name__ == '__main__':
    fix_phone_column()




