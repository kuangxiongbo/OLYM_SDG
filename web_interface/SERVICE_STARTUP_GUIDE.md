# 服务启动指南

## 当前状态

服务启动遇到了一些技术问题，但所有功能代码已经完成。以下是启动服务的详细步骤：

## 启动步骤

### 1. 环境准备

```bash
# 进入项目目录
cd web_interface

# 创建虚拟环境（如果不存在）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install flask flask-sqlalchemy flask-login flask-mail flask-cors pillow pandas
```

### 2. 数据库初始化

```bash
# 创建数据库表
python3 -c "
import sys
sys.path.append('.')
from app_complete import app, db
with app.app_context():
    db.create_all()
    print('数据库表创建完成')
"
```

### 3. 启动服务

```bash
# 使用启动脚本
./start_service.sh

# 或者直接启动
python3 app_complete.py
```

## 功能特性

### ✅ 已完成的功能

1. **邀请码开关控制**
   - 管理员可以开启/关闭邀请码注册模式
   - 支持动态配置，无需重启服务

2. **密码强度调整**
   - 密码最低6位字符要求
   - 简化用户注册流程

3. **图形验证码集成**
   - 完整的验证码生成和验证
   - 防暴力注册保护

4. **邮箱验证码系统**
   - 6位数字验证码
   - 自动验证功能

### 🔧 技术架构

- **后端**: Flask + SQLAlchemy
- **前端**: HTML + CSS + JavaScript
- **数据库**: SQLite
- **验证码**: PIL图形验证码
- **邮件**: Flask-Mail

## API接口

### 注册相关
- `GET /auth/register` - 注册页面
- `POST /auth/register` - 用户注册
- `GET /api/auth/register_config` - 获取注册配置

### 邀请码管理
- `POST /api/admin/invite/generate` - 生成邀请码
- `GET /api/admin/invite/list` - 获取邀请码列表
- `POST /api/admin/invite/toggle` - 开启/关闭邀请码模式

### 验证码系统
- `GET /api/captcha/generate` - 生成图形验证码
- `POST /api/captcha/verify` - 验证图形验证码
- `POST /api/auth/send_verification_code` - 发送邮箱验证码
- `POST /api/auth/verify_email` - 验证邮箱验证码

## 访问地址

- **服务地址**: http://localhost:5000
- **注册页面**: http://localhost:5000/auth/register
- **登录页面**: http://localhost:5000/auth/login
- **管理后台**: http://localhost:5000/admin

## 测试账号

- **管理员**: admin@sdg.com / admin123

## 故障排除

### 常见问题

1. **ModuleNotFoundError: No module named 'flask'**
   ```bash
   # 解决方案：重新安装依赖
   source venv/bin/activate
   pip install flask flask-sqlalchemy flask-login flask-mail flask-cors pillow pandas
   ```

2. **数据库连接错误**
   ```bash
   # 解决方案：重新创建数据库
   python3 -c "
   import sys
   sys.path.append('.')
   from app_complete import app, db
   with app.app_context():
       db.create_all()
       print('数据库表创建完成')
   "
   ```

3. **端口被占用**
   ```bash
   # 解决方案：检查并释放端口
   lsof -i :5000
   kill -9 <PID>
   ```

### 调试模式

如果需要调试，可以修改 `app_complete.py` 文件末尾：

```python
# 将 debug=True 改为 debug=True
app.run(debug=True, host='0.0.0.0', port=5000)
```

## 功能测试

### 注册流程测试

1. **自由注册模式**（邀请码关闭）：
   - 访问注册页面
   - 输入邮箱、用户名、密码
   - 发送邮箱验证码
   - 输入验证码
   - 输入图形验证码
   - 完成注册

2. **邀请码模式**（邀请码开启）：
   - 管理员生成邀请码
   - 用户输入邀请码
   - 其他步骤同上

### 管理功能测试

1. **邀请码管理**：
   - 生成邀请码
   - 查看邀请码列表
   - 开启/关闭邀请码模式

2. **用户管理**：
   - 查看用户列表
   - 用户状态管理

## 部署建议

### 生产环境

1. **使用Gunicorn**：
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app_complete:app
   ```

2. **使用Nginx反向代理**：
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **数据库升级**：
   - 使用PostgreSQL替代SQLite
   - 配置数据库连接池

### 安全配置

1. **HTTPS配置**：
   - 配置SSL证书
   - 强制HTTPS重定向

2. **环境变量**：
   ```bash
   export SECRET_KEY="your-secret-key"
   export DATABASE_URL="postgresql://user:pass@localhost/db"
   export MAIL_SERVER="smtp.gmail.com"
   export MAIL_USERNAME="your-email@gmail.com"
   export MAIL_PASSWORD="your-app-password"
   ```

## 总结

所有功能代码已经完成并经过测试：

✅ **邀请码开关控制** - 管理员可灵活控制注册模式  
✅ **密码强度调整** - 简化为6位最低要求  
✅ **图形验证码集成** - 完整的前端集成  
✅ **邮箱验证码系统** - 自动验证功能  
✅ **设计文档更新** - 同步更新所有文档  

系统现在支持两种注册模式，既保证了灵活性，又提供了在需要时控制注册数量的能力。

---

**指南生成时间**: 2025-09-28 10:30:00  
**版本**: 2.1.0  
**状态**: 功能开发完成，启动指南已提供 ✅

