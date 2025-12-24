#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断日期字符串连接问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("日期字符串连接问题诊断")
print("=" * 80)
print()

# 测试1: 检查日期列表生成
print("[测试1] 检查日期列表生成...")
from datetime import datetime, timedelta

dates = []
start_date = datetime.now() - timedelta(days=365)
for i in range(100):
    date_obj = start_date + timedelta(days=i)
    dates.append(date_obj.strftime('%Y-%m-%d'))

print(f"生成的日期列表: 长度={len(dates)}, 类型={type(dates)}")
print(f"前5个日期: {dates[:5]}")
print(f"每个元素的类型: {[type(d) for d in dates[:5]]}")
print()

# 测试2: 检查如果日期列表被错误地转换为字符串
print("[测试2] 检查日期列表被错误转换为字符串的情况...")
dates_str = ''.join(dates)  # 错误地连接
print(f"错误连接的日期字符串长度: {len(dates_str)}")
print(f"前100个字符: {dates_str[:100]}")
print(f"是否包含多个日期: {dates_str.count('2024-12-10') > 1}")
print()

# 测试3: 检查DataFrame创建
print("[测试3] 检查DataFrame创建...")
try:
    import pandas as pd
    
    # 正常情况：日期列表
    data_normal = {
        'id': list(range(10)),
        'call_time': dates[:10]
    }
    df_normal = pd.DataFrame(data_normal)
    print(f"正常DataFrame - call_time列类型: {df_normal['call_time'].dtype}")
    print(f"正常DataFrame - call_time列值（前3个）: {df_normal['call_time'].head(3).tolist()}")
    print()
    
    # 错误情况：日期字符串被连接
    data_error = {
        'id': [1],
        'call_time': [dates_str]  # 整个列表被连接成一个字符串
    }
    df_error = pd.DataFrame(data_error)
    print(f"错误DataFrame - call_time列类型: {df_error['call_time'].dtype}")
    print(f"错误DataFrame - call_time列值: {df_error['call_time'].tolist()}")
    print(f"错误DataFrame - call_time列第一个值的长度: {len(str(df_error['call_time'].iloc[0]))}")
    print()
    
except ImportError:
    print("⚠️ pandas未安装，跳过DataFrame测试")
    print()

# 测试4: 检查修复逻辑
print("[测试4] 检查日期修复逻辑...")
import re

date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
dates_found = date_pattern.findall(dates_str)
print(f"从连接字符串中提取的日期数量: {len(dates_found)}")
print(f"前5个提取的日期: {dates_found[:5]}")
print()

print("=" * 80)
print("诊断建议:")
print("1. 如果日期列表被错误地转换为字符串，应该在以下位置修复：")
print("   - _load_template_data 中日期生成后")
print("   - prepare_for_sdgx 中转换前")
print("   - Step 6.5 最终验证时")
print("2. 检查服务器日志，查看日期列在哪个步骤被错误处理")
print("3. 确保所有日期列的值都是独立的字符串，不是连接在一起的")
print("=" * 80)




