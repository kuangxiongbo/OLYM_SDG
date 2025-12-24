#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 数据平台 - 统一启动脚本
==========================

这是唯一的启动脚本，启动完整的AI数据平台服务
访问地址: http://localhost:5000
登录页面: http://localhost:5000/api/auth/login
"""

import sys
import os
from datetime import datetime

def main():
    """主启动函数"""
    print("=" * 60)
    print("🚀 AI 数据平台 - 启动中...")
    print("=" * 60)
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 导入应用
        print("📦 导入应用模块...")
        from app import create_app
        
        # 创建应用实例
        print("🔧 创建应用实例...")
        app = create_app()
        
        # 显示访问信息
        print()
        print("=" * 60)
        print("✅ 服务启动成功！")
        print("=" * 60)
        print("🌐 访问地址: http://localhost:5000")
        print("🔐 登录页面: http://localhost:5000/api/auth/login")
        print()
        print("📋 主要功能:")
        print("   - 合成数据生成: http://localhost:5000/synthetic-data")
        print("   - 质量评估: http://localhost:5000/quality-evaluation")
        print("   - 数据脱敏: http://localhost:5000/sensitive-detection")
        print("   - 任务中心: http://localhost:5000/api/tasks")
        print("   - 系统设置: http://localhost:5000/api/settings/ai-models")
        print()
        print("💡 测试账号:")
        print("   - 管理员: admin@sdg.com / admin123")
        print()
        print("💡 按 Ctrl+C 停止服务")
        print("=" * 60)
        print()
        
        # 启动服务
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print()
        print("💡 请确保已安装所有依赖包:")
        print("   cd web_interface")
        print("   source venv/bin/activate  # 如果使用虚拟环境")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

