#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量评估服务单元测试
"""

import unittest
import os
import sys
import pandas as pd
import numpy as np
import tempfile
import shutil
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.quality_service import QualityService
from config import Config


class TestQualityService(unittest.TestCase):
    """数据质量评估服务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.service = QualityService()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_service_init(self):
        """测试服务初始化"""
        service = QualityService()
        self.assertIsNotNone(service.upload_folder)
        self.assertIsNotNone(service.results_folder)
        self.assertTrue(os.path.exists(service.results_folder))
    
    def test_calculate_correlation(self):
        """测试相关性计算"""
        # 创建测试数据
        original_df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': [10, 20, 30, 40, 50],
            'col3': ['a', 'b', 'c', 'd', 'e']
        })
        
        synthetic_df = pd.DataFrame({
            'col1': [1.1, 2.1, 3.1, 4.1, 5.1],
            'col2': [11, 21, 31, 41, 51],
            'col3': ['a', 'b', 'c', 'd', 'e']
        })
        
        score, details = self.service._calculate_correlation(original_df, synthetic_df)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertIn('correlations', details)
    
    def test_calculate_correlation_no_synthetic(self):
        """测试无合成数据时的相关性计算"""
        original_df = pd.DataFrame({'col1': [1, 2, 3]})
        score, details = self.service._calculate_correlation(original_df, None)
        self.assertEqual(score, 0.0)
    
    def test_calculate_distribution_similarity(self):
        """测试分布相似度计算"""
        original_df = pd.DataFrame({
            'col1': np.random.normal(100, 15, 100),
            'col2': np.random.uniform(0, 100, 100)
        })
        
        synthetic_df = pd.DataFrame({
            'col1': np.random.normal(100, 15, 100),
            'col2': np.random.uniform(0, 100, 100)
        })
        
        score, details = self.service._calculate_distribution_similarity(original_df, synthetic_df)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertIn('ks_tests', details)
    
    def test_calculate_missing_rate(self):
        """测试缺失率计算"""
        original_df = pd.DataFrame({
            'col1': [1, 2, np.nan, 4, 5],
            'col2': ['a', 'b', 'c', np.nan, 'e']
        })
        
        synthetic_df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': ['a', 'b', 'c', 'd', 'e']
        })
        
        score, details = self.service._calculate_missing_rate(original_df, synthetic_df)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertIn('original_missing_rate', details)
        self.assertIn('synthetic_missing_rate', details)
    
    def test_calculate_statistical_consistency(self):
        """测试统计一致性计算"""
        original_df = pd.DataFrame({
            'col1': np.random.normal(100, 15, 100),
            'col2': np.random.uniform(0, 100, 100)
        })
        
        synthetic_df = pd.DataFrame({
            'col1': np.random.normal(100, 15, 100),
            'col2': np.random.uniform(0, 100, 100)
        })
        
        score, details = self.service._calculate_statistical_consistency(original_df, synthetic_df)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertIn('consistencies', details)
    
    def test_save_report(self):
        """测试报告保存"""
        report = {
            'summary': {
                'overall_score': 0.85,
                'total_indicators': 4,
                'passed_indicators': 3,
                'failed_indicators': 1
            },
            'indicators': {
                'correlation': {'score': 0.9, 'status': 'passed'},
                'distribution_similarity': {'score': 0.8, 'status': 'passed'}
            }
        }
        
        result_path = self.service._save_report(999, report)
        
        self.assertIsNotNone(result_path)
        self.assertTrue(os.path.exists(result_path))
        self.assertTrue(os.path.exists(os.path.join(result_path, 'report.json')))
        
        # 验证报告内容
        import json
        with open(os.path.join(result_path, 'report.json'), 'r', encoding='utf-8') as f:
            loaded_report = json.load(f)
            self.assertEqual(loaded_report['summary']['overall_score'], 0.85)
        
        # 清理
        if os.path.exists(result_path):
            shutil.rmtree(result_path)
    
    def test_get_report(self):
        """测试获取报告"""
        # 创建测试报告
        report_dir = os.path.join(self.service.results_folder, 'task_999')
        os.makedirs(report_dir, exist_ok=True)
        
        report = {
            'summary': {'overall_score': 0.85},
            'indicators': {}
        }
        
        import json
        with open(os.path.join(report_dir, 'report.json'), 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        with patch('services.quality_service.Task') as mock_task:
            mock_task.query.get.return_value = Mock(
                result_path=report_dir
            )
            
            loaded_report = self.service.get_report(999)
            
            if loaded_report:
                self.assertIn('summary', loaded_report)
                self.assertEqual(loaded_report['summary']['overall_score'], 0.85)
        
        # 清理
        if os.path.exists(report_dir):
            shutil.rmtree(report_dir)


if __name__ == '__main__':
    unittest.main()

