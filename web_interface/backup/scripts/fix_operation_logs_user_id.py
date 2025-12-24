#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 operation_logs 表的 user_id 列，使其允许 NULL
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.log import db

def fix_operation_logs_user_id():
    """修复 operation_logs 表的 user_id 列，使其允许 NULL"""
    import os
    
    # 检查环境变量中的数据库URL
    db_url_env = os.environ.get('DATABASE_URL', '')
    if db_url_env:
        print(f"从环境变量获取数据库URL: {db_url_env[:50]}...")
        # 如果环境变量存在，优先使用环境变量
        os.environ['SQLALCHEMY_DATABASE_URI'] = db_url_env
    
    app = create_app()
    
    with app.app_context():
        try:
            # 检查数据库类型
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            print(f"实际使用的数据库URL: {db_url[:80]}...")
            
            if 'postgresql' in db_url.lower() or 'postgres' in db_url.lower():
                # PostgreSQL
                print("检测到 PostgreSQL 数据库")
                
                # 检查当前列定义
                result = db.session.execute(db.text("""
                    SELECT column_name, is_nullable, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'operation_logs' AND column_name = 'user_id'
                """))
                
                row = result.fetchone()
                if row:
                    column_name, is_nullable, data_type = row
                    print(f"当前 user_id 列状态: nullable={is_nullable}, type={data_type}")
                    
                    if is_nullable == 'NO':
                        print("正在修改 user_id 列为允许 NULL...")
                        
                        # 修改列，允许 NULL
                        db.session.execute(db.text("""
                            ALTER TABLE operation_logs 
                            ALTER COLUMN user_id DROP NOT NULL
                        """))
                        
                        # 检查并更新外键约束的删除行为
                        print("检查外键约束...")
                        fk_check = db.session.execute(db.text("""
                            SELECT constraint_name, delete_rule
                            FROM information_schema.referential_constraints rc
                            JOIN information_schema.key_column_usage kcu
                            ON rc.constraint_name = kcu.constraint_name
                            WHERE kcu.table_name = 'operation_logs'
                            AND kcu.column_name = 'user_id'
                            AND kcu.referenced_table_name = 'users'
                        """))
                        
                        fk_row = fk_check.fetchone()
                        if fk_row:
                            constraint_name, delete_rule = fk_row
                            print(f"当前外键约束: {constraint_name}, 删除规则: {delete_rule}")
                            
                            if delete_rule != 'SET NULL':
                                print(f"正在修改外键约束删除规则为 SET NULL...")
                                # 删除旧的外键约束
                                db.session.execute(db.text(f"""
                                    ALTER TABLE operation_logs 
                                    DROP CONSTRAINT {constraint_name}
                                """))
                                # 创建新的外键约束，使用 SET NULL
                                db.session.execute(db.text("""
                                    ALTER TABLE operation_logs 
                                    ADD CONSTRAINT operation_logs_user_id_fkey 
                                    FOREIGN KEY (user_id) 
                                    REFERENCES users(id) 
                                    ON DELETE SET NULL
                                """))
                                print("✅ 外键约束已更新为 SET NULL")
                        
                        db.session.commit()
                        print("✅ user_id 列已修改为允许 NULL")
                    else:
                        print("✅ user_id 列已经允许 NULL，无需修改")
                else:
                    print("⚠️ 未找到 user_id 列")
                    
                # 检查外键约束，确保 ondelete 行为正确
                print("\n检查外键约束...")
                fk_result = db.session.execute(db.text("""
                    SELECT
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name,
                        rc.delete_rule
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                    JOIN information_schema.referential_constraints AS rc
                      ON rc.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                      AND tc.table_name = 'operation_logs'
                      AND kcu.column_name = 'user_id'
                """))
                
                fk_row = fk_result.fetchone()
                if fk_row:
                    constraint_name, col_name, foreign_table, foreign_col, delete_rule = fk_row
                    print(f"外键约束: {constraint_name}")
                    print(f"  列: {col_name}")
                    print(f"  引用: {foreign_table}.{foreign_col}")
                    print(f"  删除规则: {delete_rule}")
                    
                    # 如果删除规则不是 SET NULL 或 RESTRICT，可能需要修改
                    if delete_rule not in ['SET NULL', 'RESTRICT', 'NO ACTION']:
                        print(f"⚠️ 建议将删除规则改为 SET NULL 或 RESTRICT")
                else:
                    print("⚠️ 未找到外键约束")
                    
            elif 'sqlite' in db_url.lower():
                # SQLite - 需要重建表
                print("检测到 SQLite 数据库")
                print("⚠️ SQLite 不支持直接修改列，需要重建表")
                print("建议：SQLite 数据库应该已经支持 NULL（模型定义中已设置 nullable=True）")
                
            else:
                print(f"⚠️ 未识别的数据库类型: {db_url}")
                
        except Exception as e:
            print(f"❌ 修复失败: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("修复 operation_logs 表的 user_id 列")
    print("=" * 60)
    
    if fix_operation_logs_user_id():
        print("\n✅ 修复完成！")
    else:
        print("\n❌ 修复失败！")
        sys.exit(1)

