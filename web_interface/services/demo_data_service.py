#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示数据服务
===========

提供不同行业的演示数据生成功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import Dict, List, Any
import json
import os

class DemoDataService:
    """演示数据生成服务"""
    
    def __init__(self):
        self.demo_configs = self._load_demo_configs()
    
    def _load_demo_configs(self) -> Dict[str, Any]:
        """加载演示数据配置"""
        return {
            'finance': {
                'name': '金融行业数据',
                'description': '银行客户、股票交易、保险理赔数据',
                'datasets': {
                    'bank_customers': {
                        'name': '银行客户数据',
                        'fields': ['customer_id', 'age', 'income', 'credit_score', 'loan_history'],
                        'size': 2000,
                        'types': ['int', 'int', 'float', 'int', 'int']
                    },
                    'stock_trades': {
                        'name': '股票交易数据',
                        'fields': ['stock_code', 'price', 'volume', 'timestamp', 'trade_type'],
                        'size': 5000,
                        'types': ['str', 'float', 'int', 'datetime', 'str']
                    },
                    'insurance_claims': {
                        'name': '保险理赔数据',
                        'fields': ['policy_id', 'claim_amount', 'accident_type', 'process_time', 'status'],
                        'size': 1500,
                        'types': ['str', 'float', 'str', 'datetime', 'str']
                    }
                }
            },
            'ecommerce': {
                'name': '电商行业数据',
                'description': '用户购买、商品信息、订单物流数据',
                'datasets': {
                    'user_purchases': {
                        'name': '用户购买数据',
                        'fields': ['user_id', 'product_category', 'purchase_amount', 'rating', 'purchase_date'],
                        'size': 3000,
                        'types': ['int', 'str', 'float', 'int', 'datetime']
                    },
                    'product_info': {
                        'name': '商品信息数据',
                        'fields': ['product_id', 'price', 'stock', 'sales', 'category', 'brand'],
                        'size': 1000,
                        'types': ['str', 'float', 'int', 'int', 'str', 'str']
                    },
                    'order_logistics': {
                        'name': '订单物流数据',
                        'fields': ['order_id', 'delivery_address', 'delivery_status', 'delivery_time', 'tracking_code'],
                        'size': 2500,
                        'types': ['str', 'str', 'str', 'datetime', 'str']
                    }
                }
            },
            'healthcare': {
                'name': '医疗行业数据',
                'description': '患者病历、药品信息、医疗设备数据',
                'datasets': {
                    'patient_records': {
                        'name': '患者病历数据',
                        'fields': ['patient_id', 'age', 'gender', 'diagnosis', 'treatment_cost', 'admission_date'],
                        'size': 2000,
                        'types': ['str', 'int', 'str', 'str', 'float', 'datetime']
                    },
                    'drug_info': {
                        'name': '药品信息数据',
                        'fields': ['drug_name', 'specification', 'price', 'stock', 'side_effects', 'manufacturer'],
                        'size': 800,
                        'types': ['str', 'str', 'float', 'int', 'str', 'str']
                    },
                    'medical_equipment': {
                        'name': '医疗设备数据',
                        'fields': ['equipment_id', 'model', 'maintenance_record', 'usage_hours', 'last_maintenance'],
                        'size': 500,
                        'types': ['str', 'str', 'str', 'int', 'datetime']
                    }
                }
            },
            'education': {
                'name': '教育行业数据',
                'description': '学生成绩、教师信息、课程安排数据',
                'datasets': {
                    'student_grades': {
                        'name': '学生成绩数据',
                        'fields': ['student_id', 'course', 'grade', 'attendance_rate', 'homework_completion'],
                        'size': 3000,
                        'types': ['str', 'str', 'float', 'float', 'float']
                    },
                    'teacher_info': {
                        'name': '教师信息数据',
                        'fields': ['teacher_id', 'subject', 'experience_years', 'student_rating', 'salary'],
                        'size': 200,
                        'types': ['str', 'str', 'int', 'float', 'float']
                    },
                    'course_schedule': {
                        'name': '课程安排数据',
                        'fields': ['course_id', 'schedule_time', 'classroom', 'teacher_id', 'student_count'],
                        'size': 500,
                        'types': ['str', 'datetime', 'str', 'str', 'int']
                    }
                }
            },
            'manufacturing': {
                'name': '制造业数据',
                'description': '生产设备、产品质量、供应链数据',
                'datasets': {
                    'production_equipment': {
                        'name': '生产设备数据',
                        'fields': ['equipment_id', 'operation_status', 'fault_record', 'maintenance_time', 'efficiency'],
                        'size': 1000,
                        'types': ['str', 'str', 'str', 'datetime', 'float']
                    },
                    'product_quality': {
                        'name': '产品质量数据',
                        'fields': ['product_id', 'quality_result', 'defect_type', 'batch_number', 'inspection_date'],
                        'size': 2000,
                        'types': ['str', 'str', 'str', 'str', 'datetime']
                    },
                    'supply_chain': {
                        'name': '供应链数据',
                        'fields': ['supplier_id', 'material_type', 'price', 'delivery_time', 'quality_rating'],
                        'size': 800,
                        'types': ['str', 'str', 'float', 'datetime', 'int']
                    }
                }
            }
        }
    
    def get_demo_industries(self) -> List[Dict[str, str]]:
        """获取可用的演示行业列表"""
        return [
            {'id': industry_id, 'name': config['name'], 'description': config['description']}
            for industry_id, config in self.demo_configs.items()
        ]
    
    def get_demo_datasets(self, industry_id: str) -> List[Dict[str, Any]]:
        """获取指定行业的演示数据集列表"""
        if industry_id not in self.demo_configs:
            return []
        
        industry_config = self.demo_configs[industry_id]
        return [
            {
                'id': dataset_id,
                'name': dataset_config['name'],
                'fields': dataset_config['fields'],
                'size': dataset_config['size'],
                'types': dataset_config['types']
            }
            for dataset_id, dataset_config in industry_config['datasets'].items()
        ]
    
    def generate_demo_data(self, industry_id: str, dataset_id: str, size: int = None) -> pd.DataFrame:
        """生成演示数据"""
        if industry_id not in self.demo_configs:
            raise ValueError(f"不支持的行业: {industry_id}")
        
        if dataset_id not in self.demo_configs[industry_id]['datasets']:
            raise ValueError(f"不支持的数据集: {dataset_id}")
        
        dataset_config = self.demo_configs[industry_id]['datasets'][dataset_id]
        actual_size = size or dataset_config['size']
        
        # 根据数据集类型生成数据
        if industry_id == 'finance':
            return self._generate_finance_data(dataset_id, actual_size)
        elif industry_id == 'ecommerce':
            return self._generate_ecommerce_data(dataset_id, actual_size)
        elif industry_id == 'healthcare':
            return self._generate_healthcare_data(dataset_id, actual_size)
        elif industry_id == 'education':
            return self._generate_education_data(dataset_id, actual_size)
        elif industry_id == 'manufacturing':
            return self._generate_manufacturing_data(dataset_id, actual_size)
        else:
            raise ValueError(f"不支持的行业: {industry_id}")
    
    def _generate_finance_data(self, dataset_id: str, size: int) -> pd.DataFrame:
        """生成金融行业数据"""
        if dataset_id == 'bank_customers':
            data = {
                'customer_id': range(1, size + 1),
                'age': np.random.normal(35, 10, size).astype(int),
                'income': np.random.lognormal(10, 0.5, size),
                'credit_score': np.random.normal(650, 100, size).astype(int),
                'loan_history': np.random.poisson(2, size)
            }
            # 确保年龄在合理范围内
            data['age'] = np.clip(data['age'], 18, 80)
            data['credit_score'] = np.clip(data['credit_score'], 300, 850)
            data['loan_history'] = np.clip(data['loan_history'], 0, 10)
            
        elif dataset_id == 'stock_trades':
            stock_codes = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
            trade_types = ['buy', 'sell', 'hold']
            
            data = {
                'stock_code': np.random.choice(stock_codes, size),
                'price': np.random.uniform(10, 500, size),
                'volume': np.random.poisson(1000, size),
                'timestamp': [datetime.now() - timedelta(days=random.randint(0, 365)) for _ in range(size)],
                'trade_type': np.random.choice(trade_types, size)
            }
            
        elif dataset_id == 'insurance_claims':
            accident_types = ['car', 'home', 'health', 'life', 'travel']
            statuses = ['pending', 'approved', 'rejected', 'processing']
            
            data = {
                'policy_id': [f'POL{str(i).zfill(6)}' for i in range(1, size + 1)],
                'claim_amount': np.random.lognormal(8, 1, size),
                'accident_type': np.random.choice(accident_types, size),
                'process_time': [datetime.now() - timedelta(days=random.randint(0, 90)) for _ in range(size)],
                'status': np.random.choice(statuses, size)
            }
        
        return pd.DataFrame(data)
    
    def _generate_ecommerce_data(self, dataset_id: str, size: int) -> pd.DataFrame:
        """生成电商行业数据"""
        if dataset_id == 'user_purchases':
            categories = ['electronics', 'clothing', 'books', 'home', 'sports', 'beauty']
            
            data = {
                'user_id': np.random.randint(1, 10000, size),
                'product_category': np.random.choice(categories, size),
                'purchase_amount': np.random.lognormal(4, 1, size),
                'rating': np.random.randint(1, 6, size),
                'purchase_date': [datetime.now() - timedelta(days=random.randint(0, 365)) for _ in range(size)]
            }
            
        elif dataset_id == 'product_info':
            categories = ['electronics', 'clothing', 'books', 'home', 'sports', 'beauty']
            brands = ['BrandA', 'BrandB', 'BrandC', 'BrandD', 'BrandE']
            
            data = {
                'product_id': [f'PROD{str(i).zfill(6)}' for i in range(1, size + 1)],
                'price': np.random.lognormal(3, 1, size),
                'stock': np.random.poisson(100, size),
                'sales': np.random.poisson(50, size),
                'category': np.random.choice(categories, size),
                'brand': np.random.choice(brands, size)
            }
            
        elif dataset_id == 'order_logistics':
            addresses = ['Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen', 'Hangzhou', 'Nanjing']
            statuses = ['pending', 'shipped', 'delivered', 'cancelled']
            
            data = {
                'order_id': [f'ORD{str(i).zfill(8)}' for i in range(1, size + 1)],
                'delivery_address': np.random.choice(addresses, size),
                'delivery_status': np.random.choice(statuses, size),
                'delivery_time': [datetime.now() - timedelta(days=random.randint(0, 30)) for _ in range(size)],
                'tracking_code': [f'TRK{str(i).zfill(10)}' for i in range(1, size + 1)]
            }
        
        return pd.DataFrame(data)
    
    def _generate_healthcare_data(self, dataset_id: str, size: int) -> pd.DataFrame:
        """生成医疗行业数据"""
        if dataset_id == 'patient_records':
            genders = ['Male', 'Female', 'Other']
            diagnoses = ['Hypertension', 'Diabetes', 'Flu', 'Pneumonia', 'Fracture', 'Headache']
            
            data = {
                'patient_id': [f'PAT{str(i).zfill(6)}' for i in range(1, size + 1)],
                'age': np.random.normal(45, 20, size).astype(int),
                'gender': np.random.choice(genders, size),
                'diagnosis': np.random.choice(diagnoses, size),
                'treatment_cost': np.random.lognormal(6, 1, size),
                'admission_date': [datetime.now() - timedelta(days=random.randint(0, 365)) for _ in range(size)]
            }
            data['age'] = np.clip(data['age'], 0, 100)
            
        elif dataset_id == 'drug_info':
            specifications = ['100mg', '200mg', '500mg', '1g', '2ml', '5ml']
            side_effects = ['Drowsiness', 'Nausea', 'Headache', 'None', 'Rash']
            manufacturers = ['PharmaA', 'PharmaB', 'PharmaC', 'PharmaD']
            
            data = {
                'drug_name': [f'Drug{chr(65 + i % 26)}{i // 26 + 1}' for i in range(size)],
                'specification': np.random.choice(specifications, size),
                'price': np.random.uniform(10, 500, size),
                'stock': np.random.poisson(100, size),
                'side_effects': np.random.choice(side_effects, size),
                'manufacturer': np.random.choice(manufacturers, size)
            }
            
        elif dataset_id == 'medical_equipment':
            models = ['ModelA', 'ModelB', 'ModelC', 'ModelD']
            maintenance_records = ['Regular', 'Emergency', 'Preventive', 'Repair']
            
            data = {
                'equipment_id': [f'EQ{str(i).zfill(4)}' for i in range(1, size + 1)],
                'model': np.random.choice(models, size),
                'maintenance_record': np.random.choice(maintenance_records, size),
                'usage_hours': np.random.poisson(1000, size),
                'last_maintenance': [datetime.now() - timedelta(days=random.randint(0, 90)) for _ in range(size)]
            }
        
        return pd.DataFrame(data)
    
    def _generate_education_data(self, dataset_id: str, size: int) -> pd.DataFrame:
        """生成教育行业数据"""
        if dataset_id == 'student_grades':
            courses = ['Math', 'English', 'Science', 'History', 'Art', 'PE']
            
            data = {
                'student_id': [f'STU{str(i).zfill(6)}' for i in range(1, size + 1)],
                'course': np.random.choice(courses, size),
                'grade': np.random.normal(75, 15, size),
                'attendance_rate': np.random.uniform(0.6, 1.0, size),
                'homework_completion': np.random.uniform(0.5, 1.0, size)
            }
            data['grade'] = np.clip(data['grade'], 0, 100)
            
        elif dataset_id == 'teacher_info':
            subjects = ['Math', 'English', 'Science', 'History', 'Art', 'PE']
            
            data = {
                'teacher_id': [f'TCH{str(i).zfill(4)}' for i in range(1, size + 1)],
                'subject': np.random.choice(subjects, size),
                'experience_years': np.random.poisson(10, size),
                'student_rating': np.random.uniform(3.0, 5.0, size),
                'salary': np.random.normal(50000, 15000, size)
            }
            
        elif dataset_id == 'course_schedule':
            classrooms = ['Room101', 'Room102', 'Room103', 'Room201', 'Room202']
            
            data = {
                'course_id': [f'CRS{str(i).zfill(4)}' for i in range(1, size + 1)],
                'schedule_time': [datetime.now() + timedelta(hours=random.randint(8, 18)) for _ in range(size)],
                'classroom': np.random.choice(classrooms, size),
                'teacher_id': [f'TCH{str(random.randint(1, 200)).zfill(4)}' for _ in range(size)],
                'student_count': np.random.poisson(25, size)
            }
        
        return pd.DataFrame(data)
    
    def _generate_manufacturing_data(self, dataset_id: str, size: int) -> pd.DataFrame:
        """生成制造业数据"""
        if dataset_id == 'production_equipment':
            statuses = ['Running', 'Stopped', 'Maintenance', 'Error']
            fault_records = ['None', 'Minor', 'Major', 'Critical']
            
            data = {
                'equipment_id': [f'EQ{str(i).zfill(4)}' for i in range(1, size + 1)],
                'operation_status': np.random.choice(statuses, size),
                'fault_record': np.random.choice(fault_records, size),
                'maintenance_time': [datetime.now() - timedelta(days=random.randint(0, 30)) for _ in range(size)],
                'efficiency': np.random.uniform(0.6, 1.0, size)
            }
            
        elif dataset_id == 'product_quality':
            quality_results = ['Pass', 'Fail', 'Rework']
            defect_types = ['None', 'Minor', 'Major', 'Critical']
            
            data = {
                'product_id': [f'PROD{str(i).zfill(6)}' for i in range(1, size + 1)],
                'quality_result': np.random.choice(quality_results, size),
                'defect_type': np.random.choice(defect_types, size),
                'batch_number': [f'BATCH{str(random.randint(1, 100)).zfill(3)}' for _ in range(size)],
                'inspection_date': [datetime.now() - timedelta(days=random.randint(0, 30)) for _ in range(size)]
            }
            
        elif dataset_id == 'supply_chain':
            material_types = ['Raw Material', 'Component', 'Assembly', 'Packaging']
            
            data = {
                'supplier_id': [f'SUP{str(i).zfill(4)}' for i in range(1, size + 1)],
                'material_type': np.random.choice(material_types, size),
                'price': np.random.lognormal(3, 1, size),
                'delivery_time': [datetime.now() + timedelta(days=random.randint(1, 30)) for _ in range(size)],
                'quality_rating': np.random.randint(1, 6, size)
            }
        
        return pd.DataFrame(data)
    
    def get_data_sample(self, industry_id: str, dataset_id: str, sample_size: int = 10) -> Dict[str, Any]:
        """获取数据样本（用于预览）"""
        df = self.generate_demo_data(industry_id, dataset_id, sample_size)
        
        return {
            'columns': df.columns.tolist(),
            'types': df.dtypes.astype(str).to_dict(),
            'sample_data': df.head(sample_size).to_dict('records'),
            'total_rows': len(df)
        }

