#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务中心路由
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

task_bp = Blueprint('tasks', __name__)

@task_bp.route('', methods=['GET'])
@login_required
def get_tasks():
    """获取任务列表"""
    # #region agent log
    try:
        import json
        import os
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'A',
            'location': 'task.py:14',
            'message': 'get_tasks函数入口',
            'data': {
                'user_id': current_user.id if current_user.is_authenticated else None,
                'is_authenticated': current_user.is_authenticated,
                'request_args': dict(request.args),
                'accept_header': request.headers.get('Accept', '')
            },
            'timestamp': int(__import__('time').time() * 1000)
        }
        with open('/Users/kuangxb/Desktop/AI 生成数据 SDG /.cursor/debug.log', 'a') as f:
            f.write(json.dumps(log_data) + '\n')
    except Exception as e:
        pass
    # #endregion
    
    try:
        # 如果是HTML请求，返回HTML页面
        if request.headers.get('Accept', '').find('text/html') != -1:
            from flask import render_template
            try:
                return render_template('tasks.html', current_user=current_user)
            except Exception as e:
                print(f"渲染模板失败: {e}")
                # 如果模板不存在，返回简单的任务页面
                from flask import Response
                return Response('''
                <!DOCTYPE html>
                <html lang="zh-CN">
                <head>
                    <meta charset="UTF-8">
                    <title>任务中心 - AI 数据平台</title>
                    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
                    <link href="/static/css/prototype.css" rel="stylesheet">
                </head>
                <body>
                    <div class="navbar">
                        <a href="/" class="brand">AI 数据平台</a>
                        <div class="menu">
                            <a href="/">首页</a>
                            <a href="/api/tasks" class="active">任务中心</a>
                            <a href="/admin">系统设置</a>
                        </div>
                        <div class="menu">
                            <span>管理员</span>
                            <span onclick="logout()">退出</span>
                        </div>
                    </div>
                    <main>
                        <section class="section">
                            <div class="panel">
                                <table class="table">
                                    <thead>
                                        <tr><th>时间</th><th>类型</th><th>任务名称</th><th>状态</th><th>操作</th></tr>
                                    </thead>
                                    <tbody id="tasks-content">
                                        <tr><td colspan="5" style="text-align: center; color: var(--muted); padding: 40px;">加载中...</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </section>
                    </main>
                    <script>
                        async function loadTasks() {
                            try {
                                const response = await fetch('/api/tasks', {credentials: 'include', headers: {'Accept': 'application/json'}});
                                const result = await response.json();
                                if (result.success) {
                                    const tasks = result.data.tasks || [];
                                    const tbody = document.getElementById('tasks-content');
                                    if (tasks.length === 0) {
                                        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--muted); padding: 40px;">暂无任务</td></tr>';
                                    } else {
                                        tbody.innerHTML = tasks.map(task => {
                                            const typeMap = {'synthesis': '仿真数据生成', 'quality': '数据质量评估', 'masking': '数据脱敏'};
                                            const statusMap = {'pending': '待处理', 'running': '进行中', 'completed': '完成', 'failed': '失败', 'cancelled': '已取消'};
                                            const taskType = typeMap[task.task_type] || task.type || task.task_type;
                                            const taskStatus = statusMap[task.status] || task.status;
                                            const taskName = task.name || task.task_name || `任务_${task.id}`;
                                            const time = new Date(task.created_at).toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'});
                                            let action = '查看';
                                            if (task.status === 'completed' && task.task_type === 'quality') action = '报告';
                                            else if (task.status === 'pending') action = '配置';
                                            return `<tr><td>${time}</td><td>${taskType}</td><td>${taskName}</td><td>${taskStatus}</td><td style="color: var(--primary);">${action}</td></tr>`;
                                        }).join('');
                                    }
                                }
                            } catch (error) {
                                document.getElementById('tasks-content').innerHTML = '<tr><td colspan="5" style="text-align: center; color: #dc2626; padding: 40px;">加载失败，请刷新重试</td></tr>';
                            }
                        }
                        function logout() {
                            fetch('/api/auth/logout', {method: 'POST'}).then(() => window.location.href = '/auth/login');
                        }
                        loadTasks();
                    </script>
                </body>
                </html>
                ''', mimetype='text/html; charset=utf-8'), 200
        
        # JSON请求，返回API数据
        try:
            # 从当前应用上下文中获取db和Task模型
            # 使用延迟导入，确保使用正确的db实例
            try:
                from models.task import Task, db
            except ImportError as ie:
                print(f"导入Task模型失败: {ie}")
                import traceback
                traceback.print_exc()
                raise
            
            task_type = request.args.get('type')
            status = request.args.get('status')
            try:
                page = int(request.args.get('page', 1))
                page_size = int(request.args.get('page_size', 20))
            except ValueError:
                page = 1
                page_size = 20
            
            # 查询任务
            try:
                # #region agent log
                try:
                    import json
                    import os
                    log_data = {
                        'sessionId': 'debug-session',
                        'runId': 'run1',
                        'hypothesisId': 'B',
                        'location': 'task.py:118',
                        'message': '开始数据库查询',
                        'data': {
                            'user_id': current_user.id,
                            'task_type': task_type,
                            'status': status,
                            'page': page,
                            'page_size': page_size
                        },
                        'timestamp': int(__import__('time').time() * 1000)
                    }
                    with open('/Users/kuangxb/Desktop/AI 生成数据 SDG /.cursor/debug.log', 'a') as f:
                        f.write(json.dumps(log_data) + '\n')
                except Exception as e:
                    pass
                # #endregion
                
                query = Task.query.filter_by(user_id=current_user.id)
                if task_type:
                    query = query.filter_by(task_type=task_type)
                if status:
                    query = query.filter_by(status=status)
                
                pagination = query.order_by(Task.created_at.desc()).paginate(page=page, per_page=page_size, error_out=False)
                
                # #region agent log
                try:
                    import json
                    import os
                    log_data = {
                        'sessionId': 'debug-session',
                        'runId': 'run1',
                        'hypothesisId': 'B',
                        'location': 'task.py:140',
                        'message': '数据库查询成功',
                        'data': {
                            'total_tasks': pagination.total,
                            'current_page': pagination.page,
                            'total_pages': pagination.pages,
                            'items_count': len(pagination.items)
                        },
                        'timestamp': int(__import__('time').time() * 1000)
                    }
                    with open('/Users/kuangxb/Desktop/AI 生成数据 SDG /.cursor/debug.log', 'a') as f:
                        f.write(json.dumps(log_data) + '\n')
                except Exception as e:
                    pass
                # #endregion
            except Exception as db_error:
                # #region agent log
                try:
                    import json
                    import os
                    import traceback
                    error_trace = traceback.format_exc()
                    log_data = {
                        'sessionId': 'debug-session',
                        'runId': 'run1',
                        'hypothesisId': 'C',
                        'location': 'task.py:145',
                        'message': '数据库查询失败',
                        'data': {
                            'error_type': type(db_error).__name__,
                            'error_message': str(db_error),
                            'error_trace': error_trace[:500]
                        },
                        'timestamp': int(__import__('time').time() * 1000)
                    }
                    with open('/Users/kuangxb/Desktop/AI 生成数据 SDG /.cursor/debug.log', 'a') as f:
                        f.write(json.dumps(log_data) + '\n')
                except Exception as e:
                    pass
                # #endregion
                
                print(f"数据库查询失败: {db_error}")
                import traceback
                traceback.print_exc()
                # 返回空列表而不是500错误
                return jsonify({
                    'success': True,
                    'data': {
                        'tasks': [],
                        'pagination': {
                            'page': page,
                            'page_size': page_size,
                            'total': 0,
                            'total_pages': 0
                        }
                    }
                }), 200
            
            # 处理任务数据
            tasks_data = []
            for task in pagination.items:
                try:
                    if hasattr(task, 'to_dict'):
                        task_dict = task.to_dict()
                        # 确保字段名统一
                        if 'type' in task_dict and 'task_type' not in task_dict:
                            task_dict['task_type'] = task_dict['type']
                        if 'name' not in task_dict and 'task_name' in task_dict:
                            task_dict['name'] = task_dict['task_name']
                        tasks_data.append(task_dict)
                    else:
                        # 手动构建字典
                        tasks_data.append({
                            'id': task.id,
                            'task_type': getattr(task, 'task_type', 'unknown'),
                            'name': getattr(task, 'task_name', None) or getattr(task, 'name', None) or f'任务_{task.id}',
                            'status': getattr(task, 'status', 'pending'),
                            'created_at': task.created_at.isoformat() if hasattr(task, 'created_at') and task.created_at else None,
                            'progress': getattr(task, 'progress', 0)
                        })
                except Exception as e:
                    print(f"处理任务数据失败 (ID: {getattr(task, 'id', 'unknown')}): {e}")
                    continue
            
            return jsonify({
                'success': True,
                'data': {
                    'tasks': tasks_data,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total': pagination.total,
                        'total_pages': pagination.pages
                    }
                }
            }), 200
        except Exception as e:
            print(f"查询任务失败: {e}")
            import traceback
            print(traceback.format_exc())
            # 如果查询失败，返回空列表（避免500错误）
            try:
                page = int(request.args.get('page', 1))
                page_size = int(request.args.get('page_size', 20))
            except:
                page = 1
                page_size = 20
            return jsonify({
                'success': True,
                'data': {
                    'tasks': [],
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total': 0,
                        'total_pages': 0
                    }
                }
            }), 200
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"获取任务列表失败: {e}")
        print(error_trace)
        # 返回详细的错误信息（开发环境）
        error_msg = str(e)
        if current_app.config.get('DEBUG'):
            error_msg = f"{error_msg}\n\n{error_trace[:500]}"
        return jsonify({
            'success': False,
            'error': error_msg,
            'code': 'INTERNAL_ERROR',
            'data': {
                'tasks': [],
                'pagination': {
                    'page': 1,
                    'page_size': 20,
                    'total': 0,
                    'total_pages': 0
                }
            }
        }), 500

