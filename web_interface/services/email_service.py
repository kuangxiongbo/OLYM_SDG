#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件服务
"""

from flask import current_app
from flask_mail import Message
import sys

class EmailService:
    """邮件服务类"""
    
    def __init__(self):
        self.mail = current_app.mail
        # 确保使用最新的邮箱配置
        self._load_email_config()
    
    def _load_email_config(self):
        """从数据库加载邮箱配置并更新Flask-Mail配置"""
        try:
            try:
                from models.config import SystemConfig
            except ImportError:
                from models.log import SystemConfig
            from models.user import db
            from utils.encryption import encryption_service
            
            # 获取邮箱配置
            config = SystemConfig.query.filter_by(config_key='email_server').first()
            if not config:
                print("[WARNING] 邮箱配置不存在，使用默认配置", file=sys.stderr)
                return
            
            # 解析配置值
            import json
            if hasattr(config, 'get_value'):
                config_value = config.get_value()
            else:
                config_value = json.loads(config.config_value) if config.config_value else {}
            
            # 检查是否启用
            if not config_value.get('enabled', False):
                print("[WARNING] 邮箱服务未启用", file=sys.stderr)
                return
            
            # 获取邮箱配置
            email_config = config_value.get('config', {})
            if not email_config:
                print("[WARNING] 邮箱配置为空", file=sys.stderr)
                return
            
            smtp_host = email_config.get('smtp_host', '')
            smtp_port = email_config.get('smtp_port', 465)
            encryption = email_config.get('encryption', 'SSL')
            sender_email = email_config.get('sender_email', '')
            auth_code = email_config.get('auth_code', '')
            
            if not smtp_host or not sender_email:
                print("[WARNING] 邮箱配置不完整", file=sys.stderr)
                return
            
            # 更新Flask-Mail配置
            current_app.config['MAIL_SERVER'] = smtp_host
            current_app.config['MAIL_PORT'] = int(smtp_port)
            current_app.config['MAIL_USE_SSL'] = (encryption == 'SSL')
            current_app.config['MAIL_USE_TLS'] = (encryption == 'TLS')
            current_app.config['MAIL_USERNAME'] = sender_email
            
            # 解密授权码
            if auth_code and not auth_code.startswith('***'):
                if encryption_service:
                    try:
                        current_app.config['MAIL_PASSWORD'] = encryption_service.decrypt(auth_code)
                    except:
                        current_app.config['MAIL_PASSWORD'] = auth_code
                else:
                    current_app.config['MAIL_PASSWORD'] = auth_code
            
            current_app.config['MAIL_DEFAULT_SENDER'] = sender_email
            
            # 重新初始化Mail对象以应用新配置
            try:
                from flask_mail import Mail
                current_app.mail = Mail(current_app)
                print(f"[INFO] Mail对象已重新初始化", file=sys.stderr)
            except Exception as e:
                print(f"[WARNING] 重新初始化Mail对象失败: {e}", file=sys.stderr)
                # 即使重新初始化失败，也尝试使用现有配置
                pass
            
            # 更新self.mail引用
            self.mail = current_app.mail
            
            print(f"[INFO] 邮箱配置已加载: {smtp_host}:{smtp_port} ({encryption}), 发件人: {sender_email}", file=sys.stderr)
            print(f"[DEBUG] MAIL_SERVER: {current_app.config.get('MAIL_SERVER')}", file=sys.stderr)
            print(f"[DEBUG] MAIL_PORT: {current_app.config.get('MAIL_PORT')}", file=sys.stderr)
            print(f"[DEBUG] MAIL_USE_SSL: {current_app.config.get('MAIL_USE_SSL')}", file=sys.stderr)
            print(f"[DEBUG] MAIL_USE_TLS: {current_app.config.get('MAIL_USE_TLS')}", file=sys.stderr)
            print(f"[DEBUG] MAIL_USERNAME: {current_app.config.get('MAIL_USERNAME')}", file=sys.stderr)
            print(f"[DEBUG] MAIL_PASSWORD: {'***' if current_app.config.get('MAIL_PASSWORD') else 'None'}", file=sys.stderr)
            print(f"[DEBUG] MAIL_DEFAULT_SENDER: {current_app.config.get('MAIL_DEFAULT_SENDER')}", file=sys.stderr)
            
        except Exception as e:
            print(f"[ERROR] 加载邮箱配置失败: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
    
    def send_activation_email(self, email, activation_code):
        """发送激活邮件"""
        # 确保使用最新配置
        self._load_email_config()
        
        # 检查邮件配置是否完整
        if not current_app.config.get('MAIL_SERVER'):
            raise ValueError('邮件服务器未配置，请先在系统设置中配置邮箱服务器')
        
        sender_email = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
        if not sender_email:
            raise ValueError('发件人邮箱未配置')
        
        subject = "AI 数据平台 - 账号激活"
        
        # HTML格式的邮件内容
        html_body = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>账号激活</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 40px 30px;">
        <!-- 头部 -->
        <div style="text-align: center; margin-bottom: 40px;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #1e40af;">AI 数据平台</h1>
            <p style="margin: 8px 0 0 0; font-size: 14px; color: #6b7280;">欢迎加入我们！</p>
        </div>
        
        <!-- 主要内容 -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 30px; margin-bottom: 30px; text-align: center;">
            <h2 style="margin: 0 0 20px 0; font-size: 20px; font-weight: 600; color: #ffffff;">账号激活</h2>
            <p style="margin: 0; font-size: 16px; color: #ffffff; line-height: 1.6;">
                感谢您注册 AI 数据平台！<br>
                请使用以下激活码完成账号激活：
            </p>
        </div>
        
        <!-- 激活码 -->
        <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 24px; margin-bottom: 30px; text-align: center;">
            <p style="margin: 0 0 12px 0; font-size: 14px; color: #6b7280;">您的激活码</p>
            <div style="display: inline-block; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px 32px;">
                <span style="font-size: 32px; font-weight: 700; letter-spacing: 4px; color: #1e40af; font-family: 'Courier New', monospace;">{activation_code}</span>
            </div>
        </div>
        
        <!-- 说明 -->
        <div style="background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 8px; padding: 16px; margin-bottom: 30px;">
            <p style="margin: 0; font-size: 14px; color: #92400e; line-height: 1.6;">
                <strong>⚠️ 重要提示：</strong><br>
                • 激活码有效期为 <strong>24 小时</strong>，请及时激活<br>
                • 如果这不是您的操作，请忽略此邮件<br>
                • 激活码仅可使用一次，使用后即失效
            </p>
        </div>
        
        <!-- 操作指引 -->
        <div style="margin-bottom: 30px;">
            <h3 style="margin: 0 0 16px 0; font-size: 16px; font-weight: 600; color: #1f2937;">如何激活账号？</h3>
            <ol style="margin: 0; padding-left: 20px; font-size: 14px; color: #4b5563; line-height: 1.8;">
                <li>访问激活页面</li>
                <li>输入您的邮箱和激活码</li>
                <li>点击"激活账号"完成激活</li>
            </ol>
        </div>
        
        <!-- 底部 -->
        <div style="border-top: 1px solid #e5e7eb; padding-top: 24px; text-align: center;">
            <p style="margin: 0 0 8px 0; font-size: 12px; color: #9ca3af;">
                此邮件由系统自动发送，请勿回复。<br>
                如有疑问，请联系：<a href="mailto:kuangxb@myibc.net" style="color: #3b82f6; text-decoration: none;">kuangxb@myibc.net</a>
            </p>
            <p style="margin: 8px 0 0 0; font-size: 12px; color: #9ca3af;">
                © 2024 AI 数据平台. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        # 纯文本格式（作为备用）
        text_body = f"""
