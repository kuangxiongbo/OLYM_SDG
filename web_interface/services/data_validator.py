#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证模块
负责验证和修复数据格式，确保数据符合SDGX要求
"""

import re
import pandas as pd
import numpy as np
from typing import Set, Optional, List, Dict, Any


class DataValidator:
    """数据验证器"""
    
    # 日期格式正则表达式
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}')
    DATE_EXTRACT_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}')
    
    # YYYYMMDD格式（无分隔符，8位数字）- 用于检测被连接的日期
    DATE_COMPACT_PATTERN = re.compile(r'\d{8}')  # YYYYMMDD格式（8位数字）
    
    # 日期时间格式正则表达式（支持 YYYY/M/D H:MM 和 YYYY-MM-DD HH:MM:SS）
    DATETIME_PATTERN_1 = re.compile(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(:\d{2})?')  # YYYY/M/D H:MM 或 YYYY-MM-DD HH:MM:SS
    DATETIME_PATTERN_2 = re.compile(r'\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}')  # YYYY/M/D H:MM
    # 提取日期时间：匹配 YYYY/M/D H:MM 或 YYYY-MM-DD HH:MM:SS 格式
    # 注意：使用非贪婪匹配，确保只匹配第一个日期时间
    # 优化：更精确地匹配日期时间，避免匹配到部分日期
    DATETIME_EXTRACT_PATTERN = re.compile(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(:\d{2})?)')
    
    @staticmethod
    def identify_date_columns(df: pd.DataFrame, fields_config: Optional[List[Dict]] = None) -> Set[str]:
        """
        识别DataFrame中的日期列
        
        Args:
            df: DataFrame
            fields_config: 字段配置（可选）
            
        Returns:
            日期列名称集合
        """
        date_columns = set()
        
        # 1. 从字段配置中识别日期列
        if fields_config:
            for field in fields_config:
                if field.get('type') == 'date':
                    field_name = field.get('name')
                    if field_name and field_name in df.columns:
                        date_columns.add(field_name)
        
        # 2. 检查datetime类型的列
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_columns.add(col)
        
        # 3. 检查object类型列中是否包含日期格式的值
        for col in df.columns:
            if col not in date_columns and df[col].dtype == 'object':
                sample = df[col].dropna().head(10)
                if len(sample) > 0:
                    # 检查是否匹配日期格式（YYYY-MM-DD）
                    date_count = sum(1 for v in sample 
                                   if pd.notna(v) and str(v).strip() 
                                   and DataValidator.DATE_PATTERN.match(str(v)))
                    # 检查是否匹配日期时间格式（YYYY/M/D H:MM 或 YYYY-MM-DD HH:MM:SS）
                    datetime_count = sum(1 for v in sample
                                        if pd.notna(v) and str(v).strip()
                                        and (DataValidator.DATETIME_PATTERN_1.search(str(v)) or DataValidator.DATETIME_PATTERN_2.search(str(v))))
                    # 检查列名是否包含日期时间关键词
                    col_lower = col.lower()
                    is_date_like_name = any(keyword in col_lower for keyword in ['time', 'date', 'datetime', 'start', 'end', 'created', 'updated'])
                    
                    if date_count >= len(sample) * 0.8:  # 80%以上匹配日期格式
                        date_columns.add(col)
                    elif datetime_count >= len(sample) * 0.8:  # 80%以上匹配日期时间格式
                        date_columns.add(col)
                    elif is_date_like_name and (date_count > 0 or datetime_count > 0):  # 列名像日期且包含日期值
                        date_columns.add(col)
                        print(f"[DataValidator] 根据列名和内容识别日期列: {col}")
        
        return date_columns
    
    @staticmethod
    def fix_date_value(value: Any) -> str:
        """
        修复单个日期/日期时间值，确保是独立的值
        
        支持格式：
        - YYYY-MM-DD
        - YYYY/M/D H:MM
        - YYYY-MM-DD HH:MM:SS
        
        Args:
            value: 原始值
            
        Returns:
            修复后的日期/日期时间字符串
        """
        if pd.isna(value) or str(value).strip() == '':
            return ''
        
        val_str = str(value).strip()
        
        # 首先检查是否是YYYYMMDD格式被连接（如 2025040120250401...）
        # 这种格式通常是日期被转换为YYYYMMDD格式后又被连接了
        # 注意：必须检查长度>=16（至少2个8位日期），单个8位数字可能是正常的日期值
        if len(val_str) >= 16 and val_str.isdigit():
            # 检查是否包含多个8位数字（YYYYMMDD格式）
            date_matches = DataValidator.DATE_COMPACT_PATTERN.findall(val_str)
            if len(date_matches) > 1:
                # 提取第一个日期（YYYYMMDD格式）
                first_date = date_matches[0]
                # 转换为标准格式 YYYY-MM-DD
                if len(first_date) == 8:
                    year = first_date[:4]
                    month = first_date[4:6]
                    day = first_date[6:8]
                    return f"{year}-{month}-{day}"
        
        # 如果长度超过30，可能是被连接的日期时间，尝试提取第一个日期时间
        if len(val_str) > 30:
            # 先尝试提取日期时间（YYYY/M/D H:MM 或 YYYY-MM-DD HH:MM:SS）
            # 使用search而不是findall，只找第一个匹配
            datetime_match = DataValidator.DATETIME_EXTRACT_PATTERN.search(val_str)
            if datetime_match:
                first_match = datetime_match.group(0)  # 获取完整匹配
                # 标准化格式：转换为 YYYY-MM-DD HH:MM:SS
                try:
                    dt = pd.to_datetime(first_match, errors='coerce', infer_datetime_format=True)
                    if pd.notna(dt):
                        return dt.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        # 如果解析失败，尝试手动格式化 YYYY/M/D H:MM 格式
                        if '/' in first_match and ':' in first_match:
                            parts = first_match.split()
                            if len(parts) == 2:
                                date_part = parts[0]
                                time_part = parts[1]
                                date_parts = date_part.split('/')
                                if len(date_parts) == 3:
                                    year = date_parts[0]
                                    month = date_parts[1].zfill(2)
                                    day = date_parts[2].zfill(2)
                                    time_parts = time_part.split(':')
                                    if len(time_parts) == 2:
                                        hour = time_parts[0].zfill(2)
                                        minute = time_parts[1].zfill(2)
                                        return f"{year}-{month}-{day} {hour}:{minute}:00"
                        return first_match.strip()
                except Exception as e:
                    # 如果解析失败，尝试手动格式化
                    if '/' in first_match and ':' in first_match:
                        parts = first_match.split()
                        if len(parts) == 2:
                            date_part = parts[0]
                            time_part = parts[1]
                            date_parts = date_part.split('/')
                            if len(date_parts) == 3:
                                year = date_parts[0]
                                month = date_parts[1].zfill(2)
                                day = date_parts[2].zfill(2)
                                time_parts = time_part.split(':')
                                if len(time_parts) == 2:
                                    hour = time_parts[0].zfill(2)
                                    minute = time_parts[1].zfill(2)
                                    return f"{year}-{month}-{day} {hour}:{minute}:00"
                    return first_match.strip()
            
            # 如果没有日期时间，尝试提取日期
            dates_found = DataValidator.DATE_EXTRACT_PATTERN.findall(val_str)
            if len(dates_found) > 0:
                return dates_found[0]
        
        # 如果长度在15-30之间，可能是单个日期时间但格式不标准
        if 15 <= len(val_str) <= 30:
            # 尝试解析为日期时间
            datetime_match = DataValidator.DATETIME_PATTERN_1.match(val_str) or DataValidator.DATETIME_PATTERN_2.match(val_str)
            if datetime_match:
                try:
                    dt = pd.to_datetime(val_str, errors='coerce', infer_datetime_format=True)
                    if pd.notna(dt):
                        return dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
        
        # 验证日期格式（YYYY-MM-DD），只取前10个字符
        if DataValidator.DATE_PATTERN.match(val_str):
            return val_str[:10]
        
        # 如果包含日期时间格式，尝试解析
        if DataValidator.DATETIME_PATTERN_1.search(val_str) or DataValidator.DATETIME_PATTERN_2.search(val_str):
            try:
                dt = pd.to_datetime(val_str, errors='coerce', infer_datetime_format=True)
                if pd.notna(dt):
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        return val_str
    
    @staticmethod
    def fix_date_columns(df: pd.DataFrame, date_columns: Set[str], 
                        task_id: Optional[str] = None) -> pd.DataFrame:
        """
        修复日期列，确保所有值都是独立的日期字符串
        
        Args:
            df: 原始DataFrame
            date_columns: 日期列名称集合
            task_id: 任务ID（用于日志）
            
        Returns:
            修复后的DataFrame
        """
        df_fixed = df.copy()
        log_prefix = f"任务 {task_id}: " if task_id else "[DataValidator] "
        
        for col in date_columns:
            if col not in df_fixed.columns:
                continue
            
            print(f"{log_prefix}========== 修复日期列 {col} ==========")
            
            # 1. 转换为字符串类型
            df_fixed[col] = df_fixed[col].astype(str)
            
            # 2. 处理NaT和NaN值
            df_fixed[col] = df_fixed[col].replace(['NaT', 'nat', '<NaT>', 'None', 'nan', 'NaN', ''], '')
            
            # 3. 检查并修复被连接的日期/日期时间字符串
            has_concatenated = False
            fixed_count = 0
            # 使用df_fixed.index遍历，确保正确处理所有行（包括非连续索引）
            for idx in df_fixed.index:
                val = str(df_fixed.at[idx, col]).strip()
                
                # 首先检查是否是YYYYMMDD格式被连接（如 2025040120250401...）
                # 注意：必须检查长度>=16（至少2个8位日期），单个8位数字可能是正常的日期值
                if len(val) >= 16 and val.isdigit():
                    date_matches = DataValidator.DATE_COMPACT_PATTERN.findall(val)
                    if len(date_matches) > 1:
                        # 提取第一个日期（YYYYMMDD格式）并转换为标准格式
                        first_date = date_matches[0]
                        if len(first_date) == 8:
                            year = first_date[:4]
                            month = first_date[4:6]
                            day = first_date[6:8]
                            fixed_val = f"{year}-{month}-{day}"
                            df_fixed.at[idx, col] = fixed_val
                            fixed_count += 1
                            has_concatenated = True
                            if fixed_count <= 5:
                                print(f"{log_prefix}⚠️ 修复第{idx}行（YYYYMMDD格式被连接）: {val[:80]}... -> {fixed_val}")
                            continue
                
                # 检查是否是被连接的日期时间（长度超过30且包含多个日期时间）
                if len(val) > 30:
                    # 使用search找第一个匹配，然后检查是否还有更多匹配
                    first_match = DataValidator.DATETIME_EXTRACT_PATTERN.search(val)
                    if first_match:
                        # 检查是否还有更多匹配（通过查找第一个匹配之后的内容）
                        remaining = val[first_match.end():]
                        more_matches = DataValidator.DATETIME_EXTRACT_PATTERN.search(remaining)
                        if more_matches:
                            # 有多个日期时间，提取第一个
                            has_concatenated = True
                            first_match_str = first_match.group(0)
                            # 使用fix_date_value来标准化格式
                            fixed_val = DataValidator.fix_date_value(first_match_str)
                            
                            df_fixed.at[idx, col] = fixed_val
                            fixed_count += 1
                            if fixed_count <= 5:  # 只打印前5个修复的示例
                                print(f"{log_prefix}⚠️ 修复第{idx}行: {val[:80]}... -> {fixed_val}")
                            continue
                        else:
                            # 只有一个日期时间，但长度超过30，可能是格式问题，也尝试修复
                            first_match_str = first_match.group(0)
                            fixed_val = DataValidator.fix_date_value(first_match_str)
                            if fixed_val != val:
                                has_concatenated = True
                                df_fixed.at[idx, col] = fixed_val
                                fixed_count += 1
                                if fixed_count <= 5:
                                    print(f"{log_prefix}⚠️ 修复第{idx}行: {val[:80]}... -> {fixed_val}")
                                continue
                    
                    # 检查是否包含多个日期（通过年份数量判断）
                    date_count = (val.count('2024') + val.count('2025') + 
                                val.count('2023') + val.count('2026') + 
                                val.count('2027') + val.count('2028'))
                    if date_count > 1:
                        has_concatenated = True
                        dates_found = DataValidator.DATE_EXTRACT_PATTERN.findall(val)
                        if len(dates_found) > 0:
                            df_fixed.at[idx, col] = dates_found[0]
                            fixed_count += 1
                            if fixed_count <= 5:  # 只打印前5个修复的示例
                                print(f"{log_prefix}⚠️ 修复第{idx}行: {val[:50]}... -> {dates_found[0]}")
            
            if has_concatenated:
                print(f"{log_prefix}⚠️ 日期列 {col} 包含被连接的日期/日期时间字符串，已修复 {fixed_count} 个值")
            
            # 4. 统一修复所有值
            df_fixed[col] = df_fixed[col].apply(DataValidator.fix_date_value)
            
            # 5. 确保是object类型（字符串）
            df_fixed[col] = df_fixed[col].astype('object')
            
            # 6. 最终验证
            sample_values = df_fixed[col].dropna().head(5).tolist()
            print(f"{log_prefix}日期列 {col} 修复后样本值: {sample_values}")
            
            # 检查是否还有异常值（日期时间可能超过10个字符，这是正常的）
            for val in sample_values:
                val_str = str(val)
                # 日期时间格式可能达到19个字符（YYYY-MM-DD HH:MM:SS），这是正常的
                # 但如果超过30个字符，可能是被连接的值
                if len(val_str) > 30:
                    print(f"{log_prefix}❌ 警告: 日期列 {col} 仍有异常值（可能被连接）: {val_str[:80]}...")
                elif len(val_str) > 19 and not DataValidator.DATETIME_PATTERN_1.match(val_str):
                    print(f"{log_prefix}⚠️ 警告: 日期列 {col} 值长度异常: {val_str[:50]}...")
            
            print(f"{log_prefix}========== 日期列 {col} 修复完成 ==========")
        
        return df_fixed
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, task_id: Optional[str] = None, 
                           min_rows: int = 10) -> pd.DataFrame:
        """
        验证DataFrame的完整性和正确性
        
        Args:
            df: DataFrame
            task_id: 任务ID（用于日志）
            min_rows: 最小行数要求
            
        Returns:
            验证后的DataFrame
            
        Raises:
            ValueError: 如果数据验证失败
        """
        log_prefix = f"任务 {task_id}: " if task_id else "[DataValidator] "
        errors = []
        
        print(f"{log_prefix}========== 开始数据验证 ==========")
        
        # 1. 验证数据不为空
        if df.empty:
            errors.append("数据为空")
            print(f"{log_prefix}❌ 数据为空")
        else:
            print(f"{log_prefix}✅ 数据不为空: {df.shape[0]} 行 × {df.shape[1]} 列")
        
        # 2. 验证数据行数
        if df.shape[0] < min_rows:
            errors.append(f"数据行数不足（{df.shape[0]} 行），至少需要{min_rows}行")
            print(f"{log_prefix}❌ 数据行数不足: {df.shape[0]} 行")
        else:
            print(f"{log_prefix}✅ 数据行数充足: {df.shape[0]} 行")
        
        # 3. 验证列完整性
        # 注意：允许全空列（如选填字段）和部分空值，SDGX和大模型都支持
        # 全空列不会导致训练失败，只是不会用于训练（但会在生成时保持为空）
        empty_cols = []
        partial_empty_cols = []
        for col in df.columns:
            # 检查是否全部为NaN或全部为空字符串
            is_all_na = df[col].isna().all()
            # 对于object类型，也检查是否全部为空字符串
            is_all_empty_str = False
            if df[col].dtype == 'object':
                non_na_values = df[col].dropna()
                if len(non_na_values) == 0:
                    is_all_empty_str = True
                elif (non_na_values.astype(str).str.strip() == '').all():
                    is_all_empty_str = True
            
            if is_all_na or is_all_empty_str:
                empty_cols.append(col)
                # 对于全空列，这是正常的（如选填字段），只给出信息提示，不报错
                print(f"{log_prefix}ℹ️ 列 {col} 全部为空（NaN或空字符串），这是正常的（如选填字段），SDGX和大模型都支持")
            else:
                # 检查是否有部分空值（这是正常的，SDGX和大模型都支持）
                na_count = df[col].isna().sum()
                if na_count > 0:
                    na_percentage = (na_count / len(df)) * 100
                    partial_empty_cols.append((col, na_count, na_percentage))
                    print(f"{log_prefix}ℹ️ 列 {col} 包含 {na_count} 个空值（{na_percentage:.1f}%），这是正常的，SDGX和大模型都支持部分空值")
        
        if empty_cols:
            print(f"{log_prefix}ℹ️ 发现 {len(empty_cols)} 个全空列（选填字段）: {empty_cols}")
            print(f"{log_prefix}ℹ️ 这些列将被保留，SDGX和大模型都支持全空列，生成时会保持为空")
        else:
            print(f"{log_prefix}✅ 所有列都有数据")
        
        if partial_empty_cols:
            print(f"{log_prefix}ℹ️ 发现 {len(partial_empty_cols)} 个包含部分空值的列（这是正常的）")
            print(f"{log_prefix}ℹ️ SDGX和大模型都支持部分空值，这些列可以正常用于训练")
        
        # 4. 检查Inf值
        for col in df.columns:
            if df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
                inf_count = ((df[col] == float('inf')).sum() + 
                           (df[col] == float('-inf')).sum())
                if inf_count > 0:
                    print(f"{log_prefix}⚠️ 列 {col} 包含 {inf_count} 个Inf值，将替换为NaN")
                    df[col] = df[col].replace([float('inf'), float('-inf')], np.nan)
        
        if errors:
            error_msg = "; ".join(errors)
            print(f"{log_prefix}========== 数据验证失败 ==========")
            raise ValueError(error_msg)
        
        print(f"{log_prefix}========== 数据验证完成 ==========")
        return df

