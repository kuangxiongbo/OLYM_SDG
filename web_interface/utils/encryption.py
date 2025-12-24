#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密工具
"""

from cryptography.fernet import Fernet
from flask import current_app
import base64
import os

class EncryptionService:
    """加密服务"""
    
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self):
        """获取或创建加密密钥"""
        key_file = os.path.join(os.path.dirname(__file__), '..', 'instance', '.encryption_key')
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt(self, plaintext):
        """加密文本"""
        if not plaintext:
            return None
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext):
        """解密文本"""
        if not ciphertext:
            return None
        try:
            return self.cipher.decrypt(ciphertext.encode()).decode()
        except:
            return None

encryption_service = EncryptionService()



