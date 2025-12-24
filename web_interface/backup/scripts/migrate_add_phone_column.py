#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加phone列到users表
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.user import db

def migrate_add_phone_column():
    """添加phone列到users表"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查phone列是否已存在
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'phone' in columns:
                print("✅ phone列已存在，无需迁移")
                return
            
            # 添加phone列
            print("🔧 正在添加phone列到users表...")
            db.engine.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
            print("✅ phone列添加成功")
            
        except Exception as e:
            # 如果ALTER TABLE失败，尝试使用SQLAlchemy的方式
            print(f"⚠️ 直接SQL执行失败: {e}")
            print("🔧 尝试使用SQLAlchemy方式...")
            
            try:
                # 使用SQLAlchemy的text()执行SQL
                from sqlalchemy import text
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)"))
                    conn.commit()
                print("✅ phone列添加成功")
            except Exception as e2:
                print(f"❌ 迁移失败: {e2}")
                print("\n请手动执行以下SQL语句:")
                print("ALTER TABLE users ADD COLUMN phone VARCHAR(20);")
                raise

if __name__ == '__main__':
    migrate_add_phone_column()






