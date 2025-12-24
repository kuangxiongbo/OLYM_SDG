#!/bin/bash
# 启动服务器并记录日志

cd "/Users/kuangxb/Desktop/AI 生成数据 SDG /web_interface"

# 停止现有服务器（如果存在）
echo "检查并停止现有服务器进程..."
pkill -f "python.*start\.py" 2>/dev/null
pkill -f "python.*app\.py" 2>/dev/null
sleep 1

# 激活虚拟环境并启动服务器
echo "正在启动服务器..."
echo "日志将保存到: server.log"
echo "实时查看日志: tail -f server.log 或运行 ./查看日志.sh"
echo ""

# 使用虚拟环境的Python启动服务器
if [ -d "venv" ]; then
    source venv/bin/activate
fi
python start.py > server.log 2>&1 &

# 获取进程ID
SERVER_PID=$!
echo "服务器已启动，进程ID: $SERVER_PID"
echo ""
echo "访问地址: http://localhost:5000"
echo "登录页面: http://localhost:5000/api/auth/login"
echo ""
echo "查看日志: tail -f server.log 或运行 ./查看日志.sh"
echo "停止服务器: kill $SERVER_PID"
echo ""

# 等待一下，然后显示最后几行日志
sleep 3
echo "=== 最近的日志输出 ==="
tail -30 server.log