欢迎注册 AI 数据平台！

感谢您注册我们的平台。请使用以下激活码完成账号激活：

激活码：{activation_code}

重要提示：
- 激活码有效期为 24 小时，请及时激活
- 如果这不是您的操作，请忽略此邮件
- 激活码仅可使用一次，使用后即失效

如何激活账号？
1. 访问激活页面
2. 输入您的邮箱和激活码
3. 点击"激活账号"完成激活

---
此邮件由系统自动发送，请勿回复。
如有疑问，请联系：kuangxb@myibc.net

© 2024 AI 数据平台. All rights reserved.
        """
        
        msg = Message(
            subject=subject,
            recipients=[email],
            sender=sender_email
        )
        msg.body = text_body
        msg.html = html_body
        
        try:
            print(f"[DEBUG] 准备发送邮件到: {email}, 发件人: {sender_email}", file=sys.stderr)
            print(f"[DEBUG] 邮件主题: {subject}", file=sys.stderr)
            print(f"[DEBUG] 当前MAIL配置 - SERVER: {current_app.config.get('MAIL_SERVER')}, PORT: {current_app.config.get('MAIL_PORT')}", file=sys.stderr)
            
            self.mail.send(msg)
            print(f"[INFO] ✅ 激活邮件已成功发送到: {email}", file=sys.stderr)
            
            # 记录发送邮件日志（在EmailService中记录，因为这里可能没有user_id）
            try:
                from utils.helpers import log_operation_direct
                # 尝试从email查找用户ID
                from models.user import User
                user = User.query.filter_by(email=email).first()
                log_operation_direct(
                    action='系统发送邮件',
                    resource_type='email',
                    resource_id=user.id if user else None,
                    result='success',
                    user_id=user.id if user else None,
                    details={
                        'recipient': email,
                        'email_type': 'activation',
                        'sender': sender_email
                    }
                )
            except:
                pass  # 日志记录失败不影响邮件发送
            
        except Exception as e:
            print(f"[ERROR] ❌ 发送激活邮件失败: {e}", file=sys.stderr)
            print(f"[ERROR] 邮件配置检查:", file=sys.stderr)
            print(f"[ERROR]   MAIL_SERVER: {current_app.config.get('MAIL_SERVER')}", file=sys.stderr)
            print(f"[ERROR]   MAIL_PORT: {current_app.config.get('MAIL_PORT')}", file=sys.stderr)
            print(f"[ERROR]   MAIL_USERNAME: {current_app.config.get('MAIL_USERNAME')}", file=sys.stderr)
            print(f"[ERROR]   MAIL_PASSWORD: {'已设置' if current_app.config.get('MAIL_PASSWORD') else '未设置'}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            
            # 记录发送邮件失败日志
            try:
                from utils.helpers import log_operation_direct
                from models.user import User
                user = User.query.filter_by(email=email).first()
                log_operation_direct(
                    action='系统发送邮件',
                    resource_type='email',
                    resource_id=user.id if user else None,
                    result='failure',
                    user_id=user.id if user else None,
                    details={
                        'recipient': email,
                        'email_type': 'activation',
                        'sender': sender_email,
                        'error': str(e)
                    }
                )
            except:
                pass
            
            raise
    
    def send_test_email(self, recipient):
        """发送测试邮件"""
        subject = "AI 数据平台 - 测试邮件"
        body = "这是一封测试邮件，如果您收到此邮件，说明邮箱配置正确。"
        
        msg = Message(
            subject=subject,
            recipients=[recipient],
            body=body
        )
        
        self.mail.send(msg)



