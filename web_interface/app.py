#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDG Web界面主应用
================

提供Web界面用于：
1. 数据源对接和配置
2. 模型参数配置
3. 数据质量评估
4. 合成数据生成
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
import pandas as pd
import numpy as np
import os
import json
import uuid
from datetime import datetime
import traceback
from werkzeug.utils import secure_filename

# SDG相关导入
import sys
import os
# 添加SDG项目路径（从web_interface目录到根目录的synthetic-data-generator）
sdg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'synthetic-data-generator')
sys.path.append(sdg_path)

from sdgx.data_connectors.csv_connector import CsvConnector
from sdgx.data_connectors.dataframe_connector import DataFrameConnector
from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
from sdgx.models.LLM.single_table.gpt import SingleTableGPTModel
from sdgx.synthesizer import Synthesizer
from sdgx.utils import download_demo_data

# 导入API蓝图
from api import api_bp

app = Flask(__name__)
app.secret_key = 'sdg_web_interface_secret_key_2025'

# 注册API蓝图
app.register_blueprint(api_bp)

# 配置
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# 创建必要的文件夹
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# 全局变量存储当前会话数据
session_data = {}

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data_from_file(file_path):
    """从文件加载数据"""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8')
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("不支持的文件格式")
        return df
    except Exception as e:
        raise Exception(f"数据加载失败: {str(e)}")

def get_data_info(df):
    """获取数据基本信息"""
    return {
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': df.dtypes.to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'sample_data': df.head(5).to_dict('records')
    }

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/data_source')
def data_source():
    """数据源配置页面"""
    return render_template('data_source.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """文件上传处理"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 添加时间戳避免文件名冲突
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # 加载数据并获取信息
            df = load_data_from_file(file_path)
            data_info = get_data_info(df)
            
            # 生成会话ID
            session_id = str(uuid.uuid4())
            session_data[session_id] = {
                'file_path': file_path,
                'filename': filename,
                'data_info': data_info,
                'dataframe': df,
                'created_at': datetime.now()
            }
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'data_info': data_info,
                'message': '文件上传成功'
            })
        else:
            return jsonify({'success': False, 'message': '不支持的文件格式'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'上传失败: {str(e)}'})

@app.route('/demo_data')
def demo_data():
    """使用演示数据"""
    try:
        # 下载演示数据
        demo_path = download_demo_data()
        df = pd.read_csv(demo_path)
        
        # 获取数据信息
        data_info = get_data_info(df)
        
        # 生成会话ID
        session_id = str(uuid.uuid4())
        session_data[session_id] = {
            'file_path': demo_path,
            'filename': 'demo_data.csv',
            'data_info': data_info,
            'dataframe': df,
            'created_at': datetime.now()
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'data_info': data_info,
            'message': '演示数据加载成功'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'演示数据加载失败: {str(e)}'})

@app.route('/model_config')
def model_config():
    """模型配置页面"""
    return render_template('model_config.html')

