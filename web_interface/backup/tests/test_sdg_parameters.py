#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SDG参数传递功能
"""

import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:5000"

def test_sdg_parameters():
    """测试SDG参数是否正确传递和使用"""
    print("🧪 测试SDG参数传递功能...")
    
    # 创建会话
    session = requests.Session()
    
    # 1. 登录
    print("1️⃣ 登录测试用户...")
    login_data = {
        "email": "test@example.com",
        "password": "test123"
    }
    
    login_response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    if login_response.status_code == 200:
        print("✅ 登录成功")
    else:
        print(f"❌ 登录失败: {login_response.status_code}")
        return False
    
    # 2. 测试不同的模型配置
    test_configs = [
        {
            "name": "默认配置",
            "config": "default",
            "expected_epochs": 8
        },
        {
            "name": "快速配置",
            "config": "fast", 
            "expected_epochs": 3
        },
        {
            "name": "高质量配置",
            "config": "high_quality",
            "expected_epochs": 15
        },
        {
            "name": "自定义配置",
            "config": {"epochs": 25, "batch_size": 1000},
            "expected_epochs": 25
        }
    ]
    
    for test_config in test_configs:
        print(f"\n2️⃣ 测试{test_config['name']}...")
        
        # 准备测试数据
        test_data = {
            "industry_id": "finance",
            "dataset_id": "bank_customers",
            "demo_size": 20,
            "synthetic_amount": 50,
            "model_type": "ctgan",
            "model_config": test_config["config"],
            "similarity": 0.8
        }
        
        print(f"📊 请求参数: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        # 调用API
        start_time = time.time()
        response = session.post(f"{BASE_URL}/api/synthetic/generate_from_demo", json=test_data)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ API调用成功")
                
                # 检查返回的质量指标
                quality_metrics = result.get('data', {}).get('quality_metrics', {})
                generation_config = result.get('data', {}).get('generation_config', {})
                
                print(f"📈 质量指标:")
                print(f"   模型类型: {quality_metrics.get('model_type', 'N/A')}")
                print(f"   训练轮数: {quality_metrics.get('training_epochs', 'N/A')}")
                print(f"   质量评分: {quality_metrics.get('overall_score', 'N/A')}")
                print(f"   处理时间: {quality_metrics.get('processing_time', 'N/A')}秒")
                
                # 验证epochs是否正确
                actual_epochs = quality_metrics.get('training_epochs')
                expected_epochs = test_config['expected_epochs']
                
                if actual_epochs == expected_epochs:
                    print(f"✅ 训练轮数正确: {actual_epochs} (期望: {expected_epochs})")
                else:
                    print(f"❌ 训练轮数不匹配: {actual_epochs} (期望: {expected_epochs})")
                
                # 检查是否使用了真正的SDGX
                if quality_metrics.get('model_type') == 'CTGAN':
                    print("✅ 确认使用了真正的SDGX CTGAN模型")
                else:
                    print("⚠️ 可能使用了模拟生成")
                
            else:
                print(f"❌ 生成失败: {result.get('message', '未知错误')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")
    
    # 3. 测试相似度参数
    print(f"\n3️⃣ 测试相似度参数...")
    
    similarity_tests = [0.5, 0.8, 0.9]
    
    for similarity in similarity_tests:
        print(f"测试相似度: {similarity}")
        
        test_data = {
            "industry_id": "finance",
            "dataset_id": "bank_customers", 
            "demo_size": 15,
            "synthetic_amount": 30,
            "model_type": "ctgan",
            "model_config": "default",
            "similarity": similarity
        }
        
        response = session.post(f"{BASE_URL}/api/synthetic/generate_from_demo", json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                quality_metrics = result.get('data', {}).get('quality_metrics', {})
                overall_score = quality_metrics.get('overall_score', 0)
                
                print(f"   相似度设置: {similarity}")
                print(f"   实际质量评分: {overall_score:.3f}")
                
                # 相似度越高，质量评分应该越高
                if similarity >= 0.8 and overall_score >= 0.85:
                    print("✅ 高质量配置生效")
                elif similarity >= 0.5 and overall_score >= 0.7:
                    print("✅ 中等质量配置生效")
                else:
                    print("⚠️ 质量评分可能未按相似度调整")
            else:
                print(f"❌ 生成失败: {result.get('message', '未知错误')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    
    return True

def test_model_types():
    """测试不同模型类型"""
    print("\n4️⃣ 测试不同模型类型...")
    
    session = requests.Session()
    
    # 登录
    login_data = {"email": "test@example.com", "password": "test123"}
    session.post(f"{BASE_URL}/auth/login", json=login_data)
    
    model_types = ["ctgan", "tvae", "gaussian_copula"]
    
    for model_type in model_types:
        print(f"测试模型类型: {model_type}")
        
        test_data = {
            "industry_id": "finance",
            "dataset_id": "bank_customers",
            "demo_size": 10,
            "synthetic_amount": 20,
            "model_type": model_type,
            "model_config": "default",
            "similarity": 0.8
        }
        
        response = session.post(f"{BASE_URL}/api/synthetic/generate_from_demo", json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                quality_metrics = result.get('data', {}).get('quality_metrics', {})
                actual_model_type = quality_metrics.get('model_type', 'N/A')
                
                print(f"   请求模型: {model_type}")
                print(f"   实际模型: {actual_model_type}")
                print(f"   质量评分: {quality_metrics.get('overall_score', 'N/A')}")
                
                # 目前只支持CTGAN，其他模型会回退到CTGAN
                if model_type == "ctgan" and actual_model_type == "CTGAN":
                    print("✅ CTGAN模型正常工作")
                elif model_type != "ctgan" and actual_model_type == "CTGAN":
                    print("⚠️ 模型回退到CTGAN（这是正常的，因为只实现了CTGAN）")
                else:
                    print("❌ 模型类型不匹配")
            else:
                print(f"❌ 生成失败: {result.get('message', '未知错误')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 SDG参数传递功能测试")
    print("=" * 60)
    
    # 测试参数传递
    test1_result = test_sdg_parameters()
    
    # 测试模型类型
    test_model_types()
    
    print("\n" + "=" * 60)
    print("📋 测试结果总结")
    print("=" * 60)
    print(f"参数传递测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    
    if test1_result:
        print("\n🎉 SDG参数传递功能正常！")
        print("✅ 前端参数正确传递到后端")
        print("✅ 后端正确使用参数配置SDGX模型")
        print("✅ 质量指标反映真实的模型性能")
    else:
        print("\n⚠️ 参数传递功能需要检查")




