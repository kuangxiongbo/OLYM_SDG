#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理器
==========

管理不同模型的创建、配置和训练
"""

import sys
import os
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

# 添加SDG路径
sys.path.append('../../synthetic-data-generator')

try:
    from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
    from sdgx.models.LLM.single_table.gpt import SingleTableGPTModel
    from sdgx.synthesizer import Synthesizer
    from sdgx.data_connectors.dataframe_connector import DataFrameConnector
except ImportError as e:
    logging.warning(f"SDG导入失败: {e}")

logger = logging.getLogger(__name__)

class ModelManager:
    """模型管理器类"""
    
    def __init__(self):
        self.available_models = {
            'ctgan': {
                'name': 'CTGAN',
                'description': '基于GAN的表格数据生成模型',
                'suitable_for': ['数值数据', '分类数据', '混合数据'],
                'parameters': self._get_ctgan_parameters()
            },
            'gpt': {
                'name': 'GPT',
                'description': '基于大语言模型的生成模型',
                'suitable_for': ['文本数据', '小数据集', '语义数据'],
                'parameters': self._get_gpt_parameters()
            }
        }
    
    def _get_ctgan_parameters(self) -> Dict[str, Any]:
        """获取CTGAN模型参数"""
        return {
            'epochs': {
                'type': 'number',
                'default': 50,
                'min': 1,
                'max': 1000,
                'description': '训练轮数',
                'help': '训练轮数越多，模型学习越充分，但耗时越长'
            },
            'batch_size': {
                'type': 'number',
                'default': 500,
                'min': 32,
                'max': 2000,
                'description': '批次大小',
                'help': '批次大小影响训练稳定性和速度'
            },
            'generator_lr': {
                'type': 'number',
                'default': 2e-4,
                'min': 1e-6,
                'max': 1e-2,
                'step': 1e-6,
                'description': '生成器学习率',
                'help': '生成器的学习率，控制学习速度'
            },
            'discriminator_lr': {
                'type': 'number',
                'default': 2e-4,
                'min': 1e-6,
                'max': 1e-2,
                'step': 1e-6,
                'description': '判别器学习率',
                'help': '判别器的学习率，控制学习速度'
            },
            'generator_decay': {
                'type': 'number',
                'default': 1e-6,
                'min': 0,
                'max': 1e-3,
                'step': 1e-6,
                'description': '生成器衰减率',
                'help': '生成器的权重衰减，防止过拟合'
            },
            'discriminator_decay': {
                'type': 'number',
                'default': 1e-6,
                'min': 0,
                'max': 1e-3,
                'step': 1e-6,
                'description': '判别器衰减率',
                'help': '判别器的权重衰减，防止过拟合'
            },
            'generator_dim': {
                'type': 'text',
                'default': '(256, 256)',
                'description': '生成器网络维度',
                'help': '生成器网络的隐藏层维度，格式如(256, 256)'
            },
            'discriminator_dim': {
                'type': 'text',
                'default': '(256, 256)',
                'description': '判别器网络维度',
                'help': '判别器网络的隐藏层维度，格式如(256, 256)'
            }
        }
    
    def _get_gpt_parameters(self) -> Dict[str, Any]:
        """获取GPT模型参数"""
        return {
            'openai_API_key': {
                'type': 'password',
                'default': '',
                'description': 'OpenAI API密钥',
                'help': 'OpenAI API密钥，必填项',
                'required': True
            },
            'openai_API_url': {
                'type': 'text',
                'default': 'https://api.openai.com/v1/',
                'description': 'API地址',
                'help': 'OpenAI API地址，支持自定义端点'
            },
            'gpt_model': {
                'type': 'select',
                'default': 'gpt-3.5-turbo',
                'options': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'],
                'description': 'GPT模型版本',
                'help': '选择GPT模型版本，gpt-4效果更好但成本更高'
            },
            'temperature': {
                'type': 'number',
                'default': 0.1,
                'min': 0,
                'max': 2,
                'step': 0.1,
                'description': '温度参数',
                'help': '控制生成的随机性，0-2之间，越小越保守'
            },
            'max_tokens': {
                'type': 'number',
                'default': 2000,
                'min': 100,
                'max': 8000,
                'description': '最大token数',
                'help': '单次生成的最大token数量'
            },
            'timeout': {
                'type': 'number',
                'default': 90,
                'min': 10,
                'max': 300,
                'description': '超时时间',
                'help': 'API请求的超时时间（秒）'
            },
            'query_batch': {
                'type': 'number',
                'default': 10,
                'min': 1,
                'max': 50,
                'description': '查询批次大小',
                'help': '每次查询的样本数量'
            }
        }
    
    def get_available_models(self) -> Dict[str, Any]:
        """获取可用模型列表"""
        return self.available_models
    
    def get_model_parameters(self, model_type: str) -> Dict[str, Any]:
        """获取模型参数配置"""
        if model_type not in self.available_models:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        return self.available_models[model_type]['parameters']
    
    def create_model(self, model_type: str, parameters: Dict[str, Any]) -> Any:
        """创建模型实例"""
        try:
            if model_type == 'ctgan':
                return self._create_ctgan_model(parameters)
            elif model_type == 'gpt':
                return self._create_gpt_model(parameters)
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")
        except Exception as e:
            logger.error(f"创建模型失败: {e}")
            raise
    
    def _create_ctgan_model(self, parameters: Dict[str, Any]) -> CTGANSynthesizerModel:
        """创建CTGAN模型"""
        # 解析网络维度
        generator_dim = self._parse_dimension(parameters.get('generator_dim', '(256, 256)'))
        discriminator_dim = self._parse_dimension(parameters.get('discriminator_dim', '(256, 256)'))
        
        model = CTGANSynthesizerModel(
            epochs=parameters.get('epochs', 50),
            batch_size=parameters.get('batch_size', 500),
            generator_lr=parameters.get('generator_lr', 2e-4),
            discriminator_lr=parameters.get('discriminator_lr', 2e-4),
            generator_decay=parameters.get('generator_decay', 1e-6),
            discriminator_decay=parameters.get('discriminator_decay', 1e-6),
            generator_dim=generator_dim,
            discriminator_dim=discriminator_dim
        )
        
        return model
    
    def _create_gpt_model(self, parameters: Dict[str, Any]) -> SingleTableGPTModel:
        """创建GPT模型"""
        # 验证必填参数
        if not parameters.get('openai_API_key'):
            raise ValueError("GPT模型需要API密钥")
        
        model = SingleTableGPTModel(
            openai_API_key=parameters.get('openai_API_key', ''),
            openai_API_url=parameters.get('openai_API_url', 'https://api.openai.com/v1/'),
            gpt_model=parameters.get('gpt_model', 'gpt-3.5-turbo'),
            temperature=parameters.get('temperature', 0.1),
            max_tokens=parameters.get('max_tokens', 2000),
            timeout=parameters.get('timeout', 90),
            query_batch=parameters.get('query_batch', 10)
        )
        
        return model
    
    def _parse_dimension(self, dim_str: str) -> tuple:
        """解析维度字符串"""
        try:
            # 移除括号和空格
            dim_str = dim_str.strip('()').replace(' ', '')
            # 分割并转换为整数
            dims = [int(x) for x in dim_str.split(',')]
            return tuple(dims)
        except:
            # 默认维度
            return (256, 256)
    
    def validate_parameters(self, model_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证模型参数"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if model_type not in self.available_models:
            validation_result['valid'] = False
            validation_result['errors'].append(f"不支持的模型类型: {model_type}")
            return validation_result
        
        model_params = self.available_models[model_type]['parameters']
        
        # 检查必填参数
        for param_name, param_config in model_params.items():
            if param_config.get('required', False):
                if param_name not in parameters or not parameters[param_name]:
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"必填参数 {param_name} 缺失")
        
        # 检查参数范围
        for param_name, param_value in parameters.items():
            if param_name in model_params:
                param_config = model_params[param_name]
                
                if param_config['type'] == 'number':
                    try:
                        num_value = float(param_value)
                        if 'min' in param_config and num_value < param_config['min']:
                            validation_result['warnings'].append(f"参数 {param_name} 值 {num_value} 小于建议最小值 {param_config['min']}")
                        if 'max' in param_config and num_value > param_config['max']:
                            validation_result['warnings'].append(f"参数 {param_name} 值 {num_value} 大于建议最大值 {param_config['max']}")
                    except ValueError:
                        validation_result['valid'] = False
                        validation_result['errors'].append(f"参数 {param_name} 值 {param_value} 不是有效数字")
        
        return validation_result
    
    def get_model_recommendations(self, data_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据数据特征推荐模型"""
        recommendations = []
        
        # 分析数据特征
        shape = data_info.get('shape', (0, 0))
        rows, cols = shape
        
        # 检查数据类型
        column_types = data_info.get('column_types', {})
        numeric_cols = len(column_types.get('numeric', []))
        categorical_cols = len(column_types.get('categorical', []))
        text_cols = len(column_types.get('text', []))
        
        # CTGAN推荐
        ctgan_score = 0
        ctgan_reasons = []
        
        if rows > 100:  # 数据量足够
            ctgan_score += 3
            ctgan_reasons.append("数据量充足")
        
        if numeric_cols > 0:  # 有数值列
            ctgan_score += 2
            ctgan_reasons.append("包含数值数据")
        
        if categorical_cols > 0:  # 有分类列
            ctgan_score += 2
            ctgan_reasons.append("包含分类数据")
        
        if text_cols == 0:  # 没有文本列
            ctgan_score += 1
            ctgan_reasons.append("无复杂文本数据")
        
        if ctgan_score >= 5:
            recommendations.append({
                'model': 'ctgan',
                'score': ctgan_score,
                'reasons': ctgan_reasons,
                'confidence': 'high'
            })
        
        # GPT推荐
        gpt_score = 0
        gpt_reasons = []
        
        if rows < 1000:  # 小数据集
            gpt_score += 3
            gpt_reasons.append("数据集较小")
        
        if text_cols > 0:  # 有文本列
            gpt_score += 3
            gpt_reasons.append("包含文本数据")
        
        if categorical_cols > 0:  # 有分类列
            gpt_score += 1
            gpt_reasons.append("包含分类数据")
        
        if gpt_score >= 4:
            recommendations.append({
                'model': 'gpt',
                'score': gpt_score,
                'reasons': gpt_reasons,
                'confidence': 'medium'
            })
        
        # 按分数排序
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations
    
    def get_parameter_suggestions(self, model_type: str, data_info: Dict[str, Any]) -> Dict[str, Any]:
        """根据数据特征建议参数"""
        suggestions = {}
        
        if model_type == 'ctgan':
            shape = data_info.get('shape', (0, 0))
            rows, cols = shape
            
            # 根据数据量调整参数
            if rows < 500:
                suggestions['epochs'] = 30
                suggestions['batch_size'] = min(250, rows // 2)
            elif rows < 2000:
                suggestions['epochs'] = 50
                suggestions['batch_size'] = 500
            else:
                suggestions['epochs'] = 100
                suggestions['batch_size'] = 1000
            
            # 根据列数调整网络维度
            if cols < 10:
                suggestions['generator_dim'] = '(128, 128)'
                suggestions['discriminator_dim'] = '(128, 128)'
            elif cols < 50:
                suggestions['generator_dim'] = '(256, 256)'
                suggestions['discriminator_dim'] = '(256, 256)'
            else:
                suggestions['generator_dim'] = '(512, 512)'
                suggestions['discriminator_dim'] = '(512, 512)'
        
        elif model_type == 'gpt':
            shape = data_info.get('shape', (0, 0))
            rows, cols = shape
            
            # 根据数据量调整参数
            if rows < 100:
                suggestions['query_batch'] = 5
                suggestions['max_tokens'] = 1000
            elif rows < 500:
                suggestions['query_batch'] = 10
                suggestions['max_tokens'] = 2000
            else:
                suggestions['query_batch'] = 20
                suggestions['max_tokens'] = 4000
        
        return suggestions
