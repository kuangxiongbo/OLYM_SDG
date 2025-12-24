#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合成数据生成路由
"""

from flask import Blueprint, request, jsonify, send_file, render_template
from flask_login import login_required, current_user
from models.task import Task, db
from models.user import User
from models.config import SystemConfig
from models.user_parameter_template import UserParameterTemplate
from utils.helpers import save_uploaded_file, generate_file_id
from utils.decorators import log_operation
from services.synthetic_service import SyntheticService
from services.field_type_analyzer import FieldTypeAnalyzer
import os
from config import Config

synthetic_bp = Blueprint('synthesis', __name__)

@synthetic_bp.route('/templates', methods=['GET'])
@login_required
def get_templates():
    """获取行业模板列表"""
    # 如果是HTML请求或浏览器请求（Accept包含text/html或*/*），返回HTML页面
    accept = request.headers.get('Accept', '')
    is_browser_request = 'text/html' in accept or ('*/*' in accept and 'application/json' not in accept)
    is_explicit_json = 'application/json' in accept and 'text/html' not in accept
    
    if is_browser_request or (not is_explicit_json and not accept):
        from flask import render_template
        try:
            return render_template('synthesis.html', current_user=current_user)
        except Exception as e:
            from flask import redirect
            import traceback
            import sys
            print(f"渲染模板失败: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            # 返回错误信息而不是重定向，方便调试（生产环境应改为重定向）
            return redirect('/')
    
    templates = [
        {
            'id': 1,
            'name': '银行客户模板',
            'category': '金融',
            'description': '包含客户基本信息、账户行为、风险画像等字段配置',
            'fields': [
                {'name': 'customer_id', 'type': 'string', 'description': '客户ID'},
                {'name': 'name', 'type': 'string', 'description': '客户姓名'},
                {'name': 'age', 'type': 'integer', 'description': '年龄', 'range': [18, 80]},
                {'name': 'gender', 'type': 'string', 'description': '性别'},
                {'name': 'income', 'type': 'float', 'description': '年收入', 'range': [30000, 500000]},
                {'name': 'credit_score', 'type': 'integer', 'description': '信用评分', 'range': [300, 850]},
                {'name': 'account_balance', 'type': 'float', 'description': '账户余额', 'range': [0, 1000000]},
                {'name': 'loan_amount', 'type': 'float', 'description': '贷款金额', 'range': [0, 500000]},
                {'name': 'register_date', 'type': 'date', 'description': '注册日期'}
            ]
        },
        {
            'id': 2,
            'name': '话单模板',
            'category': '通信',
            'description': '含基站、时段、通话类型等字段，可快速生成通联数据',
            'fields': [
                {'name': 'call_id', 'type': 'string', 'description': '通话ID'},
                {'name': 'caller_number', 'type': 'string', 'description': '主叫号码'},
                {'name': 'callee_number', 'type': 'string', 'description': '被叫号码'},
                {'name': 'call_type', 'type': 'string', 'description': '通话类型'},
                {'name': 'call_duration', 'type': 'integer', 'description': '通话时长（秒）', 'range': [0, 3600]},
                {'name': 'base_station_id', 'type': 'string', 'description': '基站ID'},
                {'name': 'call_time', 'type': 'date', 'description': '通话时间'},
                {'name': 'location', 'type': 'string', 'description': '通话地点'},
                {'name': 'cost', 'type': 'float', 'description': '通话费用', 'range': [0, 100]}
            ]
        },
        {
            'id': 3,
            'name': '门店销售模板',
            'category': '零售',
            'description': '覆盖商品、库存、销售记录，适合场景模拟',
            'fields': [
                {'name': 'order_id', 'type': 'string', 'description': '订单ID'},
                {'name': 'product_id', 'type': 'string', 'description': '商品ID'},
                {'name': 'product_name', 'type': 'string', 'description': '商品名称'},
                {'name': 'category', 'type': 'string', 'description': '商品分类'},
                {'name': 'quantity', 'type': 'integer', 'description': '数量', 'range': [1, 100]},
                {'name': 'unit_price', 'type': 'float', 'description': '单价', 'range': [1, 10000]},
                {'name': 'total_amount', 'type': 'float', 'description': '总金额', 'range': [1, 100000]},
                {'name': 'customer_id', 'type': 'string', 'description': '客户ID'},
                {'name': 'store_id', 'type': 'string', 'description': '门店ID'},
                {'name': 'sale_date', 'type': 'date', 'description': '销售日期'}
            ]
        },
        {
            'id': 4,
            'name': '电商订单模板',
            'category': '零售',
            'description': '包含订单信息、商品详情、用户行为等字段',
            'fields': [
                {'name': 'order_id', 'type': 'string', 'description': '订单号'},
                {'name': 'user_id', 'type': 'string', 'description': '用户ID'},
                {'name': 'product_id', 'type': 'string', 'description': '商品ID'},
                {'name': 'product_name', 'type': 'string', 'description': '商品名称'},
                {'name': 'quantity', 'type': 'integer', 'description': '购买数量', 'range': [1, 50]},
                {'name': 'price', 'type': 'float', 'description': '商品价格', 'range': [1, 50000]},
                {'name': 'discount', 'type': 'float', 'description': '折扣', 'range': [0, 1]},
                {'name': 'payment_method', 'type': 'string', 'description': '支付方式'},
                {'name': 'shipping_address', 'type': 'string', 'description': '收货地址'},
                {'name': 'order_status', 'type': 'string', 'description': '订单状态'},
                {'name': 'order_time', 'type': 'date', 'description': '下单时间'}
            ]
        },
        {
            'id': 5,
            'name': '患者信息模板',
            'category': '医疗',
            'description': '包含患者基本信息、诊断记录、用药信息等字段',
            'fields': [
                {'name': 'patient_id', 'type': 'string', 'description': '患者ID'},
                {'name': 'name', 'type': 'string', 'description': '患者姓名'},
                {'name': 'age', 'type': 'integer', 'description': '年龄', 'range': [0, 120]},
                {'name': 'gender', 'type': 'string', 'description': '性别'},
                {'name': 'diagnosis', 'type': 'string', 'description': '诊断结果'},
                {'name': 'symptoms', 'type': 'string', 'description': '症状描述'},
                {'name': 'medication', 'type': 'string', 'description': '用药信息'},
                {'name': 'temperature', 'type': 'float', 'description': '体温', 'range': [35.0, 42.0]},
                {'name': 'blood_pressure', 'type': 'string', 'description': '血压'},
                {'name': 'visit_date', 'type': 'date', 'description': '就诊日期'}
            ]
        },
        {
            'id': 6,
            'name': '学生信息模板',
            'category': '教育',
            'description': '包含学生基本信息、成绩记录、课程信息等字段',
            'fields': [
                {'name': 'student_id', 'type': 'string', 'description': '学生ID'},
                {'name': 'name', 'type': 'string', 'description': '学生姓名'},
                {'name': 'age', 'type': 'integer', 'description': '年龄', 'range': [6, 25]},
                {'name': 'grade', 'type': 'string', 'description': '年级'},
                {'name': 'class', 'type': 'string', 'description': '班级'},
                {'name': 'subject', 'type': 'string', 'description': '科目'},
                {'name': 'score', 'type': 'float', 'description': '成绩', 'range': [0, 100]},
                {'name': 'attendance_rate', 'type': 'float', 'description': '出勤率', 'range': [0, 1]},
                {'name': 'exam_date', 'type': 'date', 'description': '考试日期'}
            ]
        },
        {
            'id': 7,
            'name': '保险理赔模板',
            'category': '金融',
            'description': '包含保单信息、理赔记录、审核流程等字段',
            'fields': [
                {'name': 'claim_id', 'type': 'string', 'description': '理赔ID'},
                {'name': 'policy_id', 'type': 'string', 'description': '保单号'},
                {'name': 'customer_id', 'type': 'string', 'description': '客户ID'},
                {'name': 'claim_type', 'type': 'string', 'description': '理赔类型'},
                {'name': 'claim_amount', 'type': 'float', 'description': '理赔金额', 'range': [100, 1000000]},
                {'name': 'accident_date', 'type': 'date', 'description': '事故日期'},
                {'name': 'claim_date', 'type': 'date', 'description': '申请日期'},
                {'name': 'status', 'type': 'string', 'description': '理赔状态'},
                {'name': 'approval_time', 'type': 'integer', 'description': '审核时长（天）', 'range': [1, 90]}
            ]
        },
        {
            'id': 8,
            'name': '物流配送模板',
            'category': '物流',
            'description': '包含订单信息、配送路线、物流状态等字段',
            'fields': [
                {'name': 'shipment_id', 'type': 'string', 'description': '运单号'},
                {'name': 'order_id', 'type': 'string', 'description': '订单ID'},
                {'name': 'sender_address', 'type': 'string', 'description': '发货地址'},
                {'name': 'receiver_address', 'type': 'string', 'description': '收货地址'},
                {'name': 'weight', 'type': 'float', 'description': '重量（kg）', 'range': [0.1, 100]},
                {'name': 'distance', 'type': 'float', 'description': '距离（km）', 'range': [1, 5000]},
                {'name': 'shipping_fee', 'type': 'float', 'description': '运费', 'range': [5, 500]},
                {'name': 'status', 'type': 'string', 'description': '配送状态'},
                {'name': 'ship_date', 'type': 'date', 'description': '发货日期'},
                {'name': 'delivery_date', 'type': 'date', 'description': '送达日期'}
            ]
        }
    ]
    return jsonify({
        'success': True,
        'data': {'templates': templates}
    }), 200

@synthetic_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """上传数据文件"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '未上传文件',
                'code': 'INVALID_PARAMS'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '文件名为空',
                'code': 'INVALID_PARAMS'
            }), 400
        
        # 检查文件扩展名
        from utils.helpers import allowed_file
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'不支持的文件格式，仅支持: {", ".join(Config.ALLOWED_EXTENSIONS)}',
                'code': 'UNSUPPORTED_FORMAT'
            }), 400
        
        # 确保上传目录存在
        import os
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # 保存文件
        file_id, filepath, filename = save_uploaded_file(file)
        if not file_id or not filepath:
            return jsonify({
                'success': False,
                'error': '文件保存失败，请检查文件格式和权限',
                'code': 'SAVE_FAILED'
            }), 500
        
        # 验证文件是否存在
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': '文件保存后验证失败',
                'code': 'FILE_NOT_FOUND'
            }), 500
        
        # 读取文件预览
        import pandas as pd
        try:
            if filename.endswith('.csv'):
                # 尝试UTF-8编码
                try:
                    df = pd.read_csv(filepath, nrows=10, encoding='utf-8')
                except UnicodeDecodeError:
                    # 尝试GBK编码
                    try:
                        df = pd.read_csv(filepath, nrows=10, encoding='gbk')
                    except UnicodeDecodeError:
                        # 尝试其他常见编码
                        df = pd.read_csv(filepath, nrows=10, encoding='gb18030')
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(filepath, nrows=10, engine='openpyxl')
            elif filename.endswith('.xls'):
                df = pd.read_excel(filepath, nrows=10, engine='xlrd')
            else:
                return jsonify({
                    'success': False,
                    'error': '不支持的文件格式',
                    'code': 'UNSUPPORTED_FORMAT'
                }), 400
        except UnicodeDecodeError as e:
            return jsonify({
                'success': False,
                'error': f'文件编码不支持，请转换为UTF-8格式: {str(e)}',
                'code': 'ENCODING_ERROR'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'文件读取失败: {str(e)}',
                'code': 'READ_FAILED'
            }), 500
        
        if df.empty:
            return jsonify({
                'success': False,
                'error': '文件为空或无法读取数据',
                'code': 'EMPTY_FILE'
            }), 400
        
        # 获取预览数据
        try:
            preview = df.head(5).to_dict('records') if len(df) > 0 else []
            # 清理NaN值
            for row in preview:
                for key, value in row.items():
                    if pd.isna(value):
                        row[key] = None
        except Exception as e:
            preview = []
            print(f"生成预览数据失败: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'file_id': file_id,
                'filename': file.filename,
                'rows': len(df),
                'columns': df.columns.tolist(),
                'preview': preview
            }
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'上传失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@synthetic_bp.route('/generate', methods=['POST'])
@login_required
@log_operation('创建合成数据生成任务', 'task')
def generate():
    """生成合成数据"""
    try:
        data = request.get_json()
        service = SyntheticService()
        from flask_login import current_user
        task = service.create_generation_task(
            user_id=current_user.id,
            config=data
        )
        
        return jsonify({
            'success': True,
            'data': {
                'task_id': f'task_{task.id}',
                'status': task.status,
                'message': '任务已创建，正在处理中'
            }
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ 创建生成任务失败: {str(e)}")
        print(f"详细错误堆栈:\n{error_trace}")
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR',
            'traceback': error_trace if Config.DEBUG else None
        }), 500

