#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据脱敏服务
"""

import os
import pandas as pd
import numpy as np
import re
import hashlib
from datetime import datetime
from threading import Thread
from models.task import Task, db
from config import Config
from services.synthetic_service import SyntheticService

class MaskingService:
    """数据脱敏服务"""
    
    def __init__(self):
        self.upload_folder = Config.UPLOAD_FOLDER
        self.results_folder = Config.RESULTS_FOLDER
        os.makedirs(self.results_folder, exist_ok=True)
        self.synthetic_service = SyntheticService()
    
    def detect_fields(self, file_id):
        """自动识别字段类型"""
        df = self._load_file(file_id)
        if df is None or df.empty:
            return []
        
        fields = []
        for col in df.columns:
            detected_type, confidence = self._detect_field_type(df[col])
            suggested_strategy = 'simulation' if detected_type in ['name', 'phone', 'email', 'id_card'] else 'masking'
            
            # 获取样例值
            sample_value = None
            non_null = df[col].dropna()
            if len(non_null) > 0:
                sample_value = str(non_null.iloc[0])
            
            # 生成仿真值示例
            simulation_value = self._generate_simulation_example(detected_type, sample_value)
            
            # 映射中文类型名称
            type_mapping = {
                'name': '姓名',
                'id_card': '身份证号',
                'phone': '手机号',
                'email': '邮箱',
                'bank_card': '银行卡号',
                'numeric': '数值',
                'text': '文本',
                'unknown': '未知'
            }
            detected_type_cn = type_mapping.get(detected_type, detected_type)
            
            fields.append({
                'name': col,
                'detected_type': detected_type_cn,
                'confidence': confidence,
                'suggested_strategy': suggested_strategy,
                'sample_value': sample_value,
                'simulation_value': simulation_value,
                'recommendation': self._get_recommendation(detected_type, suggested_strategy)
            })
        
        return fields
    
    def _generate_simulation_example(self, field_type, original_value):
        """生成仿真值示例"""
        if field_type == 'name':
            return '李雪'
        elif field_type == 'id_card':
            return '510324199305125621'
        elif field_type == 'phone':
            return '139****5678'
        elif field_type == 'email':
            return 'example@example.com'
        elif field_type == 'bank_card':
            return '6222**********1234'
        else:
            return '生成值'
    
    def _detect_field_type(self, series):
        """检测单个字段的类型"""
        # 移除空值
        non_null = series.dropna()
        if len(non_null) == 0:
            return 'unknown', 0.0
        
        # 转换为字符串进行分析
        sample = non_null.astype(str).head(100)
        
        # 身份证号检测
        id_card_pattern = r'^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$'
        id_card_matches = sum(1 for v in sample if re.match(id_card_pattern, str(v)))
        if id_card_matches / len(sample) > 0.8:
            return 'id_card', id_card_matches / len(sample)
        
        # 手机号检测
        phone_pattern = r'^1[3-9]\d{9}$'
        phone_matches = sum(1 for v in sample if re.match(phone_pattern, str(v)))
        if phone_matches / len(sample) > 0.8:
            return 'phone', phone_matches / len(sample)
        
        # 邮箱检测
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        email_matches = sum(1 for v in sample if re.match(email_pattern, str(v)))
        if email_matches / len(sample) > 0.8:
            return 'email', email_matches / len(sample)
        
        # 姓名检测（2-4个中文字符）
        name_pattern = r'^[\u4e00-\u9fa5]{2,4}$'
        name_matches = sum(1 for v in sample if re.match(name_pattern, str(v)))
        if name_matches / len(sample) > 0.5:
            return 'name', name_matches / len(sample)
        
        # 银行卡号检测
        bank_card_pattern = r'^\d{16,19}$'
        bank_card_matches = sum(1 for v in sample if re.match(bank_card_pattern, str(v)))
        if bank_card_matches / len(sample) > 0.8:
            return 'bank_card', bank_card_matches / len(sample)
        
        # 数值类型
        if pd.api.types.is_numeric_dtype(series):
            return 'numeric', 0.9
        
        # 默认文本类型
        return 'text', 0.5
    
    def _get_recommendation(self, field_type, strategy):
        """获取推荐说明"""
        if strategy == 'simulation':
            return f"建议使用AI仿真方案，保持数据可用性"
        else:
            if field_type == 'id_card':
                return "建议使用遮蔽方案，仅保留前3位和后4位"
            elif field_type == 'phone':
                return "建议使用遮蔽方案，仅保留前3位和后4位"
            else:
                return "建议使用遮蔽方案"
    
    def execute_masking(self, user_id, file_id, config_id, rules):
        """执行脱敏任务"""
        task = Task(
            user_id=user_id,
            task_type='masking',
            task_name='数据脱敏',
            status='pending'
        )
        task.set_config({
            'file_id': file_id,
            'config_id': config_id,
            'rules': rules
        })
        db.session.add(task)
        db.session.commit()
        
        # 异步执行脱敏任务
        from flask import current_app
        app = current_app._get_current_object()
        thread = Thread(target=self._execute_masking_task_with_app, args=(app, task.id,))
        thread.daemon = True
        thread.start()
        
        return task
    
    def _execute_masking_task_with_app(self, app, task_id):
        """执行脱敏任务（异步，带app上下文）"""
        with app.app_context():
            task = Task.query.get(task_id)
            if not task:
                return
            task.status = 'running'
            task.progress = 0
            db.session.commit()
        
        try:
            config = task.get_config()
            file_id = config.get('file_id')
            rules = config.get('rules', [])
            
            # 加载原始数据
            self._update_progress(task_id, 10)
            original_df = self._load_file(file_id)
            if original_df is None or original_df.empty:
                raise ValueError("无法加载数据")
            
            # 执行脱敏
            self._update_progress(task_id, 30)
            masked_df = original_df.copy()
            
            for rule in rules:
                field = rule.get('field')
                strategy = rule.get('strategy')
                rule_config = rule.get('config', {})
                
                if field not in masked_df.columns:
                    continue
                
                if strategy == 'simulation':
                    # AI仿真脱敏
                    masked_df[field] = self._simulate_field(masked_df[field], rule_config)
                elif strategy == 'masking':
                    # 遮蔽脱敏
                    masked_df[field] = self._mask_field(masked_df[field], rule_config)
                elif strategy == 'hashing':
                    # 哈希脱敏
                    masked_df[field] = self._hash_field(masked_df[field])
            
            # 保存结果
            self._update_progress(task_id, 80)
            result_path = self._save_result(task_id, original_df, masked_df)
            
            # 更新任务状态
            from flask import current_app
            with current_app.app_context():
                task = Task.query.get(task_id)
                task.status = 'completed'
                task.progress = 100
                task.result_path = result_path
                task.completed_at = datetime.utcnow()
                db.session.commit()
            
        except Exception as e:
            error_msg = str(e)
            print(f"脱敏任务 {task_id} 执行失败: {error_msg}")
            from flask import current_app
            with current_app.app_context():
                task = Task.query.get(task_id)
                task.status = 'failed'
                task.error_message = error_msg
                db.session.commit()
    
    def _load_file(self, file_id):
        """加载文件"""
        if not file_id:
            return None
        
        for ext in ['csv', 'xlsx', 'xls', 'json']:
            filepath = os.path.join(self.upload_folder, f"{file_id}.{ext}")
            if os.path.exists(filepath):
                try:
                    if ext == 'csv':
                        # 尝试多种编码
                        for encoding in ['utf-8', 'gbk', 'gb18030', 'latin-1']:
                            try:
                                return pd.read_csv(filepath, encoding=encoding)
                            except UnicodeDecodeError:
                                continue
                        # 如果所有编码都失败，使用默认编码
                        return pd.read_csv(filepath, encoding='utf-8', errors='ignore')
                    elif ext == 'xlsx':
                        return pd.read_excel(filepath, engine='openpyxl')
                    elif ext == 'xls':
                        return pd.read_excel(filepath, engine='xlrd')
                    elif ext == 'json':
                        return pd.read_json(filepath)
                except Exception as e:
                    print(f"加载文件 {filepath} 失败: {e}")
                    continue
        return None
    
    def _simulate_field(self, series, config):
        """使用AI仿真替换字段值"""
        # TODO: 使用SDGX生成合成数据替换
        # 这里先使用简单的随机替换
        return series.apply(lambda x: f"SIM_{hash(str(x)) % 10000:04d}" if pd.notna(x) else x)
    
    def _mask_field(self, series, config):
        """遮蔽字段值"""
        keep_prefix = config.get('keep_prefix', 0)
        keep_suffix = config.get('keep_suffix', 0)
        mask_char = config.get('mask_char', '*')
        
        def mask_value(value):
            if pd.isna(value):
                return value
            value_str = str(value)
            if len(value_str) <= keep_prefix + keep_suffix:
                return mask_char * len(value_str)
            prefix = value_str[:keep_prefix] if keep_prefix > 0 else ''
            suffix = value_str[-keep_suffix:] if keep_suffix > 0 else ''
            middle = mask_char * (len(value_str) - keep_prefix - keep_suffix)
            return prefix + middle + suffix
        
        return series.apply(mask_value)
    
    def _hash_field(self, series):
        """哈希字段值"""
        def hash_value(value):
            if pd.isna(value):
                return value
            return hashlib.md5(str(value).encode()).hexdigest()[:16]
        
        return series.apply(hash_value)
    
    def _save_result(self, task_id, original_df, masked_df):
        """保存结果"""
        result_dir = os.path.join(self.results_folder, f"task_{task_id}")
        os.makedirs(result_dir, exist_ok=True)
        
        # 保存原始数据
        original_path = os.path.join(result_dir, 'original.csv')
        original_df.to_csv(original_path, index=False)
        
        # 保存脱敏数据
        masked_path = os.path.join(result_dir, 'masked.csv')
        masked_df.to_csv(masked_path, index=False)
        
        return result_dir
    
    def _update_progress(self, task_id, progress):
        """更新任务进度"""
        try:
            from flask import current_app
            with current_app.app_context():
                task = Task.query.get(task_id)
                if task:
                    task.progress = progress
                    task.updated_at = datetime.utcnow()
                    db.session.commit()
        except Exception as e:
            print(f"更新进度失败: {e}")
    
    def get_result_preview(self, task_id, page=1, page_size=20):
        """获取结果预览"""
        task = Task.query.get(task_id)
        if not task or not task.result_path:
            return None
        
        original_path = os.path.join(task.result_path, 'original.csv')
        masked_path = os.path.join(task.result_path, 'masked.csv')
        
        if not os.path.exists(original_path) or not os.path.exists(masked_path):
            return None
        
        original_df = pd.read_csv(original_path)
        masked_df = pd.read_csv(masked_path)
        
        total = len(original_df)
        start = (page - 1) * page_size
        end = start + page_size
        
        return {
            'columns': original_df.columns.tolist(),
            'original_data': original_df.iloc[start:end].to_dict('records'),
            'masked_data': masked_df.iloc[start:end].to_dict('records'),
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size
            }
        }
