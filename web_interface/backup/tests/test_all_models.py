#!/usr/bin/env python3
"""
测试SDGX所有支持的模型
"""

import sys
import os
sys.path.append('/Users/kuangxb/Desktop/AI 生成数据 SDG /synthetic-data-generator')
sys.path.append('.')

import pandas as pd
import numpy as np
import time

def test_all_models():
    """测试所有SDGX支持的模型"""
    print("🧪 测试SDGX所有支持的模型...")
    print()
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'id': np.arange(1, 21),
        'age': np.random.randint(20, 60, 20),
        'income': np.random.randint(30000, 100000, 20),
        'education': np.random.choice(['高中', '大专', '本科', '硕士'], 20),
        'city': np.random.choice(['北京', '上海', '广州', '深圳'], 20)
    })
    
    print(f"📊 测试数据: {test_data.shape}")
    print("样本数据:")
    print(test_data.head())
    print()
    
    # 导入SDGX组件
    try:
        from sdgx.data_connectors.dataframe_connector import DataFrameConnector
        from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
        from sdgx.models.components.sdv_ctgan.synthesizers.tvae import TVAE
        from sdgx.models.statistics.single_table.copula import GaussianCopulaSynthesizerModel
        from sdgx.synthesizer import Synthesizer
        from sdgx.data_models.metadata import Metadata
        from sdgx.data_loader import DataLoader
        print("✅ SDGX组件导入成功")
    except ImportError as e:
        print(f"❌ SDGX组件导入失败: {e}")
        return False
    
    # 准备数据
    data_connector = DataFrameConnector(df=test_data)
    data_loader = DataLoader(data_connector)
    metadata = Metadata.from_dataloader(data_loader)
    print(f"✅ 元数据创建成功，字段数量: {len(metadata.column_list)}")
    print()
    
    # 测试模型
    models_to_test = [
        ('CTGAN', CTGANSynthesizerModel, {'epochs': 3}),
        ('TVAE', TVAE, {'epochs': 2}),
        ('Gaussian Copula', GaussianCopulaSynthesizerModel, {})
    ]
    
    results = []
    
    for model_name, model_class, model_params in models_to_test:
        print(f"🔬 测试 {model_name} 模型...")
        try:
            # 创建模型
            if model_params:
                model = model_class(**model_params)
            else:
                model = model_class()
            
            print(f"✅ {model_name} 模型创建成功")
            
            # 根据模型类型选择不同的处理方式
            if model_name == 'TVAE':
                # TVAE直接使用，不需要Synthesizer
                print(f"🔄 开始训练 {model_name} 模型...")
                start_time = time.time()
                model.fit(test_data)
                training_time = time.time() - start_time
                print(f"✅ {model_name} 模型训练完成，耗时: {training_time:.2f}秒")
                
                print(f"🎯 开始生成 {model_name} 合成数据...")
                start_time = time.time()
                synthetic_data = model.sample(15)
                generation_time = time.time() - start_time
            else:
                # CTGAN和Gaussian Copula使用Synthesizer
                synthesizer = Synthesizer(
                    metadata=metadata,
                    model=model,
                    data_connector=data_connector,
                )
                print(f"✅ {model_name} 合成器创建成功")
                
                # 训练模型
                print(f"🔄 开始训练 {model_name} 模型...")
                start_time = time.time()
                synthesizer.fit()
                training_time = time.time() - start_time
                print(f"✅ {model_name} 模型训练完成，耗时: {training_time:.2f}秒")
                
                # 生成合成数据
                print(f"🎯 开始生成 {model_name} 合成数据...")
                start_time = time.time()
                synthetic_data = synthesizer.sample(15)
                generation_time = time.time() - start_time
            
            print(f"✅ {model_name} 合成数据生成成功，耗时: {generation_time:.2f}秒")
            print(f"   原始数据: {test_data.shape}")
            print(f"   合成数据: {synthetic_data.shape}")
            
            # 显示合成数据样本
            print(f"   合成数据样本:")
            print(synthetic_data.head(3))
            
            results.append({
                'model': model_name,
                'success': True,
                'training_time': training_time,
                'generation_time': generation_time,
                'synthetic_shape': synthetic_data.shape
            })
            
            print(f"🎉 {model_name} 测试成功！")
            
        except Exception as e:
            print(f"❌ {model_name} 测试失败: {e}")
            results.append({
                'model': model_name,
                'success': False,
                'error': str(e)
            })
        
        print("-" * 50)
    
    # 总结结果
    print("\n📊 测试结果总结:")
    print("=" * 60)
    successful_models = 0
    for result in results:
        if result['success']:
            print(f"✅ {result['model']}: 成功")
            print(f"   训练时间: {result['training_time']:.2f}秒")
            print(f"   生成时间: {result['generation_time']:.2f}秒")
            print(f"   合成数据形状: {result['synthetic_shape']}")
            successful_models += 1
        else:
            print(f"❌ {result['model']}: 失败 - {result['error']}")
        print()
    
    print(f"🎯 成功模型数量: {successful_models}/{len(models_to_test)}")
    
    if successful_models == len(models_to_test):
        print("🎉 所有模型测试通过！SDGX完全支持这些模型！")
        return True
    else:
        print("⚠️ 部分模型测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = test_all_models()
    sys.exit(0 if success else 1)
