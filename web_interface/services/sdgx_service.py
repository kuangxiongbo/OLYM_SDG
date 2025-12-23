#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDGX服务
职责：封装SDGX的标准流程，完全按照SDGX示例代码实现
"""

import os
import pandas as pd
from typing import Optional, Any
from pathlib import Path
import sys
from config import Config

# 导入SDGX组件
sys.path.append(Config.SDGX_PATH)
try:
    from sdgx.data_connectors.csv_connector import CsvConnector
    from sdgx.data_connectors.dataframe_connector import DataFrameConnector
    from sdgx.data_loader import DataLoader
    from sdgx.data_models.metadata import Metadata
    from sdgx.synthesizer import Synthesizer
    SDGX_AVAILABLE = True
except ImportError:
    SDGX_AVAILABLE = False
    print("⚠️ SDGX组件导入失败")


class SDGXService:
    """SDGX服务 - 完全按照SDGX示例代码实现"""
    
    def __init__(self):
        """初始化SDGX服务"""
        if not SDGX_AVAILABLE:
            raise ImportError("SDGX组件不可用，请检查SDGX_PATH配置和依赖安装")
    
    def create_connector(self, source: Any, task_id: Optional[str] = None) -> Any:
        """
        创建DataConnector
        
        完全按照SDGX示例代码：
        - 如果是CSV文件路径，使用CsvConnector
        - 如果是DataFrame，使用DataFrameConnector
        
        注意：在创建连接器之前，数据应该已经通过DataPreparationService.fix_critical_issues()修复
        
        Args:
            source: 数据源（文件路径或DataFrame）
            task_id: 任务ID（用于日志）
            
        Returns:
            DataConnector (CsvConnector 或 DataFrameConnector)
        """
        log_prefix = f"任务 {task_id}: " if task_id else "[SDGXService] "
        
        # 如果是文件路径，使用CsvConnector（完全按照SDGX示例）
        if isinstance(source, (str, Path)):
            file_path = str(source)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            print(f"{log_prefix}[create_connector] 使用CsvConnector（完全按照SDGX示例）: {file_path}")
            print(f"{log_prefix}[create_connector] ⚠️ 注意：CsvConnector直接读取源文件，确保源文件已通过DataPreparationService修复")
            return CsvConnector(path=Path(file_path))
        
        # 如果是DataFrame，使用DataFrameConnector（完全按照SDGX示例）
        elif isinstance(source, pd.DataFrame):
            print(f"{log_prefix}[create_connector] 使用DataFrameConnector（完全按照SDGX示例）: {source.shape[0]} 行 × {source.shape[1]} 列")
            
            # 最后检查：确保DataFrame中没有被连接的日期时间值（双重保险）
            # 这应该在DataPreparationService中已经完成，但这里作为最后一道防线
            from .data_validator import DataValidator
            date_columns = DataValidator.identify_date_columns(source)
            if date_columns:
                print(f"{log_prefix}[create_connector] 识别到 {len(date_columns)} 个日期列: {list(date_columns)}")
                has_issue = False
                for col in date_columns:
                    if col in source.columns:
                        # 检查长度超过30的值（可能是被连接的日期时间）
                        long_values = source[col].apply(lambda x: len(str(x).strip()) > 30)
                        # 检查是否是YYYYMMDD格式被连接（纯数字且长度>=16，至少2个8位日期）
                        compact_format_values = source[col].apply(lambda x: len(str(x).strip()) >= 16 and str(x).strip().isdigit())
                        
                        if long_values.any() or compact_format_values.any():
                            has_issue = True
                            long_count = long_values.sum() if long_values.any() else 0
                            compact_count = compact_format_values.sum() if compact_format_values.any() else 0
                            print(f"{log_prefix}[create_connector] ⚠️ 警告: 在创建连接器前发现日期列 {col} 仍有问题（长度>30: {long_count}, YYYYMMDD格式: {compact_count}），立即修复...")
                            
                            # 先检查前5个值，确认问题
                            sample_values = source[col].head(5).tolist()
                            print(f"{log_prefix}[create_connector] 日期列 {col} 前5个值: {[str(v)[:50] for v in sample_values]}")
                            
                            # 使用fix_date_columns修复整个列
                            source = DataValidator.fix_date_columns(source, {col}, task_id)
                            print(f"{log_prefix}[create_connector] ✅ 日期列 {col} 已修复")
                            
                            # 验证修复结果
                            sample_after = source[col].head(5).tolist()
                            print(f"{log_prefix}[create_connector] 修复后前5个值: {[str(v)[:50] for v in sample_after]}")
                            
                            # 再次检查是否还有问题
                            long_values_after = source[col].apply(lambda x: len(str(x).strip()) > 30)
                            compact_format_values_after = source[col].apply(lambda x: len(str(x).strip()) >= 16 and str(x).strip().isdigit())
                            if long_values_after.any() or compact_format_values_after.any():
                                print(f"{log_prefix}[create_connector] ⚠️ 警告: 日期列 {col} 修复后仍有问题，进行逐行修复...")
                                # 逐行修复
                                for idx in source.index:
                                    val = str(source.at[idx, col]).strip()
                                    # YYYYMMDD格式被连接（必须长度>=16，至少2个8位日期）
                                    if len(val) >= 16 and val.isdigit():
                                        import re
                                        date_matches = re.findall(r'\d{8}', val)
                                        if len(date_matches) > 1:
                                            first_date = date_matches[0]
                                            if len(first_date) == 8:
                                                year = first_date[:4]
                                                month = first_date[4:6]
                                                day = first_date[6:8]
                                                source.at[idx, col] = f"{year}-{month}-{day}"
                                                continue
                                    # 长度超过30的被连接日期时间
                                    if len(val) > 30:
                                        # 使用fix_date_value修复
                                        fixed_val = DataValidator.fix_date_value(val)
                                        if fixed_val != val:
                                            source.at[idx, col] = fixed_val
                                print(f"{log_prefix}[create_connector] ✅ 日期列 {col} 逐行修复完成")
                
                if has_issue:
                    print(f"{log_prefix}[create_connector] ⚠️ 在创建连接器前进行了最后的日期列修复（双重保险）")
                else:
                    print(f"{log_prefix}[create_connector] ✅ 所有日期列检查通过，无需修复")
            
            return DataFrameConnector(df=source)
        
        else:
            raise ValueError(f"不支持的数据源类型: {type(source)}")
    
    def create_metadata(self, data_connector: Any, task_id: Optional[str] = None) -> Metadata:
        """
        创建Metadata（使用SDGX自动识别）
        
        完全按照SDGX示例代码：
        1. 创建DataLoader
        2. 调用Metadata.from_dataloader()
        
        Args:
            data_connector: DataConnector实例
            task_id: 任务ID（用于日志）
            
        Returns:
            Metadata实例
        """
        log_prefix = f"任务 {task_id}: " if task_id else "[SDGXService] "
        
        print(f"{log_prefix}[create_metadata] 创建DataLoader（完全按照SDGX示例）...")
        data_loader = DataLoader(data_connector)
        
        # #region agent log
        # 检查DataLoader实际读取的数据
        import json
        try:
            for i, chunk in enumerate(data_loader.iter()):
                if i == 0:  # 只检查第一个chunk
                    from .data_validator import DataValidator
                    date_cols = DataValidator.identify_date_columns(chunk)
                    for col in date_cols:
                        if col in chunk.columns:
                            all_values = chunk[col].astype(str).tolist()
                            problematic_values = [v for v in all_values if len(str(v).strip()) >= 16 and str(v).strip().isdigit() or len(str(v).strip()) > 30]
                            with open('/Users/kuangxb/Desktop/AI 生成数据 SDG /.cursor/debug.log', 'a') as f:
                                f.write(json.dumps({
                                    'sessionId': 'debug-session',
                                    'runId': 'run1',
                                    'hypothesisId': 'F',
                                    'location': 'sdgx_service.py:178',
                                    'message': 'DataLoader first chunk - FULL CHECK',
                                    'data': {
                                        'column': col,
                                        'chunk_index': i,
                                        'chunk_rows': len(all_values),
                                        'problematic_count': len(problematic_values),
                                        'problematic_samples': [str(v)[:100] for v in problematic_values[:3]] if problematic_values else []
                                    },
                                    'timestamp': int(__import__('time').time() * 1000)
                                }) + '\n')
                    break  # 只检查第一个chunk
        except Exception as e:
            with open('/Users/kuangxb/Desktop/AI 生成数据 SDG /.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'F',
                    'location': 'sdgx_service.py:178',
                    'message': 'Error checking DataLoader chunks',
                    'data': {'error': str(e)},
                    'timestamp': int(__import__('time').time() * 1000)
                }) + '\n')
        # #endregion
        
        print(f"{log_prefix}[create_metadata] 调用Metadata.from_dataloader()自动识别字段类型（完全按照SDGX示例）...")
        metadata = Metadata.from_dataloader(data_loader)
        
        print(f"{log_prefix}[create_metadata] ✅ Metadata创建成功，字段数量: {len(metadata.column_list)}")
        print(f"{log_prefix}[create_metadata] 识别的字段类型:")
        print(f"{log_prefix}[create_metadata]   - ID列: {len(metadata.id_columns)}")
        print(f"{log_prefix}[create_metadata]   - 整数列: {len(metadata.int_columns)}")
        print(f"{log_prefix}[create_metadata]   - 浮点数列: {len(metadata.float_columns)}")
        print(f"{log_prefix}[create_metadata]   - 日期时间列: {len(metadata.datetime_columns)}")
        print(f"{log_prefix}[create_metadata]   - 离散列: {len(metadata.discrete_columns)}")
        
        # 为所有日期时间列设置datetime_format，防止DatetimeFormatter移除这些列
        # 根据SDGX文档，datetime_format必须完全对应datetime_columns，否则列会被删除
        if len(metadata.datetime_columns) > 0:
            print(f"{log_prefix}[create_metadata] 为 {len(metadata.datetime_columns)} 个日期时间列设置格式...")
            from .data_validator import DataValidator
            from datetime import datetime
            
            # 获取DataFrame以检测日期格式
            if hasattr(data_connector, 'df'):
                df_for_format_detection = data_connector.df
            else:
                # 如果connector没有df属性，从DataLoader读取第一个chunk
                try:
                    df_for_format_detection = next(data_loader.iter())
                except:
                    df_for_format_detection = None
            
            # 验证并过滤：只保留真正可以解析为日期时间的列
            valid_datetime_columns = []
            invalid_datetime_columns = []
            
            for col in metadata.datetime_columns:
                if col not in metadata.column_list:
                    invalid_datetime_columns.append(col)
                    continue
                
                # 检测日期格式
                datetime_format = '%Y-%m-%d %H:%M:%S'  # 默认格式
                if df_for_format_detection is not None and col in df_for_format_detection.columns:
                    # 检查实际数据格式
                    sample_values = df_for_format_detection[col].dropna().head(10)
                    if len(sample_values) == 0:
                        # 如果列全部为空，不应该被识别为日期时间列
                        invalid_datetime_columns.append(col)
                        print(f"{log_prefix}[create_metadata]   ⚠️ 列 {col} 全部为空，从日期时间列中移除")
                        continue
                    
                    # 尝试检测格式并验证是否可以解析
                    sample_val = str(sample_values.iloc[0]).strip()
                    # 检测常见格式（按优先级顺序）
                    if len(sample_val) == 8 and sample_val.isdigit():
                        # 格式如 "20250401"
                        datetime_format = '%Y%m%d'
                    elif '/' in sample_val and ':' in sample_val:
                        # 格式如 "2025/4/1 9:28" 或 "2025/4/1 9:28:00"
                        if sample_val.count(':') == 1:
                            datetime_format = '%Y/%m/%d %H:%M'
                        else:
                            datetime_format = '%Y/%m/%d %H:%M:%S'
                    elif '-' in sample_val and ':' in sample_val:
                        # 格式如 "2025-04-01 09:28:00"
                        datetime_format = '%Y-%m-%d %H:%M:%S'
                    elif '-' in sample_val and len(sample_val) == 10:
                        # 格式如 "2025-01-18"（只有日期，没有时间）
                        datetime_format = '%Y-%m-%d'
                    elif '/' in sample_val and len(sample_val) <= 10:
                        # 格式如 "2025/1/18" 或 "2025/01/18"（只有日期，没有时间）
                        datetime_format = '%Y/%m/%d'
                    else:
                        # 默认格式
                        datetime_format = '%Y-%m-%d %H:%M:%S'
                    
                    # 关键：验证是否可以解析 - 检查至少前5个值是否可以用该格式解析
                    parseable_count = 0
                    for val in sample_values.head(5):
                        try:
                            val_str = str(val).strip()
                            datetime.strptime(val_str, datetime_format)
                            parseable_count += 1
                        except:
                            pass
                    
                    # #region agent log - 记录验证结果（无论成功或失败）
                    with open('/Users/kuangxb/Desktop/AI 生成数据 SDG /.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            'sessionId': 'debug-session',
                            'runId': 'run1',
                            'hypothesisId': 'M',
                            'location': 'sdgx_service.py:create_metadata',
                            'message': 'Datetime column validation',
                            'data': {
                                'column': col,
                                'format': datetime_format,
                                'sample_value': sample_val[:100],
                                'parseable_count': parseable_count,
                                'total_samples': len(sample_values.head(5)),
                                'is_valid': parseable_count > 0,
                                'sample_values_list': [str(v)[:50] for v in sample_values.head(5).tolist()]
                            },
                            'timestamp': int(__import__('time').time() * 1000)
                        }) + '\n')
                    # #endregion
                    
                    # 如果前5个值中没有一个可以解析，说明这不是日期时间列
                    if parseable_count == 0:
                        invalid_datetime_columns.append(col)
                        print(f"{log_prefix}[create_metadata]   ⚠️ 列 {col} 的值无法用日期时间格式解析（样本值: {sample_val[:50]}...，格式: {datetime_format}），从日期时间列中移除")
                        continue
                
                # 如果通过验证，添加到有效日期时间列列表
                valid_datetime_columns.append(col)
                # 直接赋值给metadata.datetime_format（根据SDGX示例代码）
                metadata.datetime_format[col] = datetime_format
                print(f"{log_prefix}[create_metadata]   ✅ 设置 {col} 的格式为: {datetime_format}")
            
            # 从metadata中移除无效的日期时间列
            if invalid_datetime_columns:
                print(f"{log_prefix}[create_metadata] ⚠️ 发现 {len(invalid_datetime_columns)} 个被错误识别为日期时间的列，正在移除...")
                for col in invalid_datetime_columns:
                    # 从datetime_columns中移除
                    if col in metadata.datetime_columns:
                        metadata.datetime_columns.remove(col)
                    # 从datetime_format中移除
                    if col in metadata.datetime_format:
                        del metadata.datetime_format[col]
                    print(f"{log_prefix}[create_metadata]   ✅ 已移除 {col}")
                
                print(f"{log_prefix}[create_metadata] ✅ 日期时间列验证完成，有效列数: {len(valid_datetime_columns)}，移除列数: {len(invalid_datetime_columns)}")
        
        return metadata
    
    def create_synthesizer(self, metadata: Metadata, model: Any, 
                          data_connector: Any, task_id: Optional[str] = None) -> Synthesizer:
        """
        创建Synthesizer
        
        完全按照SDGX示例代码：
        synthesizer = Synthesizer(
            metadata=metadata,
            model=model,
            data_connector=data_connector
        )
        
        Args:
            metadata: Metadata实例
            model: 模型实例（如CTGANSynthesizerModel）
            data_connector: DataConnector实例
            task_id: 任务ID（用于日志）
            
        Returns:
            Synthesizer实例
        """
        log_prefix = f"任务 {task_id}: " if task_id else "[SDGXService] "
        
        print(f"{log_prefix}[create_synthesizer] 创建Synthesizer（完全按照SDGX示例）...")
        synthesizer = Synthesizer(
            metadata=metadata,
            model=model,
            data_connector=data_connector
        )
        print(f"{log_prefix}[create_synthesizer] ✅ Synthesizer创建成功")
        
        return synthesizer
    
    def train(self, synthesizer: Synthesizer, task_id: Optional[str] = None):
        """
        训练模型
        
        完全按照SDGX示例代码：
        synthesizer.fit()
        
        Args:
            synthesizer: Synthesizer实例
            task_id: 任务ID（用于日志）
            
        Raises:
            ValueError: 如果训练失败
        """
        log_prefix = f"任务 {task_id}: " if task_id else "[SDGXService] "
        
        print(f"{log_prefix}[train] 开始训练模型（完全按照SDGX示例）...")
        # #region agent log
        import json
        try:
            # 检查DataFrameConnector中的数据
            if hasattr(synthesizer, 'data_connector') and hasattr(synthesizer.data_connector, 'df'):
                df_in_connector = synthesizer.data_connector.df
                from .data_validator import DataValidator
                date_cols = DataValidator.identify_date_columns(df_in_connector)
                for col in date_cols:
                    if col in df_in_connector.columns:
                        sample_values = df_in_connector[col].head(5).tolist()
                        with open('/Users/kuangxb/Desktop/AI 生成数据 SDG /.cursor/debug.log', 'a') as f:
                            f.write(json.dumps({
                                'sessionId': 'debug-session',
                                'runId': 'run1',
                                'hypothesisId': 'D',
                                'location': 'sdgx_service.py:224',
                                'message': 'DataFrame in connector before fit',
                                'data': {'column': col, 'samples': [str(v)[:100] for v in sample_values[:3]], 'has_issue': any(len(str(v).strip()) >= 16 and str(v).strip().isdigit() or len(str(v).strip()) > 30 for v in sample_values)},
                                'timestamp': int(__import__('time').time() * 1000)
                            }) + '\n')
        except Exception as e:
            pass
        # #endregion
        try:
            synthesizer.fit()
            print(f"{log_prefix}[train] ✅ 模型训练完成")
        except Exception as e:
            error_msg = f"模型训练失败: {str(e)}"
            print(f"{log_prefix}[train] ❌ {error_msg}")
            import traceback
            error_trace = traceback.format_exc()
            print(f"{log_prefix}[train] 详细错误堆栈:\n{error_trace}")
            raise ValueError(error_msg) from e
    
    def generate(self, synthesizer: Synthesizer, count: int, 
                task_id: Optional[str] = None, progress_callback=None) -> pd.DataFrame:
        """
        生成数据
        
        完全按照SDGX示例代码：
        synthetic_data = synthesizer.sample(count)
        
        Args:
            synthesizer: Synthesizer实例
            count: 生成数量
            task_id: 任务ID（用于日志）
            progress_callback: 进度回调函数，接收(progress, message)参数
            
        Returns:
            合成数据DataFrame
            
        Raises:
            ValueError: 如果生成失败
        """
        log_prefix = f"任务 {task_id}: " if task_id else "[SDGXService] "
        
        print(f"{log_prefix}[generate] 开始生成 {count} 条合成数据（完全按照SDGX示例）...")
        
        # 检查是否是AI模型（SingleTableGPTModel）
        is_ai_model = False
        try:
            from sdgx.models.LLM.single_table.gpt import SingleTableGPTModel
            if hasattr(synthesizer, 'model') and isinstance(synthesizer.model, SingleTableGPTModel):
                is_ai_model = True
                print(f"{log_prefix}[generate] 检测到AI模型，将使用带超时的生成方式")
        except ImportError:
            pass
        
        try:
            if is_ai_model and progress_callback:
                # 对于AI模型，使用带超时的生成方式
                import signal
                import threading
                
                synthetic_data = None
                error_occurred = [False]
                error_message = [None]
                
                def generate_with_timeout():
                    nonlocal synthetic_data
                    try:
                        # 更新进度：开始生成第一批数据
                        print(f"{log_prefix}[generate] AI模型开始生成数据，目标数量: {count}")
                        if progress_callback:
                            progress_callback(72, f"正在生成数据（AI模型，共需生成{count}条）...")
                        
                        # 记录开始时间
                        import time
                        start_time = time.time()
                        print(f"{log_prefix}[generate] 开始调用 synthesizer.sample({count})...")
                        
                        synthetic_data = synthesizer.sample(count)
                        
                        # #region agent log
                        try:
                            import json
                            import os
                            if synthetic_data is not None and hasattr(synthetic_data, 'columns'):
                                log_data = {
                                    'sessionId': 'debug-session',
                                    'runId': 'run1',
                                    'hypothesisId': 'D',
                                    'location': 'sdgx_service.py:477',
                                    'message': 'synthesizer.sample()返回后检查DataFrame',
                                    'data': {
                                        'df_shape': list(synthetic_data.shape),
                                        'df_columns': list(synthetic_data.columns),
                                        'df_columns_len': len(synthetic_data.columns),
                                        'unique_columns_len': len(set(synthetic_data.columns)),
                                        'has_duplicate_columns': len(synthetic_data.columns) != len(set(synthetic_data.columns)),
                                        'duplicate_columns': [col for col in set(synthetic_data.columns) if list(synthetic_data.columns).count(col) > 1] if len(synthetic_data.columns) != len(set(synthetic_data.columns)) else [],
                                        'df_index_duplicated': synthetic_data.index.duplicated().tolist() if hasattr(synthetic_data.index, 'duplicated') else None,
                                        'has_duplicate_index': synthetic_data.index.duplicated().any() if hasattr(synthetic_data.index, 'duplicated') else None
                                    },
                                    'timestamp': int(__import__('time').time() * 1000)
                                }
                                with open('/Users/kuangxb/Desktop/AI 生成数据 SDG /.cursor/debug.log', 'a') as f:
                                    f.write(json.dumps(log_data) + '\n')
                        except Exception as e:
                            pass
                        # #endregion
                        
                        elapsed_time = time.time() - start_time
                        print(f"{log_prefix}[generate] synthesizer.sample() 完成，耗时: {elapsed_time:.2f}秒")
                        
                        # 修复重复列名问题（在返回前修复，避免后续reindex失败）
                        if synthetic_data is not None and hasattr(synthetic_data, 'columns'):
                            if len(synthetic_data.columns) != len(set(synthetic_data.columns)):
                                # 有重复列名，保留第一个出现的列，删除后续重复的
                                seen = {}
                                cols_to_drop = []
                                for idx, col in enumerate(synthetic_data.columns):
                                    if col in seen:
                                        cols_to_drop.append(idx)
                                    else:
                                        seen[col] = idx
                                
                                # 从后往前删除，避免索引变化
                                for idx in reversed(cols_to_drop):
                                    synthetic_data = synthetic_data.drop(synthetic_data.columns[idx], axis=1)
                                
                                duplicate_cols = [col for col in set(synthetic_data.columns) if list(synthetic_data.columns).count(col) > 1]
                                print(f"{log_prefix}[generate] ⚠️ 检测到重复列名，已删除重复列: {duplicate_cols}")
                        
                        # 更新进度：生成完成
                        if progress_callback:
                            progress_callback(85, "数据生成完成，正在处理...")
                    except Exception as e:
                        error_occurred[0] = True
                        error_message[0] = str(e)
                        import traceback
                        print(f"{log_prefix}[generate] 生成线程中发生异常: {str(e)}")
                        print(f"{log_prefix}[generate] 异常堆栈:\n{traceback.format_exc()}")
                
                # 使用线程执行生成，避免阻塞
                generate_thread = threading.Thread(target=generate_with_timeout)
                generate_thread.daemon = True
                generate_thread.start()
                
                # 等待生成完成，最多等待30分钟（AI模型生成可能需要较长时间）
                max_wait_time = 30 * 60  # 30分钟
                print(f"{log_prefix}[generate] 等待生成完成，超时时间: {max_wait_time//60}分钟")
                generate_thread.join(timeout=max_wait_time)
                
                if generate_thread.is_alive():
                    error_msg = f"数据生成超时（超过{max_wait_time//60}分钟），可能是AI模型API调用卡住或响应过慢"
                    print(f"{log_prefix}[generate] ❌ {error_msg}")
                    print(f"{log_prefix}[generate] 提示: 请检查AI模型服务是否正常，网络连接是否稳定")
                    raise ValueError(error_msg)
                
                if error_occurred[0]:
                    raise ValueError(error_message[0])
                
                if synthetic_data is None:
                    raise ValueError("数据生成失败：未返回数据")
                
                # 修复重复列名问题（在返回前修复，避免后续reindex失败）
                if synthetic_data is not None and hasattr(synthetic_data, 'columns'):
                    if len(synthetic_data.columns) != len(set(synthetic_data.columns)):
                        # 有重复列名，保留第一个出现的列，删除后续重复的
                        seen = {}
                        cols_to_drop = []
                        for idx, col in enumerate(synthetic_data.columns):
                            if col in seen:
                                cols_to_drop.append(idx)
                            else:
                                seen[col] = idx
                        
                        # 从后往前删除，避免索引变化
                        for idx in reversed(cols_to_drop):
                            synthetic_data = synthetic_data.drop(synthetic_data.columns[idx], axis=1)
                        
                        duplicate_cols = [col for col in set(synthetic_data.columns) if list(synthetic_data.columns).count(col) > 1]
                        print(f"{log_prefix}[generate] ⚠️ 检测到重复列名，已删除重复列: {duplicate_cols}")
            
            else:
                # 非AI模型或没有进度回调，直接生成
                synthetic_data = synthesizer.sample(count)
                
                # 修复重复列名问题（在返回前修复，避免后续reindex失败）
                if synthetic_data is not None and hasattr(synthetic_data, 'columns'):
                    if len(synthetic_data.columns) != len(set(synthetic_data.columns)):
                        # 有重复列名，保留第一个出现的列，删除后续重复的
                        seen = {}
                        cols_to_drop = []
                        for idx, col in enumerate(synthetic_data.columns):
                            if col in seen:
                                cols_to_drop.append(idx)
                            else:
                                seen[col] = idx
                        
                        # 从后往前删除，避免索引变化
                        for idx in reversed(cols_to_drop):
                            synthetic_data = synthetic_data.drop(synthetic_data.columns[idx], axis=1)
                        
                        duplicate_cols = [col for col in set(synthetic_data.columns) if list(synthetic_data.columns).count(col) > 1]
                        print(f"{log_prefix}[generate] ⚠️ 检测到重复列名，已删除重复列: {duplicate_cols}")
            
            print(f"{log_prefix}[generate] ✅ 数据生成完成，共 {len(synthetic_data)} 行")
            return synthetic_data
            
        except Exception as e:
            error_msg = f"数据生成失败: {str(e)}"
            print(f"{log_prefix}[generate] ❌ {error_msg}")
            import traceback
            error_trace = traceback.format_exc()
            print(f"{log_prefix}[generate] 详细错误堆栈:\n{error_trace}")
            raise ValueError(error_msg) from e

