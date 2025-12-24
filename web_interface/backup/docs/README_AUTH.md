# SDG Web界面用户认证系统

## 📋 功能概述

本认证系统为SDG Web界面提供了完整的用户管理功能，包括：

- ✅ **用户注册** - 支持邮箱注册，密码强度验证
- ✅ **用户登录** - 支持邮箱/用户名登录，记住我功能
- ✅ **邮箱验证** - 注册后自动发送验证邮件
- ✅ **密码重置** - 忘记密码时通过邮箱重置
- ✅ **多账号支持** - 支持多个用户同时使用
- ✅ **会话管理** - 安全的用户会话，支持过期清理
- ✅ **权限控制** - 基于用户角色的访问控制
- ✅ **个人资料** - 用户可以管理自己的资料和密码

## 🚀 快速开始

### 1. 配置邮箱服务

复制环境配置文件并修改邮箱设置：

```bash
cp env_auth_template .env
```

编辑 `.env` 文件，配置您的邮箱服务：

```env
# 邮箱服务配置
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
SMTP_USERNAME=your_email@qq.com
SMTP_PASSWORD=your_email_password

# 发件人信息
FROM_EMAIL=your_email@qq.com
FROM_NAME=SDG Web界面

# 应用URL
APP_URL=http://localhost:5000
```

### 2. 启动应用

```bash
python app.py
```

### 3. 访问认证页面

- **注册页面**: http://localhost:5000/auth/register
- **登录页面**: http://localhost:5000/auth/login
- **个人资料**: http://localhost:5000/auth/profile

## 📁 文件结构

```
web_interface/
├── models.py              # 用户数据模型
├── database.py            # 数据库管理
├── email_service.py       # 邮箱服务
├── auth_routes.py         # 认证路由
├── templates/auth/        # 认证模板
│   ├── login.html         # 登录页面
│   ├── register.html      # 注册页面
│   ├── forgot_password.html # 忘记密码
│   ├── reset_password.html  # 重置密码
│   └── profile.html       # 个人资料
├── data/                  # 数据存储目录
│   ├── users.json         # 用户数据
│   ├── sessions.json      # 会话数据
│   ├── email_verifications.json # 邮箱验证
│   └── password_resets.json     # 密码重置
└── env_auth_template      # 环境配置模板
```

## 🔧 配置说明

### 邮箱服务配置

支持多种邮箱服务商：

#### QQ邮箱
```env
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
```

#### 163邮箱
```env
SMTP_SERVER=smtp.163.com
SMTP_PORT=25
```

#### Gmail
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

#### 企业邮箱
根据您的企业邮箱服务商配置相应的SMTP服务器和端口。

### 密码策略

系统要求密码必须满足以下条件：
- 至少8位字符
- 包含大写字母
- 包含小写字母
- 包含数字
- 包含特殊字符

### 会话管理

- 默认会话有效期：1天
- 记住我功能：7天
- 自动清理过期会话
- 支持强制登出所有设备

## 🛡️ 安全特性

### 密码安全
- 使用PBKDF2哈希算法
- 随机盐值
- 10万次迭代

### 会话安全
- 安全的会话令牌
- IP地址记录
- 用户代理记录
- 自动过期清理

### 邮箱验证
- 验证令牌有效期：24小时
- 一次性使用
- 自动清理过期令牌

### 密码重置
- 重置令牌有效期：1小时
- 一次性使用
- 重置后强制重新登录

## 📊 数据库结构

### 用户表 (users.json)
```json
{
  "email": {
    "user_id": "uuid",
    "email": "user@example.com",
    "username": "username",
    "password_hash": "hashed_password",
    "is_verified": true,
    "role": "user",
    "created_at": "2025-01-01T00:00:00",
    "last_login": "2025-01-01T00:00:00",
    "profile_data": {}
  }
}
```

### 会话表 (sessions.json)
```json
{
  "session_token": {
    "session_id": "uuid",
    "user_id": "uuid",
    "session_token": "token",
    "expires_at": "2025-01-01T00:00:00",
    "created_at": "2025-01-01T00:00:00",
    "last_activity": "2025-01-01T00:00:00",
    "ip_address": "127.0.0.1",
    "user_agent": "Mozilla/5.0...",
    "is_active": true
  }
}
```

## 🔌 API接口

### 认证相关API

#### 检查登录状态
```
GET /auth/api/check_auth
```

#### 获取当前用户信息
```
GET /auth/api/me
```

### 页面路由

#### 用户注册
```
GET/POST /auth/register
```

#### 用户登录
```
GET/POST /auth/login
```

#### 邮箱验证
```
GET /auth/verify_email?token=xxx
```

#### 忘记密码
```
GET/POST /auth/forgot_password
```

#### 重置密码
```
GET/POST /auth/reset_password?token=xxx
```

#### 个人资料
```
GET/POST /auth/profile
```

#### 修改密码
```
POST /auth/change_password
```

#### 退出登录
```
POST /auth/logout
```

## 🎨 界面特性

### 响应式设计
- 支持桌面和移动设备
- 现代化的UI设计
- 流畅的动画效果

### 用户体验
- 实时密码强度检查
- 表单验证提示
- 加载状态显示
- 错误消息提示

### 主题样式
- 渐变背景
- 卡片式布局
- 图标支持
- 统一的色彩方案

## 🚨 注意事项

### 生产环境部署

1. **修改默认密钥**
   ```python
   app.secret_key = 'your_very_secure_secret_key_here'
   ```

2. **配置HTTPS**
   - 生产环境必须使用HTTPS
   - 更新APP_URL为HTTPS地址

3. **数据库安全**
   - 定期备份用户数据
   - 设置适当的文件权限

4. **邮箱配置**
   - 使用专用的邮箱账户
   - 配置SPF、DKIM记录

### 开发环境

1. **邮箱测试**
   - 可以配置为不发送邮件（仅记录日志）
   - 使用测试邮箱服务

2. **数据清理**
   ```python
   # 清理过期数据
   auth_db.cleanup_expired_data()
   ```

## 🐛 故障排除

### 常见问题

#### 1. 邮箱发送失败
- 检查SMTP配置
- 确认邮箱密码（可能需要应用密码）
- 检查网络连接

#### 2. 会话过期
- 检查系统时间
- 清理浏览器缓存
- 重新登录

#### 3. 密码重置失败
- 检查重置链接是否过期
- 确认邮箱地址正确
- 检查令牌是否已使用

### 日志调试

启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 技术支持

如果您在使用过程中遇到问题，请：

1. 检查本文档的故障排除部分
2. 查看应用日志
3. 确认配置是否正确
4. 联系技术支持团队

---

**注意**: 本认证系统为演示版本，生产环境使用前请进行充分的安全测试和配置优化。

