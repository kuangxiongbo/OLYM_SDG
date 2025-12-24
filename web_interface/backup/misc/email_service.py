#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮箱验证服务
=============

处理用户注册和密码重置的邮箱验证功能
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailConfig:
    """邮箱配置"""
    
    def __init__(self):
        # 从环境变量或配置文件读取邮箱配置
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.qq.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', '')
        self.from_name = os.getenv('FROM_NAME', 'SDG Web界面')
        
        # 应用URL配置
        self.app_url = os.getenv('APP_URL', 'http://localhost:5000')
        
        # 是否启用邮箱服务
        self.enabled = bool(self.smtp_username and self.smtp_password and self.from_email)

class EmailService:
    """邮箱服务"""
    
    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig()
        self.logger = logger
    
    def send_verification_email(self, email: str, username: str, token: str) -> bool:
        """发送邮箱验证邮件"""
        if not self.config.enabled:
            self.logger.warning("邮箱服务未启用，跳过发送验证邮件")
            return True
        
        try:
            verification_url = f"{self.config.app_url}/auth/verify_email?token={token}"
            
            subject = f"欢迎注册 {self.config.from_name} - 请验证您的邮箱"
            
            html_content = self._get_verification_email_html(
                username, verification_url
            )
            
            text_content = self._get_verification_email_text(
                username, verification_url
            )
            
            return self._send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            self.logger.error(f"发送验证邮件失败: {str(e)}")
            return False
    
    def send_password_reset_email(self, email: str, username: str, token: str) -> bool:
        """发送密码重置邮件"""
        if not self.config.enabled:
            self.logger.warning("邮箱服务未启用，跳过发送重置邮件")
            return True
        
        try:
            reset_url = f"{self.config.app_url}/auth/reset_password?token={token}"
            
            subject = f"{self.config.from_name} - 密码重置请求"
            
            html_content = self._get_password_reset_email_html(
                username, reset_url
            )
            
            text_content = self._get_password_reset_email_text(
                username, reset_url
            )
            
            return self._send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            self.logger.error(f"发送密码重置邮件失败: {str(e)}")
            return False
    
    def send_welcome_email(self, email: str, username: str) -> bool:
        """发送欢迎邮件"""
        if not self.config.enabled:
            self.logger.warning("邮箱服务未启用，跳过发送欢迎邮件")
            return True
        
        try:
            subject = f"欢迎使用 {self.config.from_name}！"
            
            html_content = self._get_welcome_email_html(username)
            text_content = self._get_welcome_email_text(username)
            
            return self._send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            self.logger.error(f"发送欢迎邮件失败: {str(e)}")
            return False
    
    def _send_email(self, to_email: str, subject: str, 
                   html_content: str, text_content: str) -> bool:
        """发送邮件"""
        try:
            # 创建邮件
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            message["To"] = to_email
            
            # 添加文本和HTML内容
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # 发送邮件
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(message)
            
            self.logger.info(f"邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"发送邮件失败: {str(e)}")
            return False
    
    def _get_verification_email_html(self, username: str, verification_url: str) -> str:
        """获取验证邮件HTML内容"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>邮箱验证</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 欢迎加入 {self.config.from_name}！</h1>
                </div>
                <div class="content">
                    <h2>亲爱的 {username}，</h2>
                    <p>感谢您注册我们的服务！为了确保您的账户安全，请点击下面的按钮验证您的邮箱地址：</p>
                    
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">验证邮箱</a>
                    </div>
                    
                    <p>如果按钮无法点击，您也可以复制以下链接到浏览器中打开：</p>
                    <p style="word-break: break-all; background: #eee; padding: 10px; border-radius: 5px;">
                        {verification_url}
                    </p>
                    
                    <p><strong>注意事项：</strong></p>
                    <ul>
                        <li>此验证链接将在24小时后失效</li>
                        <li>如果您没有注册此账户，请忽略此邮件</li>
                        <li>验证完成后，您就可以正常使用我们的服务了</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复</p>
                    <p>&copy; 2025 {self.config.from_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_verification_email_text(self, username: str, verification_url: str) -> str:
        """获取验证邮件纯文本内容"""
        return f"""
        欢迎加入 {self.config.from_name}！
        
        亲爱的 {username}，
        
        感谢您注册我们的服务！为了确保您的账户安全，请点击以下链接验证您的邮箱地址：
        
        {verification_url}
        
        注意事项：
        - 此验证链接将在24小时后失效
        - 如果您没有注册此账户，请忽略此邮件
        - 验证完成后，您就可以正常使用我们的服务了
        
        此邮件由系统自动发送，请勿回复。
        
        © 2025 {self.config.from_name}. All rights reserved.
        """
    
    def _get_password_reset_email_html(self, username: str, reset_url: str) -> str:
        """获取密码重置邮件HTML内容"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>密码重置</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 密码重置请求</h1>
                </div>
                <div class="content">
                    <h2>亲爱的 {username}，</h2>
                    <p>我们收到了您的密码重置请求。如果您确实需要重置密码，请点击下面的按钮：</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">重置密码</a>
                    </div>
                    
                    <p>如果按钮无法点击，您也可以复制以下链接到浏览器中打开：</p>
                    <p style="word-break: break-all; background: #eee; padding: 10px; border-radius: 5px;">
                        {reset_url}
                    </p>
                    
                    <div class="warning">
                        <strong>⚠️ 安全提醒：</strong>
                        <ul>
                            <li>此重置链接将在1小时后失效</li>
                            <li>如果您没有请求重置密码，请忽略此邮件</li>
                            <li>为了您的账户安全，请不要将此链接分享给他人</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复</p>
                    <p>&copy; 2025 {self.config.from_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_password_reset_email_text(self, username: str, reset_url: str) -> str:
        """获取密码重置邮件纯文本内容"""
        return f"""
        密码重置请求 - {self.config.from_name}
        
        亲爱的 {username}，
        
        我们收到了您的密码重置请求。如果您确实需要重置密码，请点击以下链接：
        
        {reset_url}
        
        安全提醒：
        - 此重置链接将在1小时后失效
        - 如果您没有请求重置密码，请忽略此邮件
        - 为了您的账户安全，请不要将此链接分享给他人
        
        此邮件由系统自动发送，请勿回复。
        
        © 2025 {self.config.from_name}. All rights reserved.
        """
    
    def _get_welcome_email_html(self, username: str) -> str:
        """获取欢迎邮件HTML内容"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>欢迎使用</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .feature {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #28a745; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 欢迎使用 {self.config.from_name}！</h1>
                </div>
                <div class="content">
                    <h2>亲爱的 {username}，</h2>
                    <p>恭喜！您的邮箱验证成功，现在可以正常使用我们的服务了。</p>
                    
                    <h3>🚀 主要功能</h3>
                    <div class="feature">
                        <h4>📊 数据源对接</h4>
                        <p>支持多种数据格式，包括CSV、Excel等，轻松导入您的数据。</p>
                    </div>
                    
                    <div class="feature">
                        <h4>🤖 智能模型配置</h4>
                        <p>提供CTGAN、GPT等多种合成数据生成模型，满足不同场景需求。</p>
                    </div>
                    
                    <div class="feature">
                        <h4>📈 质量评估</h4>
                        <p>全面的数据质量评估工具，确保生成数据的质量和可靠性。</p>
                    </div>
                    
                    <div class="feature">
                        <h4>⚡ 批量处理</h4>
                        <p>支持批量数据处理，提高工作效率。</p>
                    </div>
                    
                    <p>如果您有任何问题或建议，请随时联系我们的技术支持团队。</p>
                    
                    <p>祝您使用愉快！</p>
                </div>
                <div class="footer">
                    <p>此邮件由系统自动发送，请勿回复</p>
                    <p>&copy; 2025 {self.config.from_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_welcome_email_text(self, username: str) -> str:
        """获取欢迎邮件纯文本内容"""
        return f"""
        欢迎使用 {self.config.from_name}！
        
        亲爱的 {username}，
        
        恭喜！您的邮箱验证成功，现在可以正常使用我们的服务了。
        
        主要功能：
        
        📊 数据源对接
        - 支持多种数据格式，包括CSV、Excel等，轻松导入您的数据
        
        🤖 智能模型配置
        - 提供CTGAN、GPT等多种合成数据生成模型，满足不同场景需求
        
        📈 质量评估
        - 全面的数据质量评估工具，确保生成数据的质量和可靠性
        
        ⚡ 批量处理
        - 支持批量数据处理，提高工作效率
        
        如果您有任何问题或建议，请随时联系我们的技术支持团队。
        
        祝您使用愉快！
        
        此邮件由系统自动发送，请勿回复。
        
        © 2025 {self.config.from_name}. All rights reserved.
        """

# 全局邮箱服务实例
email_service = EmailService()

