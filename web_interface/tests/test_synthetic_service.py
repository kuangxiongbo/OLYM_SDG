#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合成数据生成服务单元测试
"""

import unittest
import os
import sys
import pandas as pd
import numpy as np
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.synthetic_service import SyntheticService, similarity_to_parameters, create_sdgx_model
from services.synthetic_service import clean_dataframe_for_json
from config import Config


class TestSyntheticService(unittest.TestCase):
    """合成数据生成服务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.service = SyntheticService()
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_id = 'test_file_123'
        
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_similarity_to_parameters(self):
        """测试相似度参数转换"""
        # 测试高相似度
        params = similarity_to_parameters(0.9)
        self.assertIn('epochs', params)
        self.assertIn('batch_size', params)
        self.assertGreater(params['epochs'], 100)
        
        # 测试中等相似度
        params = similarity_to_parameters(0.6)
        self.assertIn('epochs', params)
        self.assertLess(params['epochs'], 200)
        
        # 测试低相似度
        params = similarity_to_parameters(0.3)
        self.assertIn('epochs', params)
        self.assertLess(params['epochs'], 100)
    
    def test_clean_dataframe_for_json(self):
        """测试DataFrame清理"""
        # 创建包含NaN的DataFrame
        df = pd.DataFrame({
            'col1': [1, 2, np.nan, 4],
            'col2': ['a', 'nan', 'NULL', 'b'],
            'col3': [1.1, 2.2, 3.3, 4.4]
        })
        
        cleaned = clean_dataframe_for_json(df)
        
        # 检查NaN是否被转换为None
        self.assertIsNone(cleaned.iloc[2]['col1'])
        self.assertIsNone(cleaned.iloc[1]['col2'])
        
        # 检查数据可以JSON序列化
        import json
        json_str = json.dumps(cleaned.to_dict('records'))
        self.assertIsInstance(json_str, str)
    
    @patch('services.synthetic_service.SDGX_AVAILABLE', False)
    def test_create_sdgx_model_no_sdgx(self):
        """测试SDGX不可用时创建模型"""
        model = create_sdgx_model('ctgan', 0.8)
        self.assertIsNone(model)
    
    def test_service_init(self):
        """测试服务初始化"""
        service = SyntheticService()
        self.assertIsNotNone(service.upload_folder)
        self.assertIsNotNone(service.results_folder)
        self.assertTrue(os.path.exists(service.results_folder))
    
    def test_load_template_data(self):
        """测试模板数据加载"""
        df = self.service._load_template_data(1)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertIn('id', df.columns)
    
    def test_clean_data(self):
        """测试数据清理"""
        df = pd.DataFrame({
            'col1': [1, 2, np.nan],
            'col2': ['a', 'nan', 'NULL'],
            'col3': ['1', '2', '3']
        })
        
        cleaned = self.service._clean_data(df)
        self.assertIsInstance(cleaned, pd.DataFrame)
        self.assertEqual(len(cleaned), len(df))
    
    def test_save_result(self):
        """测试结果保存"""
        original_df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        synthetic_df = pd.DataFrame({'col1': [4, 5, 6], 'col2': ['d', 'e', 'f']})
        
        result_path = self.service._save_result(999, original_df, synthetic_df)
        
        self.assertIsNotNone(result_path)
        self.assertTrue(os.path.exists(result_path))
        self.assertTrue(os.path.exists(os.path.join(result_path, 'original.csv')))
        self.assertTrue(os.path.exists(os.path.join(result_path, 'synthetic.csv')))
        
        # 清理
        if os.path.exists(result_path):
            shutil.rmtree(result_path)
    
    def test_get_result_preview(self):
        """测试结果预览"""
        # 创建测试结果文件
        result_dir = os.path.join(self.service.results_folder, 'task_999')
        os.makedirs(result_dir, exist_ok=True)
        
        test_df = pd.DataFrame({
            'col1': list(range(50)),
            'col2': [f'value_{i}' for i in range(50)]
        })
        test_df.to_csv(os.path.join(result_dir, 'synthetic.csv'), index=False)
        
        # 需要模拟Task对象
        with patch('services.synthetic_service.Task') as mock_task:
            mock_task.query.get.return_value = Mock(
                result_path=result_dir
            )
            
            preview = self.service.get_result_preview(999, 'synthetic', 1, 10)
            
            if preview:
                self.assertIn('columns', preview)
                self.assertIn('data', preview)
                self.assertIn('pagination', preview)
                self.assertEqual(len(preview['data']), 10)
        
        # 清理
        if os.path.exists(result_dir):
            shutil.rmtree(result_dir)
    
    def test_get_result_file_path(self):
        """测试获取结果文件路径"""
        result_dir = os.path.join(self.service.results_folder, 'task_999')
        os.makedirs(result_dir, exist_ok=True)
        
        test_df = pd.DataFrame({'col1': [1, 2, 3]})
        test_df.to_csv(os.path.join(result_dir, 'synthetic.csv'), index=False)
        
        with patch('services.synthetic_service.Task') as mock_task:
            mock_task.query.get.return_value = Mock(
                result_path=result_dir
            )
            
            file_path = self.service.get_result_file_path(999, 'synthetic', 'csv')
            self.assertIsNotNone(file_path)
            self.assertTrue(os.path.exists(file_path))
        
        # 清理
        if os.path.exists(result_dir):
            shutil.rmtree(result_dir)


if __name__ == '__main__':
    unittest.main()