@synthetic_bp.route('/templates/<int:template_id>', methods=['GET'])
@login_required
def get_template_detail(template_id):
    """获取模板详情"""
    # 模板数据定义
    templates_data = {
        1: {
            'id': 1,
            'name': '银行客户模板',
            'category': '金融',
            'fields': [
                {'name': 'customer_id', 'type': 'string', 'description': '客户ID'},
                {'name': 'name', 'type': 'string', 'description': '客户姓名'},
                {'name': 'age', 'type': 'integer', 'description': '年龄', 'range': [18, 80]},
                {'name': 'gender', 'type': 'string', 'description': '性别'},
                {'name': 'income', 'type': 'float', 'description': '年收入', 'range': [30000, 500000]},
                {'name': 'credit_score', 'type': 'integer', 'description': '信用评分', 'range': [300, 850]},
                {'name': 'account_balance', 'type': 'float', 'description': '账户余额', 'range': [0, 1000000]},
                {'name': 'loan_amount', 'type': 'float', 'description': '贷款金额', 'range': [0, 500000]},
                {'name': 'register_date', 'type': 'date', 'description': '注册日期'}
            ],
            'sample_data': [
                {'customer_id': 'C001', 'name': '张三', 'age': 35, 'gender': '男', 'income': 120000, 'credit_score': 720, 'account_balance': 50000, 'loan_amount': 200000, 'register_date': '2020-01-15'},
                {'customer_id': 'C002', 'name': '李四', 'age': 28, 'gender': '女', 'income': 80000, 'credit_score': 680, 'account_balance': 30000, 'loan_amount': 0, 'register_date': '2021-03-20'},
                {'customer_id': 'C003', 'name': '王五', 'age': 42, 'gender': '男', 'income': 150000, 'credit_score': 750, 'account_balance': 80000, 'loan_amount': 300000, 'register_date': '2019-05-10'},
                {'customer_id': 'C004', 'name': '赵六', 'age': 31, 'gender': '女', 'income': 95000, 'credit_score': 690, 'account_balance': 40000, 'loan_amount': 150000, 'register_date': '2021-08-25'},
                {'customer_id': 'C005', 'name': '孙七', 'age': 45, 'gender': '男', 'income': 180000, 'credit_score': 780, 'account_balance': 120000, 'loan_amount': 400000, 'register_date': '2018-11-30'},
                {'customer_id': 'C006', 'name': '周八', 'age': 26, 'gender': '女', 'income': 70000, 'credit_score': 650, 'account_balance': 25000, 'loan_amount': 100000, 'register_date': '2022-02-14'},
                {'customer_id': 'C007', 'name': '吴九', 'age': 38, 'gender': '男', 'income': 130000, 'credit_score': 710, 'account_balance': 60000, 'loan_amount': 250000, 'register_date': '2020-07-08'},
                {'customer_id': 'C008', 'name': '郑十', 'age': 29, 'gender': '女', 'income': 85000, 'credit_score': 670, 'account_balance': 35000, 'loan_amount': 120000, 'register_date': '2021-12-05'},
                {'customer_id': 'C009', 'name': '钱一', 'age': 50, 'gender': '男', 'income': 200000, 'credit_score': 800, 'account_balance': 150000, 'loan_amount': 500000, 'register_date': '2017-09-12'},
                {'customer_id': 'C010', 'name': '孙二', 'age': 33, 'gender': '女', 'income': 110000, 'credit_score': 700, 'account_balance': 55000, 'loan_amount': 180000, 'register_date': '2020-04-18'}
            ]
        },
        2: {
            'id': 2,
            'name': '话单模板',
            'category': '通信',
            'fields': [
                {'name': 'call_id', 'type': 'string', 'description': '通话ID'},
                {'name': 'caller_number', 'type': 'string', 'description': '主叫号码'},
                {'name': 'callee_number', 'type': 'string', 'description': '被叫号码'},
                {'name': 'call_type', 'type': 'string', 'description': '通话类型'},
                {'name': 'call_duration', 'type': 'integer', 'description': '通话时长（秒）', 'range': [0, 3600]},
                {'name': 'base_station_id', 'type': 'string', 'description': '基站ID'},
                {'name': 'call_time', 'type': 'date', 'description': '通话时间'},
                {'name': 'location', 'type': 'string', 'description': '通话地点'},
                {'name': 'cost', 'type': 'float', 'description': '通话费用', 'range': [0, 100]}
            ],
            'sample_data': [
                {'call_id': 'CALL001', 'caller_number': '13800138000', 'callee_number': '13900139000', 'call_type': '语音', 'call_duration': 120, 'base_station_id': 'BS001', 'call_time': '2025-01-18', 'location': '北京市', 'cost': 0.5},
                {'call_id': 'CALL002', 'caller_number': '13800138001', 'callee_number': '13900139001', 'call_type': '视频', 'call_duration': 300, 'base_station_id': 'BS002', 'call_time': '2025-01-19', 'location': '上海市', 'cost': 2.0},
                {'call_id': 'CALL003', 'caller_number': '13800138002', 'callee_number': '13900139002', 'call_type': '语音', 'call_duration': 180, 'base_station_id': 'BS003', 'call_time': '2025-01-20', 'location': '广州市', 'cost': 1.0},
                {'call_id': 'CALL004', 'caller_number': '13800138003', 'callee_number': '13900139003', 'call_type': '视频', 'call_duration': 450, 'base_station_id': 'BS001', 'call_time': '2025-01-21', 'location': '深圳市', 'cost': 3.0},
                {'call_id': 'CALL005', 'caller_number': '13800138004', 'callee_number': '13900139004', 'call_type': '语音', 'call_duration': 90, 'base_station_id': 'BS004', 'call_time': '2025-01-22', 'location': '杭州市', 'cost': 0.8},
                {'call_id': 'CALL006', 'caller_number': '13800138005', 'callee_number': '13900139005', 'call_type': '视频', 'call_duration': 600, 'base_station_id': 'BS002', 'call_time': '2025-01-23', 'location': '成都市', 'cost': 4.0},
                {'call_id': 'CALL007', 'caller_number': '13800138006', 'callee_number': '13900139006', 'call_type': '语音', 'call_duration': 240, 'base_station_id': 'BS005', 'call_time': '2025-01-24', 'location': '武汉市', 'cost': 1.5},
                {'call_id': 'CALL008', 'caller_number': '13800138007', 'callee_number': '13900139007', 'call_type': '视频', 'call_duration': 360, 'base_station_id': 'BS003', 'call_time': '2025-01-25', 'location': '西安市', 'cost': 2.5},
                {'call_id': 'CALL009', 'caller_number': '13800138008', 'callee_number': '13900139008', 'call_type': '语音', 'call_duration': 150, 'base_station_id': 'BS001', 'call_time': '2025-01-26', 'location': '南京市', 'cost': 1.2},
                {'call_id': 'CALL010', 'caller_number': '13800138009', 'callee_number': '13900139009', 'call_type': '视频', 'call_duration': 480, 'base_station_id': 'BS004', 'call_time': '2025-01-27', 'location': '重庆市', 'cost': 3.5}
            ]
        },
        3: {
            'id': 3,
            'name': '门店销售模板',
            'category': '零售',
            'fields': [
                {'name': 'order_id', 'type': 'string', 'description': '订单ID'},
                {'name': 'product_id', 'type': 'string', 'description': '商品ID'},
                {'name': 'product_name', 'type': 'string', 'description': '商品名称'},
                {'name': 'category', 'type': 'string', 'description': '商品分类'},
                {'name': 'quantity', 'type': 'integer', 'description': '数量', 'range': [1, 100]},
                {'name': 'unit_price', 'type': 'float', 'description': '单价', 'range': [1, 10000]},
                {'name': 'total_amount', 'type': 'float', 'description': '总金额', 'range': [1, 100000]},
                {'name': 'customer_id', 'type': 'string', 'description': '客户ID'},
                {'name': 'store_id', 'type': 'string', 'description': '门店ID'},
                {'name': 'sale_date', 'type': 'date', 'description': '销售日期'}
            ],
            'sample_data': [
                {'order_id': 'ORD001', 'product_id': 'P001', 'product_name': 'iPhone 15', 'category': '电子产品', 'quantity': 1, 'unit_price': 5999, 'total_amount': 5999, 'customer_id': 'C001', 'store_id': 'S001', 'sale_date': '2025-01-18'},
                {'order_id': 'ORD002', 'product_id': 'P002', 'product_name': 'MacBook Pro', 'category': '电子产品', 'quantity': 1, 'unit_price': 12999, 'total_amount': 12999, 'customer_id': 'C002', 'store_id': 'S001', 'sale_date': '2025-01-19'},
                {'order_id': 'ORD003', 'product_id': 'P003', 'product_name': 'iPad Air', 'category': '电子产品', 'quantity': 2, 'unit_price': 4599, 'total_amount': 9198, 'customer_id': 'C003', 'store_id': 'S002', 'sale_date': '2025-01-20'},
                {'order_id': 'ORD004', 'product_id': 'P004', 'product_name': 'AirPods Pro', 'category': '电子产品', 'quantity': 3, 'unit_price': 1899, 'total_amount': 5697, 'customer_id': 'C004', 'store_id': 'S001', 'sale_date': '2025-01-21'},
                {'order_id': 'ORD005', 'product_id': 'P005', 'product_name': 'Apple Watch', 'category': '电子产品', 'quantity': 1, 'unit_price': 2999, 'total_amount': 2999, 'customer_id': 'C005', 'store_id': 'S003', 'sale_date': '2025-01-22'},
                {'order_id': 'ORD006', 'product_id': 'P006', 'product_name': '华为Mate60', 'category': '电子产品', 'quantity': 1, 'unit_price': 6999, 'total_amount': 6999, 'customer_id': 'C006', 'store_id': 'S002', 'sale_date': '2025-01-23'},
                {'order_id': 'ORD007', 'product_id': 'P007', 'product_name': '小米14', 'category': '电子产品', 'quantity': 2, 'unit_price': 3999, 'total_amount': 7998, 'customer_id': 'C007', 'store_id': 'S001', 'sale_date': '2025-01-24'},
                {'order_id': 'ORD008', 'product_id': 'P008', 'product_name': '联想ThinkPad', 'category': '电子产品', 'quantity': 1, 'unit_price': 8999, 'total_amount': 8999, 'customer_id': 'C008', 'store_id': 'S003', 'sale_date': '2025-01-25'},
                {'order_id': 'ORD009', 'product_id': 'P009', 'product_name': '戴尔XPS', 'category': '电子产品', 'quantity': 1, 'unit_price': 10999, 'total_amount': 10999, 'customer_id': 'C009', 'store_id': 'S002', 'sale_date': '2025-01-26'},
                {'order_id': 'ORD010', 'product_id': 'P010', 'product_name': 'Surface Pro', 'category': '电子产品', 'quantity': 1, 'unit_price': 7999, 'total_amount': 7999, 'customer_id': 'C010', 'store_id': 'S001', 'sale_date': '2025-01-27'}
            ]
        },
        4: {
            'id': 4,
            'name': '电商订单模板',
            'category': '零售',
            'fields': [
                {'name': 'order_id', 'type': 'string', 'description': '订单号'},
                {'name': 'user_id', 'type': 'string', 'description': '用户ID'},
                {'name': 'product_id', 'type': 'string', 'description': '商品ID'},
                {'name': 'product_name', 'type': 'string', 'description': '商品名称'},
                {'name': 'quantity', 'type': 'integer', 'description': '购买数量', 'range': [1, 50]},
                {'name': 'price', 'type': 'float', 'description': '商品价格', 'range': [1, 50000]},
                {'name': 'discount', 'type': 'float', 'description': '折扣', 'range': [0, 1]},
                {'name': 'payment_method', 'type': 'string', 'description': '支付方式'},
                {'name': 'shipping_address', 'type': 'string', 'description': '收货地址'},
                {'name': 'order_status', 'type': 'string', 'description': '订单状态'},
                {'name': 'order_time', 'type': 'date', 'description': '下单时间'}
            ],
            'sample_data': [
                {'order_id': 'E001', 'user_id': 'U001', 'product_id': 'P001', 'product_name': '商品A', 'quantity': 2, 'price': 199, 'discount': 0.9, 'payment_method': '支付宝', 'shipping_address': '北京市朝阳区', 'order_status': '已发货', 'order_time': '2025-01-18'},
                {'order_id': 'E002', 'user_id': 'U002', 'product_id': 'P002', 'product_name': '商品B', 'quantity': 1, 'price': 299, 'discount': 0.95, 'payment_method': '微信支付', 'shipping_address': '上海市浦东新区', 'order_status': '待发货', 'order_time': '2025-01-19'},
                {'order_id': 'E003', 'user_id': 'U003', 'product_id': 'P003', 'product_name': '商品C', 'quantity': 3, 'price': 99, 'discount': 0.8, 'payment_method': '银行卡', 'shipping_address': '广州市天河区', 'order_status': '已发货', 'order_time': '2025-01-20'},
                {'order_id': 'E004', 'user_id': 'U004', 'product_id': 'P004', 'product_name': '商品D', 'quantity': 1, 'price': 599, 'discount': 1.0, 'payment_method': '支付宝', 'shipping_address': '深圳市南山区', 'order_status': '已完成', 'order_time': '2025-01-21'},
                {'order_id': 'E005', 'user_id': 'U005', 'product_id': 'P005', 'product_name': '商品E', 'quantity': 2, 'price': 399, 'discount': 0.85, 'payment_method': '微信支付', 'shipping_address': '杭州市西湖区', 'order_status': '已发货', 'order_time': '2025-01-22'},
                {'order_id': 'E006', 'user_id': 'U006', 'product_id': 'P006', 'product_name': '商品F', 'quantity': 1, 'price': 899, 'discount': 0.9, 'payment_method': '银行卡', 'shipping_address': '成都市锦江区', 'order_status': '待发货', 'order_time': '2025-01-23'},
                {'order_id': 'E007', 'user_id': 'U007', 'product_id': 'P007', 'product_name': '商品G', 'quantity': 4, 'price': 149, 'discount': 0.75, 'payment_method': '支付宝', 'shipping_address': '武汉市江汉区', 'order_status': '已发货', 'order_time': '2025-01-24'},
                {'order_id': 'E008', 'user_id': 'U008', 'product_id': 'P008', 'product_name': '商品H', 'quantity': 1, 'price': 1299, 'discount': 0.95, 'payment_method': '微信支付', 'shipping_address': '西安市雁塔区', 'order_status': '已完成', 'order_time': '2025-01-25'},
                {'order_id': 'E009', 'user_id': 'U009', 'product_id': 'P009', 'product_name': '商品I', 'quantity': 2, 'price': 499, 'discount': 0.88, 'payment_method': '银行卡', 'shipping_address': '南京市鼓楼区', 'order_status': '已发货', 'order_time': '2025-01-26'},
                {'order_id': 'E010', 'user_id': 'U010', 'product_id': 'P010', 'product_name': '商品J', 'quantity': 1, 'price': 699, 'discount': 0.92, 'payment_method': '支付宝', 'shipping_address': '重庆市渝中区', 'order_status': '待发货', 'order_time': '2025-01-27'}
            ]
        },
        5: {
            'id': 5,
            'name': '患者信息模板',
            'category': '医疗',
            'fields': [
                {'name': 'patient_id', 'type': 'string', 'description': '患者ID'},
                {'name': 'name', 'type': 'string', 'description': '患者姓名'},
                {'name': 'age', 'type': 'integer', 'description': '年龄', 'range': [0, 120]},
                {'name': 'gender', 'type': 'string', 'description': '性别'},
                {'name': 'diagnosis', 'type': 'string', 'description': '诊断结果'},
                {'name': 'symptoms', 'type': 'string', 'description': '症状描述'},
                {'name': 'medication', 'type': 'string', 'description': '用药信息'},
                {'name': 'temperature', 'type': 'float', 'description': '体温', 'range': [35.0, 42.0]},
                {'name': 'blood_pressure', 'type': 'string', 'description': '血压'},
                {'name': 'visit_date', 'type': 'date', 'description': '就诊日期'}
            ],
            'sample_data': [
                {'patient_id': 'P001', 'name': '患者A', 'age': 45, 'gender': '男', 'diagnosis': '感冒', 'symptoms': '咳嗽、发热', 'medication': '感冒药', 'temperature': 37.5, 'blood_pressure': '120/80', 'visit_date': '2025-01-18'},
                {'patient_id': 'P002', 'name': '患者B', 'age': 32, 'gender': '女', 'diagnosis': '胃炎', 'symptoms': '胃痛、恶心', 'medication': '胃药', 'temperature': 36.8, 'blood_pressure': '110/70', 'visit_date': '2025-01-19'},
                {'patient_id': 'P003', 'name': '患者C', 'age': 58, 'gender': '男', 'diagnosis': '高血压', 'symptoms': '头晕、乏力', 'medication': '降压药', 'temperature': 36.9, 'blood_pressure': '150/95', 'visit_date': '2025-01-20'},
                {'patient_id': 'P004', 'name': '患者D', 'age': 28, 'gender': '女', 'diagnosis': '过敏', 'symptoms': '皮疹、瘙痒', 'medication': '抗过敏药', 'temperature': 37.0, 'blood_pressure': '105/65', 'visit_date': '2025-01-21'},
                {'patient_id': 'P005', 'name': '患者E', 'age': 65, 'gender': '男', 'diagnosis': '糖尿病', 'symptoms': '多饮、多尿', 'medication': '降糖药', 'temperature': 36.7, 'blood_pressure': '130/85', 'visit_date': '2025-01-22'},
                {'patient_id': 'P006', 'name': '患者F', 'age': 41, 'gender': '女', 'diagnosis': '头痛', 'symptoms': '持续性头痛', 'medication': '止痛药', 'temperature': 36.8, 'blood_pressure': '115/75', 'visit_date': '2025-01-23'},
                {'patient_id': 'P007', 'name': '患者G', 'age': 52, 'gender': '男', 'diagnosis': '关节炎', 'symptoms': '关节疼痛', 'medication': '消炎药', 'temperature': 37.1, 'blood_pressure': '125/80', 'visit_date': '2025-01-24'},
                {'patient_id': 'P008', 'name': '患者H', 'age': 35, 'gender': '女', 'diagnosis': '失眠', 'symptoms': '入睡困难', 'medication': '安眠药', 'temperature': 36.6, 'blood_pressure': '108/68', 'visit_date': '2025-01-25'},
                {'patient_id': 'P009', 'name': '患者I', 'age': 48, 'gender': '男', 'diagnosis': '支气管炎', 'symptoms': '咳嗽、胸闷', 'medication': '止咳药', 'temperature': 37.3, 'blood_pressure': '118/78', 'visit_date': '2025-01-26'},
                {'patient_id': 'P010', 'name': '患者J', 'age': 29, 'gender': '女', 'diagnosis': '月经不调', 'symptoms': '周期紊乱', 'medication': '调经药', 'temperature': 36.9, 'blood_pressure': '112/72', 'visit_date': '2025-01-27'}
            ]
        },
        6: {
            'id': 6,
            'name': '学生信息模板',
            'category': '教育',
            'fields': [
                {'name': 'student_id', 'type': 'string', 'description': '学生ID'},
                {'name': 'name', 'type': 'string', 'description': '学生姓名'},
                {'name': 'age', 'type': 'integer', 'description': '年龄', 'range': [6, 25]},
                {'name': 'grade', 'type': 'string', 'description': '年级'},
                {'name': 'class', 'type': 'string', 'description': '班级'},
                {'name': 'subject', 'type': 'string', 'description': '科目'},
                {'name': 'score', 'type': 'float', 'description': '成绩', 'range': [0, 100]},
                {'name': 'attendance_rate', 'type': 'float', 'description': '出勤率', 'range': [0, 1]},
                {'name': 'exam_date', 'type': 'date', 'description': '考试日期'}
            ],
            'sample_data': [
                {'student_id': 'S001', 'name': '学生A', 'age': 15, 'grade': '初三', 'class': '3班', 'subject': '数学', 'score': 85, 'attendance_rate': 0.95, 'exam_date': '2025-01-18'},
                {'student_id': 'S002', 'name': '学生B', 'age': 16, 'grade': '高一', 'class': '1班', 'subject': '语文', 'score': 92, 'attendance_rate': 0.98, 'exam_date': '2025-01-19'},
                {'student_id': 'S003', 'name': '学生C', 'age': 14, 'grade': '初二', 'class': '2班', 'subject': '英语', 'score': 78, 'attendance_rate': 0.90, 'exam_date': '2025-01-20'},
                {'student_id': 'S004', 'name': '学生D', 'age': 17, 'grade': '高二', 'class': '5班', 'subject': '物理', 'score': 88, 'attendance_rate': 0.96, 'exam_date': '2025-01-21'},
                {'student_id': 'S005', 'name': '学生E', 'age': 15, 'grade': '初三', 'class': '4班', 'subject': '化学', 'score': 75, 'attendance_rate': 0.92, 'exam_date': '2025-01-22'},
                {'student_id': 'S006', 'name': '学生F', 'age': 16, 'grade': '高一', 'class': '2班', 'subject': '生物', 'score': 90, 'attendance_rate': 0.97, 'exam_date': '2025-01-23'},
                {'student_id': 'S007', 'name': '学生G', 'age': 14, 'grade': '初二', 'class': '1班', 'subject': '历史', 'score': 82, 'attendance_rate': 0.94, 'exam_date': '2025-01-24'},
                {'student_id': 'S008', 'name': '学生H', 'age': 17, 'grade': '高二', 'class': '3班', 'subject': '地理', 'score': 79, 'attendance_rate': 0.91, 'exam_date': '2025-01-25'},
                {'student_id': 'S009', 'name': '学生I', 'age': 15, 'grade': '初三', 'class': '5班', 'subject': '政治', 'score': 86, 'attendance_rate': 0.93, 'exam_date': '2025-01-26'},
                {'student_id': 'S010', 'name': '学生J', 'age': 16, 'grade': '高一', 'class': '4班', 'subject': '体育', 'score': 95, 'attendance_rate': 0.99, 'exam_date': '2025-01-27'}
            ]
        },
        7: {
            'id': 7,
            'name': '保险理赔模板',
            'category': '金融',
            'fields': [
                {'name': 'claim_id', 'type': 'string', 'description': '理赔ID'},
                {'name': 'policy_id', 'type': 'string', 'description': '保单号'},
                {'name': 'customer_id', 'type': 'string', 'description': '客户ID'},
                {'name': 'claim_type', 'type': 'string', 'description': '理赔类型'},
                {'name': 'claim_amount', 'type': 'float', 'description': '理赔金额', 'range': [100, 1000000]},
                {'name': 'accident_date', 'type': 'date', 'description': '事故日期'},
                {'name': 'claim_date', 'type': 'date', 'description': '申请日期'},
                {'name': 'status', 'type': 'string', 'description': '理赔状态'},
                {'name': 'approval_time', 'type': 'integer', 'description': '审核时长（天）', 'range': [1, 90]}
            ],
            'sample_data': [
                {'claim_id': 'CLM001', 'policy_id': 'POL001', 'customer_id': 'C001', 'claim_type': '医疗', 'claim_amount': 5000, 'accident_date': '2025-01-10', 'claim_date': '2025-01-15', 'status': '已审核', 'approval_time': 5},
                {'claim_id': 'CLM002', 'policy_id': 'POL002', 'customer_id': 'C002', 'claim_type': '意外', 'claim_amount': 12000, 'accident_date': '2025-01-12', 'claim_date': '2025-01-18', 'status': '已审核', 'approval_time': 6},
                {'claim_id': 'CLM003', 'policy_id': 'POL003', 'customer_id': 'C003', 'claim_type': '医疗', 'claim_amount': 8000, 'accident_date': '2025-01-08', 'claim_date': '2025-01-14', 'status': '审核中', 'approval_time': 6},
                {'claim_id': 'CLM004', 'policy_id': 'POL004', 'customer_id': 'C004', 'claim_type': '财产', 'claim_amount': 25000, 'accident_date': '2025-01-05', 'claim_date': '2025-01-12', 'status': '已审核', 'approval_time': 7},
                {'claim_id': 'CLM005', 'policy_id': 'POL005', 'customer_id': 'C005', 'claim_type': '医疗', 'claim_amount': 3500, 'accident_date': '2025-01-15', 'claim_date': '2025-01-20', 'status': '已审核', 'approval_time': 5},
                {'claim_id': 'CLM006', 'policy_id': 'POL006', 'customer_id': 'C006', 'claim_type': '意外', 'claim_amount': 15000, 'accident_date': '2025-01-11', 'claim_date': '2025-01-17', 'status': '审核中', 'approval_time': 6},
                {'claim_id': 'CLM007', 'policy_id': 'POL007', 'customer_id': 'C007', 'claim_type': '医疗', 'claim_amount': 6000, 'accident_date': '2025-01-09', 'claim_date': '2025-01-16', 'status': '已审核', 'approval_time': 7},
                {'claim_id': 'CLM008', 'policy_id': 'POL008', 'customer_id': 'C008', 'claim_type': '财产', 'claim_amount': 18000, 'accident_date': '2025-01-07', 'claim_date': '2025-01-13', 'status': '已审核', 'approval_time': 6},
                {'claim_id': 'CLM009', 'policy_id': 'POL009', 'customer_id': 'C009', 'claim_type': '医疗', 'claim_amount': 4200, 'accident_date': '2025-01-13', 'claim_date': '2025-01-19', 'status': '审核中', 'approval_time': 6},
                {'claim_id': 'CLM010', 'policy_id': 'POL010', 'customer_id': 'C010', 'claim_type': '意外', 'claim_amount': 9800, 'accident_date': '2025-01-14', 'claim_date': '2025-01-21', 'status': '已审核', 'approval_time': 7}
            ]
        },
        8: {
            'id': 8,
            'name': '物流配送模板',
            'category': '物流',
            'fields': [
                {'name': 'shipment_id', 'type': 'string', 'description': '运单号'},
                {'name': 'order_id', 'type': 'string', 'description': '订单ID'},
                {'name': 'sender_address', 'type': 'string', 'description': '发货地址'},
                {'name': 'receiver_address', 'type': 'string', 'description': '收货地址'},
                {'name': 'weight', 'type': 'float', 'description': '重量（kg）', 'range': [0.1, 100]},
                {'name': 'distance', 'type': 'float', 'description': '距离（km）', 'range': [1, 5000]},
                {'name': 'shipping_fee', 'type': 'float', 'description': '运费', 'range': [5, 500]},
                {'name': 'status', 'type': 'string', 'description': '配送状态'},
                {'name': 'ship_date', 'type': 'date', 'description': '发货日期'},
                {'name': 'delivery_date', 'type': 'date', 'description': '送达日期'}
            ],
            'sample_data': [
                {'shipment_id': 'SHIP001', 'order_id': 'ORD001', 'sender_address': '北京市', 'receiver_address': '上海市', 'weight': 2.5, 'distance': 1200, 'shipping_fee': 25, 'status': '运输中', 'ship_date': '2025-01-18', 'delivery_date': '2025-01-20'},
                {'shipment_id': 'SHIP002', 'order_id': 'ORD002', 'sender_address': '广州市', 'receiver_address': '深圳市', 'weight': 1.8, 'distance': 150, 'shipping_fee': 15, 'status': '已送达', 'ship_date': '2025-01-19', 'delivery_date': '2025-01-20'},
                {'shipment_id': 'SHIP003', 'order_id': 'ORD003', 'sender_address': '上海市', 'receiver_address': '杭州市', 'weight': 3.2, 'distance': 200, 'shipping_fee': 18, 'status': '运输中', 'ship_date': '2025-01-20', 'delivery_date': '2025-01-22'},
                {'shipment_id': 'SHIP004', 'order_id': 'ORD004', 'sender_address': '成都市', 'receiver_address': '重庆市', 'weight': 1.5, 'distance': 300, 'shipping_fee': 12, 'status': '已送达', 'ship_date': '2025-01-21', 'delivery_date': '2025-01-22'},
                {'shipment_id': 'SHIP005', 'order_id': 'ORD005', 'sender_address': '北京市', 'receiver_address': '天津市', 'weight': 4.0, 'distance': 120, 'shipping_fee': 20, 'status': '运输中', 'ship_date': '2025-01-22', 'delivery_date': '2025-01-23'},
                {'shipment_id': 'SHIP006', 'order_id': 'ORD006', 'sender_address': '武汉市', 'receiver_address': '长沙市', 'weight': 2.0, 'distance': 350, 'shipping_fee': 22, 'status': '已送达', 'ship_date': '2025-01-23', 'delivery_date': '2025-01-24'},
                {'shipment_id': 'SHIP007', 'order_id': 'ORD007', 'sender_address': '西安市', 'receiver_address': '兰州市', 'weight': 3.5, 'distance': 650, 'shipping_fee': 35, 'status': '运输中', 'ship_date': '2025-01-24', 'delivery_date': '2025-01-26'},
                {'shipment_id': 'SHIP008', 'order_id': 'ORD008', 'sender_address': '南京市', 'receiver_address': '苏州市', 'weight': 1.2, 'distance': 100, 'shipping_fee': 10, 'status': '已送达', 'ship_date': '2025-01-25', 'delivery_date': '2025-01-26'},
                {'shipment_id': 'SHIP009', 'order_id': 'ORD009', 'sender_address': '杭州市', 'receiver_address': '宁波市', 'weight': 2.8, 'distance': 150, 'shipping_fee': 16, 'status': '运输中', 'ship_date': '2025-01-26', 'delivery_date': '2025-01-27'},
                {'shipment_id': 'SHIP010', 'order_id': 'ORD010', 'sender_address': '深圳市', 'receiver_address': '东莞市', 'weight': 1.0, 'distance': 80, 'shipping_fee': 8, 'status': '已送达', 'ship_date': '2025-01-27', 'delivery_date': '2025-01-28'}
            ]
        }
    }
    
    template = templates_data.get(template_id)
    if not template:
        return jsonify({
            'success': False,
            'error': '模板不存在',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404
    
    return jsonify({
        'success': True,
        'data': {'template': template}
    }), 200

@synthetic_bp.route('/tasks/<task_id>', methods=['GET'])
@login_required
def get_task_status(task_id):
    """查询任务状态"""
    try:
        from flask_login import current_user
        # 支持 task_123 或 123 格式
        if task_id.startswith('task_'):
            task_id_int = int(task_id.replace('task_', ''))
        else:
            task_id_int = int(task_id)
        
        task = Task.query.get(task_id_int)
        if not task:
            return jsonify({
                'success': False,
                'error': '任务不存在',
                'code': 'RESOURCE_NOT_FOUND'
            }), 404
        
        if task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': '无权限访问此任务',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        task_dict = task.to_dict()
        # 确保包含进度信息
        if 'progress' not in task_dict:
            task_dict['progress'] = task.progress or 0
        if 'message' not in task_dict:
            status_messages = {
                'pending': '等待处理',
                'running': '正在生成数据...',
                'completed': '生成完成',
                'failed': '生成失败'
            }
            task_dict['message'] = status_messages.get(task.status, '未知状态')
        
        # 确保错误信息字段存在（兼容error和error_message）
        if task.status == 'failed':
            if 'error' not in task_dict and task_dict.get('error_message'):
                task_dict['error'] = task_dict['error_message']
            if 'error_message' not in task_dict and task_dict.get('error'):
                task_dict['error_message'] = task_dict['error']
        
        return jsonify({
            'success': True,
            'data': task_dict
        }), 200
    except ValueError:
        return jsonify({
            'success': False,
            'error': '无效的任务ID',
            'code': 'INVALID_PARAMS'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'查询任务状态失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@synthetic_bp.route('/tasks/<task_id>/view', methods=['GET'])
@login_required
def view_result(task_id):
    """查看生成结果页面（HTML）"""
    try:
        from flask_login import current_user
        
        # 支持 task_123 或 123 格式
        if task_id.startswith('task_'):
            task_id_int = int(task_id.replace('task_', ''))
        else:
            task_id_int = int(task_id)
        
        task = Task.query.get(task_id_int)
        if not task:
            return jsonify({
                'success': False,
                'error': '任务不存在',
                'code': 'RESOURCE_NOT_FOUND'
            }), 404
        
        if task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': '无权限访问此任务',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        if task.status != 'completed':
            return jsonify({
                'success': False,
                'error': f'任务尚未完成，当前状态: {task.status}',
                'code': 'INVALID_PARAMS'
            }), 400
        
        return render_template('result_view.html', task_id=task_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': '无效的任务ID',
            'code': 'INVALID_PARAMS'
        }), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'加载页面失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@synthetic_bp.route('/tasks/<task_id>/preview', methods=['GET'])
@login_required
def get_preview(task_id):
    """获取生成结果预览"""
    try:
        from flask_login import current_user
        # 支持 task_123 或 123 格式
        if task_id.startswith('task_'):
            task_id_int = int(task_id.replace('task_', ''))
        else:
            task_id_int = int(task_id)
        
        task = Task.query.get(task_id_int)
        if not task:
            return jsonify({
                'success': False,
                'error': '任务不存在',
                'code': 'RESOURCE_NOT_FOUND'
            }), 404
        
        if task.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': '无权限访问此任务',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        if task.status != 'completed':
            return jsonify({
                'success': False,
                'error': f'任务尚未完成，当前状态: {task.status}',
                'code': 'INVALID_PARAMS'
            }), 400
        
        data_type = request.args.get('type', 'synthetic')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 验证分页参数
        if page < 1:
            page = 1
        # 允许更大的分页大小，以便查看完整数据（最大1000行）
        if page_size < 1:
            page_size = 20
        elif page_size > 1000:
            page_size = 1000
        
        service = SyntheticService()
        preview = service.get_result_preview(task_id_int, data_type, page, page_size)
        
        if not preview:
            return jsonify({
                'success': False,
                'error': '无法获取预览数据，请检查结果文件是否存在',
                'code': 'RESOURCE_NOT_FOUND'
            }), 404
        
        return jsonify({
            'success': True,
            'data': preview
        }), 200
    except ValueError:
        return jsonify({
            'success': False,
            'error': '无效的任务ID',
            'code': 'INVALID_PARAMS'
        }), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'获取预览失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@synthetic_bp.route('/tasks/<task_id>/download', methods=['GET'])
@login_required
def download_result(task_id):
    """下载生成结果"""
    from flask_login import current_user
    import zipfile
    import shutil
    
    # 支持 task_123 或 123 格式
    if task_id.startswith('task_'):
        task_id = int(task_id.replace('task_', ''))
    else:
        task_id = int(task_id)
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({
            'success': False,
            'error': '无权限访问此任务',
            'code': 'PERMISSION_DENIED'
        }), 403
    
    if task.status != 'completed':
        return jsonify({
            'success': False,
            'error': '任务尚未完成',
            'code': 'INVALID_PARAMS'
        }), 400
    
    data_type = request.args.get('type', 'synthetic')
    format_type = request.args.get('format', 'csv')
    
    service = SyntheticService()
    file_path = service.get_result_file_path(task_id, data_type, format_type)
    
    if not file_path:
        return jsonify({
            'success': False,
            'error': '文件不存在',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404
    
    if data_type == 'both':
        # 打包两个文件
        zip_path = file_path + '.zip'
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(os.path.join(file_path, 'original.csv'), 'original.csv')
            zipf.write(os.path.join(file_path, 'synthetic.csv'), 'synthetic.csv')
        return send_file(zip_path, as_attachment=True, download_name=f'task_{task_id}_results.zip')
    else:
        return send_file(file_path, as_attachment=True, download_name=f'task_{task_id}_{data_type}.{format_type}')

# ==================== SDG模型配置接口 ====================

@synthetic_bp.route('/sdg-models', methods=['GET'])
@login_required
def get_sdg_models():
    """获取系统配置的SDG模型列表（所有用户可用）"""
    try:
        # 从系统配置获取SDG模型列表
        config = SystemConfig.query.filter_by(config_key='sdg_models').first()
        
        # 默认支持的SDG模型（参数定义与SDGX源码保持一致）
        default_models = [
            {
                'id': 'ctgan',
                'name': 'CTGAN',
                'description': 'Conditional Tabular GAN - 适用于复杂表格数据生成',
                'enabled': True,
                'parameters': {
                    'epochs': {'type': 'number', 'default': 300, 'min': 1, 'max': 1000, 'description': '训练轮数'},
                    'batch_size': {'type': 'number', 'default': 500, 'min': 32, 'max': 2000, 'description': '批次大小（必须为偶数）'},
                    'generator_lr': {'type': 'number', 'default': 2e-4, 'min': 1e-6, 'max': 1e-2, 'step': 1e-6, 'description': '生成器学习率'},
                    'discriminator_lr': {'type': 'number', 'default': 2e-4, 'min': 1e-6, 'max': 1e-2, 'step': 1e-6, 'description': '判别器学习率'},
                    'generator_decay': {'type': 'number', 'default': 1e-6, 'min': 0, 'max': 1e-3, 'step': 1e-6, 'description': '生成器权重衰减率'},
                    'discriminator_decay': {'type': 'number', 'default': 1e-6, 'min': 0, 'max': 1e-3, 'step': 1e-6, 'description': '判别器权重衰减率'},
                    'embedding_dim': {'type': 'number', 'default': 128, 'min': 32, 'max': 512, 'description': '嵌入维度（随机样本大小）'},
                    'generator_dim': {'type': 'array', 'default': [256, 256], 'description': '生成器网络维度（用逗号分隔，如：256,256）'},
                    'discriminator_dim': {'type': 'array', 'default': [256, 256], 'description': '判别器网络维度（用逗号分隔，如：256,256）'},
                    'discriminator_steps': {'type': 'number', 'default': 1, 'min': 1, 'max': 10, 'description': '判别器更新步数（每个生成器更新对应的判别器更新次数）'},
                    'pac': {'type': 'number', 'default': 10, 'min': 1, 'max': 20, 'description': 'PAC参数（应用判别器时分组样本数）'},
                    'log_frequency': {'type': 'boolean', 'default': True, 'description': '使用分类级别的对数频率进行条件采样'},
                    'device': {
                        'type': 'string', 
                        'default': 'auto', 
                        'description': '计算设备（auto/cuda/cpu，auto会自动检测CUDA）',
                        'options': ['auto', 'cuda', 'cpu']
                    }
                }
            },
            {
                'id': 'gaussian_copula',
                'name': 'Gaussian Copula',
                'description': '高斯Copula模型 - 适用于统计建模，速度快',
                'enabled': True,
                'parameters': {
                    'enforce_min_max_values': {'type': 'boolean', 'default': True, 'description': '强制最小最大值（将数值限制在训练时看到的最小最大值范围内）'},
                    'enforce_rounding': {'type': 'boolean', 'default': True, 'description': '强制四舍五入（按原始数据的舍入方式处理数值列）'},
                    'default_distribution': {
                        'type': 'string', 
                        'default': 'beta', 
                        'description': '默认数值分布类型',
                        'options': ['norm', 'beta', 'truncnorm', 'uniform', 'gamma', 'gaussian_kde']
                    },
                    'locales': {
                        'type': 'string',
                        'default': '',
                        'description': '本地化设置（用于PII数据匿名化，如：zh_CN, en_US，多个用逗号分隔）',
                        'placeholder': '留空使用默认，示例：zh_CN 或 zh_CN,en_US'
                    },
                    'numerical_distributions': {
                        'type': 'string',
                        'default': '',
                        'description': '字段特定分布配置（JSON格式，为特定字段指定分布类型，如：{"age": "truncnorm", "income": "gamma"}）',
                        'placeholder': '留空使用默认分布，示例：{"age": "truncnorm", "income": "gamma"}'
                    }
                }
            }
        ]
        
        # 注意：AI大模型（如通义千问、Ollama等）的参数定义在系统设置中配置
        # 当选择AI大模型时，使用SDGX的SingleTableGPTModel，参数包括：
        # - api_key: 从系统设置获取
        # - endpoint: 从系统设置获取
        # - selected_model: 从系统设置获取选中的模型名称
        # - temperature: 控制随机性（0-2，默认0.1）
        # - max_tokens: 最大token数（默认4000）
        # - timeout: 超时时间（秒，默认90）
        # - query_batch: 每次查询的样本数（默认30）
        # - prompt_template: 自定义提示词模板（可选）
        
        if config:
            config_value = config.get_value()
            models = config_value.get('models', default_models)
        else:
            models = default_models
        
        # 只返回启用的模型
        enabled_models = [m for m in models if m.get('enabled', True)]
        
        return jsonify({
            'success': True,
            'data': {'models': enabled_models}
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

# ==================== 参数模板接口 ====================

@synthetic_bp.route('/parameter-templates', methods=['GET'])
@login_required
def get_parameter_templates():
    """获取参数模板列表（系统模板+用户模板）"""
    try:
        model_type = request.args.get('model_type', 'ctgan')
        
        # 系统默认模板
        system_templates = {
            'ctgan': [
                {
                    'id': 'system_default',
                    'name': '默认配置（适用多类场景）',
                    'type': 'system',
                    'model_type': 'ctgan',
                    'parameters': {
                        'epochs': 300,
                        'batch_size': 500,
                        'generator_lr': 2e-4,
                        'discriminator_lr': 2e-4
                    },
                    'description': '推荐首选，平衡质量和速度，适合大多数数据生成场景'
                },
                {
                    'id': 'system_production',
                    'name': '生产环境仿真数据',
                    'type': 'system',
                    'model_type': 'ctgan',
                    'parameters': {
                        'epochs': 500,
                        'batch_size': 200,
                        'generator_lr': 0.00015,
                        'discriminator_lr': 0.00015
                    },
                    'description': '高质量配置，训练轮数多、批次小，适合生产环境生成高质量仿真数据'
                },
                {
                    'id': 'system_fast',
                    'name': '快速测试场景',
                    'type': 'system',
                    'model_type': 'ctgan',
                    'parameters': {
                        'epochs': 50,
                        'batch_size': 500,
                        'generator_lr': 0.00025,
                        'discriminator_lr': 0.00025
                    },
                    'description': '快速生成配置，训练轮数少，适合快速测试和原型验证'
                }
            ],
            'gaussian_copula': [
                {
                    'id': 'system_default',
                    'name': '默认配置（适用多类场景）',
                    'type': 'system',
                    'model_type': 'gaussian_copula',
                    'parameters': {
                        'enforce_min_max_values': True,
                        'enforce_rounding': True,
                        'default_distribution': 'beta'
                    },
                    'description': '推荐首选，Beta分布灵活适应多种数据特征，适合不确定数据分布时的通用场景'
                },
                {
                    'id': 'system_production',
                    'name': '生产环境仿真数据',
                    'type': 'system',
                    'model_type': 'gaussian_copula',
                    'parameters': {
                        'enforce_min_max_values': True,
                        'enforce_rounding': True,
                        'default_distribution': 'norm'
                    },
                    'description': '正态分布，统计特性稳定，适合生产环境生成高质量仿真数据'
                },
                {
                    'id': 'system_diversity_test',
                    'name': '数据多样化测试场景',
                    'type': 'system',
                    'model_type': 'gaussian_copula',
                    'parameters': {
                        'enforce_min_max_values': True,
                        'enforce_rounding': True,
                        'default_distribution': 'gaussian_kde'
                    },
                    'description': '高斯核密度估计，非参数方法，适合快速测试和复杂分布形状的数据'
                },
                {
                    'id': 'system_bounded_range',
                    'name': '有界范围数据（如年龄、评分）',
                    'type': 'system',
                    'model_type': 'gaussian_copula',
                    'parameters': {
                        'enforce_min_max_values': True,
                        'enforce_rounding': True,
                        'default_distribution': 'truncnorm'
                    },
                    'description': '截断正态分布，适合有明确上下限的数值数据（如年龄18-65岁、评分1-10分）'
                },
                {
                    'id': 'system_random_equal',
                    'name': '等概率随机数据',
                    'type': 'system',
                    'model_type': 'gaussian_copula',
                    'parameters': {
                        'enforce_min_max_values': True,
                        'enforce_rounding': True,
                        'default_distribution': 'uniform'
                    },
                    'description': '均匀分布，所有值出现概率相等，适合随机数生成和等概率事件'
                },
                {
                    'id': 'system_skewed_positive',
                    'name': '偏态正数数据（如金额、时长）',
                    'type': 'system',
                    'model_type': 'gaussian_copula',
                    'parameters': {
                        'enforce_min_max_values': True,
                        'enforce_rounding': True,
                        'default_distribution': 'gamma'
                    },
                    'description': 'Gamma分布，适合非负的右偏分布数据（如等待时间、服务时长、金额、计数数据）'
                }
            ]
        }
        
        # 用户自定义模板
        user_templates = UserParameterTemplate.query.filter_by(
            user_id=current_user.id,
            model_type=model_type
        ).order_by(UserParameterTemplate.is_default.desc(), UserParameterTemplate.created_at.desc()).all()
        
        templates = system_templates.get(model_type, [])
        templates.extend([{
            'id': f'user_{t.id}',
            'name': t.name,
            'type': 'user',
            'model_type': t.model_type,
            'parameters': t.get_parameters(),
            'is_default': t.is_default,
            'description': t.description,
            'created_at': t.created_at.isoformat() if t.created_at else None
        } for t in user_templates])
        
        return jsonify({
            'success': True,
            'data': {'templates': templates}
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@synthetic_bp.route('/parameter-templates', methods=['POST'])
@login_required
def create_parameter_template():
    """创建用户参数模板"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        model_type = data.get('model_type', 'ctgan')
        parameters = data.get('parameters', {})
        description = data.get('description', '').strip()
        is_default = data.get('is_default', False)
        
        if not name:
            return jsonify({
                'success': False,
                'error': '模板名称不能为空',
                'code': 'INVALID_PARAMS'
            }), 400
        
        if not parameters:
            return jsonify({
                'success': False,
                'error': '参数不能为空',
                'code': 'INVALID_PARAMS'
            }), 400
        
        # 如果设置为默认模板，取消其他默认模板
        if is_default:
            UserParameterTemplate.query.filter_by(
                user_id=current_user.id,
                model_type=model_type,
                is_default=True
            ).update({'is_default': False})
        
        template = UserParameterTemplate(
            user_id=current_user.id,
            name=name,
            model_type=model_type,
            description=description,
            is_default=is_default
        )
        template.set_parameters(parameters)
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'template': template.to_dict(),
                'message': '参数模板已创建'
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@synthetic_bp.route('/parameter-templates/<int:template_id>', methods=['PUT'])
@login_required
def update_parameter_template(template_id):
    """更新用户参数模板"""
    try:
        template = UserParameterTemplate.query.filter_by(
            id=template_id,
            user_id=current_user.id
        ).first_or_404()
        
        data = request.get_json()
        if 'name' in data:
            template.name = data['name'].strip()
        if 'parameters' in data:
            template.set_parameters(data['parameters'])
        if 'description' in data:
            template.description = data['description'].strip()
        if 'is_default' in data:
            is_default = data['is_default']
            if is_default:
                # 取消其他默认模板
                UserParameterTemplate.query.filter_by(
                    user_id=current_user.id,
                    model_type=template.model_type,
                    is_default=True
                ).update({'is_default': False})
            template.is_default = is_default
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'template': template.to_dict(),
                'message': '参数模板已更新'
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@synthetic_bp.route('/parameter-templates/<int:template_id>', methods=['DELETE'])
@login_required
def delete_parameter_template(template_id):
    """删除用户参数模板"""
    try:
        template = UserParameterTemplate.query.filter_by(
            id=template_id,
            user_id=current_user.id
        ).first_or_404()
        
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '参数模板已删除'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500



@synthetic_bp.route('/test-simple', methods=['GET'])
@login_required
def test_simple_page():
    """简单测试页面 - 用于对比测试新架构和旧架构"""
    from flask import render_template
    return render_template('test_simple.html', current_user=current_user)

@synthetic_bp.route('/analyze-field-types', methods=['POST'])
@login_required
def analyze_field_types():
    """分析上传文件的字段类型（后端准确识别）"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        template_id = data.get('template_id')
        
        if not file_id and not template_id:
            return jsonify({
                'success': False,
                'error': '缺少file_id或template_id'
            }), 400
        
        # 加载数据
        synthetic_service = SyntheticService()
        if file_id:
            # 从上传的文件加载
            from services.data_loader import DataLoader
            from config import Config
            data_loader = DataLoader(Config.UPLOAD_FOLDER)
            df = data_loader.load_from_file(file_id)
        elif template_id:
            # 从模板加载
            df = synthetic_service._load_template_data(template_id)
        
        if df is None or df.empty:
            return jsonify({
                'success': False,
                'error': '数据为空'
            }), 400
        
        # 使用FieldTypeAnalyzer分析字段类型
        fields = FieldTypeAnalyzer.analyze_dataframe(df)
        
        # 转换为前端需要的格式
        result_fields = []
        for field in fields:
            result_fields.append({
                'name': field['name'],
                'type': field['type'],
                'confidence': field['confidence'],
                'type_label': FieldTypeAnalyzer.get_type_label(field['type']),
                'sample_values': field['sample_values'][:3] if 'sample_values' in field else []  # 只返回前3个样本值
            })
        
        return jsonify({
            'success': True,
            'fields': result_fields
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"分析字段类型失败: {e}\n{error_trace}")
        return jsonify({
            'success': False,
            'error': f'分析字段类型失败: {str(e)}'
        }), 500
