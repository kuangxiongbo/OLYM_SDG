#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理API路由
===============

处理用户管理相关的API接口
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from services.user_service import UserService
from utils.decorators import json_required, validate_json

# 创建用户管理蓝图
user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """获取用户个人信息"""
    try:
        user = UserService.get_user_profile(current_user.id)
        return jsonify({'success': True, 'user': user.to_dict()})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': '获取失败'}), 500

@user_bp.route('/profile', methods=['PUT'])
@login_required
@json_required
@validate_json('username')
def update_profile():
    """更新用户个人信息"""
    try:
        data = request.get_json()
        user = UserService.update_user_profile(current_user.id, data)
        return jsonify({'success': True, 'user': user.to_dict()})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': '更新失败'}), 500

@user_bp.route('/change-password', methods=['POST'])
@login_required
@json_required
@validate_json('old_password', 'new_password')
def change_password():
    """修改密码"""
    try:
        data = request.get_json()
        UserService.change_password(
            current_user.id,
            data['old_password'],
            data['new_password']
        )
        return jsonify({'success': True, 'message': '密码修改成功'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': '修改失败'}), 500

@user_bp.route('/change-email', methods=['POST'])
@login_required
@json_required
@validate_json('new_email', 'password')
def change_email():
    """修改邮箱"""
    try:
        data = request.get_json()
        user = UserService.change_email(
            current_user.id,
            data['new_email'],
            data['password']
        )
        return jsonify({'success': True, 'message': '邮箱修改成功，请查收验证邮件'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': '修改失败'}), 500

@user_bp.route('/stats', methods=['GET'])
@login_required
def get_user_stats():
    """获取用户统计信息"""
    try:
        stats = UserService.get_user_stats(current_user.id)
        return jsonify({'success': True, 'stats': stats})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': '获取失败'}), 500

