#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员API路由
=============

处理管理员相关的API接口
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from services.admin_service import AdminService
from utils.decorators import admin_required

# 创建管理员蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/stats', methods=['GET'])
@login_required
@admin_required
def get_system_stats():
    """获取系统统计信息"""
    try:
        stats = AdminService.get_system_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': '获取失败'}), 500

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def get_all_users():
    """获取所有用户"""
    try:
        users = AdminService.get_all_users()
        return jsonify({
            'success': True, 
            'users': [user.to_dict() for user in users]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': '获取失败'}), 500

