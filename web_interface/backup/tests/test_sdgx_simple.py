#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的SDGX测试脚本
使用最基本的数据测试SDGX是否正常运行
"""

import sys
import os
import pandas as pd

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import Config

# 添加SDGX路径
sys.path.append(Config.SDGX_PATH)

try:
    from sdgx.data_connectors.dataframe_connector import DataFrameConnector
    from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
    from sdgx.synthesizer import Synthesizer
    print("✅ SDGX组件导入成功")
except ImportError as e:
    print(f"❌ SDGX组件导入失败: {e}")
    sys.exit(1)

def test_sdgx_simple():
    """使用最简单的数据测试SDGX"""
    print("\n" + "="*60)
    print("开始简单SDGX测试")
    print("="*60)
    
    # 创建最简单的测试数据：只有数值列，没有日期列
    print("\n[Step 1] 创建测试数据...")
    test_data = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'value1': [10, 20, 30, 40, 50],
        'value2': [100, 200, 300, 400, 500],
        'category': ['A', 'B', 'A', 'B', 'A']
    })
    print(f"测试数据:\n{test_data}")
    print(f"数据类型:\n{test_data.dtypes}")
    
    # 创建DataFrameConnector
    print("\n[Step 2] 创建DataFrameConnector...")
    try:
        data_connector = DataFrameConnector(df=test_data)
        print("✅ DataFrameConnector创建成功")
    except Exception as e:
        print(f"❌ DataFrameConnector创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 创建模型
    print("\n[Step 3] 创建CTGAN模型...")
    try:
        model = CTGANSynthesizerModel(epochs=5)  # 使用少量epochs快速测试
        print("✅ 模型创建成功")
    except Exception as e:
        print(f"❌ 模型创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 创建Synthesizer
    print("\n[Step 4] 创建Synthesizer...")
    try:
        synthesizer = Synthesizer(model=model, data_connector=data_connector)
        print("✅ Synthesizer创建成功")
    except Exception as e:
        print(f"❌ Synthesizer创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 训练模型
    print("\n[Step 5] 训练模型...")
    try:
        synthesizer.fit()
        print("✅ 模型训练成功")
    except Exception as e:
        print(f"❌ 模型训练失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 生成数据
    print("\n[Step 6] 生成合成数据...")
    try:
        synthetic_data = synthesizer.sample(10)
        print(f"✅ 数据生成成功，共 {len(synthetic_data)} 行")
        print(f"生成的数据:\n{synthetic_data}")
        print(f"生成数据的数据类型:\n{synthetic_data.dtypes}")
        return True
    except Exception as e:
        print(f"❌ 数据生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sdgx_with_date():
    """使用包含日期列的数据测试SDGX"""
    print("\n" + "="*60)
    print("开始带日期列的SDGX测试")
    print("="*60)
    
    # 创建包含日期列的测试数据
    print("\n[Step 1] 创建测试数据（包含日期列）...")
    test_data = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'value': [10, 20, 30, 40, 50],
        'date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05']
    })
    # 确保日期列是object类型（字符串）
    test_data['date'] = test_data['date'].astype('object')
    print(f"测试数据:\n{test_data}")
    print(f"数据类型:\n{test_data.dtypes}")
    print(f"日期列样本值: {test_data['date'].head(3).tolist()}")
    
    # 创建DataFrameConnector
    print("\n[Step 2] 创建DataFrameConnector...")
    try:
        data_connector = DataFrameConnector(df=test_data)
        print("✅ DataFrameConnector创建成功")
    except Exception as e:
        print(f"❌ DataFrameConnector创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 创建模型
    print("\n[Step 3] 创建CTGAN模型...")
    try:
        model = CTGANSynthesizerModel(epochs=5)
        print("✅ 模型创建成功")
    except Exception as e:
        print(f"❌ 模型创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 创建Synthesizer
    print("\n[Step 4] 创建Synthesizer...")
    try:
        synthesizer = Synthesizer(model=model, data_connector=data_connector)
        print("✅ Synthesizer创建成功")
    except Exception as e:
        print(f"❌ Synthesizer创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 训练模型
    print("\n[Step 5] 训练模型...")
    try:
        synthesizer.fit()
        print("✅ 模型训练成功")
    except Exception as e:
        print(f"❌ 模型训练失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 生成数据
    print("\n[Step 6] 生成合成数据...")
    try:
        synthetic_data = synthesizer.sample(10)
        print(f"✅ 数据生成成功，共 {len(synthetic_data)} 行")
        print(f"生成的数据:\n{synthetic_data}")
        print(f"生成数据的数据类型:\n{synthetic_data.dtypes}")
        return True
    except Exception as e:
        print(f"❌ 数据生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("SDGX简单测试")
    print("="*60)
    
    # 测试1：最简单的数据（无日期列）
    print("\n【测试1：最简单的数据（无日期列）】")
    result1 = test_sdgx_simple()
    
    # 测试2：包含日期列的数据
    print("\n【测试2：包含日期列的数据】")
    result2 = test_sdgx_with_date()
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"测试1（无日期列）: {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"测试2（有日期列）: {'✅ 通过' if result2 else '❌ 失败'}")
    
    if result1 and result2:
        print("\n✅ 所有测试通过！SDGX运行正常")
    else:
        print("\n❌ 部分测试失败，请检查错误信息")




