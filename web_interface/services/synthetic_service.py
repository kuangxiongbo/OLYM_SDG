#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合成数据生成服务
"""

import os
import sys
import re
import pandas as pd
import numpy as np
from datetime import datetime
from threading import Thread
from models.task import Task, db
from config import Config

# 导入SDGX组件
sys.path.append(Config.SDGX_PATH)
try:
    from sdgx.data_connectors.dataframe_connector import DataFrameConnector
    from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
    from sdgx.models.statistics.single_table.copula import GaussianCopulaSynthesizerModel
    from sdgx.models.LLM.single_table.gpt import SingleTableGPTModel
    from sdgx.synthesizer import Synthesizer
    from sdgx.data_models.metadata import Metadata
    SDGX_AVAILABLE = True
except ImportError:
    SDGX_AVAILABLE = False
    print("⚠️ SDGX组件导入失败，将使用模拟数据生成")

def similarity_to_parameters(similarity):
    """将相似度要求转换为具体的模型参数"""
    if similarity >= 0.8:
        return {'epochs': 200, 'batch_size': 200, 'generator_lr': 0.00015, 'discriminator_lr': 0.00015}
    elif similarity >= 0.6:
        return {'epochs': 100, 'batch_size': 300, 'generator_lr': 0.00022, 'discriminator_lr': 0.00022}
    else:
        return {'epochs': 50, 'batch_size': 500, 'generator_lr': 0.00025, 'discriminator_lr': 0.00025}

def create_sdgx_model(model_type, model_config=None, similarity=0.8):
    """
    创建SDGX模型
    
    Args:
        model_type: 模型类型 ('ctgan', 'gaussian_copula', 或 'ai_xxx')
        model_config: 模型配置字典，包含所有参数（如果提供，将优先使用）
        similarity: 相似度要求（仅在 model_config 未提供时使用）
    
    Returns:
        SDGX模型实例
    
    Raises:
        ValueError: 如果模型创建失败或配置不完整
    """
    if not SDGX_AVAILABLE:
        raise ValueError("SDGX组件不可用，请检查SDGX_PATH配置和依赖安装")
    
    try:
        if model_type == 'ctgan':
            # 如果提供了完整的模型配置，使用配置中的参数
            if model_config and isinstance(model_config, dict):
                # 构建CTGAN参数，只包含有效的参数
                ctgan_params = {}
                
                # 数值参数
                if 'epochs' in model_config:
                    ctgan_params['epochs'] = int(model_config['epochs'])
                if 'batch_size' in model_config:
                    batch_size = int(model_config['batch_size'])
                    # 确保batch_size是偶数（CTGAN要求）
                    if batch_size % 2 != 0:
                        batch_size += 1
                    ctgan_params['batch_size'] = batch_size
                if 'generator_lr' in model_config:
                    ctgan_params['generator_lr'] = float(model_config['generator_lr'])
                if 'discriminator_lr' in model_config:
                    ctgan_params['discriminator_lr'] = float(model_config['discriminator_lr'])
                if 'generator_decay' in model_config:
                    ctgan_params['generator_decay'] = float(model_config['generator_decay'])
                if 'discriminator_decay' in model_config:
                    ctgan_params['discriminator_decay'] = float(model_config['discriminator_decay'])
                if 'embedding_dim' in model_config:
                    ctgan_params['embedding_dim'] = int(model_config['embedding_dim'])
                if 'discriminator_steps' in model_config:
                    ctgan_params['discriminator_steps'] = int(model_config['discriminator_steps'])
                if 'pac' in model_config:
                    ctgan_params['pac'] = int(model_config['pac'])
                
                # 数组参数（需要转换为元组）
                if 'generator_dim' in model_config:
                    gen_dim = model_config['generator_dim']
                    if isinstance(gen_dim, list):
                        ctgan_params['generator_dim'] = tuple(gen_dim)
                    elif isinstance(gen_dim, str):
                        ctgan_params['generator_dim'] = tuple([int(x.strip()) for x in gen_dim.split(',') if x.strip()])
                
                if 'discriminator_dim' in model_config:
                    disc_dim = model_config['discriminator_dim']
                    if isinstance(disc_dim, list):
                        ctgan_params['discriminator_dim'] = tuple(disc_dim)
                    elif isinstance(disc_dim, str):
                        ctgan_params['discriminator_dim'] = tuple([int(x.strip()) for x in disc_dim.split(',') if x.strip()])
                
                # 布尔参数
                if 'log_frequency' in model_config:
                    ctgan_params['log_frequency'] = bool(model_config['log_frequency'])
                
                # device参数（SDGX的CTGANSynthesizerModel使用device参数，不是cuda！）
                if 'device' in model_config:
                    device_value = str(model_config['device'])
                    if device_value == 'auto':
                        # auto表示自动检测，SDGX默认会处理
                        import torch
                        ctgan_params['device'] = "cuda" if torch.cuda.is_available() else "cpu"
                    else:
                        ctgan_params['device'] = device_value
                elif 'cuda' in model_config:
                    # 兼容旧参数：如果设置了cuda，转换为device
                    if bool(model_config['cuda']):
                        ctgan_params['device'] = 'cuda'
                    else:
                        ctgan_params['device'] = 'cpu'
                # 如果没有设置device，使用SDGX默认值（会自动检测CUDA）
                
                # 注意：CTGANSynthesizerModel不支持verbose参数，已移除
                # 注意：CTGANSynthesizerModel不支持cuda参数，已转换为device
                
                print(f"[create_sdgx_model] CTGAN参数: {list(ctgan_params.keys())}")
                print(f"[create_sdgx_model] CTGAN参数值: {ctgan_params}")
                return CTGANSynthesizerModel(**ctgan_params)
            else:
                # 使用相似度参数（向后兼容）
                params = similarity_to_parameters(similarity)
                return CTGANSynthesizerModel(
                    epochs=params['epochs'],
                    batch_size=params['batch_size'],
                    generator_lr=params['generator_lr'],
                    discriminator_lr=params['discriminator_lr']
                )
        elif model_type == 'gaussian_copula':
            # 如果提供了完整的模型配置，使用配置中的参数
            if model_config and isinstance(model_config, dict):
                copula_params = {}
                
                # 布尔参数
                if 'enforce_min_max_values' in model_config:
                    copula_params['enforce_min_max_values'] = bool(model_config['enforce_min_max_values'])
                if 'enforce_rounding' in model_config:
                    copula_params['enforce_rounding'] = bool(model_config['enforce_rounding'])
                
                # 字符串参数
                if 'default_distribution' in model_config:
                    copula_params['default_distribution'] = str(model_config['default_distribution'])
                
                return GaussianCopulaSynthesizerModel(**copula_params)
            else:
                # 使用默认参数
                return GaussianCopulaSynthesizerModel()
        elif model_type.startswith('ai_'):
            # AI大模型：使用SDGX的SingleTableGPTModel
            # model_type格式：ai_ollama, ai_tongyi等
            # 注意：api_key和endpoint应该从model_config中获取（已在_execute_generation_task_with_app中处理）
            
            print(f"[create_sdgx_model] 开始创建AI大模型: {model_type}")
            print(f"[create_sdgx_model] model_config类型: {type(model_config)}, 内容keys: {list(model_config.keys()) if isinstance(model_config, dict) else 'N/A'}")
            
            if not model_config or not isinstance(model_config, dict):
                error_msg = f"AI大模型需要提供完整的配置（api_key, endpoint, selected_model等），但收到: {type(model_config)}"
                print(f"[create_sdgx_model] 错误: {error_msg}")
                raise ValueError(error_msg)
            
            api_key = model_config.get('api_key', '')
            api_url = model_config.get('endpoint', '')
            selected_model = model_config.get('selected_model', '')
            
            print(f"[create_sdgx_model] 配置检查:")
            print(f"  - api_key: {'已设置' if api_key else '未设置'} (长度: {len(api_key) if api_key else 0})")
            print(f"  - endpoint: {api_url if api_url else '未设置'}")
            print(f"  - selected_model: {selected_model if selected_model else '未设置'}")
            
            if not api_key or not api_url:
                error_msg = f"AI大模型配置不完整：api_key={'未设置' if not api_key else '已设置'}, endpoint={'未设置' if not api_url else api_url}"
                print(f"[create_sdgx_model] 错误: {error_msg}")
                raise ValueError(error_msg)
            
            if not selected_model:
                error_msg = f"AI大模型配置不完整：缺少selected_model（需要从系统设置中选择具体模型）"
                print(f"[create_sdgx_model] 错误: {error_msg}")
                raise ValueError(error_msg)
            
            # 确保API URL格式正确（SDGX要求以/结尾）
            if api_url and not api_url.endswith('/'):
                api_url = api_url + '/'
                print(f"[create_sdgx_model] API URL已修正为: {api_url}")
            
            # 创建GPT模型实例（参数与SDGX SingleTableGPTModel一致）
            # 注意：SDGX的SingleTableGPTModel在__init__中会调用_get_openai_setting_from_env()
            # 这会从环境变量读取配置，可能覆盖传入的参数
            # 因此我们需要先创建实例，然后使用set_openAI_settings()方法显式设置
            print(f"[create_sdgx_model] 开始创建SingleTableGPTModel实例...")
            try:
                # 先创建实例（使用默认参数）
                gpt_model = SingleTableGPTModel(
                    gpt_model=selected_model,
                    temperature=float(model_config.get('temperature', 0.1)),
                    max_tokens=int(model_config.get('max_tokens', 4000)),
                    timeout=int(model_config.get('timeout', 90)),
                    query_batch=int(model_config.get('query_batch', 30))
                )
                
                # 关键：使用set_openAI_settings()方法显式设置API配置
                # 这样可以确保我们的配置不会被环境变量覆盖
                gpt_model.set_openAI_settings(API_url=api_url, API_key=api_key)
                
                # 验证配置是否正确设置
                if gpt_model.openai_API_key != api_key:
                    print(f"[create_sdgx_model] 警告: API Key可能被环境变量覆盖，期望: {api_key[:10]}..., 实际: {gpt_model.openai_API_key[:10] if gpt_model.openai_API_key else 'None'}...")
                if gpt_model.openai_API_url != api_url:
                    print(f"[create_sdgx_model] 警告: API URL可能被环境变量覆盖，期望: {api_url}, 实际: {gpt_model.openai_API_url}")
                
                print(f"[create_sdgx_model] SingleTableGPTModel创建成功")
                print(f"[create_sdgx_model] 模型参数: gpt_model={gpt_model.gpt_model}, temperature={gpt_model.temperature}, max_tokens={gpt_model.max_tokens}")
                print(f"[create_sdgx_model] API配置: url={gpt_model.openai_API_url}, key={'已设置' if gpt_model.openai_API_key else '未设置'}")
            except Exception as e:
                error_msg = f"创建SingleTableGPTModel实例失败: {str(e)}"
                print(f"[create_sdgx_model] 错误: {error_msg}")
                import traceback
                traceback.print_exc()
                raise ValueError(error_msg)
            
            # 如果提供了自定义提示词模板，更新prompts
            if 'prompt_template' in model_config and model_config['prompt_template']:
                custom_prompt = model_config['prompt_template'].strip()
                if custom_prompt:
                    # 自定义提示词前缀
                    gpt_model.prompts['message_prefix'] = custom_prompt + '\n\n'
                    print(f"[create_sdgx_model] 已设置自定义提示词模板")
            
            print(f"[create_sdgx_model] AI大模型创建完成，返回模型实例")
            return gpt_model
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
    except ValueError as e:
        # ValueError 直接抛出，让调用者处理
        print(f"[create_sdgx_model] ValueError: {e}")
        raise
    except Exception as e:
        # 其他异常也抛出，但添加更多上下文信息
        error_msg = f"创建模型时发生未预期的错误: {e}"
        print(f"[create_sdgx_model] {error_msg}")
        import traceback
        error_trace = traceback.format_exc()
        print(f"[create_sdgx_model] 详细错误堆栈:\n{error_trace}")
        raise ValueError(error_msg) from e

def clean_dataframe_for_json(df):
    """清理DataFrame，将NaN转换为None以便JSON序列化"""
    df_cleaned = df.copy()
    for col in df_cleaned.columns:
        if df_cleaned[col].dtype == 'object':
            df_cleaned[col] = df_cleaned[col].replace(['NAN_VALUE', 'nan', 'NaN', 'NULL', 'null', ''], np.nan)
            try:
                df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='ignore')
            except:
                pass
    return df_cleaned.replace({np.nan: None})


class DataFrameValidator:
    """DataFrame验证和修复工具类"""
    
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}')
    DATE_EXTRACT_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}')
    
    @staticmethod
    def fix_date_value(value):
        """修复单个日期值，确保是独立的日期字符串"""
        if pd.isna(value) or str(value).strip() == '':
            return ''
        
        val_str = str(value).strip()
        
        # 如果长度超过20，可能是被连接的日期，尝试提取第一个日期
        if len(val_str) > 20:
            dates_found = DataFrameValidator.DATE_EXTRACT_PATTERN.findall(val_str)
            if len(dates_found) > 0:
                return dates_found[0]
        
        # 验证日期格式（YYYY-MM-DD），只取前10个字符
        if DataFrameValidator.DATE_PATTERN.match(val_str):
            return val_str[:10]
        
        return val_str
    
    @staticmethod
    def identify_date_columns(df, fields_config=None):
        """识别DataFrame中的日期列"""
        date_columns = set()
        
        # 1. 从字段配置中识别日期列
        if fields_config:
            for field in fields_config:
                if field.get('type') == 'date':
                    date_columns.add(field.get('name'))
        
        # 2. 检查datetime类型的列
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_columns.add(col)
        
        # 3. 检查object类型列中是否包含日期格式的值
        for col in df.columns:
            if col not in date_columns and df[col].dtype == 'object':
                sample = df[col].dropna().head(10)
                if len(sample) > 0:
                    date_count = sum(1 for v in sample 
                                   if pd.notna(v) and str(v).strip() 
                                   and DataFrameValidator.DATE_PATTERN.match(str(v)))
                    if date_count >= len(sample) * 0.8:  # 80%以上匹配日期格式
                        date_columns.add(col)
        
        return date_columns
    
    @staticmethod
    def fix_date_columns(df, date_columns, task_id=None):
        """修复日期列，确保所有值都是独立的日期字符串"""
        df_fixed = df.copy()
        log_prefix = f"任务 {task_id}: " if task_id else ""
        
        for col in date_columns:
            if col not in df_fixed.columns:
                continue
            
            print(f"{log_prefix}========== 修复日期列 {col} ==========")
            
            # 1. 转换为字符串类型
            df_fixed[col] = df_fixed[col].astype(str)
            
            # 2. 处理NaT和NaN值
            df_fixed[col] = df_fixed[col].replace(['NaT', 'nat', '<NaT>', 'None', 'nan', 'NaN', ''], '')
            
            # 3. 检查并修复被连接的日期字符串
            has_concatenated = False
            for idx in range(len(df_fixed)):
                val = str(df_fixed.at[idx, col]).strip()
                if len(val) > 20:
                    # 检查是否包含多个日期（通过年份数量判断）
                    date_count = (val.count('2024') + val.count('2025') + 
                                val.count('2023') + val.count('2026') + 
                                val.count('2027') + val.count('2028'))
                    if date_count > 1:
                        has_concatenated = True
                        dates_found = DataFrameValidator.DATE_EXTRACT_PATTERN.findall(val)
                        if len(dates_found) > 0:
                            df_fixed.at[idx, col] = dates_found[0]
                            if task_id and idx < 5:  # 只打印前5个修复的示例
                                print(f"{log_prefix}⚠️ 修复第{idx}行: {val[:50]}... -> {dates_found[0]}")
            
            if has_concatenated:
                print(f"{log_prefix}⚠️ 日期列 {col} 包含被连接的日期字符串，已修复")
            
            # 4. 统一修复所有值
            df_fixed[col] = df_fixed[col].apply(DataFrameValidator.fix_date_value)
            
            # 5. 确保是object类型（字符串）
            df_fixed[col] = df_fixed[col].astype('object')
            
            # 6. 最终验证
            sample_values = df_fixed[col].dropna().head(5).tolist()
            print(f"{log_prefix}日期列 {col} 修复后样本值: {sample_values}")
            
            # 检查是否还有异常值
            for val in sample_values:
                if len(str(val)) > 10:
                    print(f"{log_prefix}❌ 警告: 日期列 {col} 仍有异常值: {str(val)[:50]}...")
            
            print(f"{log_prefix}========== 日期列 {col} 修复完成 ==========")
        
        return df_fixed
    
    @staticmethod
    def validate_dataframe(df, task_id=None, min_rows=10):
        """验证DataFrame的完整性和正确性"""
        log_prefix = f"任务 {task_id}: " if task_id else ""
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
        empty_cols = []
        for col in df.columns:
            if df[col].isna().all():
                empty_cols.append(col)
                errors.append(f"列 {col} 全部为NaN")
        
        if empty_cols:
            print(f"{log_prefix}❌ 发现 {len(empty_cols)} 个全空列: {empty_cols}")
        else:
            print(f"{log_prefix}✅ 所有列都有数据")
        
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

class SyntheticService:
    """合成数据生成服务（重构版）"""
    
    def __init__(self):
        self.upload_folder = Config.UPLOAD_FOLDER
        self.results_folder = Config.RESULTS_FOLDER
        os.makedirs(self.results_folder, exist_ok=True)
        
        # 保存原始模板数据（用于保存结果时使用）
        self._original_template_data = None
        
        # 初始化新模块
        from .data_loader import DataLoader
        from .data_validator import DataValidator
        from .data_transformer import DataTransformer
        from .sdgx_adapter import SDGXAdapter
        
        try:
            self.data_loader = DataLoader(self.upload_folder)
            self.data_validator = DataValidator()
            self.data_transformer = DataTransformer()
            self.sdgx_adapter = SDGXAdapter() if SDGX_AVAILABLE else None
        except Exception as e:
            print(f"⚠️ 新模块初始化失败: {e}，将使用旧逻辑")
            self.data_loader = None
            self.data_validator = None
            self.data_transformer = None
            self.sdgx_adapter = None
    
    def create_generation_task(self, user_id, config):
        """创建生成任务"""
        task = Task(
            user_id=user_id,
            task_type='synthesis',
            task_name=config.get('task_name', '合成数据生成'),
            status='pending'
        )
        task.set_config(config)
        db.session.add(task)
        db.session.commit()
        
        # 异步执行生成任务
        from flask import current_app
        app = current_app._get_current_object()
        thread = Thread(target=self._execute_generation_task_with_app, args=(app, task.id,))
        thread.daemon = True
        thread.start()
        
        return task
    
    def _execute_generation_task_with_app(self, app, task_id):
        """执行生成任务（异步，带app上下文）"""
        with app.app_context():
            task = Task.query.get(task_id)
            if not task:
                print(f"任务 {task_id} 不存在")
                return
            
            # 获取配置（在app context内）
            config = task.get_config()
            
            task.status = 'running'
            task.progress = 0
            db.session.commit()
            print(f"任务 {task_id} 已启动，状态: running, 进度: 0%")
        
        try:
            # 在app context外执行耗时操作
            file_id = config.get('file_id')
            template_id = config.get('template_id')
            model_type = config.get('model_type', 'ctgan')
            model_config = config.get('model_config', {})
            data_amount = config.get('data_amount', 1000)
            similarity = config.get('similarity', 0.8)
            
            # ========== 重构：使用新模块架构 ==========
            print(f"任务 {task_id}: ========== 开始数据生成流程（新架构）==========")
            
            # 获取前端传递的字段配置（优先使用用户配置的fields）
            fields_config = config.get('fields', [])
            
            # Step 1: 加载数据（使用新模块架构）
            print(f"任务 {task_id}: [Step 1] 加载数据...")
            
            # 保存原始模板数据（用于后续保存结果时使用）
            original_template_df = None
            
            if self.data_loader:
                # 使用新模块
                # 优先从文件加载
                if file_id:
                    original_df = self.data_loader.load_from_file(file_id)
                    if original_df is not None:
                        print(f"任务 {task_id}: [Step 1] 从文件加载数据成功")
                    else:
                        original_df = None
                else:
                    original_df = None
                
                # 如果文件加载失败，从模板生成（直接使用SyntheticService的方法，避免循环导入）
                if original_df is None and template_id:
                    original_df = self._load_template_data(template_id, fields_config=fields_config)
                    print(f"任务 {task_id}: [Step 1] 从模板生成数据成功")
                    # 获取原始模板数据（如果存在）
                    if hasattr(self, '_original_template_data') and self._original_template_data is not None:
                        original_template_df = self._original_template_data.copy()
                        print(f"任务 {task_id}: [Step 1] 已获取原始模板数据: {original_template_df.shape[0]} 行 × {original_template_df.shape[1]} 列")
                
                if original_df is None or original_df.empty:
                    raise ValueError("无法加载数据：数据为空")
                
                # 确保最小行数
                original_df = self.data_loader.ensure_min_rows(original_df, min_rows=10, max_rows=100)
            else:
                # 回退到旧逻辑
                original_df = self._load_data(file_id, template_id, fields_config=fields_config)
                if original_df is None or original_df.empty:
                    raise ValueError("无法加载数据：数据为空")
                # 如果是从模板加载的，获取原始模板数据
                if template_id and hasattr(self, '_original_template_data') and self._original_template_data is not None:
                    original_template_df = self._original_template_data.copy()
                    print(f"任务 {task_id}: [Step 1] (旧逻辑) 已获取原始模板数据: {original_template_df.shape[0]} 行 × {original_template_df.shape[1]} 列")
                if original_df.shape[0] < 10:
                    min_rows = 10
                    while original_df.shape[0] < min_rows and original_df.shape[0] < 100:
                        rows_to_add = min(min_rows - original_df.shape[0], original_df.shape[0])
                        original_df = pd.concat([original_df, original_df.head(rows_to_add)], ignore_index=True)
            
            print(f"任务 {task_id}: [Step 1] 数据加载完成: {original_df.shape[0]} 行 × {original_df.shape[1]} 列")
            
            # 更新进度（需要app context）
            with app.app_context():
                self._update_progress(task_id, 20)
            
            # 如果是AI大模型，需要从系统设置获取API配置
            if model_type.startswith('ai_'):
                ai_provider = model_type.replace('ai_', '')
                print(f"任务 {task_id}: 开始创建AI大模型，provider: {ai_provider}")
                print(f"任务 {task_id}: 用户配置的model_config: {model_config}")
                
                # 从系统设置获取AI模型配置（需要app context）
                with app.app_context():
                    from models.config import SystemConfig
                    try:
                        from utils.encryption import encryption_service
                    except ImportError:
                        encryption_service = None
                    
                    config_key = f'ai_model_{ai_provider}'
                    ai_config = SystemConfig.query.filter_by(config_key=config_key).first()
                    
                    if not ai_config:
                        error_msg = f"AI模型 {ai_provider} 未在系统设置中配置"
                        print(f"任务 {task_id}: {error_msg}")
                        raise ValueError(error_msg)
                    
                    config_value = ai_config.get_value() if hasattr(ai_config, 'get_value') else {}
                    if not isinstance(config_value, dict):
                        config_value = {}
                    
                    ai_model_config = config_value.get('config', {})
                    print(f"任务 {task_id}: 系统配置的ai_model_config keys: {list(ai_model_config.keys())}")
                    
                    # 解密API Key
                    api_key = ai_model_config.get('api_key', '')
                    if api_key and encryption_service:
                        try:
                            api_key = encryption_service.decrypt(api_key)
                            print(f"任务 {task_id}: API Key已解密（长度: {len(api_key)}）")
                        except Exception as e:
                            print(f"任务 {task_id}: API Key解密失败: {e}")
                            pass
                    
                    endpoint = ai_model_config.get('endpoint', '')
                    print(f"任务 {task_id}: Endpoint: {endpoint}")
                    
                    selected_model = model_config.get('selected_model', '')
                    print(f"任务 {task_id}: 用户选择的模型: {selected_model}")
                    
                    # 合并系统配置和用户配置
                    final_model_config = {
                        'api_key': api_key,
                        'endpoint': endpoint,
                        'selected_model': selected_model,
                        'temperature': model_config.get('temperature', 0.1),
                        'max_tokens': model_config.get('max_tokens', 4000),
                        'timeout': model_config.get('timeout', 90),
                        'query_batch': model_config.get('query_batch', 30),
                        'prompt_template': model_config.get('prompt_template', '')
                    }
                    
                    # 如果没有指定selected_model，尝试从系统配置中获取
                    if not final_model_config['selected_model']:
                        selected_models = ai_model_config.get('selected_models', [])
                        print(f"任务 {task_id}: 系统配置的selected_models: {selected_models}")
                        if selected_models and len(selected_models) > 0:
                            final_model_config['selected_model'] = selected_models[0].get('id', '')
                            print(f"任务 {task_id}: 使用系统配置的第一个模型: {final_model_config['selected_model']}")
                    
                    print(f"任务 {task_id}: 最终模型配置: api_key={'***' if api_key else '空'}, endpoint={endpoint}, selected_model={final_model_config['selected_model']}")
                
                print(f"任务 {task_id}: 调用create_sdgx_model创建模型...")
                try:
                    model = create_sdgx_model(model_type, model_config=final_model_config, similarity=similarity)
                    print(f"任务 {task_id}: create_sdgx_model返回: {type(model).__name__ if model else 'None'}")
                except Exception as e:
                    error_msg = f"调用create_sdgx_model时发生异常: {str(e)}"
                    print(f"任务 {task_id}: {error_msg}")
                    import traceback
                    traceback.print_exc()
                    raise ValueError(error_msg) from e
            else:
                # 创建模型（优先使用 model_config，否则使用 similarity）
                print(f"任务 {task_id}: 创建SDG本地模型，类型: {model_type}")
                print(f"任务 {task_id}: 模型配置: {model_config}")
                try:
                    model = create_sdgx_model(model_type, model_config=model_config, similarity=similarity)
                    print(f"任务 {task_id}: create_sdgx_model返回: {type(model).__name__ if model else 'None'}")
                except Exception as e:
                    error_msg = f"调用create_sdgx_model时发生异常: {str(e)}"
                    print(f"任务 {task_id}: {error_msg}")
                    import traceback
                    traceback.print_exc()
                    raise ValueError(error_msg) from e
            
            if not model:
                error_msg = "模型创建失败：create_sdgx_model返回None，请检查日志中的详细错误信息"
                print(f"任务 {task_id}: {error_msg}")
                raise ValueError(error_msg)
            
            print(f"任务 {task_id}: 模型创建成功: {type(model).__name__}")
            
            # ========== 参数验证：确保模型参数正确传递 ==========
            print(f"任务 {task_id}: ========== 模型参数验证 ==========")
            print(f"任务 {task_id}: 模型类型: {model_type}")
            print(f"任务 {task_id}: 模型配置: {model_config}")
            if hasattr(model, '__dict__'):
                model_attrs = {k: v for k, v in model.__dict__.items() if not k.startswith('_')}
                print(f"任务 {task_id}: 模型实例属性: {list(model_attrs.keys())}")
                # 输出关键参数
                for key in ['epochs', 'batch_size', 'generator_lr', 'discriminator_lr', 'device', 'gpt_model', 'temperature', 'max_tokens']:
                    if hasattr(model, key):
                        value = getattr(model, key)
                        print(f"任务 {task_id}: 模型参数 {key} = {value}")
            print(f"任务 {task_id}: ========== 参数验证完成 ==========")
            
            # ========== 重构：使用新模块架构 ==========
            print(f"任务 {task_id}: ========== 开始数据准备和验证（新架构）==========")
            
            if self.data_validator and self.data_transformer and self.sdgx_adapter:
                # 使用新模块架构
                # 关键：如果是从模板加载的，训练时应该使用原始模板数据（只修复格式，不改变数据值）
                # 这样可以确保训练数据和模板数据一致
                training_df = original_df.copy()
                if original_template_df is not None:
                    # 使用原始模板数据作为训练数据的基础
                    print(f"任务 {task_id}: [关键] 使用原始模板数据作为训练数据基础，确保与模板数据一致")
                    print(f"任务 {task_id}: [关键] 原始模板数据形状: {original_template_df.shape}")
                    print(f"任务 {task_id}: [关键] 原始模板数据前3行:")
                    print(original_template_df.head(3).to_string())
                    training_df = original_template_df.copy()
                    # 只修复格式问题（如日期格式），不改变数据值
                    # 如果原始模板数据行数不足，需要扩展（但保持数据值不变）
                    if training_df.shape[0] < 10:
                        print(f"任务 {task_id}: [关键] 原始模板数据行数不足 ({training_df.shape[0]} 行)，扩展到10行（保持数据值不变）")
                        while training_df.shape[0] < 10:
                            rows_to_add = min(10 - training_df.shape[0], training_df.shape[0])
                            training_df = pd.concat([training_df, training_df.head(rows_to_add)], ignore_index=True)
                    elif training_df.shape[0] > 10:
                        print(f"任务 {task_id}: [关键] 原始模板数据行数过多 ({training_df.shape[0]} 行)，截取前10行")
                        training_df = training_df.head(10).copy()
                    print(f"任务 {task_id}: [关键] 训练数据准备完成，形状: {training_df.shape}")
                    print(f"任务 {task_id}: [关键] 训练数据前3行（用于验证）:")
                    print(training_df.head(3).to_string())
                else:
                    print(f"任务 {task_id}: [警告] original_template_df 为 None，使用处理后的 original_df")
                    print(f"任务 {task_id}: [警告] original_df 前3行:")
                    print(original_df.head(3).to_string())
                
                # Step 2: 识别日期列（使用DataValidator模块）
                print(f"任务 {task_id}: [Step 2] 识别日期列...")
                date_columns = self.data_validator.identify_date_columns(training_df, fields_config)
                print(f"任务 {task_id}: [Step 2] 识别的日期列: {list(date_columns)}")
                
                # Step 3: 数据清理（使用DataTransformer模块）
                print(f"任务 {task_id}: [Step 3] 清理数据...")
                cleaned_df = self.data_transformer.clean_data(training_df, date_columns)
                print(f"任务 {task_id}: [Step 3] 数据清理完成")
                
                # Step 4: 修复日期列（使用DataValidator模块）
                print(f"任务 {task_id}: [Step 4] 修复日期列...")
                fixed_df = self.data_validator.fix_date_columns(cleaned_df, date_columns, task_id)
                print(f"任务 {task_id}: [Step 4] 日期列修复完成")
                
                # Step 5: 验证数据完整性（使用DataValidator模块）
                print(f"任务 {task_id}: [Step 5] 验证数据完整性...")
                validated_df = self.data_validator.validate_dataframe(fixed_df, task_id, min_rows=10)
                print(f"任务 {task_id}: [Step 5] 数据验证完成")
                
                # Step 6: 转换为SDGX格式（使用DataTransformer模块）
                print(f"任务 {task_id}: [Step 6] 转换为SDGX格式...")
                df_for_sdgx = self.data_transformer.prepare_for_sdgx(validated_df, date_columns, task_id)
                print(f"任务 {task_id}: [Step 6] 数据转换完成")
                
                # 关键：在传递给SDGX之前，最后一次修复日期列，确保所有值都是正确的格式
                print(f"任务 {task_id}: [Step 6.5] 最终验证和修复日期列...")
                if date_columns:
                    for col in date_columns:
                        if col in df_for_sdgx.columns:
                            print(f"任务 {task_id}: [Step 6.5] 检查日期列 {col}...")
                            
                            # 先检查当前状态
                            sample_before = df_for_sdgx[col].head(10).tolist()
                            has_issue = False
                            for idx, val in enumerate(sample_before):
                                val_str = str(val).strip()
                                if len(val_str) > 20:
                                    date_count = val_str.count('2024') + val_str.count('2025') + val_str.count('2023')
                                    if date_count > 1:
                                        has_issue = True
                                        print(f"任务 {task_id}: ❌ 发现第{idx}行日期列{col}被连接: {val_str[:80]}...")
                            
                            if has_issue:
                                print(f"任务 {task_id}: [Step 6.5] 开始修复日期列 {col}...")
                                # 使用DataValidator修复
                                if self.data_validator:
                                    df_for_sdgx = self.data_validator.fix_date_columns(df_for_sdgx, {col}, task_id)
                                else:
                                    df_for_sdgx = DataFrameValidator.fix_date_columns(df_for_sdgx, {col}, task_id)
                            
                            # 确保所有值都是10个字符的日期字符串（双重保险）
                            df_for_sdgx[col] = df_for_sdgx[col].apply(lambda x: str(x)[:10] if len(str(x)) > 10 else str(x))
                            df_for_sdgx[col] = df_for_sdgx[col].astype('object')
                            
                            # 最终验证修复结果
                            sample_after = df_for_sdgx[col].head(10).tolist()
                            all_ok = True
                            for idx, val in enumerate(sample_after):
                                val_str = str(val).strip()
                                if len(val_str) > 10:
                                    all_ok = False
                                    print(f"任务 {task_id}: ❌ 严重警告: 日期列 {col} 第{idx}行仍有异常值: {val_str[:80]}...")
                            
                            if all_ok:
                                print(f"任务 {task_id}: ✅ 日期列 {col} 修复完成，所有值正常")
                            else:
                                print(f"任务 {task_id}: ⚠️ 日期列 {col} 仍有问题，尝试再次修复...")
                                # 再次修复
                                if self.data_validator:
                                    df_for_sdgx = self.data_validator.fix_date_columns(df_for_sdgx, {col}, task_id)
                                else:
                                    df_for_sdgx = DataFrameValidator.fix_date_columns(df_for_sdgx, {col}, task_id)
                                # 再次确保10字符
                                df_for_sdgx[col] = df_for_sdgx[col].apply(lambda x: str(x)[:10] if len(str(x)) > 10 else str(x))
                                df_for_sdgx[col] = df_for_sdgx[col].astype('object')
                
                print(f"任务 {task_id}: [Step 6.5] 最终验证完成")
                print(f"任务 {task_id}: 传递给SDGX的数据类型: {df_for_sdgx.dtypes.to_dict()}")
                
                # 输出数据样本（用于调试）
                print(f"任务 {task_id}: ========== 数据样本（前5行）==========")
                print(df_for_sdgx.head(5).to_string())
                
                # 特别检查日期列的值
                if date_columns:
                    print(f"任务 {task_id}: ========== 日期列样本值 ==========")
                    for col in date_columns:
                        if col in df_for_sdgx.columns:
                            sample_values = df_for_sdgx[col].head(5).tolist()
                            print(f"任务 {task_id}: {col}: {sample_values}")
                
                # 关键：在调用describe()之前，再次验证日期列
                print(f"任务 {task_id}: ========== 调用describe()前的最终验证 ==========")
                if date_columns:
                    for col in date_columns:
                        if col in df_for_sdgx.columns:
                            sample_vals = df_for_sdgx[col].head(10).tolist()
                            print(f"任务 {task_id}: 调用describe()前，日期列 {col} 的样本值: {sample_vals}")
                            # 检查是否有被连接的日期
                            for idx, val in enumerate(sample_vals):
                                val_str = str(val).strip()
                                if len(val_str) > 20:
                                    date_count = val_str.count('2024') + val_str.count('2025')
                                    if date_count > 1:
                                        print(f"任务 {task_id}: ❌ 严重错误: 调用describe()前，日期列 {col} 第{idx}行仍有被连接的日期: {val_str[:100]}...")
                                        # 立即修复
                                        if self.data_validator:
                                            df_for_sdgx = self.data_validator.fix_date_columns(df_for_sdgx, {col}, task_id)
                                        else:
                                            df_for_sdgx = DataFrameValidator.fix_date_columns(df_for_sdgx, {col}, task_id)
                                        # 再次确保10字符
                                        df_for_sdgx[col] = df_for_sdgx[col].apply(lambda x: str(x)[:10] if len(str(x)) > 10 else str(x))
                                        df_for_sdgx[col] = df_for_sdgx[col].astype('object')
                
                # 注意：describe()可能会触发pandas的内部处理，导致日期列被错误处理
                # 因此我们跳过describe()调用，或者只对非日期列调用
                print(f"任务 {task_id}: ========== 数据统计信息（跳过日期列）==========")
                try:
                    # 只对非日期列调用describe
                    non_date_cols = [col for col in df_for_sdgx.columns if col not in (date_columns or set())]
                    if non_date_cols:
                        print(df_for_sdgx[non_date_cols].describe().to_string())
                    else:
                        print("所有列都是日期列，跳过describe()")
                except Exception as e:
                    print(f"任务 {task_id}: ⚠️ describe()调用失败: {e}")
                
                # Step 6.6: 确保所有整数列都是标准int64类型（SDGX不支持Int64）
                print(f"任务 {task_id}: [Step 6.6] 检查并修复整数列类型...")
                for col in df_for_sdgx.columns:
                    if col in (date_columns or set()):
                        continue  # 跳过日期列
                    
                    dtype_str = str(df_for_sdgx[col].dtype)
                    # 检查是否是Int64类型（可空整数类型）
                    if dtype_str == 'Int64':
                        print(f"任务 {task_id}: ⚠️ 发现列 {col} 是Int64类型，转换为int64...")
                        try:
                            numeric_series = pd.to_numeric(df_for_sdgx[col], errors='coerce')
                            # 填充NaN为0，然后转换为int64
                            df_for_sdgx[col] = numeric_series.fillna(0).astype('int64')
                            print(f"任务 {task_id}: ✅ 列 {col} 已转换为int64类型")
                        except Exception as e:
                            print(f"任务 {task_id}: ❌ 列 {col} 转换为int64失败: {e}")
                            # 如果转换失败，尝试先转换为float64再转换为int64
                            try:
                                df_for_sdgx[col] = pd.to_numeric(df_for_sdgx[col], errors='coerce').fillna(0).astype('float64').astype('int64')
                                print(f"任务 {task_id}: ✅ 列 {col} 通过float64中转转换为int64成功")
                            except Exception as e2:
                                print(f"任务 {task_id}: ❌ 列 {col} 转换失败: {e2}")
                
                print(f"任务 {task_id}: [Step 6.6] 类型检查完成，最终数据类型: {df_for_sdgx.dtypes.to_dict()}")
                
                # Step 7: 创建SDGX连接器和合成器（使用SDGXAdapter模块）
                print(f"任务 {task_id}: [Step 7] 创建SDGX连接器和合成器...")
                # 关键：在传递给DataFrameConnector之前，最后一次验证和修复日期列
                if date_columns:
                    for col in date_columns:
                        if col in df_for_sdgx.columns:
                            # 确保所有值都是10个字符
                            df_for_sdgx[col] = df_for_sdgx[col].apply(lambda x: str(x)[:10] if len(str(x)) > 10 else str(x))
                            df_for_sdgx[col] = df_for_sdgx[col].astype('object')
                            # 验证
                            sample_vals = df_for_sdgx[col].head(5).tolist()
                            print(f"任务 {task_id}: 传递给DataFrameConnector前，日期列 {col} 的样本值: {sample_vals}")
                
                data_connector = self.sdgx_adapter.create_connector(df_for_sdgx, task_id, date_columns)
                synthesizer = self.sdgx_adapter.create_synthesizer(model, data_connector, date_columns, task_id)
                print(f"任务 {task_id}: [Step 7] SDGX组件创建完成")
                
                # Step 8: 训练模型（使用SDGXAdapter模块）
                with app.app_context():
                    self._update_progress(task_id, 40, "正在训练模型...")
                print(f"任务 {task_id}: [Step 8] 开始训练模型...")
                self.sdgx_adapter.fit(synthesizer, task_id, date_columns)
                
                # Step 9: 生成数据（使用SDGXAdapter模块）
                with app.app_context():
                    self._update_progress(task_id, 60, "正在生成数据...")
                print(f"任务 {task_id}: [Step 9] 开始生成数据...")
                synthetic_data = self.sdgx_adapter.sample(synthesizer, data_amount, task_id)
                # SDGXAdapter.sample() 返回的已经是DataFrame，无需再次转换
                
                # Step 9.5: 检查生成数据中的Int64类型并转换
                if isinstance(synthetic_data, pd.DataFrame):
                    print(f"任务 {task_id}: [Step 9.5] 检查生成数据中的类型...")
                    for col in synthetic_data.columns:
                        dtype_str = str(synthetic_data[col].dtype)
                        if dtype_str == 'Int64':
                            print(f"任务 {task_id}: ⚠️ 生成数据中列 {col} 是Int64类型，转换为int64...")
                            try:
                                numeric_series = pd.to_numeric(synthetic_data[col], errors='coerce')
                                synthetic_data[col] = numeric_series.fillna(0).astype('int64')
                                print(f"任务 {task_id}: ✅ 生成数据列 {col} 已转换为int64类型")
                            except Exception as e:
                                print(f"任务 {task_id}: ❌ 生成数据列 {col} 转换为int64失败: {e}")
                    print(f"任务 {task_id}: [Step 9.5] 生成数据类型检查完成: {synthetic_data.dtypes.to_dict()}")
            else:
                # 回退到旧逻辑（使用DataFrameValidator）
                print(f"任务 {task_id}: ⚠️ 新模块不可用，使用旧逻辑")
                date_columns = DataFrameValidator.identify_date_columns(original_df, fields_config)
                df_for_sdgx = DataFrameValidator.fix_date_columns(original_df, date_columns, task_id)
                df_for_sdgx = DataFrameValidator.validate_dataframe(df_for_sdgx, task_id, min_rows=10)
                
                data_connector = DataFrameConnector(df=df_for_sdgx)
                synthesizer = Synthesizer(model=model, data_connector=data_connector)
                
                with app.app_context():
                    self._update_progress(task_id, 40, "正在训练模型...")
                try:
                    synthesizer.fit()
                except Exception as e:
                    error_msg = f"模型训练失败: {str(e)}"
                    print(f"任务 {task_id}: {error_msg}")
                    import traceback
                    traceback.print_exc()
                    raise ValueError(error_msg) from e
                
                with app.app_context():
                    self._update_progress(task_id, 60, "正在生成数据...")
                synthetic_data = synthesizer.sample(data_amount)
            
            # 后处理
            with app.app_context():
                self._update_progress(task_id, 80, "正在保存结果...")
            
            # 确保synthetic_data是DataFrame（SDGXAdapter.sample()返回的已经是DataFrame）
            if not isinstance(synthetic_data, pd.DataFrame):
                synthetic_df = pd.DataFrame(synthetic_data)
            else:
                synthetic_df = synthetic_data
            
            # 保存结果（传递fields_config以保持字段类型）
            # 如果是从模板加载的，使用原始模板数据而不是处理后的数据
            original_data_to_save = original_template_df if original_template_df is not None else original_df
            result_path = self._save_result(task_id, original_data_to_save, synthetic_df, fields_config=fields_config)
            print(f"任务 {task_id}: 结果已保存到 {result_path}")
            
            # 更新任务状态
            with app.app_context():
                task = Task.query.get(task_id)
                if task:
                    task.status = 'completed'
                    task.progress = 100
                    task.result_path = result_path
                    task.completed_at = datetime.utcnow()
                    db.session.commit()
                    print(f"任务 {task_id} 已完成")
                else:
                    print(f"任务 {task_id} 不存在，无法更新状态")
            
        except Exception as e:
            error_msg = str(e)
            import traceback
            error_trace = traceback.format_exc()
            print(f"任务 {task_id} 执行失败: {error_msg}")
            print(f"错误堆栈:\n{error_trace}")
            with app.app_context():
                task = Task.query.get(task_id)
                if task:
                    # 确保错误信息包含更多细节
                    full_error_msg = f"{error_msg}\n\n详细错误:\n{error_trace[:500]}"  # 限制长度
                    task.status = 'failed'
                    task.error_message = full_error_msg
                    db.session.commit()
                    print(f"任务 {task_id} 状态已更新为 failed，错误信息: {error_msg}")
                else:
                    print(f"任务 {task_id} 不存在，无法更新失败状态")
    
    def _load_data(self, file_id, template_id, fields_config=None):
        """加载数据
        
        Args:
            file_id: 上传的文件ID
            template_id: 模板ID
            fields_config: 前端传递的字段配置（优先使用，如果提供则覆盖模板默认配置）
        """
        if file_id:
            # 从上传的文件加载
            for ext in ['csv', 'xlsx', 'xls', 'json']:
                filepath = os.path.join(self.upload_folder, f"{file_id}.{ext}")
                if os.path.exists(filepath):
                    if ext == 'csv':
                        return pd.read_csv(filepath)
                    elif ext in ['xlsx', 'xls']:
                        return pd.read_excel(filepath)
                    elif ext == 'json':
                        return pd.read_json(filepath)
        
        if template_id:
            # 从模板加载示例数据（如果提供了fields_config，使用它；否则从模板读取）
            return self._load_template_data(template_id, fields_config=fields_config)
        
        return None
    
    def _load_template_data(self, template_id, fields_config=None):
        """加载模板数据
        
        Args:
            template_id: 模板ID
            fields_config: 前端传递的字段配置（优先使用，如果提供则覆盖模板默认配置）
        """
        # 关键：无论是否有fields_config，都要先检查模板的sample_data
        # 因为sample_data是模板的真实数据，应该优先使用
        templates_data = self._get_templates_data()
        template = None
        if templates_data:
            for t in templates_data:
                if t.get('id') == template_id:
                    template = t
                    break
        
        # 优先使用模板中的sample_data（如果存在）
        if template:
            sample_data = template.get('sample_data', [])
            if sample_data and len(sample_data) > 0:
                print(f"[_load_template_data] 发现模板中的sample_data，共 {len(sample_data)} 行，优先使用（忽略fields_config）")
                
                # 获取字段配置（优先使用fields_config，否则使用模板的fields）
                fields = fields_config if fields_config and len(fields_config) > 0 else template.get('fields', [])
                
                # 关键：保存原始模板数据的深拷贝（用于后续保存原始数据）
                import copy
                original_sample_data = copy.deepcopy(sample_data)
                
                # 在转换为DataFrame之前，先修复sample_data中的日期值
                # 检查并修复被连接的日期字符串
                for row_idx, row in enumerate(sample_data):
                    if isinstance(row, dict):
                        for key, value in row.items():
                            if isinstance(value, str) and len(value) > 20:
                                # 检查是否包含多个日期
                                date_count = value.count('2024') + value.count('2025') + value.count('2023')
                                if date_count > 1:
                                    # 提取第一个日期
                                    import re
                                    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
                                    dates_found = date_pattern.findall(value)
                                    if len(dates_found) > 0:
                                        row[key] = dates_found[0]
                                        if row_idx < 3:  # 只打印前3个修复的示例
                                            print(f"[_load_template_data] ⚠️ 修复sample_data第{row_idx}行字段{key}: {value[:50]}... -> {dates_found[0]}")
                
                # 将修复后的sample_data转换为DataFrame
                df_from_sample = pd.DataFrame(sample_data)
                
                # 使用统一的数据验证和修复工具处理日期列
                # 优先使用新模块，如果不可用则使用旧类
                if self.data_validator:
                    date_columns = self.data_validator.identify_date_columns(df_from_sample)
                    if date_columns:
                        print(f"[_load_template_data] 在sample_data中识别到日期列: {list(date_columns)}")
                        # 修复日期列（确保所有值都是独立的日期字符串）
                        df_from_sample = self.data_validator.fix_date_columns(df_from_sample, date_columns)
                        # 再次验证修复结果
                        for col in date_columns:
                            sample_values = df_from_sample[col].head(5).tolist()
                            for val in sample_values:
                                val_str = str(val)
                                if len(val_str) > 20:
                                    date_count = val_str.count('2024') + val_str.count('2025')
                                    if date_count > 1:
                                        print(f"[_load_template_data] ⚠️ 警告: 日期列 {col} 仍有被连接的值: {val_str[:50]}...")
                else:
                    date_columns = DataFrameValidator.identify_date_columns(df_from_sample)
                    if date_columns:
                        print(f"[_load_template_data] 在sample_data中识别到日期列: {list(date_columns)}")
                        df_from_sample = DataFrameValidator.fix_date_columns(df_from_sample, date_columns)
                
                # 最终验证：确保所有日期列都是正确的格式
                for col in df_from_sample.columns:
                    if df_from_sample[col].dtype == 'object':
                        sample_val = df_from_sample[col].iloc[0] if len(df_from_sample) > 0 else None
                        if sample_val and isinstance(sample_val, str):
                            if len(sample_val) > 20 and ('2024' in sample_val or '2025' in sample_val):
                                date_count = sample_val.count('2024') + sample_val.count('2025')
                                if date_count > 1:
                                    # 如果发现被连接的日期，再次修复
                                    print(f"[_load_template_data] ⚠️ 检测到列 {col} 仍有被连接的日期，进行二次修复...")
                                    if self.data_validator:
                                        df_from_sample = self.data_validator.fix_date_columns(df_from_sample, {col})
                                    else:
                                        df_from_sample = DataFrameValidator.fix_date_columns(df_from_sample, {col})
                
                # 关键：不进行任何类型转换，完全保持原始数据的格式
                # 即使是数字类型的字段（如电话号码、ID等），如果原始数据是字符串格式，也应该保持为字符串
                # 这样可以确保训练数据和生成数据与模板数据完全一致
                print(f"[_load_template_data] 保持原始数据格式，不进行类型转换")
                
                # 确保sample_data正好是10行
                if df_from_sample.shape[0] < 10:
                    print(f"[_load_template_data] sample_data行数较少 ({df_from_sample.shape[0]} 行)，扩展到10行")
                    while df_from_sample.shape[0] < 10:
                        rows_to_add = min(10 - df_from_sample.shape[0], df_from_sample.shape[0])
                        df_from_sample = pd.concat([df_from_sample, df_from_sample.head(rows_to_add)], ignore_index=True)
                    print(f"[_load_template_data] sample_data已扩展到 {df_from_sample.shape[0]} 行")
                elif df_from_sample.shape[0] > 10:
                    print(f"[_load_template_data] sample_data行数过多 ({df_from_sample.shape[0]} 行)，截取前10行")
                    df_from_sample = df_from_sample.head(10).copy()
                
                # 最终验证：在返回前再次检查日期列
                print(f"[_load_template_data] 使用模板sample_data: {df_from_sample.shape[0]} 行 × {df_from_sample.shape[1]} 列")
                print(f"[_load_template_data] 数据样本（前3行）:")
                print(df_from_sample.head(3))
                
                # 关键：在返回前，最后一次检查所有日期列
                for col in df_from_sample.columns:
                    if df_from_sample[col].dtype == 'object':
                        sample_vals = df_from_sample[col].head(10).tolist()
                        for idx, val in enumerate(sample_vals):
                            val_str = str(val)
                            if len(val_str) > 20 and ('2024' in val_str or '2025' in val_str):
                                date_count = val_str.count('2024') + val_str.count('2025')
                                if date_count > 1:
                                    print(f"[_load_template_data] ❌ 严重错误: 返回前发现列 {col} 第{idx}行仍有被连接的日期: {val_str[:100]}...")
                                    # 立即修复
                                    if self.data_validator:
                                        df_from_sample = self.data_validator.fix_date_columns(df_from_sample, {col})
                                    else:
                                        df_from_sample = DataFrameValidator.fix_date_columns(df_from_sample, {col})
                                    print(f"[_load_template_data] ✅ 已修复列 {col}")
                
                # 关键：保存原始模板数据到实例变量（用于后续保存原始数据）
                # 将原始模板数据转换为DataFrame（完全保持原始状态，不进行任何处理）
                try:
                    # 直接从原始模板数据创建DataFrame，不进行任何处理（包括行数调整、类型转换等）
                    original_template_df = pd.DataFrame(original_sample_data)
                    # 保存到实例变量（完全保持模板数据的原始状态）
                    self._original_template_data = original_template_df
                    print(f"[_load_template_data] 已保存原始模板数据（完全未处理）: {original_template_df.shape[0]} 行 × {original_template_df.shape[1]} 列")
                except Exception as e:
                    print(f"[_load_template_data] 警告: 保存原始模板数据失败: {e}")
                    self._original_template_data = None
                
                return df_from_sample
        
        # 如果没有sample_data，需要获取fields配置
        if not template:
            if not templates_data:
                print(f"[_load_template_data] 警告: 无法获取模板列表，使用默认数据")
                return self._generate_default_template_data()
            print(f"[_load_template_data] 警告: 未找到模板ID {template_id}，使用默认数据")
            return self._generate_default_template_data()
        
        # 获取字段配置（优先使用fields_config，否则使用模板的fields）
        fields = fields_config if fields_config and len(fields_config) > 0 else template.get('fields', [])
        if not fields or len(fields) == 0:
            print(f"[_load_template_data] 警告: 模板 {template_id} 没有字段定义，使用默认数据")
            return self._generate_default_template_data()
        
        print(f"[_load_template_data] 模板中没有sample_data，开始生成示例数据（10行），字段数: {len(fields)}")
        
        print(f"[_load_template_data] 模板中没有sample_data，开始生成示例数据（10行），字段数: {len(fields)}")
        
        # 生成示例数据（10行）
        NUM_ROWS = 10
        data = {}
        for field in fields:
            field_name = field.get('name', '')
            field_type = field.get('type', 'string')
            
            # 自动识别ID字段：如果字段名包含"id"（不区分大小写），且类型是string，则改为integer
            field_name_lower = field_name.lower()
            if 'id' in field_name_lower and field_type == 'string':
                # 检查是否是明确的字符串ID（如customer_id, order_id等业务ID）
                # 如果字段名是纯ID或包含_id结尾，且不是明确的业务ID，则改为integer
                if field_name_lower == 'id' or (field_name_lower.endswith('_id') and field_name_lower not in ['customer_id', 'order_id', 'user_id', 'product_id', 'patient_id', 'student_id', 'call_id', 'claim_id', 'policy_id', 'shipment_id']):
                    field_type = 'integer'
                    print(f"[_load_template_data] 自动识别字段 {field_name} 为integer类型（ID字段）")
            
            if field_type == 'integer':
                # 整数类型
                field_range = field.get('range', [1, 1000])
                # 关键：将numpy数组转换为Python列表
                values = np.random.randint(
                    int(field_range[0]) if len(field_range) > 0 else 1,
                    int(field_range[1]) if len(field_range) > 1 else 1000,
                    NUM_ROWS
                )
                data[field_name] = values.tolist()  # 转换为Python列表
            elif field_type == 'float':
                # 浮点数类型
                field_range = field.get('range', [0.0, 100.0])
                # 关键：将numpy数组转换为Python列表
                values = np.random.uniform(
                    float(field_range[0]) if len(field_range) > 0 else 0.0,
                    float(field_range[1]) if len(field_range) > 1 else 100.0,
                    NUM_ROWS
                )
                data[field_name] = values.tolist()  # 转换为Python列表
            elif field_type == 'date':
                # 日期类型：生成日期序列，每个日期作为独立的字符串值
                from datetime import datetime, timedelta
                
                # 检查是否有日期范围配置
                date_range = field.get('date_range', None)
                if date_range and len(date_range) == 2:
                    # 使用配置的日期范围
                    try:
                        start_date = datetime.strptime(date_range[0], '%Y-%m-%d')
                        end_date = datetime.strptime(date_range[1], '%Y-%m-%d')
                        # 计算日期范围
                        days_diff = (end_date - start_date).days
                        if days_diff < 0:
                            raise ValueError(f"日期范围无效：开始日期 {date_range[0]} 晚于结束日期 {date_range[1]}")
                        # 生成日期序列
                        dates = []
                        for i in range(min(NUM_ROWS, days_diff + 1)):
                            date_obj = start_date + timedelta(days=i)
                            dates.append(date_obj.strftime('%Y-%m-%d'))
                        # 如果需要的日期数超过范围，循环使用
                        while len(dates) < NUM_ROWS:
                            dates.extend(dates[:min(len(dates), NUM_ROWS - len(dates))])
                        dates = dates[:NUM_ROWS]  # 确保正好NUM_ROWS个
                        print(f"使用配置的日期范围生成日期列 {field_name}: {date_range[0]} 到 {date_range[1]}, 共 {len(dates)} 个日期")
                    except Exception as e:
                        print(f"解析日期范围失败: {e}，使用默认日期范围")
                        start_date = datetime.now() - timedelta(days=365)
                        dates = []
                        for i in range(NUM_ROWS):
                            date_obj = start_date + timedelta(days=i)
                            dates.append(date_obj.strftime('%Y-%m-%d'))
                else:
                    # 使用默认日期范围（过去365天）
                    start_date = datetime.now() - timedelta(days=365)
                    dates = []
                    for i in range(NUM_ROWS):
                        date_obj = start_date + timedelta(days=i)
                        dates.append(date_obj.strftime('%Y-%m-%d'))
                
                # 关键：确保dates是一个列表，每个元素是独立的字符串
                # 验证dates的类型和内容
                if not isinstance(dates, list):
                    raise ValueError(f"日期列 {field_name} 生成失败：dates 不是列表类型，而是 {type(dates)}")
                if len(dates) != NUM_ROWS:
                    raise ValueError(f"日期列 {field_name} 生成失败：期望{NUM_ROWS}个日期，实际 {len(dates)} 个")
                # 确保每个元素都是字符串
                dates = [str(d) for d in dates]
                
                # 验证：确保每个日期都是独立的字符串，不是连接在一起的
                sample_dates = dates[:5]
                for i, d in enumerate(sample_dates):
                    if not isinstance(d, str):
                        raise ValueError(f"日期列 {field_name} 第 {i} 个日期不是字符串类型: {type(d)}")
                    if len(d) != 10 or not d.startswith('20'):
                        raise ValueError(f"日期列 {field_name} 第 {i} 个日期格式异常: {d}")
                
                print(f"日期列 {field_name} 生成成功: 列表长度={len(dates)}, 前5个={sample_dates}, 类型={type(dates)}")
                data[field_name] = dates
            elif field_type == 'boolean':
                # 布尔类型
                # 关键：将numpy数组转换为Python列表
                values = np.random.choice([True, False], NUM_ROWS)
                data[field_name] = values.tolist()  # 转换为Python列表
            else:
                # 字符串类型（默认）
                data[field_name] = [f'{field_name}_{i+1}' for i in range(NUM_ROWS)]
        
        # 验证数据字典：确保所有值都是列表，且长度一致
        # 关键：如果值是numpy数组，转换为Python列表（双重保险）
        expected_length = NUM_ROWS
        print(f"[_load_template_data] 开始验证数据字典，字段数: {len(data)}")
        for field_name, field_values in data.items():
            print(f"[_load_template_data] 验证字段 {field_name}: 类型={type(field_values)}, 值示例={field_values[:3] if isinstance(field_values, list) and len(field_values) > 0 else field_values}")
            
            # 如果是numpy数组，转换为Python列表
            if isinstance(field_values, np.ndarray):
                print(f"[_load_template_data] 检测到字段 {field_name} 是numpy数组，正在转换为Python列表...")
                data[field_name] = field_values.tolist()
                field_values = data[field_name]
                print(f"[_load_template_data] 字段 {field_name} 已转换为列表类型: {type(field_values)}")
            elif hasattr(field_values, 'tolist'):
                # 其他可能有tolist方法的对象（如pandas Series）
                print(f"[_load_template_data] 检测到字段 {field_name} 有tolist方法，正在转换...")
                data[field_name] = field_values.tolist()
                field_values = data[field_name]
                print(f"[_load_template_data] 字段 {field_name} 已转换为列表类型: {type(field_values)}")
            elif isinstance(field_values, str):
                # 关键：如果值是字符串，说明可能被错误转换了
                # 检查是否是列表的字符串表示
                if field_values.startswith('[') and field_values.endswith(']'):
                    print(f"[_load_template_data] 警告: 字段 {field_name} 是列表的字符串表示，尝试解析...")
                    try:
                        import ast
                        field_values = ast.literal_eval(field_values)
                        data[field_name] = field_values
                        print(f"[_load_template_data] 字段 {field_name} 已从字符串解析为列表")
                    except:
                        raise ValueError(f"字段 {field_name} 的值是字符串（可能是列表的字符串表示），无法解析: {field_values[:100]}")
                else:
                    # 如果是普通字符串，可能是日期被错误连接了
                    if len(field_values) > 20 and '2024' in field_values or '2025' in field_values:
                        raise ValueError(f"字段 {field_name} 的值是字符串，且看起来像被连接的日期: {field_values[:100]}... (长度: {len(field_values)})")
                    else:
                        raise ValueError(f"字段 {field_name} 的值是字符串而不是列表: {field_values[:100]}")
            
            if not isinstance(field_values, list):
                raise ValueError(f"字段 {field_name} 的值不是列表类型，而是 {type(field_values)}: {field_values}")
            if len(field_values) != expected_length:
                raise ValueError(f"字段 {field_name} 的值列表长度不一致：期望 {expected_length}，实际 {len(field_values)}")
            
            # 额外检查：如果列表中的元素是字符串，检查是否有被连接的日期
            if len(field_values) > 0 and isinstance(field_values[0], str):
                sample_val = field_values[0]
                if len(sample_val) > 20 and ('2024' in sample_val or '2025' in sample_val):
                    # 检查是否包含多个日期（被连接）
                    date_count = sample_val.count('2024') + sample_val.count('2025')
                    if date_count > 1:
                        raise ValueError(f"字段 {field_name} 的第一个值看起来像被连接的日期字符串: {sample_val[:100]}... (包含 {date_count} 个年份)")
        
        print(f"[_load_template_data] 数据字典验证完成，所有字段都是列表类型")
        
        # 关键：在创建DataFrame之前，再次验证日期列的值
        for field in fields:
            field_name = field.get('name', '')
            field_type = field.get('type', 'string')
            if field_type == 'date' and field_name in data:
                field_values = data[field_name]
                if isinstance(field_values, list) and len(field_values) > 0:
                    # 检查第一个值是否是字符串，且长度正确
                    first_val = field_values[0]
                    if isinstance(first_val, str) and len(first_val) > 20:
                        date_count = first_val.count('2024') + first_val.count('2025')
                        if date_count > 1:
                            print(f"[_load_template_data] ❌ 严重错误: 在创建DataFrame之前，日期列 {field_name} 的第一个值是被连接的字符串: {first_val[:100]}...")
                            # 立即修复：提取所有日期并重新构建列表
                            import re
                            date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
                            fixed_values = []
                            for val in field_values:
                                val_str = str(val)
                                if len(val_str) > 20:
                                    dates_found = date_pattern.findall(val_str)
                                    if len(dates_found) > 0:
                                        fixed_values.append(dates_found[0])
                                    else:
                                        fixed_values.append(val_str[:10] if len(val_str) >= 10 else val_str)
                                else:
                                    fixed_values.append(val_str[:10] if len(val_str) >= 10 else val_str)
                            data[field_name] = fixed_values
                            print(f"[_load_template_data] ✅ 已修复日期列 {field_name}，重新构建为列表，长度: {len(fixed_values)}")
        
        df = pd.DataFrame(data)
        
        # 根据字段类型确保数据类型正确
        for field in fields:
            field_name = field.get('name', '')
            field_type = field.get('type', 'string')
            
            # 自动识别ID字段
            field_name_lower = field_name.lower()
            if 'id' in field_name_lower and field_type == 'string':
                if field_name_lower == 'id' or (field_name_lower.endswith('_id') and field_name_lower not in ['customer_id', 'order_id', 'user_id', 'product_id', 'patient_id', 'student_id', 'call_id', 'claim_id', 'policy_id', 'shipment_id']):
                    field_type = 'integer'
            
            if field_name in df.columns:
                if field_type == 'integer':
                    # 确保整数类型（使用标准int64，SDGX不支持Int64）
                    try:
                        numeric_series = pd.to_numeric(df[field_name], errors='coerce')
                        # 填充NaN为0，然后转换为int64
                        df[field_name] = numeric_series.fillna(0).astype('int64')
                        print(f"[_load_template_data] 字段 {field_name} 已转换为integer类型")
                    except Exception as e:
                        print(f"[_load_template_data] 警告: 字段 {field_name} 转换为integer失败: {e}")
                elif field_type == 'float':
                    # 确保浮点数类型
                    try:
                        df[field_name] = pd.to_numeric(df[field_name], errors='coerce').astype('float64')
                        print(f"[_load_template_data] 字段 {field_name} 已转换为float类型")
                    except Exception as e:
                        print(f"[_load_template_data] 警告: 字段 {field_name} 转换为float失败: {e}")
                elif field_type == 'boolean':
                    # 确保布尔类型
                    try:
                        df[field_name] = df[field_name].astype('bool')
                        print(f"[_load_template_data] 字段 {field_name} 已转换为boolean类型")
                    except Exception as e:
                        print(f"[_load_template_data] 警告: 字段 {field_name} 转换为boolean失败: {e}")
        
        # 验证DataFrame创建后的日期列
        for field in fields:
            field_name = field.get('name', '')
            field_type = field.get('type', 'string')
            if field_type == 'date' and field_name in df.columns:
                # 验证：确保日期列是列表格式，每个元素是独立的字符串
                sample_values = df[field_name].head(10).tolist()
                print(f"[_load_template_data] DataFrame创建后，日期列 {field_name} 的样本值: {sample_values}")
                
                for i, val in enumerate(sample_values):
                    val_str = str(val).strip()
                    if len(val_str) > 20:  # 单个日期字符串不应该超过20个字符
                        date_count = val_str.count('2024') + val_str.count('2025')
                        if date_count > 1:
                            print(f"[_load_template_data] ❌ 严重错误: DataFrame创建后，日期列 {field_name} 第 {i} 行值异常（被连接）: 长度={len(val_str)}, 值={val_str[:100]}...")
                            # 立即修复
                            import re
                            date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
                            dates_found = date_pattern.findall(val_str)
                            if len(dates_found) > 0:
                                df.at[i, field_name] = dates_found[0]
                                print(f"[_load_template_data] ✅ 已修复第 {i} 行: {val_str[:50]}... -> {dates_found[0]}")
                            else:
                                df.at[i, field_name] = val_str[:10]
                                print(f"[_load_template_data] ✅ 已修复第 {i} 行: {val_str[:50]}... -> {val_str[:10]}")
                
                # 确保日期列是字符串类型，避免pandas自动转换
                df[field_name] = df[field_name].astype('object')
                # 再次确保所有值都是10个字符
                df[field_name] = df[field_name].apply(lambda x: str(x)[:10] if len(str(x)) > 10 else str(x))
                df[field_name] = df[field_name].astype('object')
                
                final_sample = df[field_name].head(5).tolist()
                print(f"[_load_template_data] 日期列 {field_name} 最终样本值: {final_sample}")
        
        # 最终验证：确保DataFrame不为空且数据正确
        if df.empty:
            raise ValueError("生成的模板数据为空，无法进行模型训练")
        
        # 确保数据正好是10行
        if df.shape[0] < 10:
            print(f"[_load_template_data] 警告: 生成的数据行数较少 ({df.shape[0]} 行)，扩展到10行")
            # 如果数据少于10行，复制数据直到有10行
            while df.shape[0] < 10:
                rows_to_add = min(10 - df.shape[0], df.shape[0])
                df = pd.concat([df, df.head(rows_to_add)], ignore_index=True)
            print(f"[_load_template_data] 数据已扩展到 {df.shape[0]} 行")
        elif df.shape[0] > 10:
            print(f"[_load_template_data] 生成的数据行数过多 ({df.shape[0]} 行)，截取前10行")
            df = df.head(10).copy()
        
        # 验证所有列都有数据
        for col in df.columns:
            if df[col].isna().all():
                raise ValueError(f"列 {col} 全部为NaN，无法进行模型训练")
            # 检查日期列是否被错误连接
            if df[col].dtype == 'object':
                sample_val = df[col].iloc[0] if len(df) > 0 else None
                if sample_val and isinstance(sample_val, str):
                    if len(sample_val) > 20 and ('2024' in sample_val or '2025' in sample_val):
                        date_count = sample_val.count('2024') + sample_val.count('2025')
                        if date_count > 1:
                            raise ValueError(f"列 {col} 的值看起来像被连接的日期字符串: {sample_val[:100]}... (包含 {date_count} 个年份)")
        
        # 最终修复：确保所有日期列都被正确修复（使用新模块或旧类）
        if self.data_validator:
            date_columns = self.data_validator.identify_date_columns(df)
            if date_columns:
                print(f"[_load_template_data] 最终修复日期列: {list(date_columns)}")
                df = self.data_validator.fix_date_columns(df, date_columns)
        else:
            date_columns = DataFrameValidator.identify_date_columns(df)
            if date_columns:
                print(f"[_load_template_data] 最终修复日期列: {list(date_columns)}")
                df = DataFrameValidator.fix_date_columns(df, date_columns)
        
        print(f"[_load_template_data] 模板数据生成完成: {df.shape[0]} 行 × {df.shape[1]} 列")
        print(f"[_load_template_data] 字段列表: {list(df.columns)}")
        print(f"[_load_template_data] 数据类型: {df.dtypes.to_dict()}")
        print(f"[_load_template_data] 数据样本（前3行）:")
        print(df.head(3))
        return df
    
    def _get_templates_data(self):
        """获取模板数据（避免循环导入）"""
        # 直接从routes/synthetic.py复制完整的模板定义
        # 这样可以避免循环导入问题，并确保字段一致性
        templates = [
            {
                'id': 1,
                'name': '银行客户模板',
                'category': '金融',
                'description': '包含客户基本信息、账户行为、风险画像等字段配置',
                'fields': [
                    {'name': 'customer_id', 'type': 'string', 'description': '客户ID'},
                    {'name': 'name', 'type': 'string', 'description': '客户姓名'},
                    {'name': 'age', 'type': 'integer', 'description': '年龄', 'range': [18, 80]},
                    {'name': 'gender', 'type': 'string', 'description': '性别'},
                    {'name': 'income', 'type': 'float', 'description': '年收入', 'range': [30000, 500000]},
                    {'name': 'credit_score', 'type': 'integer', 'description': '信用评分', 'range': [300, 850]},
                    {'name': 'account_balance', 'type': 'float', 'description': '账户余额', 'range': [0, 1000000]},
                    {'name': 'loan_amount', 'type': 'float', 'description': '贷款金额', 'range': [0, 500000]},
                    {'name': 'register_date', 'type': 'date', 'description': '注册日期'}
                ],
                'sample_data': [
                    {'customer_id': 'C001', 'name': '张三', 'age': 35, 'gender': '男', 'income': 120000, 'credit_score': 720, 'account_balance': 50000, 'loan_amount': 200000, 'register_date': '2020-01-15'},
                    {'customer_id': 'C002', 'name': '李四', 'age': 28, 'gender': '女', 'income': 80000, 'credit_score': 680, 'account_balance': 30000, 'loan_amount': 0, 'register_date': '2021-03-20'},
                    {'customer_id': 'C003', 'name': '王五', 'age': 42, 'gender': '男', 'income': 150000, 'credit_score': 750, 'account_balance': 80000, 'loan_amount': 300000, 'register_date': '2019-05-10'},
                    {'customer_id': 'C004', 'name': '赵六', 'age': 31, 'gender': '女', 'income': 95000, 'credit_score': 690, 'account_balance': 40000, 'loan_amount': 150000, 'register_date': '2021-08-25'},
                    {'customer_id': 'C005', 'name': '孙七', 'age': 45, 'gender': '男', 'income': 180000, 'credit_score': 780, 'account_balance': 120000, 'loan_amount': 400000, 'register_date': '2018-11-30'},
                    {'customer_id': 'C006', 'name': '周八', 'age': 26, 'gender': '女', 'income': 70000, 'credit_score': 650, 'account_balance': 25000, 'loan_amount': 100000, 'register_date': '2022-02-14'},
                    {'customer_id': 'C007', 'name': '吴九', 'age': 38, 'gender': '男', 'income': 130000, 'credit_score': 710, 'account_balance': 60000, 'loan_amount': 250000, 'register_date': '2020-07-08'},
                    {'customer_id': 'C008', 'name': '郑十', 'age': 29, 'gender': '女', 'income': 85000, 'credit_score': 670, 'account_balance': 35000, 'loan_amount': 120000, 'register_date': '2021-12-05'},
                    {'customer_id': 'C009', 'name': '钱一', 'age': 50, 'gender': '男', 'income': 200000, 'credit_score': 800, 'account_balance': 150000, 'loan_amount': 500000, 'register_date': '2017-09-12'},
                    {'customer_id': 'C010', 'name': '孙二', 'age': 33, 'gender': '女', 'income': 110000, 'credit_score': 700, 'account_balance': 55000, 'loan_amount': 180000, 'register_date': '2020-04-18'}
                ]
            },
            {
                'id': 2,
                'name': '话单模板',
                'category': '通信',
                'description': '含基站、时段、通话类型等字段，可快速生成通联数据',
                'fields': [
                    {'name': 'call_id', 'type': 'string', 'description': '通话ID'},
                    {'name': 'caller_number', 'type': 'string', 'description': '主叫号码'},
                    {'name': 'callee_number', 'type': 'string', 'description': '被叫号码'},
                    {'name': 'call_type', 'type': 'string', 'description': '通话类型'},
                    {'name': 'call_duration', 'type': 'integer', 'description': '通话时长（秒）', 'range': [0, 3600]},
                    {'name': 'base_station_id', 'type': 'string', 'description': '基站ID'},
                    {'name': 'call_time', 'type': 'date', 'description': '通话时间'},
                    {'name': 'location', 'type': 'string', 'description': '通话地点'},
                    {'name': 'cost', 'type': 'float', 'description': '通话费用', 'range': [0, 100]}
                ],
                'sample_data': [
                    {'call_id': 'CALL001', 'caller_number': '13800138000', 'callee_number': '13900139000', 'call_type': '语音', 'call_duration': 120, 'base_station_id': 'BS001', 'call_time': '2025-01-18', 'location': '北京市', 'cost': 0.5},
                    {'call_id': 'CALL002', 'caller_number': '13800138001', 'callee_number': '13900139001', 'call_type': '视频', 'call_duration': 300, 'base_station_id': 'BS002', 'call_time': '2025-01-19', 'location': '上海市', 'cost': 2.0},
                    {'call_id': 'CALL003', 'caller_number': '13800138002', 'callee_number': '13900139002', 'call_type': '语音', 'call_duration': 180, 'base_station_id': 'BS003', 'call_time': '2025-01-20', 'location': '广州市', 'cost': 1.0},
                    {'call_id': 'CALL004', 'caller_number': '13800138003', 'callee_number': '13900139003', 'call_type': '视频', 'call_duration': 450, 'base_station_id': 'BS001', 'call_time': '2025-01-21', 'location': '深圳市', 'cost': 3.0},
                    {'call_id': 'CALL005', 'caller_number': '13800138004', 'callee_number': '13900139004', 'call_type': '语音', 'call_duration': 90, 'base_station_id': 'BS004', 'call_time': '2025-01-22', 'location': '杭州市', 'cost': 0.8},
                    {'call_id': 'CALL006', 'caller_number': '13800138005', 'callee_number': '13900139005', 'call_type': '视频', 'call_duration': 600, 'base_station_id': 'BS002', 'call_time': '2025-01-23', 'location': '成都市', 'cost': 4.0},
                    {'call_id': 'CALL007', 'caller_number': '13800138006', 'callee_number': '13900139006', 'call_type': '语音', 'call_duration': 240, 'base_station_id': 'BS005', 'call_time': '2025-01-24', 'location': '武汉市', 'cost': 1.5},
                    {'call_id': 'CALL008', 'caller_number': '13800138007', 'callee_number': '13900139007', 'call_type': '视频', 'call_duration': 360, 'base_station_id': 'BS003', 'call_time': '2025-01-25', 'location': '西安市', 'cost': 2.5},
                    {'call_id': 'CALL009', 'caller_number': '13800138008', 'callee_number': '13900139008', 'call_type': '语音', 'call_duration': 150, 'base_station_id': 'BS001', 'call_time': '2025-01-26', 'location': '南京市', 'cost': 1.2},
                    {'call_id': 'CALL010', 'caller_number': '13800138009', 'callee_number': '13900139009', 'call_type': '视频', 'call_duration': 480, 'base_station_id': 'BS004', 'call_time': '2025-01-27', 'location': '重庆市', 'cost': 3.5}
                ]
            },
            {
                'id': 3,
                'name': '门店销售模板',
                'category': '零售',
                'description': '覆盖商品、库存、销售记录，适合场景模拟',
                'fields': [
                    {'name': 'order_id', 'type': 'string', 'description': '订单ID'},
                    {'name': 'product_id', 'type': 'string', 'description': '商品ID'},
                    {'name': 'product_name', 'type': 'string', 'description': '商品名称'},
                    {'name': 'category', 'type': 'string', 'description': '商品分类'},
                    {'name': 'quantity', 'type': 'integer', 'description': '数量', 'range': [1, 100]},
                    {'name': 'unit_price', 'type': 'float', 'description': '单价', 'range': [1, 10000]},
                    {'name': 'total_amount', 'type': 'float', 'description': '总金额', 'range': [1, 100000]},
                    {'name': 'customer_id', 'type': 'string', 'description': '客户ID'},
                    {'name': 'store_id', 'type': 'string', 'description': '门店ID'},
                    {'name': 'sale_date', 'type': 'date', 'description': '销售日期'}
                ],
                'sample_data': [
                    {'order_id': 'ORD001', 'product_id': 'P001', 'product_name': 'iPhone 15', 'category': '电子产品', 'quantity': 1, 'unit_price': 5999, 'total_amount': 5999, 'customer_id': 'C001', 'store_id': 'S001', 'sale_date': '2025-01-18'},
                    {'order_id': 'ORD002', 'product_id': 'P002', 'product_name': 'MacBook Pro', 'category': '电子产品', 'quantity': 1, 'unit_price': 12999, 'total_amount': 12999, 'customer_id': 'C002', 'store_id': 'S001', 'sale_date': '2025-01-19'},
                    {'order_id': 'ORD003', 'product_id': 'P003', 'product_name': 'iPad Air', 'category': '电子产品', 'quantity': 2, 'unit_price': 4599, 'total_amount': 9198, 'customer_id': 'C003', 'store_id': 'S002', 'sale_date': '2025-01-20'},
                    {'order_id': 'ORD004', 'product_id': 'P004', 'product_name': 'AirPods Pro', 'category': '电子产品', 'quantity': 3, 'unit_price': 1899, 'total_amount': 5697, 'customer_id': 'C004', 'store_id': 'S001', 'sale_date': '2025-01-21'},
                    {'order_id': 'ORD005', 'product_id': 'P005', 'product_name': 'Apple Watch', 'category': '电子产品', 'quantity': 1, 'unit_price': 2999, 'total_amount': 2999, 'customer_id': 'C005', 'store_id': 'S003', 'sale_date': '2025-01-22'},
                    {'order_id': 'ORD006', 'product_id': 'P006', 'product_name': '华为Mate60', 'category': '电子产品', 'quantity': 1, 'unit_price': 6999, 'total_amount': 6999, 'customer_id': 'C006', 'store_id': 'S002', 'sale_date': '2025-01-23'},
                    {'order_id': 'ORD007', 'product_id': 'P007', 'product_name': '小米14', 'category': '电子产品', 'quantity': 2, 'unit_price': 3999, 'total_amount': 7998, 'customer_id': 'C007', 'store_id': 'S001', 'sale_date': '2025-01-24'},
                    {'order_id': 'ORD008', 'product_id': 'P008', 'product_name': '联想ThinkPad', 'category': '电子产品', 'quantity': 1, 'unit_price': 8999, 'total_amount': 8999, 'customer_id': 'C008', 'store_id': 'S003', 'sale_date': '2025-01-25'},
                    {'order_id': 'ORD009', 'product_id': 'P009', 'product_name': '戴尔XPS', 'category': '电子产品', 'quantity': 1, 'unit_price': 10999, 'total_amount': 10999, 'customer_id': 'C009', 'store_id': 'S002', 'sale_date': '2025-01-26'},
                    {'order_id': 'ORD010', 'product_id': 'P010', 'product_name': 'Surface Pro', 'category': '电子产品', 'quantity': 1, 'unit_price': 7999, 'total_amount': 7999, 'customer_id': 'C010', 'store_id': 'S001', 'sale_date': '2025-01-27'}
                ]
            },
            {
                'id': 4,
                'name': '电商订单模板',
                'category': '零售',
                'description': '包含订单信息、商品详情、用户行为等字段',
                'fields': [
                    {'name': 'order_id', 'type': 'string', 'description': '订单号'},
                    {'name': 'user_id', 'type': 'string', 'description': '用户ID'},
                    {'name': 'product_id', 'type': 'string', 'description': '商品ID'},
                    {'name': 'product_name', 'type': 'string', 'description': '商品名称'},
                    {'name': 'quantity', 'type': 'integer', 'description': '购买数量', 'range': [1, 50]},
                    {'name': 'price', 'type': 'float', 'description': '商品价格', 'range': [1, 50000]},
                    {'name': 'discount', 'type': 'float', 'description': '折扣', 'range': [0, 1]},
                    {'name': 'payment_method', 'type': 'string', 'description': '支付方式'},
                    {'name': 'shipping_address', 'type': 'string', 'description': '收货地址'},
                    {'name': 'order_status', 'type': 'string', 'description': '订单状态'},
                    {'name': 'order_time', 'type': 'date', 'description': '下单时间'}
                ],
                'sample_data': [
                    {'order_id': 'E001', 'user_id': 'U001', 'product_id': 'P001', 'product_name': '商品A', 'quantity': 2, 'price': 199, 'discount': 0.9, 'payment_method': '支付宝', 'shipping_address': '北京市朝阳区', 'order_status': '已发货', 'order_time': '2025-01-18'},
                    {'order_id': 'E002', 'user_id': 'U002', 'product_id': 'P002', 'product_name': '商品B', 'quantity': 1, 'price': 299, 'discount': 0.95, 'payment_method': '微信支付', 'shipping_address': '上海市浦东新区', 'order_status': '待发货', 'order_time': '2025-01-19'},
                    {'order_id': 'E003', 'user_id': 'U003', 'product_id': 'P003', 'product_name': '商品C', 'quantity': 3, 'price': 99, 'discount': 0.8, 'payment_method': '银行卡', 'shipping_address': '广州市天河区', 'order_status': '已发货', 'order_time': '2025-01-20'},
                    {'order_id': 'E004', 'user_id': 'U004', 'product_id': 'P004', 'product_name': '商品D', 'quantity': 1, 'price': 599, 'discount': 1.0, 'payment_method': '支付宝', 'shipping_address': '深圳市南山区', 'order_status': '已完成', 'order_time': '2025-01-21'},
                    {'order_id': 'E005', 'user_id': 'U005', 'product_id': 'P005', 'product_name': '商品E', 'quantity': 2, 'price': 399, 'discount': 0.85, 'payment_method': '微信支付', 'shipping_address': '杭州市西湖区', 'order_status': '已发货', 'order_time': '2025-01-22'},
                    {'order_id': 'E006', 'user_id': 'U006', 'product_id': 'P006', 'product_name': '商品F', 'quantity': 1, 'price': 899, 'discount': 0.9, 'payment_method': '银行卡', 'shipping_address': '成都市锦江区', 'order_status': '待发货', 'order_time': '2025-01-23'},
                    {'order_id': 'E007', 'user_id': 'U007', 'product_id': 'P007', 'product_name': '商品G', 'quantity': 4, 'price': 149, 'discount': 0.75, 'payment_method': '支付宝', 'shipping_address': '武汉市江汉区', 'order_status': '已发货', 'order_time': '2025-01-24'},
                    {'order_id': 'E008', 'user_id': 'U008', 'product_id': 'P008', 'product_name': '商品H', 'quantity': 1, 'price': 1299, 'discount': 0.95, 'payment_method': '微信支付', 'shipping_address': '西安市雁塔区', 'order_status': '已完成', 'order_time': '2025-01-25'},
                    {'order_id': 'E009', 'user_id': 'U009', 'product_id': 'P009', 'product_name': '商品I', 'quantity': 2, 'price': 499, 'discount': 0.88, 'payment_method': '银行卡', 'shipping_address': '南京市鼓楼区', 'order_status': '已发货', 'order_time': '2025-01-26'},
                    {'order_id': 'E010', 'user_id': 'U010', 'product_id': 'P010', 'product_name': '商品J', 'quantity': 1, 'price': 699, 'discount': 0.92, 'payment_method': '支付宝', 'shipping_address': '重庆市渝中区', 'order_status': '待发货', 'order_time': '2025-01-27'}
                ]
            },
            {
                'id': 5,
                'name': '患者信息模板',
                'category': '医疗',
                'description': '包含患者基本信息、诊断记录、用药信息等字段',
                'fields': [
                    {'name': 'patient_id', 'type': 'string', 'description': '患者ID'},
                    {'name': 'name', 'type': 'string', 'description': '患者姓名'},
                    {'name': 'age', 'type': 'integer', 'description': '年龄', 'range': [0, 120]},
                    {'name': 'gender', 'type': 'string', 'description': '性别'},
                    {'name': 'diagnosis', 'type': 'string', 'description': '诊断结果'},
                    {'name': 'symptoms', 'type': 'string', 'description': '症状描述'},
                    {'name': 'medication', 'type': 'string', 'description': '用药信息'},
                    {'name': 'temperature', 'type': 'float', 'description': '体温', 'range': [35.0, 42.0]},
                    {'name': 'blood_pressure', 'type': 'string', 'description': '血压'},
                    {'name': 'visit_date', 'type': 'date', 'description': '就诊日期'}
                ],
                'sample_data': [
                    {'patient_id': 'P001', 'name': '患者A', 'age': 45, 'gender': '男', 'diagnosis': '感冒', 'symptoms': '咳嗽、发热', 'medication': '感冒药', 'temperature': 37.5, 'blood_pressure': '120/80', 'visit_date': '2025-01-18'},
                    {'patient_id': 'P002', 'name': '患者B', 'age': 32, 'gender': '女', 'diagnosis': '胃炎', 'symptoms': '胃痛、恶心', 'medication': '胃药', 'temperature': 36.8, 'blood_pressure': '110/70', 'visit_date': '2025-01-19'},
                    {'patient_id': 'P003', 'name': '患者C', 'age': 58, 'gender': '男', 'diagnosis': '高血压', 'symptoms': '头晕、乏力', 'medication': '降压药', 'temperature': 36.9, 'blood_pressure': '150/95', 'visit_date': '2025-01-20'},
                    {'patient_id': 'P004', 'name': '患者D', 'age': 28, 'gender': '女', 'diagnosis': '过敏', 'symptoms': '皮疹、瘙痒', 'medication': '抗过敏药', 'temperature': 37.0, 'blood_pressure': '105/65', 'visit_date': '2025-01-21'},
                    {'patient_id': 'P005', 'name': '患者E', 'age': 65, 'gender': '男', 'diagnosis': '糖尿病', 'symptoms': '多饮、多尿', 'medication': '降糖药', 'temperature': 36.7, 'blood_pressure': '130/85', 'visit_date': '2025-01-22'},
                    {'patient_id': 'P006', 'name': '患者F', 'age': 41, 'gender': '女', 'diagnosis': '头痛', 'symptoms': '持续性头痛', 'medication': '止痛药', 'temperature': 36.8, 'blood_pressure': '115/75', 'visit_date': '2025-01-23'},
                    {'patient_id': 'P007', 'name': '患者G', 'age': 52, 'gender': '男', 'diagnosis': '关节炎', 'symptoms': '关节疼痛', 'medication': '消炎药', 'temperature': 37.1, 'blood_pressure': '125/80', 'visit_date': '2025-01-24'},
                    {'patient_id': 'P008', 'name': '患者H', 'age': 35, 'gender': '女', 'diagnosis': '失眠', 'symptoms': '入睡困难', 'medication': '安眠药', 'temperature': 36.6, 'blood_pressure': '108/68', 'visit_date': '2025-01-25'},
                    {'patient_id': 'P009', 'name': '患者I', 'age': 48, 'gender': '男', 'diagnosis': '支气管炎', 'symptoms': '咳嗽、胸闷', 'medication': '止咳药', 'temperature': 37.3, 'blood_pressure': '118/78', 'visit_date': '2025-01-26'},
                    {'patient_id': 'P010', 'name': '患者J', 'age': 29, 'gender': '女', 'diagnosis': '月经不调', 'symptoms': '周期紊乱', 'medication': '调经药', 'temperature': 36.9, 'blood_pressure': '112/72', 'visit_date': '2025-01-27'}
                ]
            },
            {
                'id': 6,
                'name': '学生信息模板',
                'category': '教育',
                'description': '包含学生基本信息、成绩记录、课程信息等字段',
                'fields': [
                    {'name': 'student_id', 'type': 'string', 'description': '学生ID'},
                    {'name': 'name', 'type': 'string', 'description': '学生姓名'},
                    {'name': 'age', 'type': 'integer', 'description': '年龄', 'range': [6, 25]},
                    {'name': 'grade', 'type': 'string', 'description': '年级'},
                    {'name': 'class', 'type': 'string', 'description': '班级'},
                    {'name': 'subject', 'type': 'string', 'description': '科目'},
                    {'name': 'score', 'type': 'float', 'description': '成绩', 'range': [0, 100]},
                    {'name': 'attendance_rate', 'type': 'float', 'description': '出勤率', 'range': [0, 1]},
                    {'name': 'exam_date', 'type': 'date', 'description': '考试日期'}
                ],
                'sample_data': [
                    {'student_id': 'S001', 'name': '学生A', 'age': 15, 'grade': '初三', 'class': '3班', 'subject': '数学', 'score': 85, 'attendance_rate': 0.95, 'exam_date': '2025-01-18'},
                    {'student_id': 'S002', 'name': '学生B', 'age': 16, 'grade': '高一', 'class': '1班', 'subject': '语文', 'score': 92, 'attendance_rate': 0.98, 'exam_date': '2025-01-19'},
                    {'student_id': 'S003', 'name': '学生C', 'age': 14, 'grade': '初二', 'class': '2班', 'subject': '英语', 'score': 78, 'attendance_rate': 0.90, 'exam_date': '2025-01-20'},
                    {'student_id': 'S004', 'name': '学生D', 'age': 17, 'grade': '高二', 'class': '5班', 'subject': '物理', 'score': 88, 'attendance_rate': 0.96, 'exam_date': '2025-01-21'},
                    {'student_id': 'S005', 'name': '学生E', 'age': 15, 'grade': '初三', 'class': '4班', 'subject': '化学', 'score': 75, 'attendance_rate': 0.92, 'exam_date': '2025-01-22'},
                    {'student_id': 'S006', 'name': '学生F', 'age': 16, 'grade': '高一', 'class': '2班', 'subject': '生物', 'score': 90, 'attendance_rate': 0.97, 'exam_date': '2025-01-23'},
                    {'student_id': 'S007', 'name': '学生G', 'age': 14, 'grade': '初二', 'class': '1班', 'subject': '历史', 'score': 82, 'attendance_rate': 0.94, 'exam_date': '2025-01-24'},
                    {'student_id': 'S008', 'name': '学生H', 'age': 17, 'grade': '高二', 'class': '3班', 'subject': '地理', 'score': 79, 'attendance_rate': 0.91, 'exam_date': '2025-01-25'},
                    {'student_id': 'S009', 'name': '学生I', 'age': 15, 'grade': '初三', 'class': '5班', 'subject': '政治', 'score': 86, 'attendance_rate': 0.93, 'exam_date': '2025-01-26'},
                    {'student_id': 'S010', 'name': '学生J', 'age': 16, 'grade': '高一', 'class': '4班', 'subject': '体育', 'score': 95, 'attendance_rate': 0.99, 'exam_date': '2025-01-27'}
                ]
            },
            {
                'id': 7,
                'name': '保险理赔模板',
                'category': '金融',
                'description': '包含保单信息、理赔记录、审核流程等字段',
                'fields': [
                    {'name': 'claim_id', 'type': 'string', 'description': '理赔ID'},
                    {'name': 'policy_id', 'type': 'string', 'description': '保单号'},
                    {'name': 'customer_id', 'type': 'string', 'description': '客户ID'},
                    {'name': 'claim_type', 'type': 'string', 'description': '理赔类型'},
                    {'name': 'claim_amount', 'type': 'float', 'description': '理赔金额', 'range': [100, 1000000]},
                    {'name': 'accident_date', 'type': 'date', 'description': '事故日期'},
                    {'name': 'claim_date', 'type': 'date', 'description': '申请日期'},
                    {'name': 'status', 'type': 'string', 'description': '理赔状态'},
                    {'name': 'approval_time', 'type': 'integer', 'description': '审核时长（天）', 'range': [1, 90]}
                ],
                'sample_data': [
                    {'claim_id': 'CLM001', 'policy_id': 'POL001', 'customer_id': 'C001', 'claim_type': '医疗', 'claim_amount': 5000, 'accident_date': '2025-01-10', 'claim_date': '2025-01-15', 'status': '已审核', 'approval_time': 5},
                    {'claim_id': 'CLM002', 'policy_id': 'POL002', 'customer_id': 'C002', 'claim_type': '意外', 'claim_amount': 12000, 'accident_date': '2025-01-12', 'claim_date': '2025-01-18', 'status': '已审核', 'approval_time': 6},
                    {'claim_id': 'CLM003', 'policy_id': 'POL003', 'customer_id': 'C003', 'claim_type': '医疗', 'claim_amount': 8000, 'accident_date': '2025-01-08', 'claim_date': '2025-01-14', 'status': '审核中', 'approval_time': 6},
                    {'claim_id': 'CLM004', 'policy_id': 'POL004', 'customer_id': 'C004', 'claim_type': '财产', 'claim_amount': 25000, 'accident_date': '2025-01-05', 'claim_date': '2025-01-12', 'status': '已审核', 'approval_time': 7},
                    {'claim_id': 'CLM005', 'policy_id': 'POL005', 'customer_id': 'C005', 'claim_type': '医疗', 'claim_amount': 3500, 'accident_date': '2025-01-15', 'claim_date': '2025-01-20', 'status': '已审核', 'approval_time': 5},
                    {'claim_id': 'CLM006', 'policy_id': 'POL006', 'customer_id': 'C006', 'claim_type': '意外', 'claim_amount': 15000, 'accident_date': '2025-01-11', 'claim_date': '2025-01-17', 'status': '审核中', 'approval_time': 6},
                    {'claim_id': 'CLM007', 'policy_id': 'POL007', 'customer_id': 'C007', 'claim_type': '医疗', 'claim_amount': 6000, 'accident_date': '2025-01-09', 'claim_date': '2025-01-16', 'status': '已审核', 'approval_time': 7},
                    {'claim_id': 'CLM008', 'policy_id': 'POL008', 'customer_id': 'C008', 'claim_type': '财产', 'claim_amount': 18000, 'accident_date': '2025-01-07', 'claim_date': '2025-01-13', 'status': '已审核', 'approval_time': 6},
                    {'claim_id': 'CLM009', 'policy_id': 'POL009', 'customer_id': 'C009', 'claim_type': '医疗', 'claim_amount': 4200, 'accident_date': '2025-01-13', 'claim_date': '2025-01-19', 'status': '审核中', 'approval_time': 6},
                    {'claim_id': 'CLM010', 'policy_id': 'POL010', 'customer_id': 'C010', 'claim_type': '意外', 'claim_amount': 9800, 'accident_date': '2025-01-14', 'claim_date': '2025-01-21', 'status': '已审核', 'approval_time': 7}
                ]
            },
            {
                'id': 8,
                'name': '物流配送模板',
                'category': '物流',
                'description': '包含订单信息、配送路线、物流状态等字段',
                'fields': [
                    {'name': 'shipment_id', 'type': 'string', 'description': '运单号'},
                    {'name': 'order_id', 'type': 'string', 'description': '订单ID'},
                    {'name': 'sender_address', 'type': 'string', 'description': '发货地址'},
                    {'name': 'receiver_address', 'type': 'string', 'description': '收货地址'},
                    {'name': 'weight', 'type': 'float', 'description': '重量（kg）', 'range': [0.1, 100]},
                    {'name': 'distance', 'type': 'float', 'description': '距离（km）', 'range': [1, 5000]},
                    {'name': 'shipping_fee', 'type': 'float', 'description': '运费', 'range': [5, 500]},
                    {'name': 'status', 'type': 'string', 'description': '配送状态'},
                    {'name': 'ship_date', 'type': 'date', 'description': '发货日期'},
                    {'name': 'delivery_date', 'type': 'date', 'description': '送达日期'}
                ],
                'sample_data': [
                    {'shipment_id': 'SHIP001', 'order_id': 'ORD001', 'sender_address': '北京市', 'receiver_address': '上海市', 'weight': 2.5, 'distance': 1200, 'shipping_fee': 25, 'status': '运输中', 'ship_date': '2025-01-18', 'delivery_date': '2025-01-20'},
                    {'shipment_id': 'SHIP002', 'order_id': 'ORD002', 'sender_address': '广州市', 'receiver_address': '深圳市', 'weight': 1.8, 'distance': 150, 'shipping_fee': 15, 'status': '已送达', 'ship_date': '2025-01-19', 'delivery_date': '2025-01-20'},
                    {'shipment_id': 'SHIP003', 'order_id': 'ORD003', 'sender_address': '上海市', 'receiver_address': '杭州市', 'weight': 3.2, 'distance': 200, 'shipping_fee': 18, 'status': '运输中', 'ship_date': '2025-01-20', 'delivery_date': '2025-01-22'},
                    {'shipment_id': 'SHIP004', 'order_id': 'ORD004', 'sender_address': '成都市', 'receiver_address': '重庆市', 'weight': 1.5, 'distance': 300, 'shipping_fee': 12, 'status': '已送达', 'ship_date': '2025-01-21', 'delivery_date': '2025-01-22'},
                    {'shipment_id': 'SHIP005', 'order_id': 'ORD005', 'sender_address': '北京市', 'receiver_address': '天津市', 'weight': 4.0, 'distance': 120, 'shipping_fee': 20, 'status': '运输中', 'ship_date': '2025-01-22', 'delivery_date': '2025-01-23'},
                    {'shipment_id': 'SHIP006', 'order_id': 'ORD006', 'sender_address': '武汉市', 'receiver_address': '长沙市', 'weight': 2.0, 'distance': 350, 'shipping_fee': 22, 'status': '已送达', 'ship_date': '2025-01-23', 'delivery_date': '2025-01-24'},
                    {'shipment_id': 'SHIP007', 'order_id': 'ORD007', 'sender_address': '西安市', 'receiver_address': '兰州市', 'weight': 3.5, 'distance': 650, 'shipping_fee': 35, 'status': '运输中', 'ship_date': '2025-01-24', 'delivery_date': '2025-01-26'},
                    {'shipment_id': 'SHIP008', 'order_id': 'ORD008', 'sender_address': '南京市', 'receiver_address': '苏州市', 'weight': 1.2, 'distance': 100, 'shipping_fee': 10, 'status': '已送达', 'ship_date': '2025-01-25', 'delivery_date': '2025-01-26'},
                    {'shipment_id': 'SHIP009', 'order_id': 'ORD009', 'sender_address': '杭州市', 'receiver_address': '宁波市', 'weight': 2.8, 'distance': 150, 'shipping_fee': 16, 'status': '运输中', 'ship_date': '2025-01-26', 'delivery_date': '2025-01-27'},
                    {'shipment_id': 'SHIP010', 'order_id': 'ORD010', 'sender_address': '深圳市', 'receiver_address': '东莞市', 'weight': 1.0, 'distance': 80, 'shipping_fee': 8, 'status': '已送达', 'ship_date': '2025-01-27', 'delivery_date': '2025-01-28'}
                ]
            }
        ]
        
        return templates
    
    def _generate_default_template_data(self):
        """生成默认模板数据（向后兼容）"""
        return pd.DataFrame({
            'id': range(100),
            'name': [f'User_{i}' for i in range(100)],
            'age': np.random.randint(18, 80, 100),
            'score': np.random.uniform(0, 100, 100)
        })
    
    def _clean_data(self, df, date_columns=None):
        """清理数据
        
        Args:
            df: 原始DataFrame
            date_columns: 已知的日期列集合（从字段配置中获取），用于避免被错误处理
        """
        df_cleaned = df.copy()
        
        # 使用传入的日期列信息，或自动识别日期列
        if date_columns is None:
            date_columns = set()
        else:
            date_columns = set(date_columns)
        
        # 自动识别日期列（如果未提供）
        for col in df_cleaned.columns:
            if col in date_columns:
                continue  # 已经知道是日期列，跳过
            
            # 检查是否是datetime类型
            if pd.api.types.is_datetime64_any_dtype(df_cleaned[col]):
                date_columns.add(col)
                print(f"识别datetime类型日期列: {col}")
            elif df_cleaned[col].dtype == 'object':
                # 检查是否是日期格式的字符串列
                try:
                    sample_values = df_cleaned[col].dropna().head(10)
                    if len(sample_values) > 0:
                        # 检查是否匹配日期格式 'YYYY-MM-DD'
                        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
                        date_match_count = sum(1 for v in sample_values if pd.notna(v) and str(v).strip() and re.match(date_pattern, str(v)))
                        if date_match_count >= len(sample_values) * 0.8:  # 80%以上匹配日期格式
                            date_columns.add(col)
                            print(f"识别日期格式字符串列: {col}")
                except Exception as e:
                    print(f"检查日期列 {col} 时出错: {e}")
                    pass
        
        # 处理所有日期列：确保是字符串格式
        for col in date_columns:
            if col in df_cleaned.columns:
                # 如果是datetime类型，转换为字符串
                if pd.api.types.is_datetime64_any_dtype(df_cleaned[col]):
                    df_cleaned[col] = df_cleaned[col].astype(str)
                # 确保是字符串类型（object）
                df_cleaned[col] = df_cleaned[col].astype(str)
                # 将 NaN/NaT 转换为空字符串
                df_cleaned[col] = df_cleaned[col].replace(['nan', 'NaN', 'None', 'NaT', '<NaT>', 'nat'], '')
                print(f"日期列 {col} 已设置为字符串格式")
        
        # 清理其他 object 类型的列
        for col in df_cleaned.columns:
            if col in date_columns:
                continue  # 跳过日期列，已经处理过了
            
            if df_cleaned[col].dtype == 'object':
                df_cleaned[col] = df_cleaned[col].replace(['NAN_VALUE', 'nan', 'NaN', 'NULL', 'null', ''], np.nan)
                # 只对非日期列尝试转换为数字
                try:
                    # 使用 errors='ignore' 避免转换失败
                    numeric_col = pd.to_numeric(df_cleaned[col], errors='ignore')
                    # 只有当大部分值都能转换为数字时才转换
                    if numeric_col.notna().sum() > len(df_cleaned) * 0.5:
                        df_cleaned[col] = numeric_col
                except:
                    pass
        
        print(f"数据清理完成，日期列: {date_columns}")
        print(f"清理后数据类型: {df_cleaned.dtypes.to_dict()}")
        return df_cleaned
    
    def _save_result(self, task_id, original_df, synthetic_df, fields_config=None):
        """保存结果"""
        result_dir = os.path.join(self.results_folder, f"task_{task_id}")
        os.makedirs(result_dir, exist_ok=True)
        
        # 保存原始数据（完全保持原始格式，不进行任何类型转换）
        # 原始数据应该与模板数据完全一致，因此直接保存，不进行任何处理
        original_path = os.path.join(result_dir, 'original.csv')
        original_df_save = original_df.copy()
        # 直接保存，保持原始格式（与模板数据一致）
        original_df_save.to_csv(original_path, index=False)
        
        # 保存合成数据
        synthetic_path = os.path.join(result_dir, 'synthetic.csv')
        synthetic_df.to_csv(synthetic_path, index=False)
        
        return result_dir
    
    def _update_progress(self, task_id, progress, message=None):
        """更新任务进度（实时更新到数据库）"""
        try:
            from flask import current_app
            with current_app.app_context():
                task = Task.query.get(task_id)
                if task:
                    old_progress = task.progress
                    task.progress = progress
                    task.updated_at = datetime.utcnow()
                    if message:
                        # 如果Task模型有message字段，可以更新
                        if hasattr(task, 'message'):
                            task.message = message
                    db.session.commit()
                    # 只在进度变化时打印日志，避免日志过多
                    if old_progress != progress:
                        print(f"任务 {task_id} 进度更新: {old_progress}% -> {progress}% {f'({message})' if message else ''}")
                else:
                    print(f"更新进度失败: 任务 {task_id} 不存在")
        except Exception as e:
            print(f"更新进度失败: {e}")
            import traceback
            traceback.print_exc()
    
    def get_result_preview(self, task_id, data_type='synthetic', page=1, page_size=20):
        """获取结果预览"""
        task = Task.query.get(task_id)
        if not task or not task.result_path:
            return None
        
        file_path = os.path.join(task.result_path, f'{data_type}.csv')
        if not os.path.exists(file_path):
            return None
        
        # 对于原始数据，使用dtype=str读取所有列，保持原始格式（与模板数据一致）
        # 对于生成数据，让pandas自动推断类型
        if data_type == 'original':
            # 读取CSV时，将所有列都读取为字符串，保持原始格式
            df = pd.read_csv(file_path, dtype=str)
        else:
            df = pd.read_csv(file_path)
        
        total = len(df)
        start = (page - 1) * page_size
        end = start + page_size
        
        # 获取任务配置中的字段配置信息（用于格式化显示）
        fields_config = None
        if data_type == 'original':
            config = task.get_config()
            fields_config = config.get('fields', [])
        
        # 清理NaN值并保持字段类型
        data_records = df.iloc[start:end].to_dict('records')
        for record in data_records:
            for key, value in record.items():
                if pd.isna(value) or value == 'nan' or value == 'NaN' or value == '':
                    record[key] = None
                else:
                    # 如果是原始数据，保持字符串格式（与模板数据一致）
                    if data_type == 'original':
                        # 原始数据保持为字符串格式，与模板数据一致
                        record[key] = str(value) if value is not None else None
                    else:
                        # 生成数据根据字段类型转换
                        if fields_config:
                            field_config = next((f for f in fields_config if f.get('name') == key), None)
                            if field_config:
                                field_type = field_config.get('type', 'string')
                                if field_type == 'date':
                                    record[key] = str(value) if value is not None else None
                                elif field_type in ['number', 'integer']:
                                    try:
                                        if field_type == 'integer':
                                            record[key] = int(value) if value is not None else None
                                        else:
                                            record[key] = float(value) if value is not None else None
                                    except (ValueError, TypeError):
                                        record[key] = value
                                else:
                                    record[key] = str(value) if value is not None else None
                            else:
                                record[key] = value
                        else:
                            record[key] = value
        
        return {
            'columns': df.columns.tolist(),
            'data': data_records,
            'total': total,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size
            }
        }
    
    def get_result_file_path(self, task_id, data_type='synthetic', format='csv'):
        """获取结果文件路径"""
        task = Task.query.get(task_id)
        if not task or not task.result_path:
            return None
        
        if data_type == 'both':
            # 返回目录路径，需要打包
            return task.result_path
        else:
            file_path = os.path.join(task.result_path, f'{data_type}.csv')
            if os.path.exists(file_path):
                return file_path
        return None
