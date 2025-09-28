#!/bin/bash

echo "🚀 启动SDG多账号控制系统..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv venv
    source venv/bin/activate
    pip install flask flask-sqlalchemy flask-login flask-mail flask-cors pillow pandas
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 创建数据库表
echo "🗄️ 创建数据库表..."
python3 -c "
import sys
sys.path.append('.')
from app_complete import app, db
with app.app_context():
    db.create_all()
    print('数据库表创建完成')
"

# 启动服务
echo "🌟 启动服务..."
echo "📱 访问地址: http://localhost:5000"
echo "🔐 主要功能:"
echo "   - 注册: http://localhost:5000/auth/register"
echo "   - 登录: http://localhost:5000/auth/login"
echo "   - 管理后台: http://localhost:5000/admin"
echo ""
echo "💡 测试账号:"
echo "   - 管理员: admin@sdg.com / admin123"
echo ""
echo "💡 按Ctrl+C停止服务"
echo ""

python3 app_complete.py

