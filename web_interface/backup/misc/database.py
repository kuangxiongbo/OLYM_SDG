#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证数据库管理
==================

管理用户数据的存储和检索
"""

import os
import json
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from models import User, UserSession, EmailVerification, PasswordReset

class FileDatabase:
    """基于文件的简单数据库"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 数据文件路径
        self.users_file = self.data_dir / "users.json"
        self.sessions_file = self.data_dir / "sessions.json"
        self.verifications_file = self.data_dir / "email_verifications.json"
        self.password_resets_file = self.data_dir / "password_resets.json"
        
        # 线程锁
        self.lock = threading.Lock()
        
        # 初始化数据文件
        self._init_data_files()
    
    def _init_data_files(self):
        """初始化数据文件"""
        files = [
            self.users_file,
            self.sessions_file,
            self.verifications_file,
            self.password_resets_file
        ]
        
        for file_path in files:
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
    
    def _read_json(self, file_path: Path) -> Dict[str, Any]:
        """读取JSON文件"""
        with self.lock:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}
    
    def _write_json(self, file_path: Path, data: Dict[str, Any]):
        """写入JSON文件"""
        with self.lock:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

class UserDatabase(FileDatabase):
    """用户数据库管理"""
    
    def create_user(self, user: User) -> bool:
        """创建用户"""
        users = self._read_json(self.users_file)
        
        # 检查邮箱是否已存在
        if user.email in users:
            return False
        
        # 检查用户名是否已存在
        for existing_user in users.values():
            if existing_user['username'] == user.username:
                return False
        
        users[user.email] = user.to_dict()
        users[user.email]['password_hash'] = user.password_hash
        
        self._write_json(self.users_file, users)
        return True
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        users = self._read_json(self.users_file)
        user_data = users.get(email.lower().strip())
        
        if user_data:
            return User.from_dict(user_data)
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        users = self._read_json(self.users_file)
        
        for user_data in users.values():
            if user_data['username'] == username:
                return User.from_dict(user_data)
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """通过用户ID获取用户"""
        users = self._read_json(self.users_file)
        
        for user_data in users.values():
            if user_data['user_id'] == user_id:
                return User.from_dict(user_data)
        return None
    
    def update_user(self, user: User) -> bool:
        """更新用户信息"""
        users = self._read_json(self.users_file)
        
        if user.email not in users:
            return False
        
        user_dict = user.to_dict()
        user_dict['password_hash'] = user.password_hash
        users[user.email] = user_dict
        
        self._write_json(self.users_file, users)
        return True
    
    def delete_user(self, email: str) -> bool:
        """删除用户"""
        users = self._read_json(self.users_file)
        
        if email.lower().strip() not in users:
            return False
        
        del users[email.lower().strip()]
        self._write_json(self.users_file, users)
        return True
    
    def list_users(self, role: Optional[str] = None) -> List[User]:
        """列出用户"""
        users = self._read_json(self.users_file)
        user_list = []
        
        for user_data in users.values():
            if role is None or user_data.get('role') == role:
                user_list.append(User.from_dict(user_data))
        
        return user_list

class SessionDatabase(FileDatabase):
    """会话数据库管理"""
    
    def create_session(self, session: UserSession) -> bool:
        """创建会话"""
        sessions = self._read_json(self.sessions_file)
        
        sessions[session.session_token] = session.to_dict()
        self._write_json(self.sessions_file, sessions)
        return True
    
    def get_session(self, session_token: str) -> Optional[UserSession]:
        """获取会话"""
        sessions = self._read_json(self.sessions_file)
        session_data = sessions.get(session_token)
        
        if session_data:
            session = UserSession.from_dict(session_data)
            if session.is_expired():
                self.delete_session(session_token)
                return None
            return session
        return None
    
    def update_session(self, session: UserSession) -> bool:
        """更新会话"""
        sessions = self._read_json(self.sessions_file)
        
        if session.session_token not in sessions:
            return False
        
        sessions[session.session_token] = session.to_dict()
        self._write_json(self.sessions_file, sessions)
        return True
    
    def delete_session(self, session_token: str) -> bool:
        """删除会话"""
        sessions = self._read_json(self.sessions_file)
        
        if session_token not in sessions:
            return False
        
        del sessions[session_token]
        self._write_json(self.sessions_file, sessions)
        return True
    
    def delete_user_sessions(self, user_id: str) -> int:
        """删除用户的所有会话"""
        sessions = self._read_json(self.sessions_file)
        deleted_count = 0
        
        tokens_to_delete = []
        for token, session_data in sessions.items():
            if session_data['user_id'] == user_id:
                tokens_to_delete.append(token)
        
        for token in tokens_to_delete:
            del sessions[token]
            deleted_count += 1
        
        self._write_json(self.sessions_file, sessions)
        return deleted_count
    
    def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        sessions = self._read_json(self.sessions_file)
        expired_tokens = []
        
        for token, session_data in sessions.items():
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del sessions[token]
        
        if expired_tokens:
            self._write_json(self.sessions_file, sessions)
        
        return len(expired_tokens)

