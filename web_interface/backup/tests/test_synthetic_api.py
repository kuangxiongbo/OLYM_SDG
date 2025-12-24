#!/usr/bin/env python3
"""
测试合成数据生成API
"""

import requests
import json

def test_synthetic_api():
    """测试合成数据生成API"""
    
    # 测试URL
    base_url = "http://localhost:5000"
    
    # 登录获取session
    print("🔐 登录获取session...")
    session = requests.Session()
    
    # 登录
    login_data = {
        "email": "test@example.com",
        "password": "test123"
    }
    
    login_response = session.post(f"{base_url}/auth/login", json=login_data)
    print(f"登录响应: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print("❌ 登录失败")
        return
    
    print("✅ 登录成功")
    
    # 测试1: 使用演示数据
    print("\n🧪 测试1: 使用演示数据生成合成数据")
    demo_request = {
        "demo_data": {
            "data": [
                {"name": "张三", "age": 25, "city": "北京"},
                {"name": "李四", "age": 30, "city": "上海"},
                {"name": "王五", "age": 28, "city": "广州"}
            ]
        },
        "model_type": "ctgan",
        "data_amount": 100,
        "similarity": 0.8
    }
    
    response1 = session.post(f"{base_url}/api/synthetic/generate", json=demo_request)
    print(f"演示数据请求响应: {response1.status_code}")
    if response1.status_code != 200:
        print(f"错误响应: {response1.text}")
    else:
        print("✅ 演示数据生成成功")
    
    # 测试2: 使用数据源ID（假设ID为1）
    print("\n🧪 测试2: 使用数据源ID生成合成数据")
    upload_request = {
        "data_source": "upload",
        "data_source_id": 1,
        "data_amount": 100,
        "model_type": "ctgan",
        "similarity": 0.8
    }
    
    response2 = session.post(f"{base_url}/api/synthetic/generate", json=upload_request)
    print(f"数据源请求响应: {response2.status_code}")
    if response2.status_code != 200:
        print(f"错误响应: {response2.text}")
    else:
        print("✅ 数据源生成成功")
    
    # 测试3: 没有数据源
    print("\n🧪 测试3: 没有提供数据源（应该返回400）")
    empty_request = {
        "model_type": "ctgan",
        "data_amount": 100,
        "similarity": 0.8
    }
    
    response3 = session.post(f"{base_url}/api/synthetic/generate", json=empty_request)
    print(f"空请求响应: {response3.status_code}")
    if response3.status_code == 400:
        print("✅ 正确返回400错误")
    else:
        print(f"意外响应: {response3.text}")

if __name__ == "__main__":
    test_synthetic_api()
