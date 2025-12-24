#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行单元测试脚本
"""

import os
import sys
import subprocess

def main():
    """运行所有测试"""
    # 切换到项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 检查pytest是否安装
    try:
        import pytest
    except ImportError:
        print("错误: pytest未安装，请运行: pip install pytest pytest-cov")
        sys.exit(1)
    
    # 运行测试
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '--cov=services',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--cov-fail-under=80'
    ]
    
    print("=" * 60)
    print("开始运行单元测试...")
    print("=" * 60)
    
    result = subprocess.run(cmd, cwd=script_dir)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print("\n测试覆盖率报告已生成: htmlcov/index.html")
    else:
        print("\n" + "=" * 60)
        print("❌ 测试失败，请检查错误信息")
        print("=" * 60)
        sys.exit(1)

if __name__ == '__main__':
    main()

