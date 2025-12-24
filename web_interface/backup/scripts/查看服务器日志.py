#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看服务器日志和任务状态
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from models.task import Task, db
    from config import Config
    from flask import Flask
    
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("=" * 80)
        print("服务器日志和任务状态")
        print("=" * 80)
        print()
        
        # 获取最新的失败任务
        failed_task = Task.query.filter_by(status='failed').order_by(Task.created_at.desc()).first()
        if failed_task:
            print(f"最新失败任务ID: {failed_task.id}")
            print(f"创建时间: {failed_task.created_at}")
            print(f"进度: {failed_task.progress}%")
            print()
            print("错误信息:")
            print("-" * 80)
            if failed_task.error_message:
                error_msg = failed_task.error_message
                print(error_msg[:2000])  # 显示前2000字符
                if len(error_msg) > 2000:
                    print(f"\n... (错误信息过长，已截断，总长度: {len(error_msg)} 字符)")
            else:
                print("(无错误信息)")
            print("-" * 80)
            print()
            
            # 检查是否包含日期连接错误
            if failed_task.error_message and 'Could not convert string' in failed_task.error_message:
                print("🔴 确认：这是日期字符串连接错误")
                print()
                # 提取日期字符串
                import re
                date_pattern = re.compile(r"'(\d{4}-\d{2}-\d{2}[\d-]+)'")
                match = date_pattern.search(failed_task.error_message)
                if match:
                    date_str = match.group(1)
                    print(f"被连接的日期字符串长度: {len(date_str)}")
                    print(f"前100个字符: {date_str[:100]}")
                    # 提取所有日期
                    dates_found = re.findall(r'\d{4}-\d{2}-\d{2}', date_str)
                    print(f"包含的日期数量: {len(dates_found)}")
                    print(f"前5个日期: {dates_found[:5]}")
                    print(f"后5个日期: {dates_found[-5:]}")
                print()
            
            config = failed_task.get_config()
            print("任务配置:")
            print(f"  模型类型: {config.get('model_type', '未知')}")
            print(f"  模板ID: {config.get('template_id', '无')}")
            print(f"  文件ID: {config.get('file_id', '无')}")
            print(f"  数据量: {config.get('data_amount', '未知')}")
            
            # 检查是否有字段配置
            fields = config.get('fields', [])
            if fields:
                print(f"  字段数: {len(fields)}")
                date_fields = [f for f in fields if f.get('type') == 'date']
                if date_fields:
                    print(f"  日期字段: {[f.get('name') for f in date_fields]}")
        else:
            print("未找到失败的任务")
        
        print()
        print("=" * 80)
        print("建议：")
        print("1. 查看服务器终端输出，查找以下关键日志：")
        print("   - [_load_template_data] 相关的日志")
        print("   - [DataTransformer] 相关的日志")
        print("   - [Step 6.5] 相关的日志")
        print("   - ========== 日期列样本值 ==========")
        print("2. 如果看到 '❌ 严重错误' 或 '⚠️ 警告' 的日志，说明修复逻辑已执行")
        print("3. 如果问题仍然存在，请提供完整的服务器日志")
        print("=" * 80)
        
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的环境中运行此脚本")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()




