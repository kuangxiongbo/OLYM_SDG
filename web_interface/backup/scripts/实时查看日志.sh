#!/bin/bash
# 实时查看服务器日志

LOG_FILE="/Users/kuangxb/Desktop/AI 生成数据 SDG /web_interface/server.log"

if [ -f "$LOG_FILE" ]; then
    echo "正在实时查看服务器日志..."
    echo "按 Ctrl+C 停止"
    echo ""
    tail -f "$LOG_FILE"
else
    echo "日志文件不存在: $LOG_FILE"
    echo "请先运行: ./启动服务器并记录日志.sh"
fi




