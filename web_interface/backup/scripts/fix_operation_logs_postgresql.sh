#!/bin/bash
# 修复 PostgreSQL 数据库中 operation_logs 表的 user_id 列

# 从环境变量获取数据库URL
DATABASE_URL="${DATABASE_URL}"

if [ -z "$DATABASE_URL" ]; then
    echo "错误: 未设置 DATABASE_URL 环境变量"
    exit 1
fi

echo "使用数据库URL: ${DATABASE_URL:0:50}..."

# 使用 psql 连接数据库并执行修复
psql "$DATABASE_URL" <<EOF
-- 检查当前列状态
SELECT column_name, is_nullable, data_type 
FROM information_schema.columns 
WHERE table_name = 'operation_logs' AND column_name = 'user_id';

-- 修改列，允许 NULL
ALTER TABLE operation_logs 
ALTER COLUMN user_id DROP NOT NULL;

-- 检查外键约束
SELECT constraint_name, delete_rule
FROM information_schema.referential_constraints rc
JOIN information_schema.key_column_usage kcu
ON rc.constraint_name = kcu.constraint_name
WHERE kcu.table_name = 'operation_logs'
AND kcu.column_name = 'user_id'
AND kcu.referenced_table_name = 'users';

-- 如果外键约束存在且删除规则不是 SET NULL，需要删除并重建
DO \$\$
DECLARE
    fk_constraint_name TEXT;
    fk_delete_rule TEXT;
BEGIN
    SELECT rc.constraint_name, rc.delete_rule INTO fk_constraint_name, fk_delete_rule
    FROM information_schema.referential_constraints rc
    JOIN information_schema.key_column_usage kcu
    ON rc.constraint_name = kcu.constraint_name
    WHERE kcu.table_name = 'operation_logs'
    AND kcu.column_name = 'user_id'
    AND kcu.referenced_table_name = 'users'
    LIMIT 1;
    
    IF fk_constraint_name IS NOT NULL AND fk_delete_rule != 'SET NULL' THEN
        EXECUTE 'ALTER TABLE operation_logs DROP CONSTRAINT ' || fk_constraint_name;
        EXECUTE 'ALTER TABLE operation_logs ADD CONSTRAINT operation_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL';
        RAISE NOTICE '外键约束已更新为 SET NULL';
    END IF;
END
\$\$;

-- 验证修改结果
SELECT column_name, is_nullable, data_type 
FROM information_schema.columns 
WHERE table_name = 'operation_logs' AND column_name = 'user_id';

SELECT constraint_name, delete_rule
FROM information_schema.referential_constraints rc
JOIN information_schema.key_column_usage kcu
ON rc.constraint_name = kcu.constraint_name
WHERE kcu.table_name = 'operation_logs'
AND kcu.column_name = 'user_id'
AND kcu.referenced_table_name = 'users';

EOF

if [ $? -eq 0 ]; then
    echo "✅ 修复完成！"
else
    echo "❌ 修复失败！"
    exit 1
fi




