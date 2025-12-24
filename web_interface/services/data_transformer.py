#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据转换模块
负责将数据转换为SDGX兼容格式
"""

import pandas as pd
from typing import Set, Optional, List, Dict


class DataTransformer:
    """数据转换器"""
    
    @staticmethod
    def prepare_for_sdgx(df: pd.DataFrame, date_columns: Set[str], task_id: Optional[str] = None) -> pd.DataFrame:
        """
        准备数据以传递给SDGX
        
        Args:
            df: 原始DataFrame
            date_columns: 日期列名称集合
            task_id: 任务ID（用于日志）
            
        Returns:
            转换后的DataFrame
        """
        df_prepared = df.copy()
        log_prefix = f"任务 {task_id}: " if task_id else "[DataTransformer] "
        
        # 关键：在转换前，先清理所有可能的空值标记（包括 'NAN_VALUE'）
        # 确保所有列都没有 'NAN_VALUE', 'NULL', 'null' 等标记
        for col in df_prepared.columns:
            if col not in (date_columns or set()):
                # 检查并替换所有可能的空值标记
                if df_prepared[col].dtype == 'object':
                    # 替换所有可能的空值标记为 pd.NA
                    df_prepared[col] = df_prepared[col].replace([
                        'NAN_VALUE', 'NULL', 'null', 'nan', 'NaN', 'None', 
                        'NaT', 'nat', '<NaT>', 'N/A', 'n/a', 'NA'
                    ], pd.NA)
                    # 检查是否还有 'NAN_VALUE' 存在
                    if df_prepared[col].astype(str).str.contains('NAN_VALUE', na=False).any():
                        print(f"{log_prefix}⚠️ 警告: 列 {col} 仍有 'NAN_VALUE' 标记，强制替换为 pd.NA")
                        df_prepared[col] = df_prepared[col].replace('NAN_VALUE', pd.NA)
                else:
                    # 对于非object类型，也检查是否有字符串形式的空值标记
                    if df_prepared[col].dtype in ['int64', 'int32', 'float64', 'float32']:
                        # 数值类型列不应该有字符串，但为了安全起见，检查一下
                        pass
        
        # 关键：在转换前，先验证日期列的值
        for col in date_columns:
            if col in df_prepared.columns:
                # 检查是否有被连接的日期字符串
                sample_values = df_prepared[col].head(10).tolist()
                has_issue = False
                for idx, val in enumerate(sample_values):
                    val_str = str(val).strip()
                    if len(val_str) > 20:
                        date_count = val_str.count('2024') + val_str.count('2025') + val_str.count('2023')
                        if date_count > 1:
                            has_issue = True
                            print(f"{log_prefix}❌ 警告: prepare_for_sdgx发现列 {col} 第{idx}行有被连接的日期: {val_str[:80]}...")
                            break
                
                if has_issue:
                    print(f"{log_prefix}⚠️ 在prepare_for_sdgx中发现日期列 {col} 有问题，尝试修复...")
                    # 使用正则表达式提取第一个日期
                    import re
                    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
                    for idx in range(len(df_prepared)):
                        val = str(df_prepared.at[idx, col]).strip()
                        if len(val) > 20:
                            dates_found = date_pattern.findall(val)
                            if len(dates_found) > 0:
                                df_prepared.at[idx, col] = dates_found[0]
                                if idx < 3:
                                    print(f"{log_prefix}⚠️ 修复第{idx}行: {val[:50]}... -> {dates_found[0]}")
                    
                    # 确保所有值都是10个字符
                    df_prepared[col] = df_prepared[col].apply(lambda x: str(x)[:10] if len(str(x)) > 10 else str(x))
                
                # 确保所有日期列都是object类型（字符串）
                # 这样可以防止pandas的infer_objects()将其转换为datetime
                df_prepared[col] = df_prepared[col].astype('object')
        
        return df_prepared
    
    @staticmethod
    def clean_data(df: pd.DataFrame, date_columns: Optional[Set[str]] = None) -> pd.DataFrame:
        """
        清理数据（处理NaN、空值等）
        
        Args:
            df: 原始DataFrame
            date_columns: 日期列名称集合（可选）
            
        Returns:
            清理后的DataFrame
        """
        df_cleaned = df.copy()
        
        # 处理日期列
        if date_columns:
            for col in date_columns:
                if col in df_cleaned.columns:
                    # 处理NaT值
                    if pd.api.types.is_datetime64_any_dtype(df_cleaned[col]):
                        df_cleaned[col] = df_cleaned[col].astype(str)
                        df_cleaned[col] = df_cleaned[col].replace(['NaT', 'nat', '<NaT>', 'None', 'nan'], '')
                    elif df_cleaned[col].dtype == 'object':
                        df_cleaned[col] = df_cleaned[col].replace(['nan', 'NaN', 'None', 'NaT', '<NaT>', 'nat', ''], '')
        
        # 处理其他object列的NaN值（只替换真正的空值标记，不改变正常字符串值和空字符串）
        for col in df_cleaned.columns:
            if col not in (date_columns or set()) and df_cleaned[col].dtype == 'object':
                # 只替换真正的空值标记（如 'NAN_VALUE', 'NULL', 'null'），不改变正常字符串
                # 注意：不要将空字符串 '' 转换为NaN，因为原始数据中可能某些列就是空的
                df_cleaned[col] = df_cleaned[col].replace(['NAN_VALUE', 'NULL', 'null'], pd.NA)
                # 只替换明确的空值标记 'nan', 'NaN'，但保留空字符串 ''
                # 空字符串 '' 保持为空字符串，不转换为NaN
                mask = df_cleaned[col].isin(['nan', 'NaN'])
                df_cleaned.loc[mask, col] = pd.NA
        
        return df_cleaned

