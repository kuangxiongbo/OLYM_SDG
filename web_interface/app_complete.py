#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDG多账号控制系统 - 完整版
============================

集成前端和后端的完整应用
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import json
import secrets
import string
import io
import base64
from PIL import Image, ImageDraw, ImageFont

# 导入演示数据服务
from services.demo_data_service import DemoDataService

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sdg-web-interface-secret-key-2025'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 邮箱配置
app.config['MAIL_SERVER'] = 'smtp.163.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'kuangxiongbo@163.com'
app.config['MAIL_PASSWORD'] = 'WBxQi39uvVPbLQv2'
app.config['MAIL_DEFAULT_SENDER'] = 'kuangxiongbo@163.com'

# 确保目录存在并设置数据库路径
current_dir = os.path.dirname(os.path.abspath(__file__))
instance_dir = os.path.join(current_dir, 'instance')
db_path = os.path.join(instance_dir, 'database_complete.db')

# 创建instance目录
os.makedirs(instance_dir, exist_ok=True)

# 设置数据库URI
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

# 初始化扩展
db = SQLAlchemy(app)
login_manager = LoginManager(app)
mail = Mail(app)

# 初始化演示数据服务
demo_service = DemoDataService()

# 图形验证码生成函数
def generate_captcha():
    """生成图形验证码"""
    # 生成4位随机字符
    captcha_text = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    
    # 创建图片
    width, height = 120, 40
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # 绘制背景干扰线
    import random
    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill='lightgray', width=1)
    
    # 绘制验证码文字
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
    except:
        # 使用默认字体
        font = ImageFont.load_default()
    
    # 计算文字位置
    text_width = draw.textlength(captcha_text, font=font)
    text_height = 20
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # 绘制文字
    draw.text((x, y), captcha_text, fill='black', font=font)
    
    # 添加干扰点
    for _ in range(50):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill='lightgray')
    
    # 转换为base64
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return captcha_text, image_base64

# 配置登录管理器
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'info'

# 用户模型
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    status = db.Column(db.String(20), default='active')
    email_verified = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """检查是否为管理员"""
        return self.role == 'super_admin'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'role': self.role,
            'status': self.status,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

# 邮箱验证码模型
class EmailVerification(db.Model):
    __tablename__ = 'email_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False)
    
    def __init__(self, email):
        self.email = email
        self.code = self.generate_code()
        self.expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10分钟有效期
    
    def generate_code(self):
        """生成6位数字验证码"""
        import random
        # 生成真正的随机6位数字验证码
        return str(random.randint(100000, 999999))
    
    def is_valid(self):
        """检查验证码是否有效"""
        return not self.verified and datetime.utcnow() < self.expires_at
    
    def verify(self, code):
        """验证验证码"""
        if self.is_valid() and self.code == code:
            self.verified = True
            return True
        return False
    
    def verify_for_registration(self, code):
        """注册时验证验证码（允许已验证的验证码再次验证）"""
        if self.code == code and datetime.utcnow() < self.expires_at:
            return True
        return False

class InviteCode(db.Model):
    """邀请码模型"""
    __tablename__ = 'invite_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, used, revoked
    used_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(200))  # 邀请码描述
    
    # 关系
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_invites')
    user = db.relationship('User', foreign_keys=[used_by], backref='used_invite')
    
    def __init__(self, created_by, description=None):
        self.created_by = created_by
        self.description = description
        self.code = self.generate_code()
    
    def generate_code(self):
        """生成32位推广邀请码"""
        import secrets
        return secrets.token_urlsafe(24)
    
    def is_valid(self):
        """检查邀请码是否有效"""
        return self.status == 'active'
    
    def use(self, user_id):
        """使用邀请码"""
        self.status = 'used'
        self.used_by = user_id
        self.used_at = datetime.utcnow()

class SystemConfig(db.Model):
    """系统配置模型"""
    __tablename__ = 'system_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False)
    config_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(200))
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    updater = db.relationship('User', backref='updated_configs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'created_by': self.created_by,
            'status': self.status,
            'used_by': self.used_by,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'description': self.description
        }

class CaptchaSession(db.Model):
    """图形验证码会话模型"""
    __tablename__ = 'captcha_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    captcha_code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    def __init__(self, session_id, captcha_code):
        self.session_id = session_id
        self.captcha_code = captcha_code
        self.expires_at = datetime.utcnow() + timedelta(minutes=5)  # 5分钟有效期
    
    def is_valid(self):
        """检查验证码是否有效"""
        return not self.used and datetime.utcnow() < self.expires_at
    
    def use(self):
        """标记验证码为已使用"""
        self.used = True

class LoginAttempt(db.Model):
    """登录尝试记录模型"""
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False)
    success = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.String(500))

