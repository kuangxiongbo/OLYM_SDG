#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试脚本
按照测试用例文档进行系统测试
"""

import requests
import json
import sys
from datetime import datetime

base_url = 'http://localhost:5000'
test_results = {
    'passed': 0,
    'failed': 0,
    'warnings': 0,
    'details': []
}

def log_test(name, status, message=''):
    """记录测试结果"""
    if status == 'pass':
        test_results['passed'] += 1
        symbol = '✅'
    elif status == 'fail':
        test_results['failed'] += 1
        symbol = '❌'
    else:
        test_results['warnings'] += 1
        symbol = '⚠️'
    
    test_results['details'].append({
        'name': name,
        'status': status,
        'message': message
    })
    print(f'{symbol} {name}: {message}')

def test_health_check():
    """TC-HEALTH-001: 健康检查"""
    try:
        r = requests.get(f'{base_url}/health')
        if r.status_code == 200:
            log_test('健康检查', 'pass', '服务正常运行')
        else:
            log_test('健康检查', 'fail', f'状态码: {r.status_code}')
    except Exception as e:
        log_test('健康检查', 'fail', str(e))

def test_auth_flow():
    """测试认证流程"""
    session = requests.Session()
    
    # 测试登录
    try:
        r = session.post(f'{base_url}/api/auth/login', json={
            'email': 'admin@example.com',
            'password': 'admin123'
        })
        if r.status_code == 200 and r.json().get('success'):
            log_test('用户登录', 'pass', '登录成功')
        else:
            log_test('用户登录', 'fail', r.json().get('error', '未知错误'))
    except Exception as e:
        log_test('用户登录', 'fail', str(e))
        return None
    
    # 测试获取用户信息
    try:
        r = session.get(f'{base_url}/api/auth/me')
        if r.status_code == 200:
            log_test('获取用户信息', 'pass', '获取成功')
        else:
            log_test('获取用户信息', 'fail', f'状态码: {r.status_code}')
    except Exception as e:
        log_test('获取用户信息', 'fail', str(e))
    
    return session

def test_synthesis_module(session):
    """测试合成数据生成模块"""
    if not session:
        return
    
    # 测试模板列表
    try:
        r = session.get(f'{base_url}/api/synthesis/templates')
        if r.status_code == 200:
            result = r.json()
            if result.get('success'):
                templates = result.get('data', {}).get('templates', [])
                log_test('获取模板列表', 'pass', f'找到 {len(templates)} 个模板')
            else:
                log_test('获取模板列表', 'fail', result.get('error'))
        else:
            log_test('获取模板列表', 'fail', f'状态码: {r.status_code}')
    except Exception as e:
        log_test('获取模板列表', 'fail', str(e))

def test_task_center(session):
    """测试任务中心"""
    if not session:
        return
    
    # 测试任务列表
    try:
        r = session.get(f'{base_url}/api/tasks')
        if r.status_code == 200:
            result = r.json()
            if result.get('success'):
                total = result.get('data', {}).get('pagination', {}).get('total', 0)
                log_test('获取任务列表', 'pass', f'共 {total} 个任务')
            else:
                log_test('获取任务列表', 'fail', result.get('error'))
        else:
            log_test('获取任务列表', 'fail', f'状态码: {r.status_code}')
    except Exception as e:
        log_test('获取任务列表', 'fail', str(e))

def test_settings_module(session):
    """测试系统设置模块"""
    if not session:
        return
    
    # 测试AI模型配置
    try:
        r = session.get(f'{base_url}/api/settings/ai-models')
        if r.status_code == 200:
            result = r.json()
            if result.get('success'):
                models = result.get('data', {}).get('models', [])
                log_test('获取AI模型配置', 'pass', f'共 {len(models)} 个模型')
            else:
                log_test('获取AI模型配置', 'fail', result.get('error'))
        elif r.status_code == 403:
            log_test('获取AI模型配置', 'warn', '权限不足（需要管理员）')
        else:
            log_test('获取AI模型配置', 'fail', f'状态码: {r.status_code}')
    except Exception as e:
        log_test('获取AI模型配置', 'fail', str(e))

def test_ui_pages(session):
    """测试UI页面"""
    if not session:
        return
    
    pages = [
        ('/', '主页'),
        ('/dashboard', '仪表板'),
        ('/api/auth/login', '登录页面'),
        ('/api/auth/register', '注册页面'),
    ]
    
    for path, name in pages:
        try:
            r = session.get(f'{base_url}{path}', headers={'Accept': 'text/html'}, allow_redirects=True)
            if r.status_code == 200:
                if '<html' in r.text.lower():
                    log_test(f'UI页面: {name}', 'pass', '渲染正常')
                else:
                    log_test(f'UI页面: {name}', 'warn', '不是HTML格式')
            else:
                log_test(f'UI页面: {name}', 'fail', f'状态码: {r.status_code}')
        except Exception as e:
            log_test(f'UI页面: {name}', 'fail', str(e))

def main():
    """主测试函数"""
    print('=' * 60)
    print('AI 数据平台 - 全面测试')
    print('=' * 60)
    print(f'测试时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'测试地址: {base_url}')
    print('=' * 60)
    
    # 1. 健康检查
    print('\n[1] 基础功能测试')
    test_health_check()
    
    # 2. 认证流程
    print('\n[2] 认证模块测试')
    session = test_auth_flow()
    
    # 3. 合成数据生成
    print('\n[3] 合成数据生成模块测试')
    test_synthesis_module(session)
    
    # 4. 任务中心
    print('\n[4] 任务中心模块测试')
    test_task_center(session)
    
    # 5. 系统设置
    print('\n[5] 系统设置模块测试')
    test_settings_module(session)
    
    # 6. UI页面
    print('\n[6] UI页面测试')
    test_ui_pages(session)
    
    # 输出测试报告
    print('\n' + '=' * 60)
    print('测试报告')
    print('=' * 60)
    print(f'通过: {test_results["passed"]}')
    print(f'失败: {test_results["failed"]}')
    print(f'警告: {test_results["warnings"]}')
    print(f'总计: {test_results["passed"] + test_results["failed"] + test_results["warnings"]}')
    print('=' * 60)
    
    if test_results['failed'] > 0:
        print('\n失败的测试:')
        for detail in test_results['details']:
            if detail['status'] == 'fail':
                print(f'  - {detail["name"]}: {detail["message"]}')
    
    return test_results['failed'] == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)



