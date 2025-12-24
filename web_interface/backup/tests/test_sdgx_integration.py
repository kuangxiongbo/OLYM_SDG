#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SDGX集成功能
"""

import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:5000"
TEST_USER = {
    "email": "test@example.com",
    "password": "test123"
}

def test_sdgx_integration():
    """测试SDGX集成功能"""
    print("🧪 开始测试SDGX集成功能...")
    
    # 创建会话
    session = requests.Session()
    
    # 1. 登录
    print("1️⃣ 登录测试用户...")
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    login_response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    if login_response.status_code == 200:
        print("✅ 登录成功")
    else:
        print(f"❌ 登录失败: {login_response.status_code}")
        return False
    
    # 2. 测试合成数据生成
    print("2️⃣ 测试真正的SDGX合成数据生成...")
    
    # 准备测试数据
    test_data = {
        "demo_data": {
            "data": [
                {"id": 1, "age": 25, "income": 50000, "city": "北京", "education": "本科"},
                {"id": 2, "age": 30, "income": 60000, "city": "上海", "education": "硕士"},
                {"id": 3, "age": 28, "income": 55000, "city": "广州", "education": "本科"},
                {"id": 4, "age": 35, "income": 70000, "city": "深圳", "education": "博士"},
                {"id": 5, "age": 22, "income": 45000, "city": "杭州", "education": "大专"},
                {"id": 6, "age": 32, "income": 65000, "city": "南京", "education": "硕士"},
                {"id": 7, "age": 27, "income": 52000, "city": "武汉", "education": "本科"},
                {"id": 8, "age": 29, "income": 58000, "city": "成都", "education": "本科"}
            ]
        },
        "data_amount": 20,
        "model_type": "ctgan"
    }
    
    print(f"📊 原始数据: {len(test_data['demo_data']['data'])} 条记录")
    print("🚀 开始生成合成数据...")
    
    start_time = time.time()
    response = session.post(f"{BASE_URL}/api/synthetic/generate", json=test_data)
    end_time = time.time()
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ 合成数据生成成功！")
            
            # 分析结果
            data = result.get('data', {})
            original_data = data.get('original_data', {})
            synthetic_data = data.get('synthetic_data', {})
            quality_metrics = data.get('quality_metrics', {})
            
            print(f"📈 原始数据形状: {original_data.get('shape', 'N/A')}")
            print(f"📈 合成数据形状: {synthetic_data.get('shape', 'N/A')}")
            print(f"⏱️ 处理时间: {end_time - start_time:.2f}秒")
            print(f"🎯 模型类型: {quality_metrics.get('model_type', 'N/A')}")
            print(f"📊 质量评分: {quality_metrics.get('overall_score', 'N/A')}")
            
            # 显示合成数据样本
            sample_data = synthetic_data.get('sample', [])
            if sample_data:
                print("🔍 合成数据样本:")
                for i, record in enumerate(sample_data[:3]):
                    print(f"   {i+1}. {record}")
            
            # 检查是否使用了真正的SDGX
            if quality_metrics.get('model_type') == 'CTGAN':
                print("🎉 确认：使用了真正的SDGX CTGAN模型！")
                return True
            else:
                print("⚠️ 警告：可能使用了模拟数据生成")
                return False
        else:
            print(f"❌ 生成失败: {result.get('message', '未知错误')}")
            return False
    else:
        print(f"❌ 请求失败: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")
        return False

def test_demo_data_generation():
    """测试演示数据生成"""
    print("\n3️⃣ 测试演示数据生成...")
    
    session = requests.Session()
    
    # 登录
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    session.post(f"{BASE_URL}/auth/login", json=login_data)
    
    # 测试演示数据生成
    demo_data = {
        "industry_id": "finance",
        "dataset_id": "bank_customers",
        "demo_size": 50,
        "synthetic_amount": 100,
        "model_type": "ctgan"
    }
    
    print("🚀 开始生成演示数据...")
    start_time = time.time()
    response = session.post(f"{BASE_URL}/api/synthetic/generate_from_demo", json=demo_data)
    end_time = time.time()
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ 演示数据生成成功！")
            
            data = result.get('data', {})
            quality_metrics = data.get('quality_metrics', {})
            
            print(f"⏱️ 处理时间: {end_time - start_time:.2f}秒")
            print(f"🎯 模型类型: {quality_metrics.get('model_type', 'N/A')}")
            print(f"📊 质量评分: {quality_metrics.get('overall_score', 'N/A')}")
            
            if quality_metrics.get('model_type') == 'CTGAN':
                print("🎉 确认：演示数据使用了真正的SDGX CTGAN模型！")
                return True
            else:
                print("⚠️ 警告：演示数据可能使用了模拟生成")
                return False
        else:
            print(f"❌ 演示数据生成失败: {result.get('message', '未知错误')}")
            return False
    else:
        print(f"❌ 演示数据请求失败: {response.status_code}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 SDGX集成功能测试")
    print("=" * 60)
    
    # 测试基本合成数据生成
    test1_result = test_sdgx_integration()
    
    # 测试演示数据生成
    test2_result = test_demo_data_generation()
    
    print("\n" + "=" * 60)
    print("📋 测试结果总结")
    print("=" * 60)
    print(f"基本合成数据生成: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"演示数据生成: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！SDGX集成成功！")
    else:
        print("\n⚠️ 部分测试失败，请检查SDGX集成")




