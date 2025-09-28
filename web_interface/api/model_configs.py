#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型配置管理API路由
==================

处理模型配置管理相关的API接口
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from services.model_service import ModelService
from utils.decorators import json_required, validate_json

# 创建模型配置管理蓝图
model_bp = Blueprint('model_configs', __name__, url_prefix='/api/model-configs')

@model_bp.route('/', methods=['GET'])
@login_required
def get_model_configs():
    """获取用户模型配置列表"""
    try:
        model_configs = ModelService.get_user_model_configs(current_user.id)
        return jsonify({
            'success': True, 
            'model_configs': [mc.to_dict() for mc in model_configs]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': '获取失败'}), 500

@model_bp.route('/', methods=['POST'])
@login_required
@json_required
@validate_json('name', 'model_type')
def create_model_config():
    """创建模型配置"""
    try:
        data = request.get_json()
        model_config = ModelService.create_model_config(
            user_id=current_user.id,
            name=data['name'],
            model_type=data['model_type'],
            config=data.get('config', {})
        )
        return jsonify({
            'success': True, 
            'model_config': model_config.to_dict()
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': '创建失败'}), 500

