#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源管理API路由
================

处理数据源管理相关的API接口
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from services.data_service import DataService
from utils.decorators import json_required, validate_json

# 创建数据源管理蓝图
data_bp = Blueprint('data_sources', __name__, url_prefix='/api/data-sources')

@data_bp.route('/', methods=['GET'])
@login_required
def get_data_sources():
    """获取用户数据源列表"""
    try:
        data_sources = DataService.get_user_data_sources(current_user.id)
        return jsonify({
            'success': True, 
            'data_sources': [ds.to_dict() for ds in data_sources]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': '获取失败'}), 500

@data_bp.route('/', methods=['POST'])
@login_required
@json_required
@validate_json('name', 'type')
def create_data_source():
    """创建数据源"""
    try:
        data = request.get_json()
        data_source = DataService.create_data_source(
            user_id=current_user.id,
            name=data['name'],
            data_type=data['type'],
            file_path=data.get('file_path'),
            config=data.get('config', {})
        )
        return jsonify({
            'success': True, 
            'data_source': data_source.to_dict()
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': '创建失败'}), 500

@data_bp.route('/<int:data_source_id>', methods=['GET'])
@login_required
def get_data_source(data_source_id):
    """获取数据源详情"""
    try:
        data_source = DataService.get_data_source(data_source_id, current_user.id)
        return jsonify({
            'success': True, 
            'data_source': data_source.to_dict()
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': '获取失败'}), 500

@data_bp.route('/<int:data_source_id>', methods=['PUT'])
@login_required
@json_required
def update_data_source(data_source_id):
    """更新数据源"""
    try:
        data = request.get_json()
        data_source = DataService.update_data_source(
            data_source_id, 
            current_user.id, 
            data
        )
        return jsonify({
            'success': True, 
            'data_source': data_source.to_dict()
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': '更新失败'}), 500

@data_bp.route('/<int:data_source_id>', methods=['DELETE'])
@login_required
def delete_data_source(data_source_id):
    """删除数据源"""
    try:
        DataService.delete_data_source(data_source_id, current_user.id)
        return jsonify({'success': True, 'message': '删除成功'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': '删除失败'}), 500

@data_bp.route('/<int:data_source_id>/preview', methods=['GET'])
@login_required
def preview_data_source(data_source_id):
    """预览数据源"""
    try:
        limit = request.args.get('limit', 100, type=int)
        preview_data = DataService.preview_data_source(
            data_source_id, 
            current_user.id, 
            limit
        )
        return jsonify({
            'success': True, 
            'preview': preview_data
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': '预览失败'}), 500

@data_bp.route('/validate', methods=['POST'])
@json_required
@validate_json('file_path', 'data_type')
def validate_data_source():
    """验证数据源"""
    try:
        data = request.get_json()
        is_valid, message = DataService.validate_data_source(
            data['file_path'], 
            data['data_type']
        )
        return jsonify({
            'success': True, 
            'valid': is_valid, 
            'message': message
        })
    except Exception as e:
        return jsonify({'success': False, 'message': '验证失败'}), 500

@data_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """上传文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'}), 400
        
        # 获取上传目录
        upload_folder = 'uploads'
        file_path = DataService.upload_file(file, upload_folder)
        
        return jsonify({
            'success': True, 
            'file_path': file_path
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': '上传失败'}), 500

