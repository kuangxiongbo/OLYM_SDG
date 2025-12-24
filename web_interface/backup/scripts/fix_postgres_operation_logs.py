#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 PostgreSQL 数据库中 operation_logs 表的 user_id 列
专门用于远程 PostgreSQL 数据库
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_postgres_operation_logs():
    """修复 PostgreSQL 数据库中 operation_logs 表的 user_id 列"""
    
    # 获取数据库连接信息
    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        print("错误: 未设置 DATABASE_URL 环境变量")
        print("请设置环境变量，例如:")
        print("  export DATABASE_URL='postgresql://user:password@host:port/database'")
        return False
    
    # 检查是否是 PostgreSQL
    if 'postgresql' not in db_url.lower() and 'postgres' not in db_url.lower():
        print(f"警告: 数据库URL不是 PostgreSQL: {db_url[:50]}...")
        response = input("是否继续? (y/n): ")
        if response.lower() != 'y':
            return False
    
    print("=" * 60)
    print("修复 PostgreSQL operation_logs 表")
    print("=" * 60)
    print(f"数据库URL: {db_url[:50]}...")
    print()
    
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError
        
        # 创建数据库连接
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 1. 检查当前列状态
                print("1. 检查当前列状态...")
                result = conn.execute(text("""
                    SELECT column_name, is_nullable, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'operation_logs' AND column_name = 'user_id'
                """))
                
                row = result.fetchone()
                if not row:
                    print("❌ 未找到 operation_logs.user_id 列")
                    trans.rollback()
                    return False
                
                column_name, is_nullable, data_type = row
                print(f"   当前状态: nullable={is_nullable}, type={data_type}")
                
                # 2. 修改列，允许 NULL
                if is_nullable == 'NO':
                    print("\n2. 修改 user_id 列为允许 NULL...")
                    conn.execute(text("""
                        ALTER TABLE operation_logs 
                        ALTER COLUMN user_id DROP NOT NULL
                    """))
                    print("   ✅ 列已修改为允许 NULL")
                else:
                    print("\n2. user_id 列已经允许 NULL，跳过")
                
                # 3. 检查并更新外键约束
                print("\n3. 检查外键约束...")
                fk_result = conn.execute(text("""
                    SELECT rc.constraint_name, rc.delete_rule
                    FROM information_schema.referential_constraints rc
                    JOIN information_schema.key_column_usage kcu
                    ON rc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                    ON rc.constraint_name = ccu.constraint_name
                    WHERE kcu.table_name = 'operation_logs'
                    AND kcu.column_name = 'user_id'
                    AND ccu.table_name = 'users'
                """))
                
                fk_row = fk_result.fetchone()
                if fk_row:
                    constraint_name, delete_rule = fk_row
                    print(f"   当前外键约束: {constraint_name}, 删除规则: {delete_rule}")
                    
                    if delete_rule != 'SET NULL':
                        print(f"\n4. 更新外键约束删除规则为 SET NULL...")
                        # 删除旧的外键约束
                        conn.execute(text(f"""
                            ALTER TABLE operation_logs 
                            DROP CONSTRAINT {constraint_name}
                        """))
                        print(f"   ✅ 已删除旧约束: {constraint_name}")
                        
                        # 创建新的外键约束
                        conn.execute(text("""
                            ALTER TABLE operation_logs 
                            ADD CONSTRAINT operation_logs_user_id_fkey 
                            FOREIGN KEY (user_id) 
                            REFERENCES users(id) 
                            ON DELETE SET NULL
                        """))
                        print("   ✅ 已创建新约束，删除规则: SET NULL")
                    else:
                        print("\n4. 外键约束删除规则已经是 SET NULL，跳过")
                else:
                    print("   ⚠️ 未找到外键约束，将创建新的约束...")
                    conn.execute(text("""
                        ALTER TABLE operation_logs 
                        ADD CONSTRAINT operation_logs_user_id_fkey 
                        FOREIGN KEY (user_id) 
                        REFERENCES users(id) 
                        ON DELETE SET NULL
                    """))
                    print("   ✅ 已创建新约束")
                
                # 提交事务
                trans.commit()
                print("\n✅ 修复完成！")
                
                # 验证修改结果
                print("\n5. 验证修改结果...")
                verify_result = conn.execute(text("""
                    SELECT column_name, is_nullable, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'operation_logs' AND column_name = 'user_id'
                """))
                verify_row = verify_result.fetchone()
                if verify_row:
                    print(f"   user_id 列: nullable={verify_row[1]}, type={verify_row[2]}")
                
                verify_fk = conn.execute(text("""
                    SELECT rc.constraint_name, rc.delete_rule
                    FROM information_schema.referential_constraints rc
                    JOIN information_schema.key_column_usage kcu
                    ON rc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                    ON rc.constraint_name = ccu.constraint_name
                    WHERE kcu.table_name = 'operation_logs'
                    AND kcu.column_name = 'user_id'
                    AND ccu.table_name = 'users'
                """))
                verify_fk_row = verify_fk.fetchone()
                if verify_fk_row:
                    print(f"   外键约束: {verify_fk_row[0]}, 删除规则: {verify_fk_row[1]}")
                
                return True
                
            except SQLAlchemyError as e:
                trans.rollback()
                print(f"\n❌ 修复失败: {e}")
                import traceback
                traceback.print_exc()
                return False
                
    except ImportError:
        print("❌ 错误: 未安装 sqlalchemy 或 psycopg2")
        print("请运行: pip install sqlalchemy psycopg2-binary")
        return False
    except Exception as e:
        print(f"\n❌ 连接数据库失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_postgres_operation_logs()
    sys.exit(0 if success else 1)

