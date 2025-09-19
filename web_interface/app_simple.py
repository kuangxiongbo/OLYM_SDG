#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDG Web界面简化版主应用
====================

不依赖SDG模块的简化版本，用于测试Web界面基本功能
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

# 添加SDG项目路径（从web_interface目录到根目录的synthetic-data-generator）
import sys
sdg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'synthetic-data-generator')
sys.path.append(sdg_path)

# 添加utils目录到Python路径
utils_path = os.path.join(os.path.dirname(__file__), 'utils')
sys.path.append(utils_path)
from database_connector import DatabaseConnector

app = Flask(__name__)
app.secret_key = 'sdg_web_interface_secret_key_2025'

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

def generate_demo_data():
    """生成演示数据"""
    np.random.seed(42)
    data = {
        'age': np.random.randint(18, 65, 100),
        'income': np.random.randint(30000, 100000, 100),
        'education': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], 100),
        'gender': np.random.choice(['Male', 'Female'], 100),
        'city': np.random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston'], 100)
    }
    return pd.DataFrame(data)

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/test_demo_flow')
def test_demo_flow():
    """演示数据流程测试页面"""
    return send_file('test_demo_flow.html')

@app.route('/debug_demo_issue')
def debug_demo_issue():
    """演示数据问题调试页面"""
    return send_file('debug_demo_issue.html')

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
        # 生成演示数据
        df = generate_demo_data()
        
        # 获取数据信息
        data_info = get_data_info(df)
        
        # 生成会话ID
        session_id = str(uuid.uuid4())
        session_data[session_id] = {
            'file_path': 'demo_data',
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
            }
        elif model_type == 'gpt':
            config = {
                'openai_API_key': {'type': 'password', 'default': '', 'description': 'OpenAI API密钥'},
                'openai_API_url': {'type': 'text', 'default': 'https://api.openai.com/v1/', 'description': 'API地址'},
                'gpt_model': {'type': 'select', 'default': 'gpt-3.5-turbo', 'options': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'], 'description': 'GPT模型'},
                'temperature': {'type': 'number', 'default': 0.1, 'min': 0, 'max': 2, 'step': 0.1, 'description': '温度参数'},
                'max_tokens': {'type': 'number', 'default': 2000, 'min': 100, 'max': 8000, 'description': '最大token数'},
            }
        else:
            config = {}
        
        return jsonify({'success': True, 'config': config})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取配置失败: {str(e)}'})

@app.route('/generate', methods=['POST'])
def generate_synthetic_data():
    """生成合成数据（模拟版本）"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        model_config = data.get('model_config', {})
        num_samples = data.get('num_samples', 100)
        
        if session_id not in session_data:
            return jsonify({'success': False, 'message': '会话已过期，请重新上传数据'})
        
        # 获取数据
        df = session_data[session_id]['dataframe']
        
        # 模拟生成合成数据（实际应用中这里会调用SDG）
        synthetic_data = df.sample(n=min(num_samples, len(df) * 2), replace=True).copy()
        
        # 添加一些随机变化
        for col in synthetic_data.select_dtypes(include=[np.number]).columns:
            noise = np.random.normal(0, 0.1, len(synthetic_data))
            synthetic_data[col] = synthetic_data[col] * (1 + noise)
        
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
    """数据质量评估（模拟版本）"""
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

@app.route('/llm_config')
def llm_config():
    """大模型配置页面"""
    return render_template('llm_config.html')

@app.route('/system_config')
def system_config():
    """系统配置页面"""
    return render_template('system_config.html')

@app.route('/quick_wizard')
def quick_wizard():
    """快速向导页面"""
    return render_template('quick_wizard.html')


@app.route('/quality_evaluation')
def quality_evaluation():
    """脱敏数据质量评测页面"""
    return render_template('quality_evaluation.html')

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

@app.route('/test_config')
def test_config():
    """配置测试页面"""
    return send_file('test_config.html')

@app.route('/simple_test')
def simple_test():
    """简单配置测试页面"""
    return send_file('simple_test.html')

@app.route('/verify_config')
def verify_config():
    """配置保存验证页面"""
    return send_file('verify_config.html')

@app.route('/test_status')
def test_status():
    """配置状态显示测试页面"""
    return send_file('test_status.html')

@app.route('/test_model_config')
def test_model_config():
    """测试模型配置页面"""
    return send_file('test_model_config.html')

@app.route('/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0-simple'
    })

@app.route('/api/synthesis/generate', methods=['POST'])
def api_generate_synthetic_data():
    """SDG API接口 - 生成合成数据"""
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
        raw_data = data['data']
        if not raw_data or len(raw_data) < 2:
            return jsonify({
                'success': False,
                'error': '数据格式错误，至少需要表头和数据行'
            }), 400
        
        # 第一行作为列名，其余行作为数据
        columns = raw_data[0]
        data_rows = raw_data[1:]
        df = pd.DataFrame(data_rows, columns=columns)
        
        num_samples = data['num_samples']
        model_type = data['model_type']
        field_config = data.get('field_config', {})
        field_types = data.get('field_types', {})
        
        # 模拟SDG生成过程（实际应用中这里会调用真正的SDG）
        print(f"SDG API调用: 模型类型={model_type}, 样本数={num_samples}, 数据行数={len(df)}")
        print(f"字段配置: {field_config}")
        print(f"字段类型: {field_types}")
        print(f"列名: {columns}")
        
        # 根据字段配置生成合成数据
        synthetic_data = []
        
        # 确定要保留的列
        columns_to_keep = [col for col in columns if field_config.get(col, 'regenerate') != 'remove']
        
        for i in range(num_samples):
            row = {}
            for col in columns_to_keep:
                action = field_config.get(col, 'regenerate')
                field_type = field_types.get(col, 'text')
                
                if action == 'keep':
                    # 维持原数据：从原始数据中随机选择
                    row[col] = df[col].iloc[np.random.randint(0, len(df))]
                elif action == 'regenerate':
                    # 重新脱敏合成：基于字段类型和原始数据的统计特征
                    if field_type == 'numeric':
                        # 数值列：基于原始数据的均值和标准差生成
                        try:
                            # 尝试转换为数值类型
                            numeric_series = pd.to_numeric(df[col], errors='coerce')
                            mean_val = numeric_series.mean()
                            std_val = numeric_series.std()
                            if pd.isna(std_val) or std_val == 0:
                                row[col] = mean_val
                            else:
                                row[col] = np.random.normal(mean_val, std_val)
                        except:
                            # 如果转换失败，生成随机数值
                            row[col] = np.random.randint(1, 1000)
                    elif field_type == 'id':
                        # ID列：生成新的唯一ID
                        row[col] = f"{col}_{i+1:06d}"
                    elif field_type == 'pii':
                        # 敏感信息：生成脱敏数据
                        if '姓名' in col or 'name' in col.lower():
                            row[col] = f"用户{i+1:04d}"
                        elif '电话' in col or 'phone' in col.lower():
                            row[col] = f"138****{np.random.randint(1000, 9999)}"
                        elif '邮箱' in col or 'email' in col.lower():
                            row[col] = f"user{i+1:04d}@example.com"
                        else:
                            # 其他敏感信息：生成通用脱敏数据
                            row[col] = f"***{i+1:04d}***"
                    elif field_type == 'date':
                        # 日期列：生成随机日期
                        start_date = pd.Timestamp('2020-01-01')
                        end_date = pd.Timestamp('2024-12-31')
                        random_date = start_date + pd.Timedelta(days=np.random.randint(0, (end_date - start_date).days))
                        row[col] = random_date.strftime('%Y-%m-%d')
                    else:
                        # 文本列：基于原始数据的分布生成
                        values = df[col].value_counts()
                        if len(values) > 0:
                            row[col] = np.random.choice(values.index, p=values.values/values.sum())
                        else:
                            row[col] = f"文本数据{i+1}"
                # action == 'remove' 的字段不添加到结果中
            
            synthetic_data.append(row)
        
        synthetic_df = pd.DataFrame(synthetic_data)
        
        # 转换为前端期望的格式
        synthetic_data_list = synthetic_df.values.tolist()
        
        return jsonify({
            'success': True,
            'synthetic_data': synthetic_data_list,
            'message': f'成功生成{num_samples}条合成数据',
            'model_type': model_type,
            'original_rows': len(df),
            'synthetic_rows': len(synthetic_df)
        })
        
    except Exception as e:
        print(f"SDG API错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'SDG生成失败: {str(e)}'
        }), 500

# 初始化数据库连接器
db_connector = DatabaseConnector()

@app.route('/api/datasource/test', methods=['POST'])
def test_datasource_connection():
    """测试数据源连接"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        required_fields = ['type', 'host', 'port', 'database', 'username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需参数: {field}'
                }), 400
        
        # 测试连接
        result = db_connector.test_connection(data)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"测试数据源连接错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'连接测试失败: {str(e)}'
        }), 500

@app.route('/api/datasource/tables', methods=['POST'])
def get_datasource_tables():
    """获取数据源中的表列表"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        required_fields = ['type', 'host', 'port', 'database', 'username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需参数: {field}'
                }), 400
        
        # 获取表列表
        result = db_connector.get_tables(data)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"获取表列表错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取表列表失败: {str(e)}'
        }), 500

@app.route('/api/datasource/table-data', methods=['POST'])
def get_table_data():
    """获取表数据"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        required_fields = ['type', 'host', 'port', 'database', 'username', 'password', 'table_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需参数: {field}'
                }), 400
        
        # 获取表数据
        limit = data.get('limit', 100)
        result = db_connector.get_table_data(data, data['table_name'], limit)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"获取表数据错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取表数据失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 启动SDG Web界面简化版...")
    print("📱 访问地址: http://localhost:5000")
    print("🔧 这是简化版本，不依赖SDG模块")
    print("💡 用于测试Web界面基本功能")
    app.run(debug=True, host='0.0.0.0', port=5000)
