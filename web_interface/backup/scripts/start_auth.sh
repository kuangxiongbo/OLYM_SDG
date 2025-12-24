#!/bin/bash

# SDG Web界面认证系统启动脚本
# =================================

echo "🚀 启动SDG Web界面认证系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "app.py" ]; then
    echo "❌ 错误: 请在web_interface目录下运行此脚本"
    exit 1
fi

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data

# 检查环境配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: 未找到.env配置文件"
    echo "📋 请复制env_auth_template为.env并配置邮箱设置:"
    echo "   cp env_auth_template .env"
    echo ""
    echo "📧 邮箱配置示例:"
    echo "   SMTP_SERVER=smtp.qq.com"
    echo "   SMTP_PORT=587"
    echo "   SMTP_USERNAME=your_email@qq.com"
    echo "   SMTP_PASSWORD=your_email_password"
    echo "   FROM_EMAIL=your_email@qq.com"
    echo "   FROM_NAME=SDG Web界面"
    echo "   APP_URL=http://localhost:5000"
    echo ""
    echo "🔧 如果不需要邮箱功能，可以直接启动应用（注册后需要手动验证）"
    echo ""
    read -p "是否继续启动应用？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 设置环境变量（如果.env文件存在）
if [ -f ".env" ]; then
    echo "📧 加载邮箱配置..."
    export $(grep -v '^#' .env | xargs)
fi

# 启动应用
echo "🌟 启动Flask应用..."
echo "📱 访问地址: http://localhost:5000"
echo "🔐 认证页面:"
echo "   - 注册: http://localhost:5000/auth/register"
echo "   - 登录: http://localhost:5000/auth/login"
echo ""
echo "💡 提示: 按Ctrl+C停止服务"
echo ""

python3 app.py