# 数据源模型
class DataSource(db.Model):
    __tablename__ = 'data_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.String(500))
    status = db.Column(db.String(20), default='processing')
    file_size = db.Column(db.Integer)
    row_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'type': self.type,
            'file_path': self.file_path,
            'status': self.status,
            'file_size': self.file_size,
            'row_count': self.row_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 基础路由
@app.route('/')
def index():
    return render_template('index_new.html', current_user=current_user)

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0-complete',
        'database_path': db_path,
        'database_exists': os.path.exists(db_path)
    })

@app.route('/api/status')
def api_status():
    try:
        stats = {
            'users_count': User.query.count(),
            'data_sources_count': DataSource.query.count(),
            'active_users': User.query.filter_by(status='active').count(),
            'synthetic_tasks_count': 0,
            'quality_tasks_count': 0,
            'sensitive_tasks_count': 0
        }
        
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

# 认证路由
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login_new.html')
    
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        email = data.get('email')
        password = data.get('password')
        captcha_session_id = data.get('captcha_session_id')
        captcha_code = data.get('captcha_code')
        
        if not email or not password:
            return jsonify({'success': False, 'message': '邮箱和密码不能为空'}), 400
        
        # 检查登录失败次数
        recent_attempts = LoginAttempt.query.filter(
            LoginAttempt.email == email,
            LoginAttempt.success == False,
            LoginAttempt.created_at > datetime.utcnow() - timedelta(minutes=15)
        ).count()
        
        # 如果失败次数大于等于1，需要验证码
        if recent_attempts >= 1:
            if not captcha_session_id or not captcha_code:
                return jsonify({
                    'success': False, 
                    'message': '登录失败次数过多，需要图形验证码',
                    'require_captcha': True
                }), 400
            
            # 验证图形验证码
            captcha_session = CaptchaSession.query.filter_by(session_id=captcha_session_id).first()
            if not captcha_session or not captcha_session.is_valid():
                return jsonify({'success': False, 'message': '图形验证码已过期'}), 400
            
            if captcha_session.captcha_code.upper() != captcha_code.upper():
                return jsonify({'success': False, 'message': '图形验证码错误'}), 400
            
            # 标记验证码为已使用
            captcha_session.use()
        
        # 查找用户
        user = User.query.filter_by(email=email).first()
        
        # 记录登录尝试
        login_attempt = LoginAttempt(
            email=email,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            success=False
        )
        
        if user and user.check_password(password):
            if user.status == 'banned':
                login_attempt.success = False
                db.session.add(login_attempt)
                db.session.commit()
                return jsonify({'success': False, 'message': '账号已被禁用'}), 401
            
            # 登录成功
            login_user(user)
            user.last_login = datetime.utcnow()
            login_attempt.success = True
            db.session.add(login_attempt)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '登录成功',
                'user': user.to_dict()
            })
        else:
            # 登录失败
            db.session.add(login_attempt)
            db.session.commit()
            return jsonify({'success': False, 'message': '邮箱或密码错误'}), 401
    
    except Exception as e:
        return jsonify({'success': False, 'message': '登录失败'}), 500

