#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试脚本
测试完整的数据生成流程（模拟真实场景）
"""

import sys
import os
import pandas as pd

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_loader import DataLoader
from services.data_validator import DataValidator
from services.data_transformer import DataTransformer


def test_complete_workflow():
    """测试完整的数据处理流程"""
    print("=" * 60)
    print("集成测试：完整数据处理流程")
    print("=" * 60)
    
    # 模拟问题场景：包含被连接的日期字符串的数据
    print("\n[测试场景] 模拟包含被连接日期字符串的数据")
    problem_data = {
        'id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'name': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
        'date_col': [
            '2024-12-102024-12-11',  # 被连接的日期
            '2024-12-12',
            '2025-01-01',
            '2025-01-02',
            '2025-01-03',
            '2024-12-102024-12-11',  # 另一个被连接的日期
            '2025-01-05',
            '2025-01-06',
            '2025-01-07',
            '2025-01-08'
        ],
        'value': [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    }
    
    df_original = pd.DataFrame(problem_data)
    print(f"\n原始数据形状: {df_original.shape}")
    print(f"日期列原始值（前5个）: {df_original['date_col'].head(5).tolist()}")
    
    # Step 1: 识别日期列
    print("\n[Step 1] 识别日期列...")
    date_columns = DataValidator.identify_date_columns(df_original)
    print(f"识别的日期列: {list(date_columns)}")
    
    # Step 2: 清理数据
    print("\n[Step 2] 清理数据...")
    transformer = DataTransformer()
    cleaned_df = transformer.clean_data(df_original, date_columns)
    print(f"清理完成")
    
    # Step 3: 修复日期列
    print("\n[Step 3] 修复日期列...")
    fixed_df = DataValidator.fix_date_columns(cleaned_df, date_columns)
    print(f"修复后的日期列值（前5个）: {fixed_df['date_col'].head(5).tolist()}")
    
    # 验证修复结果
    print("\n[验证] 检查修复结果...")
    all_fixed = True
    for idx, val in enumerate(fixed_df['date_col']):
        val_str = str(val)
        if len(val_str) > 10:
            print(f"❌ 第{idx}行仍有问题: {val_str[:50]}...")
            all_fixed = False
        elif len(val_str) > 0 and not val_str.startswith('202'):
            print(f"⚠️ 第{idx}行格式异常: {val_str}")
    
    if all_fixed:
        print("✅ 所有日期值都已修复为正确的格式（10个字符）")
    
    # Step 4: 验证数据完整性
    print("\n[Step 4] 验证数据完整性...")
    validated_df = DataValidator.validate_dataframe(fixed_df, min_rows=10)
    print(f"验证通过: {validated_df.shape}")
    
    # Step 5: 转换为SDGX格式
    print("\n[Step 5] 转换为SDGX格式...")
    df_for_sdgx = transformer.prepare_for_sdgx(validated_df, date_columns)
    print(f"转换完成")
    print(f"最终数据类型: {df_for_sdgx.dtypes.to_dict()}")
    
    # 最终验证
    print("\n[最终验证] 检查传递给SDGX的数据...")
    print(f"数据形状: {df_for_sdgx.shape}")
    print(f"日期列类型: {df_for_sdgx['date_col'].dtype}")
    print(f"日期列样本值: {df_for_sdgx['date_col'].head(5).tolist()}")
    
    # 检查是否还有被连接的日期
    has_concatenated = False
    for val in df_for_sdgx['date_col']:
        val_str = str(val)
        if len(val_str) > 20:
            date_count = val_str.count('2024') + val_str.count('2025')
            if date_count > 1:
                has_concatenated = True
                print(f"❌ 发现被连接的日期: {val_str[:50]}...")
    
    if not has_concatenated:
        print("✅ 所有日期值都是独立的字符串，可以安全传递给SDGX")
    else:
        print("❌ 仍有被连接的日期字符串，需要进一步修复")
    
    print("\n" + "=" * 60)
    if all_fixed and not has_concatenated:
        print("✅ 集成测试通过：数据已正确修复，可以传递给SDGX")
    else:
        print("❌ 集成测试失败：数据仍有问题")
    print("=" * 60)
    
    return all_fixed and not has_concatenated


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("新架构集成测试")
    print("=" * 60 + "\n")
    
    try:
        success = test_complete_workflow()
        if success:
            print("\n✅ 所有测试通过，新架构可以投入使用")
            sys.exit(0)
        else:
            print("\n❌ 测试失败，需要进一步修复")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




