#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量评估服务
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from threading import Thread
from scipy import stats
from models.task import Task, db
from config import Config

class QualityService:
    """数据质量评估服务"""
    
    def __init__(self):
        self.upload_folder = Config.UPLOAD_FOLDER
        self.results_folder = Config.RESULTS_FOLDER
        os.makedirs(self.results_folder, exist_ok=True)
    
    def create_assessment_task(self, user_id, config):
        """创建评估任务"""
        task = Task(
            user_id=user_id,
            task_type='quality',
            task_name=config.get('task_name', '数据质量评估'),
            status='pending'
        )
        task.set_config(config)
        db.session.add(task)
        db.session.commit()
        
        # 异步执行评估任务
        from flask import current_app
        app = current_app._get_current_object()
        thread = Thread(target=self._execute_assessment_task_with_app, args=(app, task.id,))
        thread.daemon = True
        thread.start()
        
        return task
    
    def _execute_assessment_task_with_app(self, app, task_id):
        """执行评估任务（异步，带app上下文）"""
        with app.app_context():
            task = Task.query.get(task_id)
            if not task:
                return
            task.status = 'running'
            task.progress = 0
            db.session.commit()
        
        try:
            config = task.get_config()
            original_file_id = config.get('original_file_id')
            synthetic_file_id = config.get('synthetic_file_id')
            indicators = config.get('indicators', [])
            
            # 加载数据
            self._update_progress(task_id, 10)
            original_df = self._load_file(original_file_id)
            synthetic_df = self._load_file(synthetic_file_id) if synthetic_file_id else None
            
            if original_df is None or original_df.empty:
                raise ValueError("无法加载原始数据")
            
            # 计算评估指标
            self._update_progress(task_id, 30)
            results = {}
            passed_count = 0
            failed_count = 0
            
            for indicator_config in indicators:
                if not indicator_config.get('enabled', True):
                    continue
                
                indicator_name = indicator_config['name']
                threshold = indicator_config.get('threshold', 0.7)
                
                if indicator_name == 'correlation':
                    score, details = self._calculate_correlation(original_df, synthetic_df)
                elif indicator_name == 'distribution_similarity':
                    score, details = self._calculate_distribution_similarity(original_df, synthetic_df)
                elif indicator_name == 'missing_rate':
                    score, details = self._calculate_missing_rate(original_df, synthetic_df)
                elif indicator_name == 'statistical_consistency':
                    score, details = self._calculate_statistical_consistency(original_df, synthetic_df)
                else:
                    continue
                
                status = 'passed' if score >= threshold else 'failed'
                if status == 'passed':
                    passed_count += 1
                else:
                    failed_count += 1
                
                results[indicator_name] = {
                    'score': score,
                    'status': status,
                    'threshold': threshold,
                    'details': details
                }
            
            # 计算总体得分
            overall_score = sum(r['score'] for r in results.values()) / len(results) if results else 0
            
            # 生成报告
            self._update_progress(task_id, 80)
            report = {
                'summary': {
                    'overall_score': overall_score,
                    'total_indicators': len(results),
                    'passed_indicators': passed_count,
                    'failed_indicators': failed_count
                },
                'indicators': results
            }
            
            # 保存报告
            report_path = self._save_report(task_id, report)
            
            # 更新任务状态
            from flask import current_app
            with current_app.app_context():
                task = Task.query.get(task_id)
                task.status = 'completed'
                task.progress = 100
                task.result_path = report_path
                task.completed_at = datetime.utcnow()
                db.session.commit()
            
        except Exception as e:
            error_msg = str(e)
            print(f"评估任务 {task_id} 执行失败: {error_msg}")
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
    
    def _calculate_correlation(self, original_df, synthetic_df):
        """计算相关性"""
        if synthetic_df is None:
            return 0.0, {}
        
        # 只计算数值列的相关性
        numeric_cols = original_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return 1.0, {}
        
        correlations = []
        for col in numeric_cols:
            if col in synthetic_df.columns:
                orig_col = original_df[col].dropna()
                synth_col = synthetic_df[col].dropna()
                if len(orig_col) > 0 and len(synth_col) > 0:
                    corr = orig_col.corr(synth_col) if len(orig_col) == len(synth_col) else 0.5
                    correlations.append(abs(corr) if not np.isnan(corr) else 0)
        
        avg_correlation = np.mean(correlations) if correlations else 0.5
        return avg_correlation, {'correlations': correlations}
    
    def _calculate_distribution_similarity(self, original_df, synthetic_df):
        """计算分布相似度"""
        if synthetic_df is None:
            return 0.0, {}
        
        numeric_cols = original_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return 1.0, {}
        
        similarities = []
        ks_tests = []
        
        for col in numeric_cols:
            if col in synthetic_df.columns:
                orig_col = original_df[col].dropna()
                synth_col = synthetic_df[col].dropna()
                if len(orig_col) > 0 and len(synth_col) > 0:
                    # KS测试
                    try:
                        ks_stat, p_value = stats.ks_2samp(orig_col, synth_col)
                        similarities.append(1 - ks_stat)  # KS统计量越小，相似度越高
                        ks_tests.append({'statistic': float(ks_stat), 'p_value': float(p_value)})
                    except:
                        similarities.append(0.5)
        
        avg_similarity = np.mean(similarities) if similarities else 0.5
        return avg_similarity, {'ks_tests': ks_tests}
    
    def _calculate_missing_rate(self, original_df, synthetic_df):
        """计算缺失率"""
        if synthetic_df is None:
            orig_missing = original_df.isnull().sum().sum() / (len(original_df) * len(original_df.columns))
            return 1.0 - orig_missing, {'original_missing_rate': float(orig_missing)}
        
        orig_missing = original_df.isnull().sum().sum() / (len(original_df) * len(original_df.columns))
        synth_missing = synthetic_df.isnull().sum().sum() / (len(synthetic_df) * len(synthetic_df.columns))
        
        # 缺失率差异越小，得分越高
        missing_diff = abs(orig_missing - synth_missing)
        score = 1.0 - min(missing_diff, 1.0)
        
        return score, {
            'original_missing_rate': float(orig_missing),
            'synthetic_missing_rate': float(synth_missing),
            'difference': float(missing_diff)
        }
    
    def _calculate_statistical_consistency(self, original_df, synthetic_df):
        """计算统计一致性"""
        if synthetic_df is None:
            return 0.0, {}
        
        numeric_cols = original_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return 1.0, {}
        
        consistencies = []
        for col in numeric_cols:
            if col in synthetic_df.columns:
                orig_col = original_df[col].dropna()
                synth_col = synthetic_df[col].dropna()
                if len(orig_col) > 0 and len(synth_col) > 0:
                    # 比较均值和标准差
                    orig_mean = orig_col.mean()
                    synth_mean = synth_col.mean()
                    orig_std = orig_col.std()
                    synth_std = synth_col.std()
                    
                    mean_diff = abs(orig_mean - synth_mean) / (abs(orig_mean) + 1e-10)
                    std_diff = abs(orig_std - synth_std) / (abs(orig_std) + 1e-10)
                    
                    consistency = 1.0 - min((mean_diff + std_diff) / 2, 1.0)
                    consistencies.append(consistency)
        
        avg_consistency = np.mean(consistencies) if consistencies else 0.5
        return avg_consistency, {'consistencies': consistencies}
    
    def _save_report(self, task_id, report):
        """保存评估报告"""
        import json
        report_dir = os.path.join(self.results_folder, f"task_{task_id}")
        os.makedirs(report_dir, exist_ok=True)
        
        report_path = os.path.join(report_dir, 'report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report_dir
    
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
    
    def get_report(self, task_id):
        """获取评估报告"""
        import json
        task = Task.query.get(task_id)
        if not task or not task.result_path:
            return None
        
        report_path = os.path.join(task.result_path, 'report.json')
        if not os.path.exists(report_path):
            return None
        
        with open(report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
