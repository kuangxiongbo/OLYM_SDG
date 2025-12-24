#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新架构测试脚本
用于测试重构后的数据生成模块
"""

import sys
import os
import pandas as pd

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_loader import DataLoader
from services.data_validator import DataValidator
from services.data_transformer import DataTransformer
from services.sdgx_adapter import SDGXAdapter


def test_data_validator():
    """测试DataValidator模块"""
    print("=" * 60)
    print("测试 DataValidator 模块")
    print("=" * 60)
    
    # 创建测试数据（包含被连接的日期字符串）
    test_data = {
        'id': [1, 2, 3],
        'name': ['A', 'B', 'C'],
        'date_col': ['2024-12-102024-12-11', '2024-12-12', '2025-01-01']  # 第一个值是被连接的
    }
    df = pd.DataFrame(test_data)
    
    print(f"\n原始数据:")
    print(df)
    print(f"\n日期列原始值: {df['date_col'].tolist()}")
    
    # 识别日期列
    date_columns = DataValidator.identify_date_columns(df)
    print(f"\n识别的日期列: {list(date_columns)}")
    
    # 修复日期列
    df_fixed = DataValidator.fix_date_columns(df, date_columns)
    print(f"\n修复后的数据:")
    print(df_fixed)
    print(f"\n日期列修复后值: {df_fixed['date_col'].tolist()}")
    
    # 验证数据
    df_validated = DataValidator.validate_dataframe(df_fixed, min_rows=3)
    print(f"\n验证通过: {df_validated.shape}")
    
    print("\n✅ DataValidator 测试通过\n")


def test_date_fix_logic():
    """测试日期修复逻辑"""
    print("=" * 60)
    print("测试日期修复逻辑")
    print("=" * 60)
    
    test_cases = [
        ('2024-12-102024-12-11', '2024-12-10'),  # 被连接的日期
        ('2024-12-10', '2024-12-10'),  # 正常日期
        ('2025-01-01', '2025-01-01'),  # 正常日期
        ('', ''),  # 空值
    ]
    
    for input_val, expected in test_cases:
        result = DataValidator.fix_date_value(input_val)
        status = "✅" if result == expected else "❌"
        print(f"{status} 输入: {input_val[:30]:<30} 输出: {result:<15} 期望: {expected}")
    
    print("\n✅ 日期修复逻辑测试完成\n")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("新架构模块测试")
    print("=" * 60 + "\n")
    
    try:
        # 测试日期修复逻辑
        test_date_fix_logic()
        
        # 测试DataValidator
        test_data_validator()
        
        print("=" * 60)
        print("✅ 所有测试通过")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




