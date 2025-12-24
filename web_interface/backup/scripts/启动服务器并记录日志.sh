#!/bin/bash
# 启动服务器并记录日志到文件

cd "/Users/kuangxb/Desktop/AI 生成数据 SDG /web_interface"

# 停止现有服务器（如果存在）
pkill -f "python.*app\.py"

# 等待一下
sleep 2

# 启动服务器并记录日志
echo "正在启动服务器..."
echo "日志将保存到: server.log"
echo "实时查看日志: tail -f server.log"
echo ""

python3 app.py > server.log 2>&1 &

# 获取进程ID
SERVER_PID=$!
echo "服务器已启动，进程ID: $SERVER_PID"
echo ""
echo "查看日志: tail -f server.log"
echo "停止服务器: kill $SERVER_PID"
echo ""

# 等待一下，然后显示最后几行日志
sleep 2
echo "=== 最近的日志输出 ==="
tail -20 server.log




