#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试SDGX组件功能
"""

import sys
import os
import pandas as pd
import numpy as np
import time

# 添加SDGX路径
sys.path.append('/Users/kuangxb/Desktop/AI 生成数据 SDG /synthetic-data-generator')

def test_sdgx_components():
    """直接测试SDGX组件"""
    print("🧪 直接测试SDGX组件功能...")
    
    try:
        # 导入SDGX组件
        from sdgx.data_connectors.dataframe_connector import DataFrameConnector
        from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
        from sdgx.synthesizer import Synthesizer
        from sdgx.data_models.metadata import Metadata
        from sdgx.data_loader import DataLoader
        
        print("✅ SDGX组件导入成功")
        
        # 创建测试数据
        print("📊 创建测试数据...")
        test_data = pd.DataFrame({
            'id': range(1, 21),
            'age': np.random.randint(20, 60, 20),
            'income': np.random.randint(30000, 100000, 20),
            'education': np.random.choice(['高中', '大专', '本科', '硕士', '博士'], 20),
            'city': np.random.choice(['北京', '上海', '广州', '深圳', '杭州'], 20)
        })
        
        print(f"原始数据形状: {test_data.shape}")
        print("原始数据样本:")
        print(test_data.head())
        
        # 创建数据连接器
        print("🔗 创建数据连接器...")
        data_connector = DataFrameConnector(df=test_data)
        data_loader = DataLoader(data_connector)
        
        # 创建元数据
        print("📋 创建元数据...")
        metadata = Metadata.from_dataloader(data_loader)
        print(f"✅ 元数据创建成功，字段数量: {len(metadata.column_list)}")
        
        # 创建CTGAN模型
        print("🤖 创建CTGAN模型...")
        epochs = 5  # 使用较少的训练轮数进行测试
        model = CTGANSynthesizerModel(epochs=epochs)
        print(f"✅ CTGAN模型创建成功，训练轮数: {epochs}")
        
        # 创建合成器
        print("⚙️ 创建合成器...")
        synthesizer = Synthesizer(
            metadata=metadata,
            model=model,
            data_connector=data_connector,
        )
        print("✅ 合成器创建成功")
        
        # 训练模型
        print("🔄 开始训练SDGX模型...")
        start_time = time.time()
        synthesizer.fit()
        training_time = time.time() - start_time
        print(f"✅ 模型训练完成，耗时: {training_time:.2f}秒")
        
        # 生成合成数据
        print("🎯 开始生成合成数据...")
        num_samples = 30
        start_time = time.time()
        synthetic_data = synthesizer.sample(num_samples)
        generation_time = time.time() - start_time
        
        # 转换为pandas DataFrame
        synthetic_df = synthetic_data  # 已经是DataFrame了
        
        print(f"✅ 合成数据生成成功！")
        print(f"   原始数据: {test_data.shape}")
        print(f"   合成数据: {synthetic_df.shape}")
        print(f"   训练时间: {training_time:.2f}秒")
        print(f"   生成时间: {generation_time:.2f}秒")
        
        print("\n🔍 合成数据样本:")
        print(synthetic_df.head())
        
        print("\n📊 数据质量对比:")
        print("原始数据统计:")
        print(test_data.describe())
        print("\n合成数据统计:")
        print(synthetic_df.describe())
        
        # 计算相似度指标
        print("\n📈 质量评估:")
        
        # 数值列的相关性
        numeric_cols = test_data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            original_corr = test_data[numeric_cols].corr()
            synthetic_corr = synthetic_df[numeric_cols].corr()
            
            # 计算相关性矩阵的相似度
            corr_diff = np.abs(original_corr - synthetic_corr).mean().mean()
            print(f"相关性保持度: {1 - corr_diff:.3f}")
        
        # 分布相似度
        for col in numeric_cols:
            orig_mean = test_data[col].mean()
            synth_mean = synthetic_df[col].mean()
            mean_diff = abs(orig_mean - synth_mean) / orig_mean
            print(f"{col} 均值相似度: {1 - mean_diff:.3f}")
        
        print("\n🎉 SDGX组件测试成功！真正的合成数据生成功能正常工作！")
        return True
        
    except Exception as e:
        print(f"❌ SDGX组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_simulation():
    """测试回退模拟功能"""
    print("\n🧪 测试回退模拟功能...")
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'id': range(1, 11),
        'age': np.random.randint(20, 60, 10),
        'income': np.random.randint(30000, 100000, 10),
        'city': np.random.choice(['北京', '上海', '广州'], 10)
    })
    
    print(f"原始数据形状: {test_data.shape}")
    
    # 模拟生成过程
    synthetic_df = test_data.copy()
    
    # 添加一些随机噪声来模拟合成效果
    for col in synthetic_df.select_dtypes(include=[np.number]).columns:
        noise = np.random.normal(0, 0.1, len(synthetic_df))
        synthetic_df[col] = synthetic_df[col] + noise * synthetic_df[col].std()
    
    print(f"模拟合成数据形状: {synthetic_df.shape}")
    print("模拟合成数据样本:")
    print(synthetic_df.head())
    
    print("✅ 回退模拟功能测试成功！")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 SDGX组件直接测试")
    print("=" * 60)
    
    # 测试真正的SDGX组件
    sdgx_result = test_sdgx_components()
    
    # 测试回退模拟功能
    fallback_result = test_fallback_simulation()
    
    print("\n" + "=" * 60)
    print("📋 测试结果总结")
    print("=" * 60)
    print(f"SDGX组件测试: {'✅ 通过' if sdgx_result else '❌ 失败'}")
    print(f"回退模拟测试: {'✅ 通过' if fallback_result else '❌ 失败'}")
    
    if sdgx_result:
        print("\n🎉 SDGX集成成功！真正的合成数据生成功能可用！")
    else:
        print("\n⚠️ SDGX集成失败，将使用模拟数据生成")
