#!/usr/bin/env python3
"""
简单测试合成数据生成API的参数处理
"""

def test_parameter_processing():
    """测试参数处理逻辑"""
    
    # 模拟前端发送的请求数据
    test_cases = [
        {
            "name": "演示数据请求",
            "data": {
                "demo_data": {
                    "data": [
                        {"name": "张三", "age": 25, "city": "北京"},
                        {"name": "李四", "age": 30, "city": "上海"}
                    ]
                },
                "model_type": "ctgan",
                "data_amount": 100,
                "similarity": 0.8
            }
        },
        {
            "name": "上传数据请求",
            "data": {
                "data_source": "upload",
                "data_source_id": 1,
                "data_amount": 100,
                "model_type": "ctgan",
                "similarity": 0.8
            }
        },
        {
            "name": "空请求（应该失败）",
            "data": {
                "model_type": "ctgan",
                "data_amount": 100,
                "similarity": 0.8
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 测试: {test_case['name']}")
        data = test_case['data']
        
        # 模拟后端参数处理逻辑
        demo_data = data.get('demo_data')
        model_type = data.get('model_type', 'ctgan')
        model_config = data.get('model_config', 'default')
        data_amount = data.get('data_amount', 1000)
        similarity = data.get('similarity', 0.8)
        
        # 检查是否有演示数据或数据源
        has_demo_data = demo_data and demo_data.get('data') and len(demo_data.get('data', [])) > 0
        has_data_source = data.get('data_source_id')
        
        print(f"   demo_data: {demo_data}")
        print(f"   data_source_id: {data.get('data_source_id')}")
        print(f"   has_demo_data: {has_demo_data}")
        print(f"   has_data_source: {has_data_source}")
        
        if not has_demo_data and not has_data_source:
            print("   ❌ 错误: 没有提供演示数据或数据源")
        else:
            print("   ✅ 参数检查通过")

if __name__ == "__main__":
    test_parameter_processing()




