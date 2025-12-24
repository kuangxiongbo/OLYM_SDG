#!/usr/bin/env python3
"""
模型类型问题诊断脚本
检查SDGX状态和模型创建问题
"""

import sys
import os

def check_sdgx_imports():
    """检查SDGX组件导入状态"""
    print("🔍 检查SDGX组件导入状态...")
    
    try:
        from sdgx.models.components.sdv_ctgan.synthesizers.ctgan import CTGANSynthesizerModel
        print("✅ CTGAN模型导入成功")
    except ImportError as e:
        print(f"❌ CTGAN模型导入失败: {e}")
        return False
    
    try:
        from sdgx.models.components.sdv_copulas.synthesizers.gaussian_copula import GaussianCopulaSynthesizerModel
        print("✅ Gaussian Copula模型导入成功")
    except ImportError as e:
        print(f"❌ Gaussian Copula模型导入失败: {e}")
        return False
    
    try:
        from sdgx.synthesizer import Synthesizer
        print("✅ Synthesizer导入成功")
    except ImportError as e:
        print(f"❌ Synthesizer导入失败: {e}")
        return False
    
    try:
        from sdgx.data_models.metadata import Metadata
        print("✅ Metadata导入成功")
    except ImportError as e:
        print(f"❌ Metadata导入失败: {e}")
        return False
    
    try:
        from sdgx.data_loader import DataLoader
        print("✅ DataLoader导入成功")
    except ImportError as e:
        print(f"❌ DataLoader导入失败: {e}")
        return False
    
    return True

def test_model_creation():
    """测试模型创建"""
    print("\n🧪 测试模型创建...")
    
    try:
        from sdgx.models.components.sdv_ctgan.synthesizers.ctgan import CTGANSynthesizerModel
        
        # 测试CTGAN模型创建
        print("测试CTGAN模型创建...")
        model = CTGANSynthesizerModel(
            epochs=10,
            batch_size=500,
            generator_lr=0.0002,
            discriminator_lr=0.0002
        )
        print("✅ CTGAN模型创建成功")
        
        # 测试Gaussian Copula模型创建
        print("测试Gaussian Copula模型创建...")
        from sdgx.models.components.sdv_copulas.synthesizers.gaussian_copula import GaussianCopulaSynthesizerModel
        model = GaussianCopulaSynthesizerModel(
            enforce_min_max_values=True,
            enforce_rounding=True
        )
        print("✅ Gaussian Copula模型创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型创建失败: {e}")
        return False

def test_similarity_parameters():
    """测试相似度参数映射"""
    print("\n📊 测试相似度参数映射...")
    
    # 导入相似度参数函数
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from app_complete import similarity_to_parameters
    
    test_values = [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    
    for similarity in test_values:
        params = similarity_to_parameters(similarity)
        print(f"相似度 {similarity}: epochs={params['epochs']}, batch_size={params['batch_size']}")
    
    return True

def test_model_creation_function():
    """测试模型创建函数"""
    print("\n🔧 测试模型创建函数...")
    
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from app_complete import create_sdgx_model
    
    # 测试CTGAN模型创建
    print("测试CTGAN模型创建...")
    try:
        model = create_sdgx_model('ctgan', 0.8)
        if model:
            print("✅ CTGAN模型创建成功")
        else:
            print("❌ CTGAN模型创建失败，返回None")
            return False
    except Exception as e:
        print(f"❌ CTGAN模型创建异常: {e}")
        return False
    
    # 测试Gaussian Copula模型创建
    print("测试Gaussian Copula模型创建...")
    try:
        model = create_sdgx_model('gaussian_copula', 0.8)
        if model:
            print("✅ Gaussian Copula模型创建成功")
        else:
            print("❌ Gaussian Copula模型创建失败，返回None")
            return False
    except Exception as e:
        print(f"❌ Gaussian Copula模型创建异常: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 SDGX模型类型问题诊断开始...\n")
    
    # 检查导入
    if not check_sdgx_imports():
        print("\n❌ SDGX组件导入失败，这是导致fallback_simulation的原因")
        return
    
    # 测试模型创建
    if not test_model_creation():
        print("\n❌ 基础模型创建失败")
        return
    
    # 测试相似度参数
    if not test_similarity_parameters():
        print("\n❌ 相似度参数映射失败")
        return
    
    # 测试模型创建函数
    if not test_model_creation_function():
        print("\n❌ 模型创建函数失败")
        return
    
    print("\n✅ 所有测试通过！SDGX应该可以正常工作")
    print("💡 如果仍然显示fallback_simulation，请检查：")
    print("   1. 服务是否重启")
    print("   2. 虚拟环境是否正确激活")
    print("   3. 是否有其他错误导致模型创建失败")

if __name__ == "__main__":
    main()




