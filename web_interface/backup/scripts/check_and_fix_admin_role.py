#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查并修复admin用户的角色
确保admin用户是管理员而不是普通用户
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect, text

# 从运行中的应用获取的数据库连接
DATABASE_URL = "postgresql+psycopg2://SDC:nScWntDCaEajtJmD@192.168.210.90:5433/SDC"

def check_and_fix_admin_role():
    """检查并修复admin用户的角色"""
    print(f"连接到PostgreSQL数据库: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'PostgreSQL'}")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.begin() as conn:
            # 检查users表结构
            inspector = inspect(engine)
            if not inspector.has_table('users'):
                print("❌ users表不存在")
                return
            
            # 获取现有列
            existing_columns = {col['name'] for col in inspector.get_columns('users')}
            print(f"现有列: {sorted(existing_columns)}")
            
            # 检查role列是否存在
            if 'role' not in existing_columns:
                print("⚠️ role列不存在，正在添加...")
                trans = conn.begin()
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL"))
                    trans.commit()
                    print("✅ role列添加成功")
                except Exception as e:
                    trans.rollback()
                    print(f"❌ 添加role列失败: {e}")
                    return
            
            # 查询admin用户
            print("\n查询admin用户信息...")
            result = conn.execute(text("""
                SELECT id, email, username, name, role, status 
                FROM users 
                WHERE email = 'admin@sdg.com' OR username = 'admin' OR email LIKE '%admin%'
            """))
            
            users = result.fetchall()
            
            if not users:
                print("⚠️ 未找到admin用户")
                print("查询所有用户...")
                result = conn.execute(text("SELECT id, email, username, name, role, status FROM users LIMIT 10"))
                all_users = result.fetchall()
                if all_users:
                    print("\n当前用户列表:")
                    for user in all_users:
                        print(f"  ID: {user[0]}, Email: {user[1]}, Username: {user[2]}, Name: {user[3]}, Role: {user[4]}, Status: {user[5]}")
                return
            
            print(f"\n找到 {len(users)} 个admin相关用户:")
            users_to_fix = []
            for user in users:
                user_id, email, username, name, role, status = user
                print(f"  ID: {user_id}, Email: {email}, Username: {username}, Name: {name}, Role: {role}, Status: {status}")
                
                # 检查并记录需要修复的用户
                if role != 'admin':
                    print(f"  ⚠️ 用户 {email} 的角色是 '{role}'，应该是 'admin'")
                    users_to_fix.append(user_id)
                else:
                    print(f"  ✅ 用户 {email} 的角色已经是 'admin'")
            
            # 批量修复角色
            if users_to_fix:
                print(f"\n🔧 正在更新 {len(users_to_fix)} 个用户的角色为 'admin'...")
                for user_id in users_to_fix:
                    conn.execute(text("""
                        UPDATE users 
                        SET role = 'admin' 
                        WHERE id = :user_id
                    """), {"user_id": user_id})
                print(f"✅ 所有admin用户的角色已更新为 'admin'")
            
            # 验证修复结果
            print("\n验证修复结果...")
            result = conn.execute(text("""
                SELECT id, email, username, name, role, status 
                FROM users 
                WHERE email = 'admin@sdg.com' OR username = 'admin' OR email LIKE '%admin%'
            """))
            
            users_after = result.fetchall()
            print("\n修复后的用户信息:")
            for user in users_after:
                user_id, email, username, name, role, status = user
                print(f"  ID: {user_id}, Email: {email}, Username: {username}, Name: {name}, Role: {role}, Status: {status}")
                if role == 'admin':
                    print(f"  ✅ {email} 是管理员")
                else:
                    print(f"  ⚠️ {email} 不是管理员 (role: {role})")
                
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_and_fix_admin_role()

