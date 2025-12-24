#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据脱敏服务单元测试
"""

import unittest
import os
import sys
import pandas as pd
import numpy as np
import tempfile
import shutil
import re
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.masking_service import MaskingService
from config import Config


class TestMaskingService(unittest.TestCase):
    """数据脱敏服务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.service = MaskingService()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_service_init(self):
        """测试服务初始化"""
        service = MaskingService()
        self.assertIsNotNone(service.upload_folder)
        self.assertIsNotNone(service.results_folder)
        self.assertTrue(os.path.exists(service.results_folder))
    
    def test_detect_field_type_id_card(self):
        """测试身份证号识别"""
        series = pd.Series([
            '320121199212121234',
            '510324199305125621',
            '110101199001011234',
            '320121199212121234'
        ])
        
        detected_type, confidence = self.service._detect_field_type(series)
        self.assertEqual(detected_type, 'id_card')
        self.assertGreater(confidence, 0.8)
    
    def test_detect_field_type_phone(self):
        """测试手机号识别"""
        series = pd.Series([
            '13800138000',
            '13900139000',
            '15000150000',
            '13800138000'
        ])
        
        detected_type, confidence = self.service._detect_field_type(series)
        self.assertEqual(detected_type, 'phone')
        self.assertGreater(confidence, 0.8)
    
    def test_detect_field_type_email(self):
        """测试邮箱识别"""
        series = pd.Series([
            'test@example.com',
            'user@test.com',
            'admin@example.org',
            'test@example.com'
        ])
        
        detected_type, confidence = self.service._detect_field_type(series)
        self.assertEqual(detected_type, 'email')
        self.assertGreater(confidence, 0.8)
    
    def test_detect_field_type_name(self):
        """测试姓名识别"""
        series = pd.Series([
            '张三',
            '李四',
            '王五',
            '赵六'
        ])
        
        detected_type, confidence = self.service._detect_field_type(series)
        self.assertEqual(detected_type, 'name')
        self.assertGreater(confidence, 0.5)
    
    def test_detect_field_type_numeric(self):
        """测试数值类型识别"""
        series = pd.Series([1, 2, 3, 4, 5])
        
        detected_type, confidence = self.service._detect_field_type(series)
        self.assertEqual(detected_type, 'numeric')
        self.assertGreater(confidence, 0.8)
    
    def test_generate_simulation_example(self):
        """测试生成仿真值示例"""
        examples = {
            'name': self.service._generate_simulation_example('name', '张三'),
            'id_card': self.service._generate_simulation_example('id_card', '320121199212121234'),
            'phone': self.service._generate_simulation_example('phone', '13800138000'),
            'email': self.service._generate_simulation_example('email', 'test@example.com')
        }
        
        self.assertEqual(examples['name'], '李雪')
        self.assertEqual(examples['id_card'], '510324199305125621')
        self.assertIn('139', examples['phone'])
        self.assertIn('@', examples['email'])
    
    def test_mask_field(self):
        """测试字段遮蔽"""
        series = pd.Series(['13800138000', '13900139000', '15000150000'])
        
        # 测试保留前3位和后4位
        masked = self.service._mask_field(series, {
            'keep_prefix': 3,
            'keep_suffix': 4,
            'mask_char': '*'
        })
        
        self.assertEqual(masked.iloc[0], '138****8000')
        self.assertEqual(masked.iloc[1], '139****9000')
    
    def test_hash_field(self):
        """测试字段哈希"""
        series = pd.Series(['value1', 'value2', 'value3'])
        
        hashed = self.service._hash_field(series)
        
        # 检查哈希值长度（MD5前16位）
        self.assertEqual(len(hashed.iloc[0]), 16)
        # 检查不同值产生不同哈希
        self.assertNotEqual(hashed.iloc[0], hashed.iloc[1])
        # 检查哈希值只包含十六进制字符
        import re
        self.assertTrue(re.match(r'^[0-9a-f]{16}$', hashed.iloc[0]))
    
    def test_save_result(self):
        """测试结果保存"""
        original_df = pd.DataFrame({
            'name': ['张三', '李四', '王五'],
            'phone': ['13800138000', '13900139000', '15000150000']
        })
        
        masked_df = pd.DataFrame({
            'name': ['李雪', '王明', '张强'],
            'phone': ['138****8000', '139****9000', '150****0000']
        })
        
        result_path = self.service._save_result(999, original_df, masked_df)
        
        self.assertIsNotNone(result_path)
        self.assertTrue(os.path.exists(result_path))
        self.assertTrue(os.path.exists(os.path.join(result_path, 'original.csv')))
        self.assertTrue(os.path.exists(os.path.join(result_path, 'masked.csv')))
        
        # 验证文件内容
        loaded_original = pd.read_csv(os.path.join(result_path, 'original.csv'))
        loaded_masked = pd.read_csv(os.path.join(result_path, 'masked.csv'))
        
        self.assertEqual(len(loaded_original), 3)
        self.assertEqual(len(loaded_masked), 3)
        
        # 清理
        if os.path.exists(result_path):
            shutil.rmtree(result_path)
    
    def test_get_result_preview(self):
        """测试结果预览"""
        # 创建测试结果文件
        result_dir = os.path.join(self.service.results_folder, 'task_999')
        os.makedirs(result_dir, exist_ok=True)
        
        original_df = pd.DataFrame({
            'name': [f'name_{i}' for i in range(50)],
            'phone': [f'138{i:08d}' for i in range(50)]
        })
        
        masked_df = pd.DataFrame({
            'name': [f'masked_name_{i}' for i in range(50)],
            'phone': [f'138****{i:04d}' for i in range(50)]
        })
        
        original_df.to_csv(os.path.join(result_dir, 'original.csv'), index=False)
        masked_df.to_csv(os.path.join(result_dir, 'masked.csv'), index=False)
        
        with patch('services.masking_service.Task') as mock_task:
            mock_task.query.get.return_value = Mock(
                result_path=result_dir
            )
            
            preview = self.service.get_result_preview(999, page=1, page_size=10)
            
            if preview:
                self.assertIn('columns', preview)
                self.assertIn('original_data', preview)
                self.assertIn('masked_data', preview)
                self.assertIn('pagination', preview)
                self.assertEqual(len(preview['original_data']), 10)
                self.assertEqual(len(preview['masked_data']), 10)
        
        # 清理
        if os.path.exists(result_dir):
            shutil.rmtree(result_dir)


if __name__ == '__main__':
    unittest.main()

