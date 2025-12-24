#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 数据平台 - 主应用
基于架构设计重新构建的模块化应用
"""

# 加载环境变量（必须在导入 config 之前）
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, redirect, url_for, render_template, request
from flask_login import LoginManager, current_user, login_required
from flask_mail import Mail
from config import Config
from models.user import db, User
from routes.auth import auth_bp
from routes.synthetic import synthetic_bp
from routes.quality import quality_bp
from routes.masking import masking_bp
from routes.task import task_bp
from routes.settings import settings_bp

def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    # 初始化扩展
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    
    mail = Mail(app)
    app.mail = mail
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(synthetic_bp, url_prefix='/api/synthesis')
    app.register_blueprint(quality_bp, url_prefix='/api/quality')
    app.register_blueprint(masking_bp, url_prefix='/api/masking')
    app.register_blueprint(task_bp, url_prefix='/api/tasks')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    
    # 根路径和健康检查
    @app.route('/')
    def index():
        """主页 - 根据请求类型返回HTML或JSON"""
        # 如果请求头包含 Accept: application/json，返回JSON
        if request.headers.get('Accept', '').find('application/json') != -1:
            from flask import Response
            import json
            data = {
                'name': 'AI 数据平台 API',
                'version': '2.0.0',
                'status': 'running',
                'endpoints': {
                    'auth': '/api/auth',
                    'synthesis': '/api/synthesis',
                    'quality': '/api/quality',
                    'masking': '/api/masking',
                    'tasks': '/api/tasks',
                    'settings': '/api/settings'
                },
                'documentation': '请参考 docs/开发文档/前后端接口文档.md'
            }
            return Response(
                json.dumps(data, ensure_ascii=False, indent=2),
                mimetype='application/json; charset=utf-8'
            ), 200
        else:
            # 返回HTML页面
            if current_user.is_authenticated:
                return render_template('index_new.html', current_user=current_user)
            else:
                return redirect(url_for('auth.login_page'))
    
    # 添加缺失的路由端点（用于模板引用）
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """仪表板页面"""
        return render_template('index_new.html', current_user=current_user)
    
    @app.route('/admin')
    @login_required
    def admin_page():
        """系统设置页面（重定向到设置页面）"""
        from utils.decorators import admin_required
        if not current_user.is_admin():
            return redirect(url_for('index'))
        return redirect('/api/settings/ai-models')
    
    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        """管理员仪表板"""
        from utils.decorators import admin_required
        if not current_user.is_admin():
            return redirect(url_for('index'))
        try:
            return render_template('admin_dashboard.html', current_user=current_user)
        except:
            return redirect(url_for('index'))
    
    @app.route('/api/settings')
    @login_required
    def settings_page():
        """系统设置页面（重定向到AI模型配置）"""
        from utils.decorators import admin_required
        if not current_user.is_admin():
            return redirect(url_for('index'))
        return redirect('/api/settings/ai-models')
    
    @app.route('/api/settings/ai-models', methods=['GET'])
    @login_required
    def settings_ai_models_page():
        """AI模型配置页面"""
        from utils.decorators import admin_required
        if not current_user.is_admin():
            return redirect(url_for('index'))
        # 如果是JSON请求，返回API数据
        if request.headers.get('Accept', '').find('application/json') != -1:
            from routes.settings import get_ai_models
            return get_ai_models()
        try:
            return render_template('settings.html', current_user=current_user, active_tab='model')
        except:
            return redirect(url_for('index'))
    
    @app.route('/api/tasks', methods=['GET'])
    @login_required
    def tasks_page():
        """任务中心页面"""
        # 如果是JSON请求，返回API数据
        if request.headers.get('Accept', '').find('application/json') != -1:
            from routes.task import get_tasks
            return get_tasks()
        try:
            return render_template('tasks.html', current_user=current_user)
        except:
            # 如果模板不存在，返回简单的任务页面
            return '''
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
                        <a href="/api/settings/ai-models">系统设置</a>
                    </div>
                    <div class="menu">
                        <span>管理员</span>
                        <span onclick="logout()">退出</span>
                    </div>
                </div>
                <main>
                    <section class="section">
                        <h2>任务中心</h2>
                        <div class="panel">
                            <div id="tasks-content">加载中...</div>
                        </div>
                    </section>
                </main>
                <script>
                    async function loadTasks() {
                        const response = await fetch('/api/tasks');
                        const result = await response.json();
                        if (result.success) {
                            const tasks = result.data.tasks;
                            const pagination = result.data.pagination;
                            let html = '<table class="table"><thead><tr><th>时间</th><th>类型</th><th>任务名称</th><th>状态</th><th>操作</th></tr></thead><tbody>';
                            if (tasks.length === 0) {
                                html += '<tr><td colspan="5" style="text-align: center; color: var(--muted);">暂无任务</td></tr>';
                            } else {
                                tasks.forEach(task => {
                                    html += `<tr><td>${new Date(task.created_at).toLocaleString()}</td><td>${task.task_type}</td><td>${task.id}</td><td>${task.status}</td><td style="color: var(--primary);">查看</td></tr>`;
                                });
                            }
                            html += '</tbody></table>';
                            document.getElementById('tasks-content').innerHTML = html;
                        }
                    }
                    function logout() {
                        fetch('/api/auth/logout', {method: 'POST'}).then(() => {
                            window.location.href = '/api/auth/login';
                        });
                    }
                    loadTasks();
                </script>
            </body>
            </html>
            ''', 200
    
    @app.route('/synthetic-data', methods=['GET'])
    @login_required
    def synthetic_data_page():
        """合成数据生成页面"""
        try:
            return render_template('synthesis.html', current_user=current_user)
        except:
            try:
                return render_template('synthetic_data.html', current_user=current_user)
            except:
                return redirect('/api/synthesis/templates')
    
    @app.route('/api/synthesis/templates', methods=['GET'])
    @login_required
    def synthesis_templates_page():
        """合成数据生成页面（API路由）"""
        # 如果是JSON请求，返回API数据
        if request.headers.get('Accept', '').find('application/json') != -1:
            from routes.synthetic import get_templates
            return get_templates()
        try:
            return render_template('synthesis.html', current_user=current_user)
        except:
            return redirect(url_for('index'))
    
    @app.route('/quality-evaluation', methods=['GET'])
    @login_required
    def quality_evaluation_page():
        """数据质量评估页面"""
        try:
            return render_template('quality.html', current_user=current_user)
        except:
            return redirect('/api/quality/upload')
    
    @app.route('/api/quality/upload', methods=['GET'])
    @login_required
    def quality_upload_page():
        """数据质量评估页面（API路由）"""
        try:
            return render_template('quality.html', current_user=current_user)
        except:
            return redirect(url_for('index'))
    
    @app.route('/sensitive-detection', methods=['GET'])
    @login_required
    def sensitive_detection_page():
        """数据脱敏页面"""
        try:
            return render_template('masking.html', current_user=current_user)
        except:
            try:
                return render_template('sensitive_detection.html', current_user=current_user)
            except:
                return redirect('/api/masking/upload')
    
    @app.route('/api/masking/upload', methods=['GET'])
    @login_required
    def masking_upload_page():
        """数据脱敏页面（API路由）"""
        try:
            return render_template('masking.html', current_user=current_user)
        except:
            return redirect(url_for('index'))
    
    @app.route('/health')
    def health_check():
        """健康检查接口"""
        from flask import Response
        import json
        data = {
            'status': 'healthy',
            'service': 'AI 数据平台',
            'version': '2.0.0'
        }
        # 使用 ensure_ascii=False 确保中文正常显示
        return Response(
            json.dumps(data, ensure_ascii=False, indent=2),
            mimetype='application/json; charset=utf-8'
        ), 200
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
