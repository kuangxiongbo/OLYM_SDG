#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试日期连接问题的脚本
逐步检查：
1. 上传的文件内容
2. 读取后的文件内容
3. 修复后的文件内容
4. 传递给SDGX的内容
"""

import os
import sys
import pandas as pd
import re

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_validator import DataValidator
from services.data_preparation_service import DataPreparationService
from config import Config

def check_csv_file(filepath):
    """检查CSV文件内容"""
    print("=" * 80)
    print("步骤1: 检查原始CSV文件内容")
    print("=" * 80)
    
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return None
    
    print(f"文件路径: {filepath}")
    print(f"文件大小: {os.path.getsize(filepath)} 字节")
    
    # 使用dtype=str读取，避免自动类型推断
    df = pd.read_csv(filepath, dtype=str, keep_default_na=False, nrows=20)
    print(f"读取行数: {len(df)}")
    print(f"列数: {len(df.columns)}")
    print(f"列名: {list(df.columns)}")
    
    # 检查START_TIME列
    if 'START_TIME' in df.columns:
        print(f"\nSTART_TIME列的前10个值:")
        for idx, val in enumerate(df['START_TIME'].head(10)):
            val_str = str(val).strip()
            print(f"  行{idx+1}: {repr(val_str)} (长度: {len(val_str)})")
            if len(val_str) >= 16 and val_str.isdigit():
                print(f"    ⚠️ 警告: 可能是YYYYMMDD格式被连接")
                # 检查是否包含多个8位数字
                date_matches = re.findall(r'\d{8}', val_str)
                if len(date_matches) > 1:
                    print(f"    ⚠️ 确认: 包含 {len(date_matches)} 个8位数字: {date_matches[:5]}")
            elif len(val_str) > 30:
                print(f"    ⚠️ 警告: 长度超过30，可能被连接")
    else:
        print("\n未找到START_TIME列")
    
    return df

def check_after_fix(df):
    """检查修复后的内容"""
    print("\n" + "=" * 80)
    print("步骤2: 检查修复后的内容")
    print("=" * 80)
    
    # 识别日期列
    date_columns = DataValidator.identify_date_columns(df)
    print(f"识别到 {len(date_columns)} 个日期列: {list(date_columns)}")
    
    if 'START_TIME' in date_columns:
        print("\n修复START_TIME列...")
        df_fixed = DataValidator.fix_date_columns(df.copy(), {'START_TIME'}, task_id='debug')
        
        print(f"\n修复后START_TIME列的前10个值:")
        for idx, val in enumerate(df_fixed['START_TIME'].head(10)):
            val_str = str(val).strip()
            print(f"  行{idx+1}: {repr(val_str)} (长度: {len(val_str)})")
            if len(val_str) >= 16 and val_str.isdigit():
                print(f"    ⚠️ 警告: 修复后仍有问题")
            elif len(val_str) > 30:
                print(f"    ⚠️ 警告: 修复后仍有问题")
        
        return df_fixed
    else:
        print("⚠️ START_TIME未被识别为日期列")
        return df

def main():
    """主函数"""
    # 查找最近上传的CSV文件
    upload_folder = Config.UPLOAD_FOLDER
    csv_files = [f for f in os.listdir(upload_folder) if f.endswith('.csv')]
    
    if not csv_files:
        print("❌ 未找到CSV文件")
        return
    
    # 获取最新的文件
    csv_file = max([os.path.join(upload_folder, f) for f in csv_files], key=os.path.getmtime)
    print(f"找到最新文件: {csv_file}\n")
    
    # 步骤1: 检查原始文件
    df_original = check_csv_file(csv_file)
    if df_original is None:
        return
    
    # 步骤2: 检查修复后
    df_fixed = check_after_fix(df_original)
    
    # 步骤3: 检查DataPreparationService的处理
    print("\n" + "=" * 80)
    print("步骤3: 检查DataPreparationService的处理")
    print("=" * 80)
    
    data_prep_service = DataPreparationService(upload_folder=upload_folder)
    
    # 获取文件ID（从文件名提取）
    file_id = os.path.splitext(os.path.basename(csv_file))[0]
    print(f"文件ID: {file_id}")
    
    try:
        df_loaded, original_data, source_file_path = data_prep_service.load_data(file_id=file_id)
        print(f"\n加载后的数据形状: {df_loaded.shape}")
        
        if 'START_TIME' in df_loaded.columns:
            print(f"\n加载后START_TIME列的前10个值:")
            for idx, val in enumerate(df_loaded['START_TIME'].head(10)):
                val_str = str(val).strip()
                print(f"  行{idx+1}: {repr(val_str)} (长度: {len(val_str)})")
                if len(val_str) >= 16 and val_str.isdigit():
                    print(f"    ⚠️ 警告: 加载后仍有问题")
                elif len(val_str) > 30:
                    print(f"    ⚠️ 警告: 加载后仍有问题")
        
        # 检查修复后
        df_prepared = data_prep_service.fix_critical_issues(df_loaded, task_id='debug')
        print(f"\n修复后数据形状: {df_prepared.shape}")
        
        if 'START_TIME' in df_prepared.columns:
            print(f"\n修复后START_TIME列的前10个值:")
            for idx, val in enumerate(df_prepared['START_TIME'].head(10)):
                val_str = str(val).strip()
                print(f"  行{idx+1}: {repr(val_str)} (长度: {len(val_str)})")
                if len(val_str) >= 16 and val_str.isdigit():
                    print(f"    ❌ 错误: 修复后仍有问题")
                elif len(val_str) > 30:
                    print(f"    ❌ 错误: 修复后仍有问题")
                else:
                    print(f"    ✅ 正常")
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()



