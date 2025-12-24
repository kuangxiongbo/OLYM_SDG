#!/bin/bash
# 实时查看服务器日志

LOG_FILE="/Users/kuangxb/Desktop/AI 生成数据 SDG /web_interface/server.log"

if [ -f "$LOG_FILE" ]; then
    echo "正在实时查看服务器日志..."
    echo "按 Ctrl+C 停止"
    echo ""
    echo "=== 最近的日志（最后50行）==="
    tail -50 "$LOG_FILE"
    echo ""
    echo "=== 实时日志输出 ==="
    tail -f "$LOG_FILE"
else
    echo "日志文件不存在: $LOG_FILE"
    echo "请等待服务器启动..."
fi




