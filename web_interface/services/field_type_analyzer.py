#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段类型分析器
提供准确的字段类型识别功能
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any


class FieldTypeAnalyzer:
    """字段类型分析器"""
    
    # 日期格式正则表达式
    DATE_PATTERN = re.compile(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$')
    DATETIME_PATTERN = re.compile(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}(\s+\d{1,2}:\d{1,2}(:\d{1,2})?)?$')
    
    @staticmethod
    def analyze_field_type(series: pd.Series, column_name: str, sample_size: int = 100) -> Tuple[str, float]:
        """
        分析字段类型
        
        Args:
            series: 数据列
            column_name: 列名
            sample_size: 采样大小
            
        Returns:
            (字段类型, 置信度)
        """
        non_null = series.dropna()
        if len(non_null) == 0:
            return 'string', 0.0
        
        sample = non_null.head(sample_size)
        sample_size_actual = len(sample)
        
        if sample_size_actual == 0:
            return 'string', 0.0
        
        # 1. 检查字段名语义
        name_lower = column_name.lower()
        
        # 2. 日期时间识别（最严格）
        date_count = 0
        datetime_count = 0
        for val in sample:
            val_str = str(val).strip()
            if FieldTypeAnalyzer.DATETIME_PATTERN.match(val_str):
                if ':' in val_str:
                    datetime_count += 1
                else:
                    date_count += 1
            elif FieldTypeAnalyzer.DATE_PATTERN.match(val_str):
                date_count += 1
        
        date_ratio = date_count / sample_size_actual
        datetime_ratio = datetime_count / sample_size_actual
        
        if datetime_ratio > 0.8:
            return 'datetime', datetime_ratio
        elif date_ratio > 0.8:
            return 'date', date_ratio
        
        # 3. 数值识别（区分整数和浮点数）
        integer_count = 0
        float_count = 0
        numeric_count = 0
        
        for val in sample:
            try:
                val_str = str(val).strip()
                # 跳过空字符串
                if not val_str:
                    continue
                
                # 尝试转换为数值
                num = pd.to_numeric(val_str, errors='coerce')
                if pd.notna(num):
                    numeric_count += 1
                    # 检查是否为整数：如果原始字符串不包含小数点，且转换后的值等于其整数部分
                    if '.' not in val_str and num == int(num):
                        integer_count += 1
                    else:
                        float_count += 1
            except (ValueError, TypeError, AttributeError):
                pass
        
        numeric_ratio = numeric_count / sample_size_actual if sample_size_actual > 0 else 0
        if numeric_ratio > 0.8:
            # 如果主要是整数，返回integer；否则返回float
            if integer_count > float_count * 2 or (integer_count > 0 and float_count == 0):
                return 'integer', numeric_ratio
            else:
                return 'float', numeric_ratio
        
        # 4. ID字段识别
        if FieldTypeAnalyzer._is_id_field(name_lower, sample):
            return 'id', 0.9
        
        # 5. 布尔值识别
        bool_count = 0
        for val in sample:
            val_str = str(val).strip().lower()
            if val_str in ['true', 'false', '1', '0', 'yes', 'no', '是', '否']:
                bool_count += 1
        
        if bool_count / sample_size_actual > 0.8:
            return 'boolean', bool_count / sample_size_actual
        
        # 6. 离散值识别（分类）
        unique_ratio = sample.nunique() / sample_size_actual
        if unique_ratio < 0.1 and sample_size_actual > 10:
            # 唯一值比例很低，可能是分类字段
            return 'discrete', 1.0 - unique_ratio
        
        # 7. 默认字符串
        return 'string', 0.5
    
    @staticmethod
    def _is_id_field(column_name: str, sample: pd.Series) -> bool:
        """
        判断是否为ID字段
        
        Args:
            column_name: 列名（小写）
            sample: 数据样本
            
        Returns:
            是否为ID字段
        """
        # 检查列名是否包含ID关键词
        id_keywords = ['id', '_id', '编号', '序号', '流水号', '交易号', '订单号']
        if any(keyword in column_name for keyword in id_keywords):
            # 检查数据是否像ID（唯一、递增等）
            if len(sample) > 1:
                unique_ratio = sample.nunique() / len(sample)
                if unique_ratio > 0.9:
                    return True
        
        return False
    
    @staticmethod
    def analyze_dataframe(df: pd.DataFrame, sample_size: int = 100) -> List[Dict[str, Any]]:
        """
        分析整个DataFrame的字段类型
        
        Args:
            df: DataFrame
            sample_size: 每个字段的采样大小
            
        Returns:
            字段类型列表
        """
        fields = []
        
        print(f"[FieldTypeAnalyzer] 开始分析DataFrame，共 {len(df.columns)} 列")
        print(f"[FieldTypeAnalyzer] DataFrame dtypes: {df.dtypes.to_dict()}")
        
        for col in df.columns:
            field_type, confidence = FieldTypeAnalyzer.analyze_field_type(
                df[col], col, sample_size
            )
            
            # 获取样本值用于调试
            sample_values = df[col].dropna().head(5).tolist()
            print(f"[FieldTypeAnalyzer] 列 '{col}': 类型={field_type}, 置信度={confidence:.2f}, 样本值={sample_values[:3]}")
            
            fields.append({
                'name': col,
                'type': field_type,
                'confidence': round(confidence, 2),
                'sample_values': sample_values
            })
        
        print(f"[FieldTypeAnalyzer] 分析完成，共识别 {len(fields)} 个字段")
        return fields
    
    @staticmethod
    def get_type_label(field_type: str) -> str:
        """
        获取字段类型的中文标签
        
        Args:
            field_type: 字段类型
            
        Returns:
            中文标签
        """
        type_labels = {
            'string': '字符串',
            'integer': '整数',
            'float': '浮点数',
            'boolean': '布尔值',
            'date': '日期',
            'datetime': '日期时间',
            'id': 'ID',
            'discrete': '离散/分类'
        }
        return type_labels.get(field_type, '未知')



