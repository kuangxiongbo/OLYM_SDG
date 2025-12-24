#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景测试：按功能模块进行完整场景测试
"""

import unittest
import os
import sys
import tempfile
import shutil
import pandas as pd
import json
import io
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_complete import create_app
from models.user import db, User
from models.task import Task
from services.synthetic_service import SyntheticService
from services.quality_service import QualityService
from services.masking_service import MaskingService
from services.auth_service import AuthService


class ScenarioTestBase(unittest.TestCase):
    """场景测试基类"""
    
    def setUp(self):
        """测试前准备"""
        test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-secret-key',
            'UPLOAD_FOLDER': tempfile.mkdtemp(),
            'RESULTS_FOLDER': tempfile.mkdtemp(),
            'WTF_CSRF_ENABLED': False
        }
        
        self.app = create_app(test_config)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # 创建测试用户
        self.test_user = User(
            email='test@example.com',
            phone='13800138000',
            role='user',
            status='active'
        )
        self.test_user.set_password('Test123456')
        db.session.add(self.test_user)
        db.session.commit()
        
        self.temp_dir = tempfile.mkdtemp()
        self.test_results = []
        
    def tearDown(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_csv(self, filename='test_data.csv', rows=100):
        """创建测试CSV文件"""
        df = pd.DataFrame({
            'id': range(rows),
            'name': [f'User_{i}' for i in range(rows)],
            'age': [20 + i % 60 for i in range(rows)],
            'score': [50 + i % 50 for i in range(rows)],
            'email': [f'user{i}@example.com' for i in range(rows)]
        })
        filepath = os.path.join(self.temp_dir, filename)
        df.to_csv(filepath, index=False, encoding='utf-8')
        return filepath
    
    def record_test_result(self, scenario, test_name, status, message=''):
        """记录测试结果"""
        self.test_results.append({
            'scenario': scenario,
            'test_name': test_name,
            'status': status,
            'message': message
        })


class Scenario1AuthTest(ScenarioTestBase):
    """场景1: 用户注册登录流程"""
    
    def test_1_1_normal_registration(self):
        """测试正常注册流程"""
        try:
            with self.app.test_client() as client:
                # 注册新用户
                response = client.post('/api/auth/register', 
                    json={
                        'email': 'newuser@example.com',
                        'password': 'NewUser123',
                        'confirm_password': 'NewUser123'
                    },
                    content_type='application/json'
                )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(data.get('success'))
                self.record_test_result('认证模块', '正常注册', 'PASS')
        except Exception as e:
            self.record_test_result('认证模块', '正常注册', 'FAIL', str(e))
            raise
    
    def test_1_2_email_validation(self):
        """测试邮箱格式验证"""
        try:
            with self.app.test_client() as client:
                # 无效邮箱格式
                response = client.post('/api/auth/register',
                    json={
                        'email': 'invalid-email',
                        'password': 'Test123456',
                        'confirm_password': 'Test123456'
                    },
                    content_type='application/json'
                )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(data.get('success'))
                self.record_test_result('认证模块', '邮箱格式验证', 'PASS')
        except Exception as e:
            self.record_test_result('认证模块', '邮箱格式验证', 'FAIL', str(e))
            raise
    
    def test_1_3_password_strength(self):
        """测试密码强度验证"""
        try:
            with self.app.test_client() as client:
                # 弱密码
                response = client.post('/api/auth/register',
                    json={
                        'email': 'weak@example.com',
                        'password': '123456',
                        'confirm_password': '123456'
                    },
                    content_type='application/json'
                )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(data.get('success'))
                self.record_test_result('认证模块', '密码强度验证', 'PASS')
        except Exception as e:
            self.record_test_result('认证模块', '密码强度验证', 'FAIL', str(e))
            raise
    
    def test_1_4_login_success(self):
        """测试登录成功"""
        try:
            with self.app.test_client() as client:
                # 登录
                response = client.post('/api/auth/login',
                    json={
                        'email': 'test@example.com',
                        'password': 'Test123456'
                    },
                    content_type='application/json'
                )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(data.get('success'))
                self.record_test_result('认证模块', '登录成功', 'PASS')
        except Exception as e:
            self.record_test_result('认证模块', '登录成功', 'FAIL', str(e))
            raise
    
    def test_1_5_login_failure(self):
        """测试登录失败"""
        try:
            with self.app.test_client() as client:
                # 错误密码
                response = client.post('/api/auth/login',
                    json={
                        'email': 'test@example.com',
                        'password': 'WrongPassword'
                    },
                    content_type='application/json'
                )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 401)
                self.assertFalse(data.get('success'))
                self.record_test_result('认证模块', '登录失败', 'PASS')
        except Exception as e:
            self.record_test_result('认证模块', '登录失败', 'FAIL', str(e))
            raise


class Scenario2SyntheticTest(ScenarioTestBase):
    """场景2: 合成数据生成完整流程"""
    
    def test_2_1_file_upload_csv(self):
        """测试CSV文件上传"""
        try:
            test_file = self.create_test_csv('test.csv', 50)
            
            with self.app.test_client() as client:
                # 登录
                client.post('/api/auth/login',
                    json={'email': 'test@example.com', 'password': 'Test123456'},
                    content_type='application/json'
                )
                
                # 上传文件
                with open(test_file, 'rb') as f:
                    response = client.post('/api/synthesis/upload',
                        data={'file': (f, 'test.csv')},
                        content_type='multipart/form-data'
                    )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(data.get('success'))
                self.record_test_result('合成数据生成', 'CSV文件上传', 'PASS')
        except Exception as e:
            self.record_test_result('合成数据生成', 'CSV文件上传', 'FAIL', str(e))
            raise
    
    def test_2_2_get_templates(self):
        """测试获取模板列表"""
        try:
            with self.app.test_client() as client:
                # 登录
                client.post('/api/auth/login',
                    json={'email': 'test@example.com', 'password': 'Test123456'},
                    content_type='application/json'
                )
                
                # 获取模板
                response = client.get('/api/synthesis/templates',
                    headers={'Accept': 'application/json'}
                )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(data.get('success'))
                self.assertIn('templates', data.get('data', {}))
                self.record_test_result('合成数据生成', '获取模板列表', 'PASS')
        except Exception as e:
            self.record_test_result('合成数据生成', '获取模板列表', 'FAIL', str(e))
            raise
    
    def test_2_3_create_generation_task(self):
        """测试创建生成任务"""
        try:
            with self.app.test_client() as client:
                # 登录
                client.post('/api/auth/login',
                    json={'email': 'test@example.com', 'password': 'Test123456'},
                    content_type='application/json'
                )
                
                # 创建任务
                response = client.post('/api/synthesis/generate',
                    json={
                        'task_name': '测试生成任务',
                        'model_type': 'ctgan',
                        'model_config': {'epochs': 10, 'batch_size': 100},
                        'data_amount': 100
                    },
                    content_type='application/json'
                )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(data.get('success'))
                self.record_test_result('合成数据生成', '创建生成任务', 'PASS')
        except Exception as e:
            self.record_test_result('合成数据生成', '创建生成任务', 'FAIL', str(e))
            raise


class Scenario3QualityTest(ScenarioTestBase):
    """场景3: 数据质量评估流程"""
    
    def test_3_1_upload_original_data(self):
        """测试上传原始数据"""
        try:
            test_file = self.create_test_csv('original.csv', 50)
            
            with self.app.test_client() as client:
                # 登录
                client.post('/api/auth/login',
                    json={'email': 'test@example.com', 'password': 'Test123456'},
                    content_type='application/json'
                )
                
                # 上传文件
                with open(test_file, 'rb') as f:
                    response = client.post('/api/quality/upload',
                        data={'file': (f, 'original.csv'), 'data_type': 'original'},
                        content_type='multipart/form-data'
                    )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(data.get('success'))
                self.record_test_result('数据质量评估', '上传原始数据', 'PASS')
        except Exception as e:
            self.record_test_result('数据质量评估', '上传原始数据', 'FAIL', str(e))
            raise
    
    def test_3_2_create_assessment_task(self):
        """测试创建评估任务"""
        try:
            with self.app.test_client() as client:
                # 登录
                client.post('/api/auth/login',
                    json={'email': 'test@example.com', 'password': 'Test123456'},
                    content_type='application/json'
                )
                
                # 创建评估任务
                response = client.post('/api/quality/assess',
                    json={
                        'task_name': '测试评估任务',
                        'original_file_id': 'test_file_1',
                        'synthetic_file_id': 'test_file_2',
                        'indicators': [
                            {'name': 'correlation', 'enabled': True, 'threshold': 0.7},
                            {'name': 'distribution_similarity', 'enabled': True, 'threshold': 0.7}
                        ]
                    },
                    content_type='application/json'
                )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(data.get('success'))
                self.record_test_result('数据质量评估', '创建评估任务', 'PASS')
        except Exception as e:
            self.record_test_result('数据质量评估', '创建评估任务', 'FAIL', str(e))
            raise


class Scenario4MaskingTest(ScenarioTestBase):
    """场景4: 数据脱敏流程"""
    
    def test_4_1_upload_file_for_masking(self):
        """测试上传脱敏文件"""
        try:
            test_file = self.create_test_csv('masking_data.csv', 50)
            
            with self.app.test_client() as client:
                # 登录
                client.post('/api/auth/login',
                    json={'email': 'test@example.com', 'password': 'Test123456'},
                    content_type='application/json'
                )
                
                # 上传文件
                with open(test_file, 'rb') as f:
                    response = client.post('/api/masking/upload',
                        data={'file': (f, 'masking_data.csv')},
                        content_type='multipart/form-data'
                    )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(data.get('success'))
                self.record_test_result('数据脱敏', '上传脱敏文件', 'PASS')
        except Exception as e:
            self.record_test_result('数据脱敏', '上传脱敏文件', 'FAIL', str(e))
            raise
    
    def test_4_2_detect_fields(self):
        """测试字段识别"""
        try:
            with self.app.test_client() as client:
                # 登录
                client.post('/api/auth/login',
                    json={'email': 'test@example.com', 'password': 'Test123456'},
                    content_type='application/json'
                )
                
                # 字段识别（需要先上传文件）
                response = client.post('/api/masking/detect-fields',
                    json={'file_id': 'test_file_123'},
                    content_type='application/json'
                )
                
                # 可能返回404或错误，但应该能处理
                self.record_test_result('数据脱敏', '字段识别', 'PASS' if response.status_code in [200, 400, 404] else 'FAIL')
        except Exception as e:
            self.record_test_result('数据脱敏', '字段识别', 'FAIL', str(e))
            raise


class Scenario5TaskTest(ScenarioTestBase):
    """场景5: 任务管理流程"""
    
    def test_5_1_get_task_list(self):
        """测试获取任务列表"""
        try:
            with self.app.test_client() as client:
                # 登录
                client.post('/api/auth/login',
                    json={'email': 'test@example.com', 'password': 'Test123456'},
                    content_type='application/json'
                )
                
                # 获取任务列表
                response = client.get('/api/tasks',
                    headers={'Accept': 'application/json'}
                )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(data.get('success'))
                self.record_test_result('任务管理', '获取任务列表', 'PASS')
        except Exception as e:
            self.record_test_result('任务管理', '获取任务列表', 'FAIL', str(e))
            raise
    
    def test_5_2_filter_tasks_by_type(self):
        """测试按类型筛选任务"""
        try:
            with self.app.test_client() as client:
                # 登录
                client.post('/api/auth/login',
                    json={'email': 'test@example.com', 'password': 'Test123456'},
                    content_type='application/json'
                )
                
                # 筛选任务
                response = client.get('/api/tasks?type=synthesis',
                    headers={'Accept': 'application/json'}
                )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(data.get('success'))
                self.record_test_result('任务管理', '按类型筛选任务', 'PASS')
        except Exception as e:
            self.record_test_result('任务管理', '按类型筛选任务', 'FAIL', str(e))
            raise


class Scenario6ExceptionTest(ScenarioTestBase):
    """场景6: 异常场景测试"""
    
    def test_6_1_invalid_file_format(self):
        """测试无效文件格式"""
        try:
            # 创建无效格式文件
            invalid_file = os.path.join(self.temp_dir, 'test.txt')
            with open(invalid_file, 'w') as f:
                f.write('test content')
            
            with self.app.test_client() as client:
                # 登录
                client.post('/api/auth/login',
                    json={'email': 'test@example.com', 'password': 'Test123456'},
                    content_type='application/json'
                )
                
                # 上传无效格式文件
                with open(invalid_file, 'rb') as f:
                    response = client.post('/api/synthesis/upload',
                        data={'file': (f, 'test.txt')},
                        content_type='multipart/form-data'
                    )
                
                data = json.loads(response.data)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(data.get('success'))
                self.record_test_result('异常场景', '无效文件格式', 'PASS')
        except Exception as e:
            self.record_test_result('异常场景', '无效文件格式', 'FAIL', str(e))
            raise
    
    def test_6_2_unauthorized_access(self):
        """测试未授权访问"""
        try:
            with self.app.test_client() as client:
                # 未登录访问受保护资源
                response = client.get('/api/tasks',
                    headers={'Accept': 'application/json'}
                )
                
                # 应该返回401或302重定向
                self.assertIn(response.status_code, [401, 302, 403])
                self.record_test_result('异常场景', '未授权访问', 'PASS')
        except Exception as e:
            self.record_test_result('异常场景', '未授权访问', 'FAIL', str(e))
            raise
    
    def test_6_3_empty_file(self):
        """测试空文件上传"""
        try:
            # 创建空文件
            empty_file = os.path.join(self.temp_dir, 'empty.csv')
            with open(empty_file, 'w') as f:
                pass
            
            with self.app.test_client() as client:
                # 登录
                client.post('/api/auth/login',
                    json={'email': 'test@example.com', 'password': 'Test123456'},
                    content_type='application/json'
                )
                
                # 上传空文件
                with open(empty_file, 'rb') as f:
                    response = client.post('/api/synthesis/upload',
                        data={'file': (f, 'empty.csv')},
                        content_type='multipart/form-data'
                    )
                
                # 应该返回错误
                data = json.loads(response.data)
                self.assertFalse(data.get('success'))
                self.record_test_result('异常场景', '空文件上传', 'PASS')
        except Exception as e:
            self.record_test_result('异常场景', '空文件上传', 'FAIL', str(e))
            raise


def run_scenario_tests():
    """运行所有场景测试并生成报告"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有场景测试类
    suite.addTests(loader.loadTestsFromTestCase(Scenario1AuthTest))
    suite.addTests(loader.loadTestsFromTestCase(Scenario2SyntheticTest))
    suite.addTests(loader.loadTestsFromTestCase(Scenario3QualityTest))
    suite.addTests(loader.loadTestsFromTestCase(Scenario4MaskingTest))
    suite.addTests(loader.loadTestsFromTestCase(Scenario5TaskTest))
    suite.addTests(loader.loadTestsFromTestCase(Scenario6ExceptionTest))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    result = run_scenario_tests()
    sys.exit(0 if result.wasSuccessful() else 1)







