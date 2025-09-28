#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置
========

Flask应用配置文件
"""

import os
from datetime import timedelta

class Config:
    """基础配置"""
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sdg-web-interface-secret-key-2025'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # 开发环境设为False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls'}
    
    # SDV完整参数配置
    MODEL_CONFIGS = {
        'ctgan': {
            # 训练参数
            'epochs': 300,
            'batch_size': 500,
            'generator_lr': 2e-4,
            'discriminator_lr': 2e-4,
            'generator_decay': 1e-6,
            'discriminator_decay': 1e-6,
            'generator_steps': 1,
            'discriminator_steps': 5,
            
            # 网络结构参数
            'generator_dim': (256, 256),
            'discriminator_dim': (256, 256),
            
            # 损失函数参数
            'loss_factor': 2,
            'pac': 10,
            'log_frequency': True,
            
            # 数据预处理参数
            'enforce_min_max_values': True,
            'enforce_rounding': False,
            'max_tries_per_batch': 100,
            
            # 隐私保护参数
            'dp': False,
            'epsilon': 1.0,
            'delta': 1e-8
        },
        'tvae': {
            # 训练参数
            'epochs': 300,
            'batch_size': 500,
            'lr': 2e-3,
            'weight_decay': 1e-5,
            
            # 网络结构参数
            'compress_dims': (128, 128),
            'decompress_dims': (128, 128),
            'embedding_dim': 128,
            'l2norm': 1e-5,
            
            # 损失函数参数
            'loss_factor': 2,
            'log_frequency': True,
            
            # 数据预处理参数
            'enforce_min_max_values': True,
            'enforce_rounding': False,
            
            # VAE特定参数
            'beta': 1.0,
            'gamma': 1.0
        },
        'gaussian_copula': {
            # 分布参数
            'default_distribution': 'gaussian',
            'enforce_min_max_values': True,
            'enforce_rounding': False,
            
            # 数值处理参数
            'numerical_distributions': ['gaussian', 'beta', 'gamma', 'uniform'],
            'categorical_fill_value': 'mode',
            'numerical_fill_value': 'mean',
            
            # 相关性参数
            'distribution': 'gaussian',
            'max_clusters': 10,
            'categorical_transformer': 'label_encoding',
            'numerical_transformer': 'float',
            
            # 隐私保护参数
            'dp': False,
            'epsilon': 1.0,
            'delta': 1e-8
        },
        'copula_gan': {
            # 训练参数
            'epochs': 300,
            'batch_size': 500,
            'generator_lr': 2e-4,
            'discriminator_lr': 2e-4,
            'pac': 10,
            
            # 网络结构参数
            'generator_dim': (256, 256),
            'discriminator_dim': (256, 256),
            
            # Copula特定参数
            'latent_dim': 128,
            'generator_side': None,
            'discriminator_side': None,
            
            # 数据预处理参数
            'enforce_min_max_values': True,
            'enforce_rounding': False
        },
        'tab_ddpm': {
            # 训练参数
            'epochs': 1000,
            'batch_size': 1024,
            'lr': 2e-4,
            
            # 网络结构参数
            'model_type': 'mlp',
            'model_params': {
                'num_timesteps': 1000,
                'num_layers': 4,
                'num_units': 256
            },
            
            # 数据预处理参数
            'enforce_min_max_values': True,
            'enforce_rounding': False,
            
            # 扩散模型参数
            'beta_start': 0.0001,
            'beta_end': 0.02,
            'beta_schedule': 'linear',
            'num_timesteps': 1000
        }
    }
    
    # 演示数据配置
    DEMO_DATASETS = {
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
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1小时
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'app.log')

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    
    # 开发环境数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/dev_database.db'
    
    # 开发环境日志
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    
    # 生产环境数据库
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/sdg_db'
    
    # 生产环境安全配置
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True
    
    # 生产环境日志
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    
    # 测试环境数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # 禁用CSRF保护
    WTF_CSRF_ENABLED = False

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """获取当前配置"""
    config_name = os.environ.get('FLASK_ENV') or 'development'
    return config.get(config_name, config['default'])