class VerificationDatabase(FileDatabase):
    """邮箱验证数据库管理"""
    
    def create_verification(self, verification: EmailVerification) -> bool:
        """创建邮箱验证"""
        verifications = self._read_json(self.verifications_file)
        
        verifications[verification.token] = verification.to_dict()
        self._write_json(self.verifications_file, verifications)
        return True
    
    def get_verification(self, token: str) -> Optional[EmailVerification]:
        """获取邮箱验证"""
        verifications = self._read_json(self.verifications_file)
        verification_data = verifications.get(token)
        
        if verification_data:
            verification = EmailVerification.from_dict(verification_data)
            if verification.is_expired() or verification.is_used:
                self.delete_verification(token)
                return None
            return verification
        return None
    
    def mark_verification_used(self, token: str) -> bool:
        """标记验证为已使用"""
        verifications = self._read_json(self.verifications_file)
        
        if token not in verifications:
            return False
        
        verifications[token]['is_used'] = True
        self._write_json(self.verifications_file, verifications)
        return True
    
    def delete_verification(self, token: str) -> bool:
        """删除验证"""
        verifications = self._read_json(self.verifications_file)
        
        if token not in verifications:
            return False
        
        del verifications[token]
        self._write_json(self.verifications_file, verifications)
        return True
    
    def cleanup_expired_verifications(self) -> int:
        """清理过期验证"""
        verifications = self._read_json(self.verifications_file)
        expired_tokens = []
        
        for token, verification_data in verifications.items():
            expires_at = datetime.fromisoformat(verification_data['expires_at'])
            if datetime.now() > expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del verifications[token]
        
        if expired_tokens:
            self._write_json(self.verifications_file, verifications)
        
        return len(expired_tokens)

class PasswordResetDatabase(FileDatabase):
    """密码重置数据库管理"""
    
    def create_reset(self, reset: PasswordReset) -> bool:
        """创建密码重置"""
        resets = self._read_json(self.password_resets_file)
        
        resets[reset.token] = reset.to_dict()
        self._write_json(self.password_resets_file, resets)
        return True
    
    def get_reset(self, token: str) -> Optional[PasswordReset]:
        """获取密码重置"""
        resets = self._read_json(self.password_resets_file)
        reset_data = resets.get(token)
        
        if reset_data:
            reset = PasswordReset.from_dict(reset_data)
            if reset.is_expired() or reset.is_used:
                self.delete_reset(token)
                return None
            return reset
        return None
    
    def mark_reset_used(self, token: str) -> bool:
        """标记重置为已使用"""
        resets = self._read_json(self.password_resets_file)
        
        if token not in resets:
            return False
        
        resets[token]['is_used'] = True
        self._write_json(self.password_resets_file, resets)
        return True
    
    def delete_reset(self, token: str) -> bool:
        """删除重置"""
        resets = self._read_json(self.password_resets_file)
        
        if token not in resets:
            return False
        
        del resets[token]
        self._write_json(self.password_resets_file, resets)
        return True
    
    def cleanup_expired_resets(self) -> int:
        """清理过期重置"""
        resets = self._read_json(self.password_resets_file)
        expired_tokens = []
        
        for token, reset_data in resets.items():
            expires_at = datetime.fromisoformat(reset_data['expires_at'])
            if datetime.now() > expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del resets[token]
        
        if expired_tokens:
            self._write_json(self.password_resets_file, resets)
        
        return len(expired_tokens)

class AuthDatabase:
    """认证数据库管理器"""
    
    def __init__(self, data_dir: str = "data"):
        self.users = UserDatabase(data_dir)
        self.sessions = SessionDatabase(data_dir)
        self.verifications = VerificationDatabase(data_dir)
        self.password_resets = PasswordResetDatabase(data_dir)
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """清理过期数据"""
        return {
            'expired_sessions': self.sessions.cleanup_expired_sessions(),
            'expired_verifications': self.verifications.cleanup_expired_verifications(),
            'expired_resets': self.password_resets.cleanup_expired_resets()
        }

# 全局数据库实例
auth_db = AuthDatabase()

