#!/bin/bash

# SDG Web界面启动脚本（根目录版本）
# =====================================

echo "🚀 启动SDG Web界面..."
echo "========================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装，请先安装Python3"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -d "web_interface" ]; then
    echo "❌ 请在SDG项目根目录中运行此脚本"
    exit 1
fi

# 进入web_interface目录
cd web_interface

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
pip install -r requirements.txt

# 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p uploads results

# 设置环境变量
export FLASK_ENV=development
export FLASK_DEBUG=True

# 启动应用
echo "🌐 启动Web服务器..."
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务器"
echo "========================"

# 选择启动方式
echo "请选择启动方式:"
echo "1) 完整版 (需要SDG模块)"
echo "2) 简化版 (不依赖SDG模块)"
read -p "请输入选择 (1/2): " choice

case $choice in
    1)
        echo "启动完整版..."
        python app.py
        ;;
    2)
        echo "启动简化版..."
        python app_simple.py
        ;;
    *)
        echo "无效选择，启动简化版..."
        python app_simple.py
        ;;
esac