@task_bp.route('/<task_id>/cancel', methods=['POST'])
@login_required
def cancel_task(task_id):
    """取消任务"""
    try:
        from models.task import Task, db
        
        # 支持 task_123 或 123 格式
        if isinstance(task_id, str) and task_id.startswith('task_'):
            task_id = int(task_id.replace('task_', ''))
        task = Task.query.get_or_404(task_id)
        if task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': '无权限',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        if task.status not in ['pending', 'running']:
            return jsonify({
                'success': False,
                'error': '任务无法取消',
                'code': 'INVALID_PARAMS'
            }), 400
        
        task.status = 'cancelled'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '任务已取消'
        }), 200
    except Exception as e:
        import traceback
        print(f"取消任务失败: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@task_bp.route('/<task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """删除任务"""
    try:
        from models.task import Task, db
        
        # 支持 task_123 或 123 格式
        if isinstance(task_id, str) and task_id.startswith('task_'):
            task_id = int(task_id.replace('task_', ''))
        task = Task.query.get_or_404(task_id)
        if task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': '无权限',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        # 删除结果文件（如果存在）
        if task.result_path:
            import shutil
            import os
            try:
                if os.path.exists(task.result_path):
                    shutil.rmtree(task.result_path)
            except:
                pass
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '任务已删除'
        }), 200
    except Exception as e:
        import traceback
        print(f"删除任务失败: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

