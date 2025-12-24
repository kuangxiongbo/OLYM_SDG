#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接修复PostgreSQL数据库phone列
使用运行中的应用的数据库连接
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect, text

# 从运行中的应用获取的数据库连接
DATABASE_URL = "postgresql+psycopg2://SDC:nScWntDCaEajtJmD@192.168.210.90:5433/SDC"

def fix_postgres_phone_column():
    """修复PostgreSQL数据库phone列"""
    print(f"连接到PostgreSQL数据库: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'PostgreSQL'}")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # 检查users表是否存在
            if not inspector.has_table('users'):
                print("❌ users表不存在")
                return
            
            # 获取现有列
            existing_columns = {col['name'] for col in inspector.get_columns('users')}
            print(f"现有列: {sorted(existing_columns)}")
            
            # 检查phone列
            if 'phone' not in existing_columns:
                print("⚠️ phone列不存在，正在添加...")
                trans = conn.begin()
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)"))
                    trans.commit()
                    print("✅ phone列添加成功")
                except Exception as e:
                    trans.rollback()
                    if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                        print("ℹ️ phone列已存在")
                    else:
                        print(f"❌ 添加phone列失败: {e}")
                        raise
            else:
                print("✅ phone列已存在")
            
            # 验证修复
            inspector = inspect(engine)
            columns_after = {col['name'] for col in inspector.get_columns('users')}
            if 'phone' in columns_after:
                print("\n✅ 数据库修复完成，phone列已存在")
                print(f"最终列列表: {sorted(columns_after)}")
            else:
                print("\n⚠️ 警告：修复后phone列仍然不存在")
                
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n请手动执行以下SQL:")
        print("ALTER TABLE users ADD COLUMN phone VARCHAR(20);")

if __name__ == '__main__':
    fix_postgres_phone_column()




