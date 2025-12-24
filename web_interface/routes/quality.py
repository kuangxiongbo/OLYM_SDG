#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量评估路由
"""

from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from models.task import Task, db
from utils.helpers import save_uploaded_file
from utils.decorators import log_operation
from services.quality_service import QualityService
import os

quality_bp = Blueprint('quality', __name__)

@quality_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    """上传评估数据"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '未上传文件',
                'code': 'INVALID_PARAMS'
            }), 400
        
        file = request.files['file']
        data_type = request.form.get('data_type', 'original')
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '文件名为空',
                'code': 'INVALID_PARAMS'
            }), 400
        
        # 检查文件扩展名
        from utils.helpers import allowed_file
        from config import Config
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'不支持的文件格式，仅支持: {", ".join(Config.ALLOWED_EXTENSIONS)}',
                'code': 'UNSUPPORTED_FORMAT'
            }), 400
        
        # 确保上传目录存在
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # 保存文件
        file_id, filepath, filename = save_uploaded_file(file)
        if not file_id or not filepath:
            return jsonify({
                'success': False,
                'error': '文件保存失败，请检查文件格式和权限',
                'code': 'SAVE_FAILED'
            }), 500
        
        # 验证文件是否存在
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': '文件保存后验证失败',
                'code': 'FILE_NOT_FOUND'
            }), 500
        
        # 读取文件预览
        import pandas as pd
        try:
            if filename.endswith('.csv'):
                # 尝试UTF-8编码
                try:
                    df = pd.read_csv(filepath, nrows=10, encoding='utf-8')
                except UnicodeDecodeError:
                    # 尝试GBK编码
                    try:
                        df = pd.read_csv(filepath, nrows=10, encoding='gbk')
                    except UnicodeDecodeError:
                        df = pd.read_csv(filepath, nrows=10, encoding='gb18030')
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(filepath, nrows=10, engine='openpyxl')
            elif filename.endswith('.xls'):
                df = pd.read_excel(filepath, nrows=10, engine='xlrd')
            else:
                return jsonify({
                    'success': False,
                    'error': '不支持的文件格式',
                    'code': 'UNSUPPORTED_FORMAT'
                }), 400
        except UnicodeDecodeError as e:
            return jsonify({
                'success': False,
                'error': f'文件编码不支持，请转换为UTF-8格式: {str(e)}',
                'code': 'ENCODING_ERROR'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'文件读取失败: {str(e)}',
                'code': 'READ_FAILED'
            }), 500
        
        if df.empty:
            return jsonify({
                'success': False,
                'error': '文件为空或无法读取数据',
                'code': 'EMPTY_FILE'
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'file_id': file_id,
                'data_type': data_type,
                'filename': file.filename,
                'rows': len(df),
                'columns': df.columns.tolist()
            }
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'上传失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@quality_bp.route('/assess', methods=['POST'])
@login_required
@log_operation('创建数据质量评估任务', 'task')
def assess():
    """创建评估任务"""
    try:
        data = request.get_json()
        service = QualityService()
        task = service.create_assessment_task(
            user_id=current_user.id,
            config=data
        )
        
        return jsonify({
            'success': True,
            'data': {
                'task_id': f'task_{task.id}',
                'status': task.status
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@quality_bp.route('/tasks/<task_id>', methods=['GET'])
@login_required
def get_task_status(task_id):
    """查询评估任务状态"""
    try:
        # 支持 task_123 或 123 格式
        if isinstance(task_id, str) and task_id.startswith('task_'):
            task_id_int = int(task_id.replace('task_', ''))
        else:
            task_id_int = int(task_id)
        
        task = Task.query.get(task_id_int)
        if not task:
            return jsonify({
                'success': False,
                'error': '任务不存在',
                'code': 'RESOURCE_NOT_FOUND'
            }), 404
        
        if task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': '无权限访问此任务',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        task_dict = task.to_dict()
        # 确保包含进度信息
        if 'progress' not in task_dict:
            task_dict['progress'] = task.progress or 0
        if 'message' not in task_dict:
            status_messages = {
                'pending': '等待处理',
                'running': '正在评估数据质量...',
                'completed': '评估完成',
                'failed': '评估失败'
            }
            task_dict['message'] = status_messages.get(task.status, '未知状态')
        
        return jsonify({
            'success': True,
            'data': task_dict
        }), 200
    except ValueError:
        return jsonify({
            'success': False,
            'error': '无效的任务ID',
            'code': 'INVALID_PARAMS'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'查询任务状态失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@quality_bp.route('/tasks/<task_id>/report', methods=['GET'])
@login_required
def get_report(task_id):
    """获取评估报告"""
    try:
        # 支持 task_123 或 123 格式
        if isinstance(task_id, str) and task_id.startswith('task_'):
            task_id_int = int(task_id.replace('task_', ''))
        else:
            task_id_int = int(task_id)
        
        task = Task.query.get(task_id_int)
        if not task:
            return jsonify({
                'success': False,
                'error': '任务不存在',
                'code': 'RESOURCE_NOT_FOUND'
            }), 404
        
        if task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': '无权限访问此任务',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        if task.status != 'completed':
            return jsonify({
                'success': False,
                'error': f'任务尚未完成，当前状态: {task.status}',
                'code': 'INVALID_PARAMS'
            }), 400
        
        service = QualityService()
        report = service.get_report(task_id_int)
        
        if not report:
            return jsonify({
                'success': False,
                'error': '报告不存在，请检查结果文件',
                'code': 'RESOURCE_NOT_FOUND'
            }), 404
        
        return jsonify({
            'success': True,
            'data': report
        }), 200
    except ValueError:
        return jsonify({
            'success': False,
            'error': '无效的任务ID',
            'code': 'INVALID_PARAMS'
        }), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'获取报告失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@quality_bp.route('/tasks/<task_id>/export', methods=['GET'])
@login_required
def export_report(task_id):
    """导出评估报告"""
    # 支持 task_123 或 123 格式
    if isinstance(task_id, str) and task_id.startswith('task_'):
        task_id = int(task_id.replace('task_', ''))
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({
            'success': False,
            'error': '无权限访问此任务',
            'code': 'PERMISSION_DENIED'
        }), 403
    
    format_type = request.args.get('format', 'pdf')
    service = QualityService()
    report = service.get_report(task_id)
    
    if not report:
        return jsonify({
            'success': False,
            'error': '报告不存在',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404
    
    # TODO: 根据format_type生成PDF/HTML/JSON文件
    # 这里先返回JSON格式
    import json
    from io import BytesIO
    report_json = json.dumps(report, ensure_ascii=False, indent=2)
    return send_file(
        BytesIO(report_json.encode('utf-8')),
        mimetype='application/json',
        as_attachment=True,
        download_name=f'quality_report_{task_id}.json'
    )