@app.route('/get_model_config', methods=['POST'])
def get_model_config():
    """获取模型配置"""
    try:
        data = request.get_json()
        model_type = data.get('model_type', 'ctgan')
        
        # 根据模型类型返回不同的配置选项
        if model_type == 'ctgan':
            config = {
                'epochs': {'type': 'number', 'default': 50, 'min': 1, 'max': 1000, 'description': '训练轮数'},
                'batch_size': {'type': 'number', 'default': 500, 'min': 32, 'max': 2000, 'description': '批次大小'},
                'generator_lr': {'type': 'number', 'default': 2e-4, 'min': 1e-6, 'max': 1e-2, 'step': 1e-6, 'description': '生成器学习率'},
                'discriminator_lr': {'type': 'number', 'default': 2e-4, 'min': 1e-6, 'max': 1e-2, 'step': 1e-6, 'description': '判别器学习率'},
                'generator_decay': {'type': 'number', 'default': 1e-6, 'min': 0, 'max': 1e-3, 'step': 1e-6, 'description': '生成器衰减率'},
                'discriminator_decay': {'type': 'number', 'default': 1e-6, 'min': 0, 'max': 1e-3, 'step': 1e-6, 'description': '判别器衰减率'},
                'generator_dim': {'type': 'text', 'default': '(256, 256)', 'description': '生成器维度'},
                'discriminator_dim': {'type': 'text', 'default': '(256, 256)', 'description': '判别器维度'}
            }
        elif model_type == 'gpt':
            config = {
                'openai_API_key': {'type': 'password', 'default': '', 'description': 'OpenAI API密钥'},
                'openai_API_url': {'type': 'text', 'default': 'https://api.openai.com/v1/', 'description': 'API地址'},
                'gpt_model': {'type': 'select', 'default': 'gpt-3.5-turbo', 'options': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'], 'description': 'GPT模型'},
                'temperature': {'type': 'number', 'default': 0.1, 'min': 0, 'max': 2, 'step': 0.1, 'description': '温度参数'},
                'max_tokens': {'type': 'number', 'default': 2000, 'min': 100, 'max': 8000, 'description': '最大token数'},
                'timeout': {'type': 'number', 'default': 90, 'min': 10, 'max': 300, 'description': '超时时间(秒)'},
                'query_batch': {'type': 'number', 'default': 10, 'min': 1, 'max': 50, 'description': '查询批次大小'}
            }
        else:
            config = {}
        
        return jsonify({'success': True, 'config': config})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取配置失败: {str(e)}'})

@app.route('/generate', methods=['POST'])
def generate_synthetic_data():
    """生成合成数据"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        model_config = data.get('model_config', {})
        num_samples = data.get('num_samples', 100)
        
        if session_id not in session_data:
            return jsonify({'success': False, 'message': '会话已过期，请重新上传数据'})
        
        # 获取数据
        df = session_data[session_id]['dataframe']
        model_type = model_config.get('model_type', 'ctgan')
        
        # 创建数据连接器
        data_connector = DataFrameConnector(df)
        
        # 创建模型
        if model_type == 'ctgan':
            model = CTGANSynthesizerModel(
                epochs=model_config.get('epochs', 50),
                batch_size=model_config.get('batch_size', 500),
                generator_lr=model_config.get('generator_lr', 2e-4),
                discriminator_lr=model_config.get('discriminator_lr', 2e-4),
                generator_decay=model_config.get('generator_decay', 1e-6),
                discriminator_decay=model_config.get('discriminator_decay', 1e-6)
            )
        elif model_type == 'gpt':
            model = SingleTableGPTModel(
                openai_API_key=model_config.get('openai_API_key', ''),
                openai_API_url=model_config.get('openai_API_url', 'https://api.openai.com/v1/'),
                gpt_model=model_config.get('gpt_model', 'gpt-3.5-turbo'),
                temperature=model_config.get('temperature', 0.1),
                max_tokens=model_config.get('max_tokens', 2000),
                timeout=model_config.get('timeout', 90),
                query_batch=model_config.get('query_batch', 10)
            )
        else:
            return jsonify({'success': False, 'message': '不支持的模型类型'})
        
        # 创建合成器
        synthesizer = Synthesizer(
            model=model,
            data_connector=data_connector
        )
        
        # 训练模型
        synthesizer.fit()
        
        # 生成合成数据
        synthetic_data = synthesizer.sample(num_samples)
        
        # 保存结果
        result_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        csv_filename = f"synthetic_data_{timestamp}_{result_id[:8]}.csv"
        excel_filename = f"synthetic_data_{timestamp}_{result_id[:8]}.xlsx"
        
        csv_path = os.path.join(RESULTS_FOLDER, csv_filename)
        excel_path = os.path.join(RESULTS_FOLDER, excel_filename)
        
        synthetic_data.to_csv(csv_path, index=False, encoding='utf-8-sig')
        synthetic_data.to_excel(excel_path, index=False)
        
        # 更新会话数据
        session_data[session_id]['synthetic_data'] = synthetic_data
        session_data[session_id]['result_id'] = result_id
        session_data[session_id]['result_files'] = {
            'csv': csv_filename,
            'excel': excel_filename
        }
        
        return jsonify({
            'success': True,
            'result_id': result_id,
            'synthetic_data_info': get_data_info(synthetic_data),
            'result_files': {
                'csv': csv_filename,
                'excel': excel_filename
            },
            'message': '合成数据生成成功'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'})

@app.route('/evaluate', methods=['POST'])
def evaluate_data():
    """数据质量评估"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if session_id not in session_data:
            return jsonify({'success': False, 'message': '会话已过期'})
        
        session = session_data[session_id]
        if 'synthetic_data' not in session:
            return jsonify({'success': False, 'message': '请先生成合成数据'})
        
        original_df = session['dataframe']
        synthetic_df = session['synthetic_data']
        
        # 基本统计对比
        numeric_cols = original_df.select_dtypes(include=[np.number]).columns
        evaluation_results = {
            'basic_stats': {},
            'distribution_similarity': {},
            'overall_score': 0
        }
        
        # 数值列统计对比
        for col in numeric_cols[:5]:  # 只评估前5个数值列
            if col in synthetic_df.columns:
                orig_mean = original_df[col].mean()
                synth_mean = synthetic_df[col].mean()
                orig_std = original_df[col].std()
                synth_std = synthetic_df[col].std()
                
                mean_diff = abs(orig_mean - synth_mean) / abs(orig_mean) * 100 if orig_mean != 0 else 0
                std_diff = abs(orig_std - synth_std) / abs(orig_std) * 100 if orig_std != 0 else 0
                
                evaluation_results['basic_stats'][col] = {
                    'original_mean': orig_mean,
                    'synthetic_mean': synth_mean,
                    'mean_diff_percent': mean_diff,
                    'original_std': orig_std,
                    'synthetic_std': synth_std,
                    'std_diff_percent': std_diff
                }
        
        # 计算总体质量分数
        if evaluation_results['basic_stats']:
            mean_diffs = [stats['mean_diff_percent'] for stats in evaluation_results['basic_stats'].values()]
            std_diffs = [stats['std_diff_percent'] for stats in evaluation_results['basic_stats'].values()]
            avg_mean_diff = np.mean(mean_diffs)
            avg_std_diff = np.mean(std_diffs)
            overall_score = max(0, 100 - (avg_mean_diff + avg_std_diff) / 2)
            evaluation_results['overall_score'] = overall_score
        
        # 保存评估结果
        session['evaluation_results'] = evaluation_results
        
        return jsonify({
            'success': True,
            'evaluation_results': evaluation_results,
            'message': '数据质量评估完成'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'评估失败: {str(e)}'})

@app.route('/download/<filename>')
def download_file(filename):
    """下载生成的文件"""
    try:
        file_path = os.path.join(RESULTS_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'success': False, 'message': '文件不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'下载失败: {str(e)}'})

@app.route('/results')
def results():
    """结果展示页面"""
    return render_template('results.html')

@app.route('/batch')
def batch_processing():
    """批量处理页面"""
    return render_template('batch_processing.html')

@app.route('/get_session_data/<session_id>')
def get_session_data(session_id):
    """获取会话数据"""
    if session_id in session_data:
        session = session_data[session_id]
        return jsonify({
            'success': True,
            'data_info': session['data_info'],
            'synthetic_data_info': get_data_info(session.get('synthetic_data', pd.DataFrame())),
            'evaluation_results': session.get('evaluation_results', {}),
            'result_files': session.get('result_files', {})
        })
    else:
        return jsonify({'success': False, 'message': '会话不存在'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
