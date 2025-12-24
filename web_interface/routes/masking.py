#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据脱敏路由
"""

from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from models.task import Task, db
from utils.helpers import save_uploaded_file, allowed_file
from utils.decorators import log_operation
from services.masking_service import MaskingService
from config import Config
import os

masking_bp = Blueprint('masking', __name__)

@masking_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    """上传脱敏数据"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '未上传文件',
                'code': 'INVALID_PARAMS'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '文件名为空',
                'code': 'INVALID_PARAMS'
            }), 400
        
        # 检查文件扩展名
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
        
        # 读取文件
        import pandas as pd
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath, nrows=10, encoding='utf-8')
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
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(filepath, nrows=10, encoding='gbk')
                else:
                    raise
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'文件读取失败: {str(e)}',
                    'code': 'READ_FAILED'
                }), 500
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
        
        # 获取预览数据
        try:
            preview = df.head(5).to_dict('records') if len(df) > 0 else []
        except Exception as e:
            preview = []
            print(f"生成预览数据失败: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'file_id': file_id,
                'filename': file.filename,
                'rows': len(df),
                'columns': df.columns.tolist(),
                'preview': preview
            }
        }), 200
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"上传文件错误: {error_detail}")
        return jsonify({
            'success': False,
            'error': f'上传失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@masking_bp.route('/detect-fields', methods=['POST'])
@login_required
def detect_fields():
    """自动识别字段类型"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        
        if not file_id:
            return jsonify({
                'success': False,
                'error': '缺少file_id参数',
                'code': 'INVALID_PARAMS'
            }), 400
        
        service = MaskingService()
        fields = service.detect_fields(file_id)
        
        return jsonify({
            'success': True,
            'data': {'fields': fields}
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@masking_bp.route('/configure', methods=['POST'])
@login_required
def configure():
    """配置脱敏规则"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        rules = data.get('rules', [])
        
        if not file_id or not rules:
            return jsonify({
                'success': False,
                'error': '缺少必要参数',
                'code': 'INVALID_PARAMS'
            }), 400
        
        # 生成配置ID（实际应该保存到数据库）
        import uuid
        config_id = f"config_{uuid.uuid4().hex[:12]}"
        
        return jsonify({
            'success': True,
            'data': {
                'config_id': config_id,
                'message': '脱敏规则配置成功'
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@masking_bp.route('/execute', methods=['POST'])
@login_required
@log_operation('创建数据脱敏任务', 'task')
def execute():
    """执行脱敏任务"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        config_id = data.get('config_id')
        rules = data.get('rules', [])
        
        if not file_id or not rules:
            return jsonify({
                'success': False,
                'error': '缺少必要参数',
                'code': 'INVALID_PARAMS'
            }), 400
        
        service = MaskingService()
        task = service.execute_masking(
            user_id=current_user.id,
            file_id=file_id,
            config_id=config_id,
            rules=rules
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

@masking_bp.route('/tasks/<task_id>', methods=['GET'])
@login_required
def get_task_status(task_id):
    """查询脱敏任务状态"""
    try:
        # 支持 task_123 或 123 格式
        if isinstance(task_id, str) and task_id.startswith('task_'):
            task_id_int = int(task_id.replace('task_', ''))
        else:
            try:
                task_id_int = int(task_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '无效的任务ID',
                    'code': 'INVALID_PARAMS'
                }), 400
        
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
        
        # 添加进度消息
        if task.status == 'running':
            task_dict['message'] = f'正在处理 · 已完成 {task.progress or 0}%'
        elif task.status == 'completed':
            task_dict['message'] = '处理完成'
        elif task.status == 'failed':
            task_dict['message'] = f'处理失败: {task.error_message or "未知错误"}'
        else:
            task_dict['message'] = '等待开始'
        
        return jsonify({
            'success': True,
            'data': task_dict
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'查询任务状态失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@masking_bp.route('/tasks/<task_id>/preview', methods=['GET'])
@login_required
def get_preview(task_id):
    """获取脱敏结果预览"""
    try:
        # 支持 task_123 或 123 格式
        if isinstance(task_id, str) and task_id.startswith('task_'):
            task_id_int = int(task_id.replace('task_', ''))
        else:
            try:
                task_id_int = int(task_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '无效的任务ID',
                    'code': 'INVALID_PARAMS'
                }), 400
        
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
        
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 验证分页参数
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        
        service = MaskingService()
        preview = service.get_result_preview(task_id_int, page, page_size)
        
        if not preview:
            return jsonify({
                'success': False,
                'error': '无法获取预览数据，请检查结果文件是否存在',
                'code': 'RESOURCE_NOT_FOUND'
            }), 404
        
        # 转换数据格式以匹配前端期望
        columns = preview.get('columns', [])
        original_data = preview.get('original_data', [])
        masked_data = preview.get('masked_data', [])
        
        # 合并原始和处理后的数据
        combined_data = []
        max_rows = min(len(original_data) if original_data else 0, len(masked_data) if masked_data else 0)
        for i in range(max_rows):
            row = {}
            for col in columns:
                orig_val = original_data[i].get(col) if original_data and i < len(original_data) else None
                masked_val = masked_data[i].get(col) if masked_data and i < len(masked_data) else None
                row[f'original_{col}'] = orig_val if orig_val is not None else '-'
                row[col] = masked_val if masked_val is not None else '-'
            combined_data.append(row)
        
        return jsonify({
            'success': True,
            'data': {
                'columns': columns,
                'data': combined_data,
                'original_data': original_data[:max_rows] if original_data else [],
                'masked_data': masked_data[:max_rows] if masked_data else [],
                'pagination': preview.get('pagination', {})
            }
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'获取预览失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@masking_bp.route('/tasks/<task_id>/download', methods=['GET'])
@login_required
def download_result(task_id):
    """下载脱敏结果"""
    # 支持 task_123 或 123 格式
    if isinstance(task_id, str) and task_id.startswith('task_'):
        task_id = int(task_id.replace('task_', ''))
    else:
        try:
            task_id = int(task_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': '无效的任务ID',
                'code': 'INVALID_PARAMS'
            }), 400
    
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({
            'success': False,
            'error': '无权限访问此任务',
            'code': 'PERMISSION_DENIED'
        }), 403
    
    if task.status != 'completed':
        return jsonify({
            'success': False,
            'error': '任务尚未完成',
            'code': 'INVALID_PARAMS'
        }), 400
    
    format_type = request.args.get('format', 'csv')
    file_path = os.path.join(task.result_path, f'masked.{format_type}')
    
    if not os.path.exists(file_path):
        return jsonify({
            'success': False,
            'error': '文件不存在',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404
    
    return send_file(file_path, as_attachment=True, download_name=f'masked_data_{task_id}.{format_type}')

@masking_bp.route('/tasks/<task_id>/export', methods=['GET'])
@login_required
def export_report(task_id):
    """导出脱敏处理报告"""
    # 支持 task_123 或 123 格式
    if isinstance(task_id, str) and task_id.startswith('task_'):
        task_id = int(task_id.replace('task_', ''))
    else:
        try:
            task_id = int(task_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': '无效的任务ID',
                'code': 'INVALID_PARAMS'
            }), 400
    
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({
            'success': False,
            'error': '无权限访问此任务',
            'code': 'PERMISSION_DENIED'
        }), 403
    
    if task.status != 'completed':
        return jsonify({
            'success': False,
            'error': '任务尚未完成',
            'code': 'INVALID_PARAMS'
        }), 400
    
    # 生成报告文件
    import pandas as pd
    import json
    from datetime import datetime
    
    service = MaskingService()
    preview = service.get_result_preview(task_id, 1, 100)
    
    if not preview:
        return jsonify({
            'success': False,
            'error': '无法获取预览数据',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404
    
    # 创建报告内容
    report_data = {
        'task_id': task_id,
        'task_name': task.task_name,
        'created_at': task.created_at.isoformat() if task.created_at else None,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        'status': task.status,
        'fields_count': len(preview.get('columns', [])),
        'total_rows': preview.get('pagination', {}).get('total', 0),
        'preview_data': preview.get('original_data', [])[:10]  # 只包含前10条预览
    }
    
    # 保存报告为JSON文件
    report_path = os.path.join(task.result_path, 'report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    return send_file(report_path, as_attachment=True, download_name=f'masking_report_{task_id}.json')

