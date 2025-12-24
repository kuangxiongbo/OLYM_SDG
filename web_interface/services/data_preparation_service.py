#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据准备服务
职责：最小化预处理，只修复关键数据质量问题
原则：不进行类型转换，不修改数据内容，只修复格式问题
"""

import os
import csv
import pandas as pd
from typing import Optional, Set, Dict, Any
from pathlib import Path


class DataPreparationService:
    """数据准备服务 - 最小化预处理"""
    
    def __init__(self, upload_folder: str):
        """
        初始化数据准备服务
        
        Args:
            upload_folder: 上传文件存储目录
        """
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
        
        # 导入数据验证器（用于修复日期时间问题）
        from .data_validator import DataValidator
        self.data_validator = DataValidator()
    
    def load_data(self, file_id: Optional[str] = None, 
                  template_id: Optional[str] = None,
                  template_service=None,
                  fields_config: Optional[list] = None) -> tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[str]]:
        """
        加载数据（文件或模板）
        
        Args:
            file_id: 文件ID
            template_id: 模板ID
            template_service: 模板服务（用于加载模板数据）
            fields_config: 字段配置（用于模板生成）
            
        Returns:
            (数据DataFrame, 原始数据DataFrame, 源文件路径)
            原始数据用于后续保存结果时使用
            源文件路径用于日志记录（如果是CSV文件）
        """
        original_data = None
        
        # 优先从文件加载
        if file_id:
            for ext in ['csv', 'xlsx', 'xls']:
                filepath = os.path.join(self.upload_folder, f"{file_id}.{ext}")
                if os.path.exists(filepath):
                    try:
                        if ext == 'csv':
                            # 使用更安全的参数读取CSV，避免日期时间值被错误解析
                            # 关键参数：
                            # - dtype=str: 将所有列读取为字符串，避免pandas自动类型推断导致的问题
                            # - keep_default_na=False: 不将空字符串转换为NaN
                            # - quoting=csv.QUOTE_MINIMAL: 正确处理引号
                            # - escapechar=None: 不使用转义字符
                            df = pd.read_csv(
                                filepath, 
                                dtype=str, 
                                keep_default_na=False,
                                quoting=csv.QUOTE_MINIMAL,
                                escapechar=None
                            )
                            print(f"[DataPreparationService] CSV文件读取完成，使用dtype=str避免自动类型推断")
                            
                            # 立即检查并修复日期时间列（在读取后立即修复，确保数据干净）
                            date_columns = self.data_validator.identify_date_columns(df)
                            if date_columns:
                                print(f"[DataPreparationService] 识别到 {len(date_columns)} 个日期列: {list(date_columns)}")
                                # 检查是否有被连接的值
                                has_concatenated = False
                                for col in date_columns:
                                    if col in df.columns:
                                        # 检查长度超过30的值或长度>=16的纯数字（YYYYMMDD格式被连接）
                                        long_values = df[col].apply(lambda x: len(str(x).strip()) > 30 or (len(str(x).strip()) >= 16 and str(x).strip().isdigit()))
                                        if long_values.any():
                                            has_concatenated = True
                                            long_count = long_values.sum()
                                            print(f"[DataPreparationService] ⚠️ 警告: 日期列 {col} 在读取后发现有 {long_count} 个值可能被连接，立即修复...")
                                            
                                            # 显示前5个问题值
                                            sample_values = df[col][long_values].head(5).tolist()
                                            print(f"[DataPreparationService] {col}列前5个问题值:")
                                            for idx, val in enumerate(sample_values):
                                                val_str = str(val).strip()
                                                print(f"  值{idx+1}: {repr(val_str[:80])}... (长度: {len(val_str)})")
                                
                                # 如果有被连接的值，立即修复
                                if has_concatenated:
                                    print(f"[DataPreparationService] 开始修复日期列中被连接的值...")
                                    df = self.data_validator.fix_date_columns(df, date_columns, task_id=None)
                                    print(f"[DataPreparationService] ✅ 日期列修复完成")
                                    
                                    # 验证修复结果
                                    for col in date_columns:
                                        if col in df.columns:
                                            long_values_after = df[col].apply(lambda x: len(str(x).strip()) > 30 or (len(str(x).strip()) >= 16 and str(x).strip().isdigit()))
                                            if long_values_after.any():
                                                print(f"[DataPreparationService] ⚠️ 警告: 日期列 {col} 修复后仍有 {long_values_after.sum()} 个值可能被连接")
                                            else:
                                                print(f"[DataPreparationService] ✅ 日期列 {col} 修复验证通过")
                                else:
                                    print(f"[DataPreparationService] ✅ 所有日期列检查通过，无需修复")
                            
                            # 显示START_TIME列的前5个值（用于调试）
                            if 'START_TIME' in df.columns:
                                sample_values = df['START_TIME'].head(5).tolist()
                                print(f"[DataPreparationService] START_TIME列读取并修复后的前5个值:")
                                for idx, val in enumerate(sample_values):
                                    val_str = str(val).strip()
                                    print(f"  行{idx+1}: {repr(val_str)} (长度: {len(val_str)})")
                        elif ext in ['xlsx', 'xls']:
                            df = pd.read_excel(filepath)
                        else:
                            continue
                        
                        # 保存原始数据副本
                        original_data = df.copy(deep=True)
                        source_file_path = filepath if ext == 'csv' else None
                        print(f"[DataPreparationService] 从文件加载数据: {df.shape[0]} 行 × {df.shape[1]} 列")
                        return df, original_data, source_file_path
                    except Exception as e:
                        print(f"[DataPreparationService] 加载文件失败: {e}")
                        continue
        
        # 如果文件加载失败，从模板生成
        if template_id and template_service:
            try:
                # 调用模板服务的加载方法
                if hasattr(template_service, '_load_template_data'):
                    df = template_service._load_template_data(template_id, fields_config=fields_config)
                    # 获取原始模板数据
                    if hasattr(template_service, '_original_template_data') and template_service._original_template_data is not None:
                        original_data = template_service._original_template_data.copy(deep=True)
                    else:
                        original_data = df.copy(deep=True)
                    print(f"[DataPreparationService] 从模板生成数据: {df.shape[0]} 行 × {df.shape[1]} 列")
                    return df, original_data, None
            except Exception as e:
                print(f"[DataPreparationService] 从模板加载失败: {e}")
                raise ValueError(f"无法加载数据: {e}")
        
        raise ValueError("无法加载数据：未提供文件ID或模板ID")
    
    def fix_critical_issues(self, df: pd.DataFrame, task_id: Optional[str] = None) -> pd.DataFrame:
        """
        修复关键数据质量问题
        
        只修复会导致SDGX失败的问题：
        1. 日期时间列被连接（会导致类型转换失败）
        2. 'NAN_VALUE'字符串（会导致类型转换失败）
        
        不进行：
        - 类型转换（让SDGX自动识别）
        - 数据内容修改（保持原始数据）
        
        Args:
            df: 原始DataFrame
            task_id: 任务ID（用于日志）
            
        Returns:
            修复后的DataFrame
        """
        log_prefix = f"任务 {task_id}: " if task_id else "[DataPreparationService] "
        df_fixed = df.copy(deep=True)
        
        print(f"{log_prefix}[fix_critical_issues] 开始修复关键数据质量问题...")
        
        # 1. 识别日期列（用于修复被连接的值）
        date_columns = self.data_validator.identify_date_columns(df_fixed)
        if date_columns:
            print(f"{log_prefix}[fix_critical_issues] 识别到 {len(date_columns)} 个日期列: {list(date_columns)}")
            
            # 修复日期列中被连接的值（关键：在数据传递给SDGX之前完成）
            print(f"{log_prefix}[fix_critical_issues] 开始修复日期列中被连接的值...")
            df_fixed = self.data_validator.fix_date_columns(df_fixed, date_columns, task_id)
            
            # 验证修复结果：确保没有遗漏的被连接值
            print(f"{log_prefix}[fix_critical_issues] 验证日期列修复结果...")
            for col in date_columns:
                if col in df_fixed.columns:
                    # 检查长度超过30的值（被连接的日期时间）或长度>=16的纯数字（YYYYMMDD格式被连接）
                    long_values = df_fixed[col].apply(lambda x: len(str(x).strip()) > 30 or (len(str(x).strip()) >= 16 and str(x).strip().isdigit()))
                    if long_values.any():
                        long_count = long_values.sum()
                        print(f"{log_prefix}[fix_critical_issues] ⚠️ 警告: 日期列 {col} 仍有 {long_count} 个值可能被连接，开始二次修复...")
                        # 再次修复这些值
                        for idx in df_fixed.index[long_values]:
                            val = str(df_fixed.at[idx, col]).strip()
                            # 检查是否是YYYYMMDD格式被连接（必须长度>=16，至少2个8位日期）
                            if len(val) >= 16 and val.isdigit():
                                import re
                                date_matches = re.findall(r'\d{8}', val)
                                if len(date_matches) > 1:
                                    # 提取第一个日期并转换
                                    first_date = date_matches[0]
                                    if len(first_date) == 8:
                                        year = first_date[:4]
                                        month = first_date[4:6]
                                        day = first_date[6:8]
                                        fixed_val = f"{year}-{month}-{day}"
                                        df_fixed.at[idx, col] = fixed_val
                                        print(f"{log_prefix}[fix_critical_issues] ⚠️ 二次修复第{idx}行（YYYYMMDD格式）: {val[:80]}... -> {fixed_val}")
                                        continue
                            # 其他情况使用fix_date_value修复
                            if len(val) > 30:
                                fixed_val = self.data_validator.fix_date_value(val)
                                if fixed_val != val:
                                    df_fixed.at[idx, col] = fixed_val
                                    print(f"{log_prefix}[fix_critical_issues] ⚠️ 二次修复第{idx}行: {val[:80]}... -> {fixed_val}")
                    else:
                        print(f"{log_prefix}[fix_critical_issues] ✅ 日期列 {col} 修复验证通过")
            
            print(f"{log_prefix}[fix_critical_issues] 日期列修复完成")
        else:
            print(f"{log_prefix}[fix_critical_issues] 未识别到日期列")
        
        # 2. 清理'NAN_VALUE'字符串（会导致类型转换失败）
        has_nan_value = False
        for col in df_fixed.columns:
            if df_fixed[col].dtype == 'object':
                # 检查是否有'NAN_VALUE'字符串
                if df_fixed[col].astype(str).str.contains('NAN_VALUE', na=False).any():
                    has_nan_value = True
                    print(f"{log_prefix}[fix_critical_issues] ⚠️ 发现列 {col} 包含'NAN_VALUE'字符串，清理为pd.NA...")
                    df_fixed[col] = df_fixed[col].replace('NAN_VALUE', pd.NA)
                    print(f"{log_prefix}[fix_critical_issues] ✅ 列 {col} 清理完成")
        
        if has_nan_value:
            print(f"{log_prefix}[fix_critical_issues] ⚠️ 数据源包含'NAN_VALUE'字符串，已清理")
        else:
            print(f"{log_prefix}[fix_critical_issues] ✅ 数据源干净，无'NAN_VALUE'字符串")
        
        print(f"{log_prefix}[fix_critical_issues] 关键数据质量问题修复完成")
        return df_fixed
    
    def validate_minimal(self, df: pd.DataFrame, task_id: Optional[str] = None, min_rows: int = 10) -> pd.DataFrame:
        """
        最小化验证
        
        只验证：
        1. 数据不为空
        2. 最小行数
        
        允许：
        - 空列（SDGX支持）
        - 部分空值（SDGX支持）
        
        Args:
            df: 数据DataFrame
            task_id: 任务ID（用于日志）
            min_rows: 最小行数
            
        Returns:
            验证后的DataFrame（如果验证通过）
            
        Raises:
            ValueError: 如果验证失败
        """
        log_prefix = f"任务 {task_id}: " if task_id else "[DataPreparationService] "
        
        print(f"{log_prefix}[validate_minimal] 开始最小化验证...")
        
        # 1. 检查数据不为空
        if df is None or df.empty:
            raise ValueError("数据为空")
        
        # 2. 检查最小行数
        if len(df) < min_rows:
            print(f"{log_prefix}[validate_minimal] ⚠️ 数据行数不足 ({len(df)} < {min_rows})，将扩展到 {min_rows} 行")
            # 扩展数据到最小行数
            while len(df) < min_rows:
                rows_to_add = min(min_rows - len(df), len(df))
                df = pd.concat([df, df.head(rows_to_add)], ignore_index=True)
            print(f"{log_prefix}[validate_minimal] ✅ 数据已扩展到 {len(df)} 行")
        
        # 3. 检查列完整性（允许空列）
        empty_cols = []
        for col in df.columns:
            if df[col].isna().all():
                empty_cols.append(col)
        
        if empty_cols:
            print(f"{log_prefix}[validate_minimal] ⚠️ 发现 {len(empty_cols)} 个空列: {empty_cols}（SDGX支持空列）")
        else:
            print(f"{log_prefix}[validate_minimal] ✅ 所有列都有数据")
        
        print(f"{log_prefix}[validate_minimal] 最小化验证完成: {df.shape[0]} 行 × {df.shape[1]} 列")
        return df
    
    def get_source_file_path(self, file_id: str) -> Optional[str]:
        """
        获取源文件路径（用于直接使用CsvConnector）
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件路径（如果是CSV文件），否则None
        """
        csv_path = os.path.join(self.upload_folder, f"{file_id}.csv")
        if os.path.exists(csv_path):
            return csv_path
        return None

