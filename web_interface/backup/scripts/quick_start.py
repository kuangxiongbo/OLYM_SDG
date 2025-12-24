#!/usr/bin/env python3
"""
快速启动脚本 - SDG多账号控制系统
"""

import sys
import os
from datetime import datetime

def main():
    print("🚀 启动SDG多账号控制系统...")
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 导入应用
        print("📦 导入应用模块...")
        from app_complete import app, db
        
        # 创建数据库表
        print("🗄️ 初始化数据库...")
        with app.app_context():
            db.create_all()
            print("✅ 数据库表创建完成")
        
        # 显示访问信息
        print("\n" + "="*60)
        print("🌟 服务启动成功！")
        print("="*60)
        print("📱 访问地址: http://localhost:4000")
        print("🔐 主要功能:")
        print("   - 注册: http://localhost:4000/auth/register")
        print("   - 登录: http://localhost:4000/auth/login")
        print("   - 管理后台: http://localhost:4000/admin")
        print("")
        print("💡 测试账号:")
        print("   - 管理员: admin@sdg.com / admin123")
        print("")
        print("💡 按Ctrl+C停止服务")
        print("="*60)
        print("")
        
        # 启动服务
        app.run(debug=True, host='0.0.0.0', port=4000)
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("💡 请确保已安装所有依赖包:")
        print("   pip install flask flask-sqlalchemy flask-login flask-mail flask-cors pillow pandas")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

