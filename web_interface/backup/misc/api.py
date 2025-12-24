#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDG Web界面API接口
=================

提供RESTful API接口用于外部系统集成
"""

from flask import Blueprint, request, jsonify, current_app
import pandas as pd
import numpy as np
import os
import uuid
from datetime import datetime
import logging

from utils.data_processor import DataProcessor
from utils.model_manager import ModelManager
from utils.quality_evaluator import QualityEvaluator

# 创建API蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# 初始化工具类
data_processor = DataProcessor()
model_manager = ModelManager()
quality_evaluator = QualityEvaluator()

# 全局存储（生产环境应使用数据库）
api_sessions = {}

@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@api_bp.route('/models', methods=['GET'])
def get_available_models():
    """获取可用模型列表"""
    try:
        models = model_manager.get_available_models()
        return jsonify({
            'success': True,
            'models': models
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/models/<model_type>/parameters', methods=['GET'])
def get_model_parameters(model_type):
    """获取模型参数配置"""
    try:
        parameters = model_manager.get_model_parameters(model_type)
        return jsonify({
            'success': True,
            'model_type': model_type,
            'parameters': parameters
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@api_bp.route('/models/<model_type>/recommendations', methods=['POST'])
def get_model_recommendations(model_type):
    """获取模型推荐"""
    try:
        data = request.get_json()
        data_info = data.get('data_info', {})
        
        recommendations = model_manager.get_model_recommendations(data_info)
        suggestions = model_manager.get_parameter_suggestions(model_type, data_info)
        
        return jsonify({
            'success': True,
            'model_type': model_type,
            'recommendations': recommendations,
            'parameter_suggestions': suggestions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@api_bp.route('/data/analyze', methods=['POST'])
def analyze_data():
    """分析数据"""
    try:
        data = request.get_json()
        
        # 从JSON数据创建DataFrame
        if 'data' in data:
            df = pd.DataFrame(data['data'])
        elif 'csv_data' in data:
            from io import StringIO
            df = pd.read_csv(StringIO(data['csv_data']))
        else:
            return jsonify({
                'success': False,
                'error': '需要提供data或csv_data字段'
            }), 400
        
        # 分析数据
        analysis = data_processor.analyze_data(df)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@api_bp.route('/data/clean', methods=['POST'])
def clean_data():
    """清洗数据"""
    try:
        data = request.get_json()
        
        # 从JSON数据创建DataFrame
        if 'data' in data:
            df = pd.DataFrame(data['data'])
        elif 'csv_data' in data:
            from io import StringIO
            df = pd.read_csv(StringIO(data['csv_data']))
        else:
            return jsonify({
                'success': False,
                'error': '需要提供data或csv_data字段'
            }), 400
        
        # 获取清洗选项
        options = data.get('options', {})
        
        # 清洗数据
        cleaned_df = data_processor.clean_data(df, options)
        
        # 返回清洗后的数据
        return jsonify({
            'success': True,
            'cleaned_data': cleaned_df.to_dict('records'),
            'shape': cleaned_df.shape,
            'columns': list(cleaned_df.columns)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@api_bp.route('/synthesis/generate', methods=['POST'])
def generate_synthetic_data():
    """生成合成数据"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        required_fields = ['data', 'model_type', 'model_config', 'num_samples']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需参数: {field}'
                }), 400
        
        # 创建DataFrame
        df = pd.DataFrame(data['data'])
        
        # 验证模型参数
        validation_result = model_manager.validate_parameters(
            data['model_type'], 
            data['model_config']
        )
        
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': '模型参数验证失败',
                'validation_errors': validation_result['errors']
            }), 400
        
        # 创建模型
        model = model_manager.create_model(
            data['model_type'], 
            data['model_config']
        )
        
        # 准备数据
        prepared_df = data_processor.prepare_for_synthesis(df)
        
        # 创建数据连接器
        from sdgx.data_connectors.dataframe_connector import DataFrameConnector
        data_connector = DataFrameConnector(df=prepared_df)
        
        # 创建合成器
        from sdgx.synthesizer import Synthesizer
        synthesizer = Synthesizer(
            model=model,
            data_connector=data_connector
        )
        
        # 训练模型
        synthesizer.fit()
        
        # 生成合成数据
        num_samples = data['num_samples']
        synthetic_data = synthesizer.sample(num_samples)
        
        # 后处理合成数据
        processed_synthetic = data_processor.post_process_synthetic(synthetic_data, df)
        
        # 生成会话ID
        session_id = str(uuid.uuid4())
        api_sessions[session_id] = {
            'original_data': df.to_dict('records'),
            'synthetic_data': processed_synthetic.to_dict('records'),
            'model_type': data['model_type'],
            'model_config': data['model_config'],
            'created_at': datetime.now()
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'synthetic_data': processed_synthetic.to_dict('records'),
            'shape': processed_synthetic.shape,
            'columns': list(processed_synthetic.columns)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/evaluation/evaluate', methods=['POST'])
def evaluate_quality():
    """评估数据质量"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        if 'session_id' in data:
            # 从会话获取数据
            session_id = data['session_id']
            if session_id not in api_sessions:
                return jsonify({
                    'success': False,
                    'error': '会话不存在'
                }), 404
            
            session = api_sessions[session_id]
            original_df = pd.DataFrame(session['original_data'])
            synthetic_df = pd.DataFrame(session['synthetic_data'])
        else:
            # 直接提供数据
            if 'original_data' not in data or 'synthetic_data' not in data:
                return jsonify({
                    'success': False,
                    'error': '需要提供session_id或original_data和synthetic_data'
                }), 400
            
            original_df = pd.DataFrame(data['original_data'])
            synthetic_df = pd.DataFrame(data['synthetic_data'])
        
        # 执行质量评估
        evaluation_results = quality_evaluator.evaluate(original_df, synthetic_df)
        
        return jsonify({
            'success': True,
            'evaluation_results': evaluation_results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取会话信息"""
    try:
        if session_id not in api_sessions:
            return jsonify({
                'success': False,
                'error': '会话不存在'
            }), 404
        
        session = api_sessions[session_id]
        
        return jsonify({
            'success': True,
            'session': {
                'session_id': session_id,
                'model_type': session['model_type'],
                'model_config': session['model_config'],
                'created_at': session['created_at'].isoformat(),
                'original_shape': (len(session['original_data']), len(session['original_data'][0]) if session['original_data'] else 0),
                'synthetic_shape': (len(session['synthetic_data']), len(session['synthetic_data'][0]) if session['synthetic_data'] else 0)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sessions/<session_id>/data', methods=['GET'])
def get_session_data(session_id):
    """获取会话数据"""
    try:
        if session_id not in api_sessions:
            return jsonify({
                'success': False,
                'error': '会话不存在'
            }), 404
        
        session = api_sessions[session_id]
        data_type = request.args.get('type', 'synthetic')  # original 或 synthetic
        
        if data_type == 'original':
            data = session['original_data']
        else:
            data = session['synthetic_data']
        
        return jsonify({
            'success': True,
            'data_type': data_type,
            'data': data,
            'shape': (len(data), len(data[0]) if data else 0)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除会话"""
    try:
        if session_id not in api_sessions:
            return jsonify({
                'success': False,
                'error': '会话不存在'
            }), 404
        
        del api_sessions[session_id]
        
        return jsonify({
            'success': True,
            'message': '会话已删除'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """列出所有会话"""
    try:
        sessions = []
        for session_id, session in api_sessions.items():
            sessions.append({
                'session_id': session_id,
                'model_type': session['model_type'],
                'created_at': session['created_at'].isoformat(),
                'original_shape': (len(session['original_data']), len(session['original_data'][0]) if session['original_data'] else 0),
                'synthetic_shape': (len(session['synthetic_data']), len(session['synthetic_data'][0]) if session['synthetic_data'] else 0)
            })
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'total': len(sessions)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/batch/process', methods=['POST'])
def batch_process():
    """批量处理"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        if 'datasets' not in data:
            return jsonify({
                'success': False,
                'error': '需要提供datasets字段'
            }), 400
        
        datasets = data['datasets']
        model_type = data.get('model_type', 'ctgan')
        model_config = data.get('model_config', {})
        num_samples = data.get('num_samples', 100)
        
        results = []
        
        for i, dataset in enumerate(datasets):
            try:
                # 创建DataFrame
                df = pd.DataFrame(dataset['data'])
                
                # 创建模型
                model = model_manager.create_model(model_type, model_config)
                
                # 准备数据
                prepared_df = data_processor.prepare_for_synthesis(df)
                
                # 创建数据连接器
                from sdgx.data_connectors.dataframe_connector import DataFrameConnector
                data_connector = DataFrameConnector(df=prepared_df)
                
                # 创建合成器
                from sdgx.synthesizer import Synthesizer
                synthesizer = Synthesizer(
                    model=model,
                    data_connector=data_connector
                )
                
                # 训练模型
                synthesizer.fit()
                
                # 生成合成数据
                synthetic_data = synthesizer.sample(num_samples)
                
                # 后处理合成数据
                processed_synthetic = data_processor.post_process_synthetic(synthetic_data, df)
                
                results.append({
                    'index': i,
                    'success': True,
                    'synthetic_data': processed_synthetic.to_dict('records'),
                    'shape': processed_synthetic.shape
                })
                
            except Exception as e:
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(results),
            'successful': sum(1 for r in results if r['success'])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 错误处理
@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '接口不存在'
    }), 404

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500

@api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': '请求参数错误'
    }), 400
