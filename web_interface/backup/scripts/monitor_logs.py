#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器日志监测脚本
实时监测服务器日志，特别关注日期列修复相关的信息
"""

import subprocess
import sys
import re
from datetime import datetime

# 关键词列表，用于高亮显示重要信息
KEYWORDS = {
    'error': ['❌', '错误', '失败', 'Error', 'Exception', 'Traceback', '失败'],
    'warning': ['⚠️', '警告', 'Warning', '修复'],
    'date_fix': ['日期列', 'date_col', '修复日期', 'fix_date', 'Step 6.5', '最终验证', '日期列样本值'],
    'step': ['Step 1', 'Step 2', 'Step 3', 'Step 4', 'Step 5', 'Step 6', 'Step 7', 'Step 8', 'Step 9'],
    'success': ['✅', '成功', '完成', 'Success']
}

def colorize_line(line):
    """根据关键词为日志行添加颜色"""
    # ANSI颜色代码
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    original_line = line
    
    # 检查错误关键词
    for keyword in KEYWORDS['error']:
        if keyword in line:
            return f"{RED}{BOLD}{line}{RESET}"
    
    # 检查警告关键词
    for keyword in KEYWORDS['warning']:
        if keyword in line:
            return f"{YELLOW}{line}{RESET}"
    
    # 检查日期修复关键词（高优先级）
    for keyword in KEYWORDS['date_fix']:
        if keyword in line:
            return f"{MAGENTA}{BOLD}{line}{RESET}"
    
    # 检查步骤关键词
    for keyword in KEYWORDS['step']:
        if keyword in line:
            return f"{CYAN}{line}{RESET}"
    
    # 检查成功关键词
    for keyword in KEYWORDS['success']:
        if keyword in line:
            return f"{GREEN}{line}{RESET}"
    
    return line

def monitor_process_logs(pid):
    """监测指定进程的日志输出"""
    print(f"\n{'='*80}")
    print(f"📊 开始监测进程 {pid} 的日志输出")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    print("💡 重点关注以下信息：")
    print("   - 🔴 错误信息（红色加粗）")
    print("   - 🟡 警告信息（黄色）")
    print("   - 🟣 日期列修复信息（紫色加粗）")
    print("   - 🔵 步骤信息（青色）")
    print("   - 🟢 成功信息（绿色）")
    print(f"\n{'='*80}\n")
    
    try:
        # 使用 log stream 命令监测进程日志（macOS）
        # 注意：这需要适当的权限
        cmd = f"log stream --predicate 'processIdentifier == {pid}' --level debug"
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            if line.strip():
                colored_line = colorize_line(line.strip())
                print(colored_line)
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        print("\n\n⚠️ 监测已停止")
    except Exception as e:
        print(f"\n❌ 监测失败: {e}")
        print("\n💡 提示：如果无法监测进程日志，请直接查看终端输出")

def monitor_stdout():
    """监测标准输出（如果服务器输出到stdout）"""
    print(f"\n{'='*80}")
    print(f"📊 开始监测标准输出")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    print("💡 请确保服务器输出到标准输出")
    print("💡 按 Ctrl+C 停止监测\n")
    print(f"{'='*80}\n")
    
    try:
        for line in sys.stdin:
            if line.strip():
                colored_line = colorize_line(line.strip())
                print(colored_line)
                sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n\n⚠️ 监测已停止")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # 如果提供了PID，监测该进程
        try:
            pid = int(sys.argv[1])
            monitor_process_logs(pid)
        except ValueError:
            print(f"❌ 无效的进程ID: {sys.argv[1]}")
            sys.exit(1)
    else:
        # 否则监测标准输入
        print("💡 使用方法：")
        print("   1. 监测进程: python3 monitor_logs.py <PID>")
        print("   2. 监测stdin: python3 monitor_logs.py < 日志文件")
        print("   3. 或者直接运行服务器: python3 app.py | python3 monitor_logs.py")
        print("\n📋 当前运行的服务器进程：")
        
        # 查找运行中的服务器进程
        try:
            result = subprocess.run(
                r"ps aux | grep -E 'python.*app\.py' | grep -v grep",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                print(result.stdout)
                print("\n💡 使用以下命令监测进程日志：")
                for line in result.stdout.strip().split('\n'):
                    if line:
                        pid = line.split()[1]
                        print(f"   python3 monitor_logs.py {pid}")
            else:
                print("   (未找到运行中的服务器进程)")
        except Exception as e:
            print(f"   (无法查找进程: {e})")
        
        print("\n💡 或者直接运行服务器并监测：")
        print("   python3 app.py 2>&1 | python3 monitor_logs.py")

