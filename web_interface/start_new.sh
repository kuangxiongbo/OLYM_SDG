#!/bin/bash

# SDG多账号控制系统启动脚本
# ==============================

echo "🚀 启动SDG多账号控制系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖包..."
pip install --upgrade pip
pip install flask flask-sqlalchemy flask-login flask-mail flask-cors
pip install pandas numpy scikit-learn
pip install python-dotenv

# 设置环境变量
export FLASK_ENV=development
export SECRET_KEY="sdg-web-interface-secret-key-2025"
export ADMIN_EMAIL="admin@sdg.com"
export ADMIN_PASSWORD="admin123"

# 创建必要的目录
mkdir -p instance
mkdir -p uploads
mkdir -p logs

# 启动应用
echo "🌟 启动应用..."
python app_new.py

