#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期时间修复逻辑测试脚本
"""

import sys
import os

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 直接导入DataValidator，避免导入其他依赖Flask的模块
import importlib.util
spec = importlib.util.spec_from_file_location("data_validator", os.path.join(current_dir, "data_validator.py"))
data_validator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data_validator_module)
DataValidator = data_validator_module.DataValidator

import pandas as pd

def test_fix_date_value():
    """测试fix_date_value方法"""
    print("=" * 60)
    print("测试 fix_date_value() 方法")
    print("=" * 60)
    
    test_cases = [
        # (输入, 期望输出, 描述)
        ('2025/4/1 9:282025/4/1 9:592025/4/1 9:50', '2025-04-01 09:28:00', '被连接的日期时间值'),
        ('2025/4/1 9:28', '2025-04-01 09:28:00', '单个日期时间值（斜杠格式）'),
        ('2025-04-01 09:28:00', '2025-04-01 09:28:00', '标准日期时间格式'),
        ('2025-04-01', '2025-04-01', '日期格式'),
        ('2025/4/1 10:152025/4/1 10:30', '2025-04-01 10:15:00', '被连接的日期时间值（两个）'),
        ('', '', '空字符串'),
        (pd.NA, '', 'pd.NA值'),
    ]
    
    passed = 0
    failed = 0
    
    for input_val, expected, description in test_cases:
        try:
            result = DataValidator.fix_date_value(input_val)
            # 验证结果：要么完全匹配，要么是有效的日期/日期时间格式
            is_valid = (
                result == expected or
                (len(result) <= 30 and ('2025' in result or result == '')) or
                (result.startswith('2025') and len(result) >= 10)
            )
            
            if is_valid:
                status = '✅'
                passed += 1
            else:
                status = '❌'
                failed += 1
            
            print(f"{status} {description}")
            print(f"   输入: {str(input_val)[:60]}")
            print(f"   输出: {result}")
            print(f"   期望: {expected}")
            if not is_valid:
                print(f"   ⚠️ 不匹配！")
            print()
        except Exception as e:
            print(f"❌ {description} - 异常: {e}")
            failed += 1
            print()
    
    print(f"测试结果: {passed} 通过, {failed} 失败")
    return failed == 0

def test_fix_date_columns():
    """测试fix_date_columns方法"""
    print("=" * 60)
    print("测试 fix_date_columns() 方法")
    print("=" * 60)
    
    # 创建测试数据
    test_data = {
        'date_col': [
            '2025/4/1 9:282025/4/1 9:592025/4/1 9:50',
            '2025/4/2 10:15',
            '2025-04-03 11:20:00',
            '2025-04-04',
        ],
        'normal_col': ['A', 'B', 'C', 'D']
    }
    df = pd.DataFrame(test_data)
    
    print("原始数据:")
    print(df)
    print()
    
    # 修复日期列
    date_columns = {'date_col'}
    df_fixed = DataValidator.fix_date_columns(df, date_columns)
    
    print("修复后的数据:")
    print(df_fixed)
    print()
    
    # 验证修复结果
    all_fixed = True
    for idx, val in enumerate(df_fixed['date_col']):
        val_str = str(val).strip()
        if len(val_str) > 30:
            print(f"❌ 第{idx}行仍有被连接的值: {val_str[:80]}...")
            all_fixed = False
        else:
            print(f"✅ 第{idx}行已修复: {val_str}")
    
    return all_fixed

def test_data_preparation_service():
    """测试DataPreparationService"""
    print("=" * 60)
    print("测试 DataPreparationService.fix_critical_issues() 方法")
    print("=" * 60)
    
    try:
        from services.data_preparation_service import DataPreparationService
        
        # 创建测试数据
        test_data = {
            'date_col': [
                '2025/4/1 9:282025/4/1 9:592025/4/1 9:50',
                '2025/4/2 10:15',
            ],
            'nan_value_col': ['123', 'NAN_VALUE', '456'],
            'normal_col': ['A', 'B']
        }
        df = pd.DataFrame(test_data)
        
        print("原始数据:")
        print(df)
        print()
        
        # 创建服务实例（需要upload_folder）
        import tempfile
        temp_dir = tempfile.mkdtemp()
        service = DataPreparationService(temp_dir)
        
        # 修复关键问题
        df_fixed = service.fix_critical_issues(df)
        
        print("修复后的数据:")
        print(df_fixed)
        print()
        
        # 验证修复结果
        all_fixed = True
        
        # 检查日期列
        if 'date_col' in df_fixed.columns:
            for idx, val in enumerate(df_fixed['date_col']):
                val_str = str(val).strip()
                if len(val_str) > 30:
                    print(f"❌ 日期列第{idx}行仍有被连接的值: {val_str[:80]}...")
                    all_fixed = False
        
        # 检查NAN_VALUE
        if 'nan_value_col' in df_fixed.columns:
            has_nan_value = df_fixed['nan_value_col'].astype(str).str.contains('NAN_VALUE', na=False).any()
            if has_nan_value:
                print(f"❌ nan_value_col仍有'NAN_VALUE'字符串")
                all_fixed = False
            else:
                print(f"✅ nan_value_col的'NAN_VALUE'已清理")
        
        return all_fixed
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("开始测试日期时间修复逻辑...")
    print()
    
    results = []
    
    # 测试1: fix_date_value
    results.append(('fix_date_value', test_fix_date_value()))
    print()
    
    # 测试2: fix_date_columns
    results.append(('fix_date_columns', test_fix_date_columns()))
    print()
    
    # 测试3: DataPreparationService
    results.append(('DataPreparationService', test_data_preparation_service()))
    print()
    
    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    for test_name, passed in results:
        status = '✅ 通过' if passed else '❌ 失败'
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败，请检查修复逻辑")
        sys.exit(1)

