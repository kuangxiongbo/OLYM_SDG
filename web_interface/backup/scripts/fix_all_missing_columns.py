#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复PostgreSQL数据库所有缺失的列
根据模型定义添加所有必需的列
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect, text

# 从运行中的应用获取的数据库连接
DATABASE_URL = "postgresql+psycopg2://SDC:nScWntDCaEajtJmD@192.168.210.90:5433/SDC"

def fix_all_missing_columns():
    """修复所有缺失的列"""
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
            
            # 模型定义需要的所有列
            required_columns = {
                'name': 'VARCHAR(100)',
                'activation_code': 'VARCHAR(100)',
                'activation_expires_at': 'TIMESTAMP',
                'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'last_login_at': 'TIMESTAMP'
            }
            
            # 添加缺失的列（每个列单独处理，避免事务回滚影响其他列）
            for col_name, col_type in required_columns.items():
                if col_name not in existing_columns:
                    print(f"⚠️ {col_name}列不存在，正在添加...")
                    trans = conn.begin()
                    try:
                        sql = text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                        conn.execute(sql)
                        trans.commit()
                        print(f"✅ {col_name}列添加成功")
                        existing_columns.add(col_name)  # 更新现有列列表
                    except Exception as e:
                        trans.rollback()
                        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                            print(f"ℹ️ {col_name}列已存在")
                            existing_columns.add(col_name)
                        else:
                            print(f"❌ 添加{col_name}列失败: {e}")
                else:
                    print(f"ℹ️ {col_name}列已存在")
            
            # 如果存在last_login但没有last_login_at，添加last_login_at
            if 'last_login' in existing_columns and 'last_login_at' not in existing_columns:
                print("⚠️ 发现last_login列，但需要last_login_at列")
                print("   添加last_login_at列...")
                trans = conn.begin()
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP"))
                    trans.commit()
                    print("✅ last_login_at列添加成功")
                    existing_columns.add('last_login_at')
                except Exception as e:
                    trans.rollback()
                    if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                        print("ℹ️ last_login_at列已存在")
                        existing_columns.add('last_login_at')
                    else:
                        print(f"❌ 添加last_login_at列失败: {e}")
            
            print("\n✅ 所有列修复完成")
            
            # 验证修复
            inspector = inspect(engine)
            columns_after = {col['name'] for col in inspector.get_columns('users')}
            print(f"\n最终列列表: {sorted(columns_after)}")
            
            # 检查是否所有必需的列都存在
            missing = set(required_columns.keys()) - columns_after
            if 'last_login_at' not in columns_after and 'last_login' not in columns_after:
                missing.add('last_login_at')
            
            if missing:
                print(f"\n⚠️ 仍然缺失的列: {missing}")
            else:
                print("\n✅ 所有必需的列都已存在")
                
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n请手动执行以下SQL:")
        print("ALTER TABLE users ADD COLUMN name VARCHAR(100);")
        print("ALTER TABLE users ADD COLUMN activation_code VARCHAR(100);")
        print("ALTER TABLE users ADD COLUMN activation_expires_at TIMESTAMP;")
        print("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
        print("ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;")

if __name__ == '__main__':
    fix_all_missing_columns()

