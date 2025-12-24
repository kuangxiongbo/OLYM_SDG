# 修复数据库phone列问题

## 问题描述

错误信息显示：
```
(psycopg2.errors.UndefinedColumn) column users.phone does not exist
```

这表明PostgreSQL数据库中的`users`表缺少`phone`列。

## 解决方案

### 方案1: 使用修复脚本（推荐）

如果您的应用连接的是PostgreSQL数据库，运行以下命令：

```bash
cd web_interface
source venv/bin/activate
python3 fix_postgres_schema.py
```

### 方案2: 手动执行SQL

如果修复脚本无法运行，请手动连接到PostgreSQL数据库并执行：

```sql
-- 添加phone列
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- 如果还有其他缺失的列，也一并添加：
ALTER TABLE users ADD COLUMN name VARCHAR(100);
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL;
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'pending' NOT NULL;
ALTER TABLE users ADD COLUMN activation_code VARCHAR(100);
ALTER TABLE users ADD COLUMN activation_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;
```

### 方案3: 重新创建表结构

如果允许清空数据，可以删除表后重新创建：

```python
from app import create_app
from models.user import db

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    print("✅ 数据库表已重新创建")
```

**注意**: 这会删除所有现有数据！

## 检查当前数据库配置

运行以下命令检查当前使用的数据库：

```bash
cd web_interface
source venv/bin/activate
python3 -c "
from app import create_app
import os

app = create_app()
db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
print(f'当前数据库: {db_uri}')

env_db = os.environ.get('DATABASE_URL')
if env_db:
    print(f'环境变量DATABASE_URL: {env_db[:50]}...')
"
```

## 预防措施

为了避免类似问题，建议：

1. **使用数据库迁移工具**: 使用Flask-Migrate或Alembic管理数据库迁移
2. **统一数据库结构**: 确保开发、测试、生产环境的数据库结构一致
3. **版本控制**: 将数据库迁移脚本纳入版本控制

## 相关文件

- `fix_postgres_schema.py` - PostgreSQL数据库修复脚本
- `fix_database_schema.py` - 通用数据库修复脚本
- `models/user.py` - User模型定义






