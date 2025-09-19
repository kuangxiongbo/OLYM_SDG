#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理器
==========

提供数据预处理、清洗和转换功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """数据处理器类"""
    
    def __init__(self):
        self.numeric_columns = []
        self.categorical_columns = []
        self.datetime_columns = []
        self.text_columns = []
        
    def analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析数据结构"""
        analysis = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'column_types': self._classify_columns(df),
            'basic_stats': self._get_basic_stats(df),
            'data_quality': self._assess_data_quality(df)
        }
        
        return analysis
    
    def _classify_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """分类列类型"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        # 进一步分类文本列
        text_cols = []
        for col in categorical_cols:
            if df[col].dtype == 'object':
                # 检查是否为文本列（长度变化大）
                lengths = df[col].astype(str).str.len()
                if lengths.std() > 5:  # 标准差大于5认为是文本
                    text_cols.append(col)
        
        # 从分类列中移除文本列
        categorical_cols = [col for col in categorical_cols if col not in text_cols]
        
        return {
            'numeric': numeric_cols,
            'categorical': categorical_cols,
            'datetime': datetime_cols,
            'text': text_cols
        }
    
    def _get_basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """获取基本统计信息"""
        stats = {}
        
        # 数值列统计
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            stats['numeric'] = df[numeric_cols].describe().to_dict()
        
        # 分类列统计
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            stats['categorical'] = {}
            for col in categorical_cols:
                stats['categorical'][col] = {
                    'unique_count': df[col].nunique(),
                    'most_common': df[col].value_counts().head(5).to_dict(),
                    'missing_count': df[col].isnull().sum()
                }
        
        return stats
    
    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """评估数据质量"""
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        duplicate_rows = df.duplicated().sum()
        
        quality_score = max(0, 100 - (missing_cells / total_cells * 100) - (duplicate_rows / df.shape[0] * 100))
        
        return {
            'missing_percentage': (missing_cells / total_cells) * 100,
            'duplicate_percentage': (duplicate_rows / df.shape[0]) * 100,
            'quality_score': quality_score,
            'recommendations': self._get_quality_recommendations(df, quality_score)
        }
    
    def _get_quality_recommendations(self, df: pd.DataFrame, quality_score: float) -> List[str]:
        """获取数据质量改进建议"""
        recommendations = []
        
        if quality_score < 80:
            recommendations.append("数据质量较低，建议进行数据清洗")
        
        missing_cols = df.columns[df.isnull().any()].tolist()
        if missing_cols:
            recommendations.append(f"列 {missing_cols} 存在缺失值，建议处理")
        
        if df.duplicated().any():
            recommendations.append("存在重复行，建议去重")
        
        # 检查异常值
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
            if len(outliers) > 0:
                recommendations.append(f"列 {col} 存在异常值，建议检查")
        
        return recommendations
    
    def clean_data(self, df: pd.DataFrame, options: Dict[str, Any] = None) -> pd.DataFrame:
        """清洗数据"""
        if options is None:
            options = {}
        
        cleaned_df = df.copy()
        
        # 处理缺失值
        if options.get('handle_missing', True):
            cleaned_df = self._handle_missing_values(cleaned_df, options.get('missing_strategy', 'drop'))
        
        # 处理重复值
        if options.get('remove_duplicates', True):
            cleaned_df = cleaned_df.drop_duplicates()
        
        # 处理异常值
        if options.get('handle_outliers', False):
            cleaned_df = self._handle_outliers(cleaned_df, options.get('outlier_strategy', 'clip'))
        
        # 数据类型转换
        if options.get('convert_dtypes', True):
            cleaned_df = self._convert_dtypes(cleaned_df)
        
        return cleaned_df
    
    def _handle_missing_values(self, df: pd.DataFrame, strategy: str = 'drop') -> pd.DataFrame:
        """处理缺失值"""
        if strategy == 'drop':
            return df.dropna()
        elif strategy == 'fill_numeric':
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            df[categorical_cols] = df[categorical_cols].fillna('Unknown')
            return df
        elif strategy == 'fill_mode':
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown')
                else:
                    df[col] = df[col].fillna(df[col].median())
            return df
        else:
            return df
    
    def _handle_outliers(self, df: pd.DataFrame, strategy: str = 'clip') -> pd.DataFrame:
        """处理异常值"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            if strategy == 'clip':
                df[col] = df[col].clip(lower_bound, upper_bound)
            elif strategy == 'remove':
                df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
        
        return df
    
    def _convert_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """转换数据类型"""
        # 尝试转换数值列
        for col in df.columns:
            if df[col].dtype == 'object':
                # 尝试转换为数值
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
                
                # 尝试转换为日期时间
                if df[col].dtype == 'object':
                    try:
                        df[col] = pd.to_datetime(df[col], errors='ignore')
                    except:
                        pass
        
        return df
    
    def prepare_for_synthesis(self, df: pd.DataFrame, target_columns: List[str] = None) -> pd.DataFrame:
        """为合成数据生成准备数据"""
        prepared_df = df.copy()
        
        # 选择目标列
        if target_columns:
            prepared_df = prepared_df[target_columns]
        
        # 处理分类变量
        categorical_cols = prepared_df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            # 编码分类变量
            prepared_df[col] = pd.Categorical(prepared_df[col]).codes
        
        # 处理日期时间变量
        datetime_cols = prepared_df.select_dtypes(include=['datetime64']).columns
        for col in datetime_cols:
            # 转换为时间戳
            prepared_df[col] = prepared_df[col].astype('int64') // 10**9
        
        return prepared_df
    
    def post_process_synthetic(self, synthetic_df: pd.DataFrame, original_df: pd.DataFrame) -> pd.DataFrame:
        """后处理合成数据"""
        processed_df = synthetic_df.copy()
        
        # 恢复分类变量
        categorical_cols = original_df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            if col in processed_df.columns:
                # 获取原始分类值
                original_categories = original_df[col].cat.categories if hasattr(original_df[col], 'cat') else original_df[col].unique()
                # 映射回原始值
                processed_df[col] = processed_df[col].map(lambda x: original_categories[int(x)] if 0 <= int(x) < len(original_categories) else 'Unknown')
        
        # 恢复日期时间变量
        datetime_cols = original_df.select_dtypes(include=['datetime64']).columns
        for col in datetime_cols:
            if col in processed_df.columns:
                # 转换回日期时间
                processed_df[col] = pd.to_datetime(processed_df[col], unit='s')
        
        return processed_df
    
    def validate_synthetic_data(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Dict[str, Any]:
        """验证合成数据质量"""
        validation_results = {
            'shape_match': original_df.shape[1] == synthetic_df.shape[1],
            'column_match': set(original_df.columns) == set(synthetic_df.columns),
            'dtype_match': {},
            'statistical_similarity': {},
            'overall_score': 0
        }
        
        # 检查数据类型匹配
        for col in original_df.columns:
            if col in synthetic_df.columns:
                validation_results['dtype_match'][col] = original_df[col].dtype == synthetic_df[col].dtype
        
        # 计算统计相似性
        numeric_cols = original_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in synthetic_df.columns:
                orig_mean = original_df[col].mean()
                synth_mean = synthetic_df[col].mean()
                orig_std = original_df[col].std()
                synth_std = synthetic_df[col].std()
                
                mean_diff = abs(orig_mean - synth_mean) / abs(orig_mean) * 100 if orig_mean != 0 else 0
                std_diff = abs(orig_std - synth_std) / abs(orig_std) * 100 if orig_std != 0 else 0
                
                validation_results['statistical_similarity'][col] = {
                    'mean_diff_percent': mean_diff,
                    'std_diff_percent': std_diff,
                    'similarity_score': max(0, 100 - (mean_diff + std_diff) / 2)
                }
        
        # 计算总体质量分数
        if validation_results['statistical_similarity']:
            scores = [stats['similarity_score'] for stats in validation_results['statistical_similarity'].values()]
            validation_results['overall_score'] = np.mean(scores)
        
        return validation_results