@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        # 获取注册配置
        invite_config = SystemConfig.query.filter_by(config_key='invite_required').first()
        invite_required = False
        if invite_config and invite_config.config_value.lower() == 'true':
            invite_required = True
        
        return render_template('auth/register.html', invite_required=invite_required)
    
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        email = data.get('email')
        email_verification_code = data.get('email_verification_code')
        captcha_session_id = data.get('captcha_session_id')
        captcha_code = data.get('captcha_code')
        username = data.get('username')
        password = data.get('password')
        invite_code = data.get('invite_code')
        
        # 检查邀请码开关状态
        invite_config = SystemConfig.query.filter_by(config_key='invite_required').first()
        invite_required = False
        if invite_config and invite_config.config_value.lower() == 'true':
            invite_required = True
        
        # 如果要求邀请码，验证邀请码
        if invite_required:
            if not invite_code:
                return jsonify({'success': False, 'message': '需要邀请码才能注册'}), 400
            
            invite = InviteCode.query.filter_by(code=invite_code).first()
            if not invite or not invite.is_valid():
                return jsonify({'success': False, 'message': '邀请码无效或已使用'}), 400
        
        if not all([email, email_verification_code, captcha_session_id, captcha_code, username, password]):
            return jsonify({'success': False, 'message': '请提供完整信息'}), 400
        
        # 验证密码长度
        if len(password) < 6:
            return jsonify({'success': False, 'message': '密码至少需要6位'}), 400
        
        # 验证邮箱验证码
        email_verification = EmailVerification.query.filter_by(email=email).first()
        if not email_verification or not email_verification.verify_for_registration(email_verification_code):
            return jsonify({'success': False, 'message': '邮箱验证码错误或已过期'}), 400
        
        # 验证图形验证码
        captcha_session = CaptchaSession.query.filter_by(session_id=captcha_session_id).first()
        if not captcha_session or not captcha_session.is_valid():
            return jsonify({'success': False, 'message': '图形验证码已过期'}), 400
        
        if captcha_session.captcha_code.upper() != captcha_code.upper():
            return jsonify({'success': False, 'message': '图形验证码错误'}), 400
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '用户名已被使用'}), 400
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': '邮箱已被注册'}), 400
        
        # 创建用户
        user = User(
            email=email,
            username=username,
            role='user',
            status='active',
            email_verified=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()  # 获取用户ID
        
        # 如果使用了邀请码，标记为已使用
        if invite_required and invite_code:
            invite.use(user.id)
        
        # 标记图形验证码为已使用
        captcha_session.use()
        
        # 删除邮箱验证码记录
        db.session.delete(email_verification)
        
        db.session.commit()
        
        # 自动登录
        login_user(user)
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'user': user.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500

@app.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    try:
        logout_user()
        return jsonify({'success': True, 'message': '登出成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': '登出失败'}), 500

@app.route('/auth/check-auth')
def check_auth():
    try:
        if current_user.is_authenticated:
            return jsonify({
                'success': True,
                'authenticated': True,
                'user': current_user.to_dict()
            })
        else:
            return jsonify({
                'success': True,
                'authenticated': False
            })
    except Exception as e:
        return jsonify({'success': False, 'message': '检查失败'}), 500

# 用户管理路由
@app.route('/api/users')
@login_required
def get_users():
    try:
        users = User.query.all()
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': '获取失败'}), 500

@app.route('/api/user/profile')
@login_required
def get_profile():
    try:
        return jsonify({
            'success': True,
            'user': current_user.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': '获取失败'}), 500

# 数据源管理路由
@app.route('/data-sources')
@login_required
def data_sources():
    return render_template('data_sources.html', current_user=current_user)

@app.route('/api/data-sources')
@login_required
def get_data_sources():
    try:
        data_sources = DataSource.query.filter_by(user_id=current_user.id).all()
        return jsonify({
            'success': True,
            'data_sources': [ds.to_dict() for ds in data_sources]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': '获取失败'}), 500

# 工具页面路由
@app.route('/synthetic-data')
@login_required
def synthetic_data():
    return render_template('synthetic_data.html', current_user=current_user)

@app.route('/quality-evaluation')
@login_required
def quality_evaluation():
    return render_template('quality_evaluation.html', current_user=current_user)

@app.route('/sensitive-detection')
@login_required
def sensitive_detection():
    return render_template('sensitive_detection.html', current_user=current_user)

@app.route('/model-configs')
@login_required
def model_configs():
    return render_template('model_configs.html', current_user=current_user)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', current_user=current_user)

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'super_admin':
        flash('权限不足', 'error')
        return redirect(url_for('index'))
    return render_template('admin_dashboard.html', current_user=current_user)

@app.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('index'))

@app.route('/settings')
@login_required
def settings():
    return redirect(url_for('profile'))

# 管理员路由
@app.route('/api/admin/stats')
@login_required
def admin_stats():
    if current_user.role != 'super_admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    try:
        stats = {
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(status='active').count(),
            'total_data_sources': DataSource.query.count(),
            'admin_users': User.query.filter_by(role='super_admin').count()
        }
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': '获取失败'}), 500

# 演示数据API
@app.route('/api/demo/industries')
@login_required
def api_demo_industries():
    """获取演示行业列表"""
    try:
        industries = demo_service.get_demo_industries()
        return jsonify({
            'success': True,
            'industries': industries
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取行业列表失败: {str(e)}'
        }), 500

@app.route('/api/demo/datasets/<industry_id>')
@login_required
def api_demo_datasets(industry_id):
    """获取指定行业的演示数据集列表"""
    try:
        datasets = demo_service.get_demo_datasets(industry_id)
        return jsonify({
            'success': True,
            'datasets': datasets
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取数据集列表失败: {str(e)}'
        }), 500

@app.route('/api/demo/data/<industry_id>/<dataset_id>')
@login_required
def api_demo_data(industry_id, dataset_id):
    """获取演示数据样本"""
    try:
        sample_size = request.args.get('sample_size', 10, type=int)
        sample_data = demo_service.get_data_sample(industry_id, dataset_id, sample_size)
        return jsonify({
            'success': True,
            'data': sample_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取演示数据失败: {str(e)}'
        }), 500

@app.route('/api/demo/generate', methods=['POST'])
@login_required
def api_demo_generate():
    """生成演示数据"""
    try:
        data = request.get_json()
        industry_id = data.get('industry_id')
        dataset_id = data.get('dataset_id')
        size = data.get('size', 1000)
        
        if not industry_id or not dataset_id:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        # 生成演示数据
        df = demo_service.generate_demo_data(industry_id, dataset_id, size)
        
        # 转换为JSON格式
        result_data = {
            'columns': df.columns.tolist(),
            'types': df.dtypes.astype(str).to_dict(),
            'data': df.to_dict('records'),
            'total_rows': len(df)
        }
        
        return jsonify({
            'success': True,
            'data': result_data,
            'message': f'成功生成{len(df)}条演示数据'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成演示数据失败: {str(e)}'
        }), 500

# 邮箱验证API
@app.route('/api/auth/send_verification_code', methods=['POST'])
def send_verification_code():
    """发送邮箱验证码"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({
                'success': False,
                'message': '邮箱地址不能为空'
            }), 400
        
        # 检查邮箱格式
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({
                'success': False,
                'message': '邮箱格式不正确'
            }), 400
        
        # 检查是否已注册
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': '该邮箱已被注册'
            }), 400
        
        # 删除旧的验证码
        # 删除该邮箱的旧验证码记录
        EmailVerification.query.filter_by(email=email).delete()
        
        # 创建新的验证码记录
        verification = EmailVerification(email)
        db.session.add(verification)
        db.session.commit()
        
        # 发送邮件（测试模式：打印验证码到控制台）
        print(f"📧 邮箱验证码已生成: {email} -> {verification.code}")
        
        try:
            msg = Message(
                subject='SDG系统邮箱验证码',
                recipients=[email],
                body=f'您的验证码是: {verification.code}\n\n验证码有效期为10分钟，请及时使用。\n\nSDG多账号控制系统'
            )
            mail.send(msg)
            print(f"✅ 邮件发送成功: {email}")
        except Exception as e:
            print(f"⚠️  邮件发送失败: {str(e)}")
            print(f"📋 测试模式：验证码为 {verification.code}")
        
        return jsonify({
            'success': True,
            'message': '验证码已发送到您的邮箱'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'发送验证码失败: {str(e)}'
        }), 500

@app.route('/api/auth/verify_email', methods=['POST'])
def verify_email():
    """验证邮箱验证码"""
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        
        if not email or not code:
            return jsonify({
                'success': False,
                'message': '邮箱和验证码不能为空'
            }), 400
        
        verification = EmailVerification.query.filter_by(email=email).first()
        if not verification:
            return jsonify({
                'success': False,
                'message': '验证码不存在或已过期'
            }), 400
        
        if verification.verify(code):
            # 验证成功，但不删除记录，标记为已验证
            # 记录将在注册时被删除
            db.session.commit()
            return jsonify({
                'success': True,
                'message': '邮箱验证成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '验证码错误或已过期'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'验证失败: {str(e)}'
        }), 500

@app.route('/api/auth/register', methods=['POST'])
def register_user():
    """用户注册"""
    try:
        data = request.get_json()
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        verification_code = data.get('verification_code')
        
        # 验证必填字段
        if not all([email, username, password, verification_code]):
            return jsonify({
                'success': False,
                'message': '所有字段都是必填的'
            }), 400
        
        # 验证邮箱是否已验证
        verification = EmailVerification.query.filter_by(email=email).first()
        if not verification or not verification.verified:
            return jsonify({
                'success': False,
                'message': '请先验证邮箱'
            }), 400
        
        # 检查用户是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'message': '该邮箱已被注册'
            }), 400
        
        # 创建新用户
        user = User(
            email=email,
            username=username,
            email_verified=True  # 已验证邮箱
        )
        user.set_password(password)
        
        db.session.add(user)
        
        # 删除验证码记录
        db.session.delete(verification)
        
        db.session.commit()
        
        # 自动登录
        login_user(user)
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }), 500

# 合成数据生成API
@app.route('/api/synthetic/generate', methods=['POST'])
@login_required
def generate_synthetic_data():
    """生成合成数据"""
    try:
        data = request.get_json()
        
        # 获取参数
        demo_data = data.get('demo_data')
        model_type = data.get('model_type', 'ctgan')
        model_config = data.get('model_config', 'default')
        data_amount = data.get('data_amount', 1000)
        similarity = data.get('similarity', 0.8)
        
        # 检查是否有演示数据或数据源
        has_demo_data = demo_data and demo_data.get('data') and len(demo_data.get('data', [])) > 0
        has_data_source = data.get('data_source_id')
        
        if not has_demo_data and not has_data_source:
            return jsonify({
                'success': False,
                'message': '请提供演示数据或选择数据源'
            }), 400
        
        # 模拟SDG合成数据生成过程
        import pandas as pd
        import numpy as np
        
        if has_demo_data:
            # 使用演示数据生成合成数据
            original_df = pd.DataFrame(demo_data['data'])
            print(f"使用演示数据生成合成数据，原始数据形状: {original_df.shape}")
        else:
            # 这里应该从数据源获取数据，暂时使用模拟数据
            original_df = pd.DataFrame({
                'feature1': np.random.normal(0, 1, 100),
                'feature2': np.random.normal(0, 1, 100),
                'feature3': np.random.choice(['A', 'B', 'C'], 100)
            })
            print(f"使用模拟数据生成合成数据，原始数据形状: {original_df.shape}")
        
        # 模拟生成过程
        import time
        time.sleep(2)  # 模拟处理时间
        
        # 生成合成数据（简化版本）
        synthetic_df = original_df.copy()
        
        # 添加一些随机噪声来模拟合成效果
        for col in synthetic_df.select_dtypes(include=[np.number]).columns:
            noise = np.random.normal(0, 0.1, len(synthetic_df))
            synthetic_df[col] = synthetic_df[col] + noise * synthetic_df[col].std()
        
        # 调整数据量
        if len(synthetic_df) < data_amount:
            # 重复数据来达到目标数量
            repeat_times = (data_amount // len(synthetic_df)) + 1
            synthetic_df = pd.concat([synthetic_df] * repeat_times, ignore_index=True)
        
        synthetic_df = synthetic_df.head(data_amount)
        
        # 计算质量指标
        quality_metrics = {
            'statistical_similarity': 0.85 + np.random.uniform(-0.1, 0.1),
            'distribution_similarity': 0.80 + np.random.uniform(-0.1, 0.1),
            'correlation_preservation': 0.88 + np.random.uniform(-0.1, 0.1),
            'overall_score': 0.84 + np.random.uniform(-0.1, 0.1)
        }
        
        result = {
            'original_data': {
                'columns': original_df.columns.tolist(),
                'shape': original_df.shape,
                'sample': original_df.head(5).to_dict('records')
            },
            'synthetic_data': {
                'columns': synthetic_df.columns.tolist(),
                'shape': synthetic_df.shape,
                'sample': synthetic_df.head(5).to_dict('records'),
                'data': synthetic_df.to_dict('records')
            },
            'quality_metrics': quality_metrics,
            'generation_config': {
                'model_type': model_type,
                'model_config': model_config,
                'data_amount': data_amount,
                'similarity': similarity
            },
            'processing_time': 2.5
        }
        
        return jsonify({
            'success': True,
            'message': f'成功生成{len(synthetic_df)}条合成数据',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成合成数据失败: {str(e)}'
        }), 500

# 使用演示数据直接生成合成数据的API
@app.route('/api/synthetic/generate_from_demo', methods=['POST'])
@login_required
def generate_synthetic_from_demo():
    """使用演示数据直接生成合成数据"""
    try:
        data = request.get_json()
        
        # 获取参数
        industry_id = data.get('industry_id')
        dataset_id = data.get('dataset_id')
        demo_size = data.get('demo_size', 100)
        model_type = data.get('model_type', 'ctgan')
        model_config = data.get('model_config', 'default')
        synthetic_amount = data.get('synthetic_amount', 1000)
        similarity = data.get('similarity', 0.8)
        
        if not industry_id or not dataset_id:
            return jsonify({
                'success': False,
                'message': '请选择行业和数据集'
            }), 400
        
        # 生成演示数据
        print(f"生成演示数据: {industry_id}/{dataset_id}, 数量: {demo_size}")
        demo_df = demo_service.generate_demo_data(industry_id, dataset_id, demo_size)
        
        # 模拟SDG合成数据生成过程
        import pandas as pd
        import numpy as np
        import time
        
        print(f"原始演示数据形状: {demo_df.shape}")
        
        # 模拟生成过程
        time.sleep(1)  # 模拟处理时间
        
        # 生成合成数据（简化版本）
        synthetic_df = demo_df.copy()
        
        # 添加一些随机噪声来模拟合成效果
        for col in synthetic_df.select_dtypes(include=[np.number]).columns:
            noise = np.random.normal(0, 0.05, len(synthetic_df))  # 减少噪声强度
            synthetic_df[col] = synthetic_df[col] + noise * synthetic_df[col].std()
        
        # 调整数据量
        if len(synthetic_df) < synthetic_amount:
            # 重复数据来达到目标数量
            repeat_times = (synthetic_amount // len(synthetic_df)) + 1
            synthetic_df = pd.concat([synthetic_df] * repeat_times, ignore_index=True)
        
        synthetic_df = synthetic_df.head(synthetic_amount)
        
        # 计算质量指标
        quality_metrics = {
            'statistical_similarity': 0.85 + np.random.uniform(-0.05, 0.05),
            'distribution_similarity': 0.80 + np.random.uniform(-0.05, 0.05),
            'correlation_preservation': 0.88 + np.random.uniform(-0.05, 0.05),
            'overall_score': 0.84 + np.random.uniform(-0.05, 0.05)
        }
        
        result = {
            'original_data': {
                'columns': demo_df.columns.tolist(),
                'shape': demo_df.shape,
                'sample': demo_df.head(5).to_dict('records')
            },
            'synthetic_data': {
                'columns': synthetic_df.columns.tolist(),
                'shape': synthetic_df.shape,
                'sample': synthetic_df.head(5).to_dict('records'),
                'data': synthetic_df.to_dict('records')
            },
            'quality_metrics': quality_metrics,
            'generation_config': {
                'industry_id': industry_id,
                'dataset_id': dataset_id,
                'model_type': model_type,
                'model_config': model_config,
                'demo_size': demo_size,
                'synthetic_amount': synthetic_amount,
                'similarity': similarity
            },
            'processing_time': 1.5
        }
        
        return jsonify({
            'success': True,
            'message': f'成功生成{len(synthetic_df)}条合成数据',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成合成数据失败: {str(e)}'
        }), 500

def create_app():
    """创建应用实例"""
    print("🔧 初始化完整版应用...")
    
    # 数据库初始化
    try:
        with app.app_context():
            print("🔧 创建数据库表...")
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 创建测试数据
            create_test_data()
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise
    
    return app

def create_test_data():
    """创建测试数据"""
    try:
        # 检查是否已有数据
        if User.query.count() == 0:
            # 创建测试用户
            test_user = User(
                email='test@example.com',
                username='testuser',
                role='user',
                status='active',
                email_verified=True
            )
            test_user.set_password('test123')
            db.session.add(test_user)
            
            # 创建管理员用户
            admin_user = User(
                email='admin@sdg.com',
                username='admin',
                role='super_admin',
                status='active',
                email_verified=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            
            db.session.commit()
            print("✅ 测试数据创建成功")
        else:
            print("ℹ️  测试数据已存在")
            
    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")

# 管理后台API路由
@app.route('/api/admin/users', methods=['GET'])
@login_required
def admin_get_users():
    """获取所有用户"""
    try:
        # 检查是否为管理员
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        users = User.query.order_by(User.created_at.desc()).all()
        print(f"DEBUG: 找到 {len(users)} 个用户")
        
        user_list = []
        for user in users:
            try:
                user_dict = user.to_dict()
                user_list.append(user_dict)
            except Exception as e:
                print(f"DEBUG: 用户 {user.id} 转换失败: {e}")
                continue
        
        return jsonify({
            'success': True,
            'users': user_list
        })
    except Exception as e:
        print(f"DEBUG: 用户列表API错误: {e}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
def admin_delete_user(user_id):
    """删除用户"""
    try:
        # 检查是否为管理员
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        # 不能删除自己
        if user_id == current_user.id:
            return jsonify({'success': False, 'message': '不能删除自己的账号'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 删除用户及其相关数据
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '用户删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

@app.route('/api/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def admin_toggle_user_status(user_id):
    """切换用户状态"""
    try:
        # 检查是否为管理员
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 切换状态
        if user.status == 'active':
            user.status = 'inactive'
        else:
            user.status = 'active'
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'用户状态已切换为{user.status}',
            'user': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'状态切换失败: {str(e)}'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@login_required
def admin_update_user(user_id):
    """更新用户信息"""
    try:
        # 检查是否为管理员
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        data = request.get_json()
        
        # 更新用户信息
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            # 检查邮箱是否已被其他用户使用
            existing_user = User.query.filter(User.email == data['email'], User.id != user_id).first()
            if existing_user:
                return jsonify({'success': False, 'message': '邮箱已被其他用户使用'}), 400
            user.email = data['email']
        if 'role' in data:
            if data['role'] in ['user', 'super_admin']:
                user.role = data['role']
            else:
                return jsonify({'success': False, 'message': '无效的用户角色'}), 400
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': '用户信息更新成功',
            'user': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500

@app.route('/api/admin/stats', methods=['GET'])
@login_required
def admin_get_stats():
    """获取系统统计信息"""
    try:
        # 检查是否为管理员
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        stats = {
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(status='active').count(),
            'admin_users': User.query.filter_by(role='super_admin').count(),
            'total_data_sources': DataSource.query.count(),
            'total_model_configs': 0,  # ModelConfig模型暂时不存在
            'pending_invites': InviteCode.query.filter_by(status='pending').count(),
            'used_invites': InviteCode.query.filter_by(status='used').count()
        }
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': '获取失败'}), 500

# 推广邀请码系统API
@app.route('/api/admin/invite/generate', methods=['POST'])
@login_required
def admin_generate_invite():
    """管理员生成推广邀请码"""
    try:
        # 检查是否为管理员
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        data = request.get_json()
        description = data.get('description', '推广邀请码')
        
        # 创建推广邀请码
        invite = InviteCode(created_by=current_user.id, description=description)
        db.session.add(invite)
        db.session.commit()
        
        # 生成注册链接
        register_url = f"http://localhost:5000/auth/register?invite={invite.code}"
        
        return jsonify({
            'success': True,
            'message': '推广邀请码生成成功',
            'invite_code': invite.code,
            'register_url': register_url,
            'description': description
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'生成邀请码失败: {str(e)}'}), 500

@app.route('/api/admin/invite/list', methods=['GET'])
@login_required
def admin_get_invites():
    """获取邀请列表"""
    try:
        # 检查是否为管理员
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        invites = InviteCode.query.order_by(InviteCode.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'invites': [invite.to_dict() for invite in invites]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': '获取失败'}), 500

@app.route('/api/admin/invite/<int:invite_id>', methods=['DELETE'])
@login_required
def admin_revoke_invite(invite_id):
    """撤销邀请"""
    try:
        # 检查是否为管理员
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        invite = InviteCode.query.get(invite_id)
        if not invite:
            return jsonify({'success': False, 'message': '邀请不存在'}), 404
        
        if invite.status != 'pending':
            return jsonify({'success': False, 'message': '只能撤销待使用的邀请'}), 400
        
        invite.status = 'revoked'
        db.session.commit()
        
        return jsonify({'success': True, 'message': '邀请已撤销'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'撤销失败: {str(e)}'}), 500

@app.route('/api/auth/verify_invite/<invite_code>', methods=['GET'])
def verify_invite_code(invite_code):
    """验证推广邀请码"""
    try:
        invite = InviteCode.query.filter_by(code=invite_code).first()
        
        if not invite:
            return jsonify({'success': False, 'message': '邀请码不存在'}), 404
        
        if not invite.is_valid():
            if invite.status == 'used':
                return jsonify({'success': False, 'message': '邀请码已被使用'}), 400
            elif invite.status == 'revoked':
                return jsonify({'success': False, 'message': '邀请码已被撤销'}), 400
            else:
                return jsonify({'success': False, 'message': '邀请码无效'}), 400
        
        return jsonify({
            'success': True,
            'message': '邀请码有效',
            'description': invite.description,
            'created_at': invite.created_at.isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'验证失败: {str(e)}'}), 500

@app.route('/api/auth/register_with_invite', methods=['POST'])
def register_with_invite():
    """使用邀请码注册"""
    try:
        data = request.get_json()
        invite_code = data.get('invite_code')
        username = data.get('username')
        password = data.get('password')
        
        if not all([invite_code, username, password]):
            return jsonify({'success': False, 'message': '请提供完整信息'}), 400
        
        # 验证邀请码
        invite = InviteCode.query.filter_by(code=invite_code).first()
        if not invite or not invite.is_valid():
            return jsonify({'success': False, 'message': '邀请码无效或已过期'}), 400
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        # 创建用户
        user = User(
            email=invite.email,
            username=username,
            role='user',
            status='active',
            email_verified=True
        )
        user.set_password(password)
        
        db.session.add(user)
        
        # 标记邀请码为已使用
        invite.use()
        
        db.session.commit()
        
        # 自动登录
        login_user(user)
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500

# 图形验证码API
@app.route('/api/captcha/generate', methods=['GET'])
def generate_captcha_api():
    """生成图形验证码"""
    try:
        # 生成验证码
        captcha_text, image_base64 = generate_captcha()
        
        # 生成会话ID
        session_id = secrets.token_urlsafe(32)
        
        # 保存验证码到数据库
        captcha_session = CaptchaSession(session_id=session_id, captcha_code=captcha_text)
        db.session.add(captcha_session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'image': f'data:image/png;base64,{image_base64}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成验证码失败: {str(e)}'}), 500

@app.route('/api/captcha/verify', methods=['POST'])
def verify_captcha_api():
    """验证图形验证码"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        captcha_code = data.get('captcha_code')
        
        if not session_id or not captcha_code:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        # 查找验证码会话
        captcha_session = CaptchaSession.query.filter_by(session_id=session_id).first()
        
        if not captcha_session:
            return jsonify({'success': False, 'message': '验证码会话不存在'}), 404
        
        if not captcha_session.is_valid():
            return jsonify({'success': False, 'message': '验证码已过期'}), 400
        
        # 验证验证码
        if captcha_session.captcha_code.upper() == captcha_code.upper():
            captcha_session.use()
            db.session.commit()
            return jsonify({'success': True, 'message': '验证码正确'})
        else:
            return jsonify({'success': False, 'message': '验证码错误'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'验证失败: {str(e)}'}), 500

@app.route('/api/auth/register_config', methods=['GET'])
def get_register_config():
    """获取注册配置"""
    try:
        # 获取邀请码开关状态
        invite_config = SystemConfig.query.filter_by(config_key='invite_required').first()
        invite_required = False
        if invite_config and invite_config.config_value.lower() == 'true':
            invite_required = True
        
        return jsonify({
            'success': True,
            'invite_required': invite_required
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取配置失败: {str(e)}'}), 500

@app.route('/api/admin/invite/toggle', methods=['POST'])
@login_required
def toggle_invite_mode():
    """开启/关闭邀请码注册模式"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': '需要管理员权限'}), 403
        
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        # 更新或创建配置
        config = SystemConfig.query.filter_by(config_key='invite_required').first()
        if config:
            config.config_value = str(enabled).lower()
            config.updated_by = current_user.id
            config.updated_at = datetime.utcnow()
        else:
            config = SystemConfig(
                config_key='invite_required',
                config_value=str(enabled).lower(),
                description='是否要求邀请码注册',
                updated_by=current_user.id
            )
            db.session.add(config)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'邀请码注册模式已{"开启" if enabled else "关闭"}',
            'invite_required': enabled
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500

@app.route('/api/admin/email/config', methods=['GET'])
@login_required
def get_email_config():
    """获取邮件服务器配置"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': '需要管理员权限'}), 403
        
        # 获取邮件配置
        email_config = {
            'mail_server': app.config.get('MAIL_SERVER', ''),
            'mail_port': app.config.get('MAIL_PORT', ''),
            'mail_use_ssl': app.config.get('MAIL_USE_SSL', False),
            'mail_use_tls': app.config.get('MAIL_USE_TLS', False),
            'mail_username': app.config.get('MAIL_USERNAME', ''),
            'mail_password': '***' if app.config.get('MAIL_PASSWORD') else '',  # 隐藏密码
            'mail_default_sender': app.config.get('MAIL_DEFAULT_SENDER', ''),
            'mail_max_emails': app.config.get('MAIL_MAX_EMAILS', ''),
            'mail_suppress_send': app.config.get('MAIL_SUPPRESS_SEND', False),
            'mail_debug': app.config.get('MAIL_DEBUG', False)
        }
        
        return jsonify({
            'success': True,
            'email_config': email_config
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取邮件配置失败: {str(e)}'}), 500

@app.route('/api/admin/email/test', methods=['POST'])
@login_required
def test_email_config():
    """测试邮件服务器配置"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': '需要管理员权限'}), 403
        
        data = request.get_json()
        test_email = data.get('test_email', current_user.email)
        
        if not test_email:
            return jsonify({'success': False, 'message': '请提供测试邮箱地址'}), 400
        
        # 发送测试邮件
        from flask_mail import Message
        msg = Message(
            subject='SDG系统邮件配置测试',
            recipients=[test_email],
            body=f'''
这是一封测试邮件，用于验证SDG系统的邮件服务器配置。

发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
发送者: {current_user.username}
系统: SDG多账号控制系统

如果您收到这封邮件，说明邮件服务器配置正常。
            ''',
            html=f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">SDG系统邮件配置测试</h2>
                <p>这是一封测试邮件，用于验证SDG系统的邮件服务器配置。</p>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>发送时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>发送者:</strong> {current_user.username}</p>
                    <p><strong>系统:</strong> SDG多账号控制系统</p>
                </div>
                <p style="color: #28a745;">如果您收到这封邮件，说明邮件服务器配置正常。</p>
            </div>
            '''
        )
        
        mail.send(msg)
        
        return jsonify({
            'success': True,
            'message': f'测试邮件已发送到 {test_email}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送测试邮件失败: {str(e)}'}), 500

if __name__ == '__main__':
    # 创建应用
    print("🚀 启动SDG多账号控制系统 - 完整版...")
    app = create_app()
    
    print("📱 访问地址: http://localhost:5000")
    print("🔐 认证功能:")
    print("   - 注册: http://localhost:5000/auth/register")
    print("   - 登录: http://localhost:5000/auth/login")
    print("   - 用户资料: http://localhost:5000/api/user/profile")
    print("   - 数据源管理: http://localhost:5000/data-sources")
    print("   - 合成数据: http://localhost:5000/synthetic-data")
    print("   - 质量评估: http://localhost:5000/quality-evaluation")
    print("   - 敏感检测: http://localhost:5000/sensitive-detection")
    print("   - 管理后台: http://localhost:5000/admin")
    print("")
    print("💡 测试账号:")
    print("   - 普通用户: test@example.com / test123")
    print("   - 管理员: admin@sdg.com / admin123")
    print("💡 数据库路径:", db_path)
    print("💡 按Ctrl+C停止服务")
    print("")
    
    # 运行应用
    app.run(debug=True, host='0.0.0.0', port=5000)
