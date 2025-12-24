#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据加载模块
负责从各种源加载数据（文件、模板等）
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any


class DataLoader:
    """数据加载器"""
    
    def __init__(self, upload_folder: str):
        """
        初始化数据加载器
        
        Args:
            upload_folder: 上传文件存储目录
        """
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    def load_from_file(self, file_id: str) -> Optional[pd.DataFrame]:
        """
        从文件加载数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            DataFrame或None（如果文件不存在）
        """
        for ext in ['csv', 'xlsx', 'xls', 'json']:
            filepath = os.path.join(self.upload_folder, f"{file_id}.{ext}")
            if os.path.exists(filepath):
                try:
                    if ext == 'csv':
                        # 使用dtype=str读取CSV，避免pandas自动类型推断导致日期时间值被连接
                        df = pd.read_csv(filepath, dtype=str, keep_default_na=False)
                    elif ext in ['xlsx', 'xls']:
                        df = pd.read_excel(filepath)
                    elif ext == 'json':
                        df = pd.read_json(filepath)
                    else:
                        continue
                    
                    # 关键：在返回前，清理所有可能的空值标记（包括 'NAN_VALUE'）
                    # 这可以防止后续处理时遇到 'NAN_VALUE' 字符串而失败
                    print(f"[DataLoader] 清理空值标记（包括所有列）...")
                    for col in df.columns:
                        if df[col].dtype == 'object':
                            # 先检查是否包含 'NAN_VALUE'
                            nan_value_count = df[col].astype(str).str.contains('NAN_VALUE', na=False).sum()
                            if nan_value_count > 0:
                                print(f"[DataLoader] 发现列 {col} 包含 {nan_value_count} 个 'NAN_VALUE' 标记，清理中...")
                            
                            # 替换所有可能的空值标记为 pd.NA
                            df[col] = df[col].replace([
                                'NAN_VALUE', 'NULL', 'null', 'nan', 'NaN', 'None', 
                                'NaT', 'nat', '<NaT>', 'N/A', 'n/a', 'NA'
                            ], pd.NA)
                            
                            # 双重检查：确保没有遗漏
                            if df[col].astype(str).str.contains('NAN_VALUE', na=False).any():
                                print(f"[DataLoader] ⚠️ 列 {col} 仍有 'NAN_VALUE' 标记，强制清理...")
                                df[col] = df[col].astype(str).replace('NAN_VALUE', pd.NA)
                                # 再次检查
                                if df[col].astype(str).str.contains('NAN_VALUE', na=False).any():
                                    print(f"[DataLoader] ❌ 列 {col} 清理失败，使用更彻底的方法...")
                                    df[col] = df[col].astype(str).apply(
                                        lambda x: pd.NA if 'NAN_VALUE' in str(x) else x
                                    )
                                else:
                                    if nan_value_count > 0:
                                        print(f"[DataLoader] ✅ 列 {col} 清理成功")
                    
                    print(f"[DataLoader] 从文件加载数据成功: {df.shape[0]} 行 × {df.shape[1]} 列")
                    return df
                except Exception as e:
                    print(f"[DataLoader] 加载文件失败: {e}")
                    raise
        
        return None
    
    def load_from_template(self, template_id: int, fields_config: Optional[List[Dict]] = None) -> pd.DataFrame:
        """
        从模板生成数据
        
        Args:
            template_id: 模板ID
            fields_config: 字段配置（如果提供，优先使用）
            
        Returns:
            DataFrame
        """
        # 避免循环导入，直接调用模板数据生成逻辑
        # 这里需要访问SyntheticService的_load_template_data方法
        # 由于可能存在循环导入，我们暂时保留原有逻辑
        # 在实际使用中，可以通过依赖注入的方式解决
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 临时方案：直接在这里实现模板数据加载逻辑
        # 或者通过参数传递service实例
        raise NotImplementedError("模板数据加载需要通过SyntheticService实例调用")
    
    def load(self, file_id: Optional[str] = None, 
             template_id: Optional[int] = None,
             fields_config: Optional[List[Dict]] = None,
             template_loader_callback: Optional[callable] = None) -> pd.DataFrame:
        """
        加载数据（优先从文件，其次从模板）
        
        Args:
            file_id: 文件ID
            template_id: 模板ID
            fields_config: 字段配置
            template_loader_callback: 模板加载回调函数（用于避免循环导入）
            
        Returns:
            DataFrame
            
        Raises:
            ValueError: 如果无法加载数据
        """
        # 优先从文件加载
        if file_id:
            df = self.load_from_file(file_id)
            if df is not None:
                return df
        
        # 其次从模板生成（使用回调函数避免循环导入）
        if template_id:
            if template_loader_callback:
                return template_loader_callback(template_id, fields_config)
            else:
                # 如果没有提供回调，尝试直接调用（可能失败）
                return self.load_from_template(template_id, fields_config)
        
        raise ValueError("必须提供 file_id 或 template_id")
    
    def ensure_min_rows(self, df: pd.DataFrame, min_rows: int = 10, max_rows: int = 100) -> pd.DataFrame:
        """
        确保DataFrame至少有min_rows行数据
        
        Args:
            df: 原始DataFrame
            min_rows: 最小行数
            max_rows: 最大行数（避免无限扩展）
            
        Returns:
            扩展后的DataFrame
        """
        if df.shape[0] >= min_rows:
            return df
        
        print(f"[DataLoader] 数据行数不足 ({df.shape[0]} 行)，扩展到至少 {min_rows} 行")
        df_extended = df.copy()
        
        while df_extended.shape[0] < min_rows and df_extended.shape[0] < max_rows:
            rows_to_add = min(min_rows - df_extended.shape[0], df_extended.shape[0])
            df_extended = pd.concat([df_extended, df_extended.head(rows_to_add)], ignore_index=True)
        
        print(f"[DataLoader] 数据已扩展到 {df_extended.shape[0]} 行")
        return df_extended

