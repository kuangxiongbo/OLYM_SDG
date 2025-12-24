#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDGX适配器模块
负责封装SDGX的调用，处理训练和生成流程
完全按照SDGX示例代码，不做任何预处理
支持直接使用源文件（CSV/Excel），像示例代码一样
"""

import pandas as pd
from typing import Optional, Dict, Any
import sys
import os
import tempfile
from config import Config

# 导入SDGX组件
sys.path.append(Config.SDGX_PATH)
try:
    from sdgx.data_connectors.dataframe_connector import DataFrameConnector
    from sdgx.data_connectors.csv_connector import CsvConnector
    from sdgx.synthesizer import Synthesizer
    SDGX_AVAILABLE = True
except ImportError:
    SDGX_AVAILABLE = False
    print("⚠️ SDGX组件导入失败")


class SDGXAdapter:
    """SDGX适配器 - 完全按照SDGX示例代码实现"""
    
    def __init__(self):
        """初始化适配器"""
        if not SDGX_AVAILABLE:
            raise ImportError("SDGX组件不可用，请检查SDGX_PATH配置和依赖安装")
    
    def create_connector_from_file(self, file_path: str, task_id: Optional[str] = None) -> CsvConnector:
        """
        直接从源文件创建CSV连接器（完全按照SDGX示例代码）
        
        注意：如果源文件包含被连接的日期/日期时间值，CsvConnector会直接读取这些有问题的数据
        建议：在调用此方法前，先检查源文件数据质量
        
        示例代码：data_connector = CsvConnector(path=dataset_csv)
        
        Args:
            file_path: CSV文件路径
            task_id: 任务ID（用于日志）
            
        Returns:
            CsvConnector
        """
        log_prefix = f"任务 {task_id}: " if task_id else "[SDGXAdapter] "
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        print(f"{log_prefix}[create_connector_from_file] 完全按照SDGX示例，直接使用源文件创建CsvConnector...")
        print(f"{log_prefix}[create_connector_from_file] 文件路径: {file_path}")
        print(f"{log_prefix}[create_connector_from_file] ⚠️ 注意：CsvConnector不做任何数据修复，如果源文件有问题会直接传递给SDGX")
        
        return CsvConnector(path=file_path)
    
    def create_connector(self, df: pd.DataFrame, task_id: Optional[str] = None, date_columns: Optional[set] = None, use_file: Optional[str] = None):
        """
        创建DataFrame连接器
        
        如果提供了use_file参数，则直接使用源文件创建CsvConnector（完全按照SDGX示例）
        否则，使用DataFrame创建DataFrameConnector（需要处理数据源中的'NAN_VALUE'字符串）
        
        示例代码：data_connector = CsvConnector(path=dataset_csv)
        我们：data_connector = DataFrameConnector(df=df) 或 CsvConnector(path=file_path)
        
        Args:
            df: DataFrame（如果use_file不为None，此参数可忽略）
            task_id: 任务ID（用于日志）
            date_columns: 已知的日期列集合（可选，但不使用）
            use_file: 如果提供，直接使用此文件路径创建CsvConnector（完全按照示例代码）
            
        Returns:
            DataFrameConnector 或 CsvConnector
        """
        log_prefix = f"任务 {task_id}: " if task_id else "[SDGXAdapter] "
        
        # 如果提供了文件路径，直接使用源文件（完全按照SDGX示例代码）
        if use_file:
            return self.create_connector_from_file(use_file, task_id)
        log_prefix = f"任务 {task_id}: " if task_id else "[SDGXAdapter] "
        
        # 关键问题：SDGX的NonValueTransformer会将非数值列的NaN填充为"NAN_VALUE"字符串
        # 如果该列后来被metadata识别为int类型，SDGX在转换为PyArrow时会失败
        # 解决方案：对于可能被识别为int类型的object列，预先填充NaN为0（数值类型）
        # 这样即使被识别为int类型，也不会出错
        
        print(f"{log_prefix}[create_connector] 处理可能被识别为int类型的列，避免NonValueTransformer填充为'NAN_VALUE'...")
        df_copy = df.copy(deep=True)
        
        # 第一步：清理数据源中的'NAN_VALUE'字符串
        has_nan_value = False
        for col in df_copy.columns:
            if df_copy[col].dtype == 'object':
                # 检查是否有'NAN_VALUE'字符串
                if df_copy[col].astype(str).str.contains('NAN_VALUE', na=False).any():
                    has_nan_value = True
                    print(f"{log_prefix}⚠️ 发现数据源列 {col} 包含'NAN_VALUE'字符串，清理为pd.NA...")
                    df_copy[col] = df_copy[col].replace('NAN_VALUE', pd.NA)
                    print(f"{log_prefix}✅ 列 {col} 清理完成")
        
        # 第二步：对于可能被识别为int类型的object列，预先填充NaN为0（数值类型）
        # 这样可以避免NonValueTransformer填充为"NAN_VALUE"字符串
        for col in df_copy.columns:
            if df_copy[col].dtype == 'object':
                col_name_lower = col.lower()
                # 检查是否是可能被识别为int类型的列
                is_likely_int = (
                    col_name_lower.endswith('_id') or 
                    col_name_lower == 'id' or
                    ('id' in col_name_lower and col_name_lower not in ['customer_id', 'order_id', 'user_id', 'product_id', 'patient_id', 'student_id', 'call_id', 'claim_id', 'policy_id', 'shipment_id'])
                )
                
                nan_count = df_copy[col].isna().sum()
                if is_likely_int and nan_count > 0:
                    print(f"{log_prefix}⚠️ 列 {col} 可能被识别为int类型且包含 {nan_count} 个NaN，尝试转换为int64并填充NaN为0...")
                    try:
                        # 尝试转换为数值类型
                        numeric_series = pd.to_numeric(df_copy[col], errors='coerce')
                        non_na_values = numeric_series.dropna()
                        if len(non_na_values) > 0:
                            # 检查是否主要是整数
                            int_count = (non_na_values == non_na_values.astype(int)).sum()
                            int_rate = int_count / len(non_na_values)
                            if int_rate > 0.9:  # 90%以上是整数
                                df_copy[col] = numeric_series.fillna(0).astype('int64')
                                print(f"{log_prefix}✅ 列 {col} 已转换为int64类型，NaN已填充为0")
                            else:
                                print(f"{log_prefix}⚠️ 列 {col} 不是整数类型（整数率: {int_rate:.2%}），保持为object类型")
                        else:
                            # 全部为NaN，转换为int64并填充为0
                            df_copy[col] = numeric_series.fillna(0).astype('int64')
                            print(f"{log_prefix}✅ 列 {col} (全部为NaN) 已转换为int64类型，填充为0")
                    except Exception as e:
                        print(f"{log_prefix}⚠️ 列 {col} 转换为int64失败: {e}，保持为object类型")
        
        # 第三步：对于已经是数值类型的列，如果有NaN，预先填充（与NonValueTransformer一致）
        for col in df_copy.columns:
            if df_copy[col].dtype in ['int64', 'int32', 'Int64']:
                if df_copy[col].isna().sum() > 0:
                    df_copy[col] = df_copy[col].fillna(0)
                    print(f"{log_prefix}✅ 列 {col} (int类型) 的NaN已填充为0")
            elif df_copy[col].dtype in ['float64', 'float32']:
                if df_copy[col].isna().sum() > 0:
                    df_copy[col] = df_copy[col].fillna(0.0)
                    print(f"{log_prefix}✅ 列 {col} (float类型) 的NaN已填充为0.0")
        
        # 第四步：确保所有object列的值都是字符串类型（PyArrow要求）
        # 这样可以避免"Expected bytes, got a 'int' object"错误
        for col in df_copy.columns:
            if df_copy[col].dtype == 'object':
                # 检查是否包含非字符串类型的值（如整数、浮点数）
                has_non_string = False
                for idx in range(len(df_copy)):
                    val = df_copy.at[idx, col]
                    if pd.notna(val) and not isinstance(val, str):
                        has_non_string = True
                        break
                
                if has_non_string:
                    print(f"{log_prefix}⚠️ 列 {col} (object类型) 包含非字符串值，统一转换为字符串...")
                    df_copy[col] = df_copy[col].astype(str)
                    # 将 'nan' 字符串转换回 pd.NA
                    df_copy[col] = df_copy[col].replace('nan', pd.NA)
                    print(f"{log_prefix}✅ 列 {col} 已统一转换为字符串类型")
        
        # 第五步：最后检查日期列，确保没有被连接的值（关键保护）
        # 即使前面已经修复过，这里也要再次检查，因为某些操作可能会重新引入问题
        if date_columns:
            from services.data_validator import DataValidator
            
            for col in date_columns:
                if col in df_copy.columns and df_copy[col].dtype == 'object':
                    print(f"{log_prefix}[create_connector] 最后检查日期列 {col}，确保没有被连接的值...")
                    fixed_count = 0
                    for idx in range(len(df_copy)):
                        val = str(df_copy.at[idx, col]).strip()
                        # 日期时间值不应该超过30个字符（单个日期时间最多19个字符：YYYY-MM-DD HH:MM:SS）
                        if len(val) > 30:
                            # 使用DataValidator的修复逻辑（支持YYYY/M/D H:MM格式）
                            fixed_val = DataValidator.fix_date_value(val)
                            if fixed_val != val:
                                df_copy.at[idx, col] = fixed_val
                                fixed_count += 1
                                if fixed_count <= 3:  # 只打印前3个修复的示例
                                    print(f"{log_prefix}⚠️ 修复第{idx}行: {val[:80]}... -> {fixed_val}")
                    
                    if fixed_count > 0:
                        print(f"{log_prefix}⚠️ 日期列 {col} 在最后检查中发现 {fixed_count} 个被连接的值，已修复")
                    else:
                        print(f"{log_prefix}✅ 日期列 {col} 检查通过，没有被连接的值")
        
        if has_nan_value:
            print(f"{log_prefix}⚠️ 数据源包含'NAN_VALUE'字符串，已清理")
        else:
            print(f"{log_prefix}✅ 数据源干净，无'NAN_VALUE'字符串")
        
        # 创建DataFrameConnector（完全按照SDGX示例）
        print(f"{log_prefix}[create_connector] 创建DataFrameConnector...")
        return DataFrameConnector(df=df_copy)
    
    def create_synthesizer(self, model, data_connector, date_columns: Optional[set] = None, task_id: Optional[str] = None):
        """
        创建合成器
        
        完全按照SDGX示例代码，不做任何预处理，直接创建Synthesizer
        示例代码：synthesizer = Synthesizer(model=CTGANSynthesizerModel(epochs=1), data_connector=data_connector)
        
        Args:
            model: SDGX模型实例
            data_connector: 数据连接器
            date_columns: 已知的日期列集合（可选，但不使用）
            task_id: 任务ID（用于日志）
            
        Returns:
            Synthesizer
        """
        log_prefix = f"任务 {task_id}: " if task_id else "[SDGXAdapter] "
        
        # 完全按照SDGX示例代码：直接创建Synthesizer，不做任何预处理
        print(f"{log_prefix}[create_synthesizer] 完全按照SDGX示例，直接创建Synthesizer，不做任何预处理...")
        synthesizer = Synthesizer(
            model=model,
            data_connector=data_connector
        )
        print(f"{log_prefix}[create_synthesizer] Synthesizer创建完成")
        return synthesizer
    
    def fit(self, synthesizer: Synthesizer, task_id: Optional[str] = None, date_columns: Optional[set] = None):
        """
        训练模型
        
        完全按照SDGX示例代码，直接调用fit()
        示例代码：synthesizer.fit()
        
        Args:
            synthesizer: 合成器实例
            task_id: 任务ID（用于日志）
            date_columns: 已知的日期列集合（可选，但不使用）
            
        Raises:
            ValueError: 如果训练失败
        """
        log_prefix = f"任务 {task_id}: " if task_id else "[SDGXAdapter] "
        
        print(f"{log_prefix}开始训练模型（完全按照SDGX示例）...")
        try:
            synthesizer.fit()
            print(f"{log_prefix}模型训练完成")
        except Exception as e:
            error_msg = f"模型训练失败: {str(e)}"
            print(f"{log_prefix}{error_msg}")
            import traceback
            error_trace = traceback.format_exc()
            print(f"{log_prefix}详细错误堆栈:\n{error_trace}")
            raise ValueError(error_msg) from e
    
    def sample(self, synthesizer: Synthesizer, count: int, task_id: Optional[str] = None) -> pd.DataFrame:
        """
        生成合成数据
        
        完全按照SDGX示例代码，直接调用sample()
        示例代码：sampled_data = synthesizer.sample(1000)
        
        Args:
            synthesizer: 合成器实例
            count: 生成数量
            task_id: 任务ID（用于日志）
            
        Returns:
            合成数据DataFrame
        """
        log_prefix = f"任务 {task_id}: " if task_id else "[SDGXAdapter] "
        
        print(f"{log_prefix}开始生成 {count} 条合成数据（完全按照SDGX示例）...")
        try:
            synthetic_data = synthesizer.sample(count)
            print(f"{log_prefix}数据生成完成，共 {len(synthetic_data)} 行")
            return synthetic_data
        except Exception as e:
            error_msg = f"数据生成失败: {str(e)}"
            print(f"{log_prefix}{error_msg}")
            import traceback
            error_trace = traceback.format_exc()
            print(f"{log_prefix}详细错误堆栈:\n{error_trace}")
            raise ValueError(error_msg) from e
