#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查最近的服务器日志和任务状态
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.task import Task, db
from config import Config
from flask import Flask
import json

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print("=" * 80)
    print("最近失败的任务分析")
    print("=" * 80)
    print()
    
    # 获取最近5个失败的任务
    failed_tasks = Task.query.filter_by(status='failed').order_by(Task.created_at.desc()).limit(5).all()
    
    if not failed_tasks:
        print("未找到失败的任务")
    else:
        for task in failed_tasks:
            print(f"\n{'='*80}")
            print(f"任务ID: {task.id}")
            print(f"状态: {task.status}")
            print(f"进度: {task.progress}%")
            print(f"创建时间: {task.created_at}")
            print(f"更新时间: {task.updated_at}")
            print(f"{'-'*80}")
            
            if task.error_message:
                print("错误信息:")
                print(task.error_message[:500])  # 只显示前500字符
                print()
                
                # 检查是否包含日期连接错误
                if 'Could not convert string' in task.error_message and '2024-12-10' in task.error_message:
                    print("🔴 确认：这是日期字符串连接错误")
                    print("   日期字符串被错误地连接成了长字符串")
                    print()
            
            config = task.get_config()
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
    
    print("\n" + "=" * 80)
    print("建议：")
    print("1. 检查服务器日志中的以下信息：")
    print("   - [Step 6.5] 最终验证和修复日期列...")
    print("   - ========== 日期列样本值 ==========")
    print("   - ❌ 严重警告 或 ⚠️ 最终修复")
    print("2. 如果看到日期列仍有被连接的值，说明修复逻辑没有完全生效")
    print("3. 请提供完整的服务器日志，特别是 Step 6.5 部分的输出")
    print("=" * 80)




