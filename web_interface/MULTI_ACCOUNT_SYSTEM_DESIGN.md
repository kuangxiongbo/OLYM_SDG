# 多账号控制系统设计方案

## 系统概述

本系统是一个基于Flask的多账号数据生成平台，提供合成数据生成、质量评估和敏感字段发现三大核心功能。系统采用邮箱注册登录机制，支持验证码验证，每个用户拥有完全独立的工作空间和配置环境。

### 核心特性
- **邮箱注册登录**: 支持邮箱账号注册，邮箱验证机制
- **验证码保护**: 登录失败时触发验证码验证
- **独立数据源配置**: 每个普通用户拥有完全独立的数据源配置空间
- **独立大模型配置**: 每个用户可自定义大模型参数配置
- **三大工具集成**: 合成数据生成、质量评估、敏感字段发现
- **管理员系统**: 超级管理员可配置系统全局设置

## 系统架构

### 1. 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    用户界面层 (UI Layer)                      │
├─────────────────────────────────────────────────────────────┤
│  登录页面  │  注册页面  │  仪表板  │  工具页面  │  管理页面     │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                   业务逻辑层 (Business Layer)                 │
├─────────────────────────────────────────────────────────────┤
│  用户认证  │  配置管理  │  数据生成  │  质量评估  │  敏感检测    │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                   数据访问层 (Data Layer)                     │
├─────────────────────────────────────────────────────────────┤
│  用户数据  │  配置数据  │  任务数据  │  结果数据  │  系统配置    │
└─────────────────────────────────────────────────────────────┘
```

### 2. 核心模块

```
├── 用户认证模块 (Authentication)
│   ├── 邮箱注册/登录
│   ├── 邮箱验证机制
│   ├── 验证码验证 (失败触发)
│   ├── 会话管理
│   └── 密码重置
├── 用户配置模块 (User Configuration)
│   ├── 个人数据源配置
│   ├── 大模型参数配置
│   └── 账号信息管理
├── 合成数据生成模块 (Synthetic Data Generation)
│   ├── 数据源导入
│   ├── 模型训练配置
│   ├── 生成任务管理
│   └── 结果导出
├── 质量评估模块 (Quality Assessment)
│   ├── 统计指标计算
│   ├── 相似度分析
│   ├── 分布对比
│   └── 评估报告生成
├── 敏感字段发现模块 (Sensitive Field Detection)
│   ├── 字段类型识别
│   ├── 敏感度评分
│   ├── 风险评估
│   └── 建议报告
└── 系统管理模块 (System Administration)
    ├── 邮件服务配置
    ├── 管理员账号管理
    ├── 系统日志管理
    └── 全局配置管理
```

### 3. 用户角色设计

| 角色 | 权限 | 描述 |
|------|------|------|
| **超级管理员** | 全部权限 | 系统管理、用户管理、所有工具使用、个人配置管理、独立数据源配置、独立大模型配置 |
| **普通用户** | 工具使用权限 | 三大工具使用、个人配置管理、独立数据源配置、独立大模型配置 |

### 4. 用户权限矩阵

| 功能模块 | 普通用户 | 超级管理员 |
|----------|----------|------------|
| 邮箱注册登录 | ✅ | ✅ |
| 验证码验证 | ✅ | ✅ |
| 个人配置管理 | ✅ | ✅ |
| 独立数据源配置 | ✅ | ✅ |
| 独立大模型配置 | ✅ | ✅ |
| 合成数据生成 | ✅ | ✅ |
| 质量评估 | ✅ | ✅ |
| 敏感字段发现 | ✅ | ✅ |
| 邮件服务配置 | ❌ | ✅ |
| 管理员账号管理 | ❌ | ✅ |
| 系统日志查看 | ❌ | ✅ |
| 全局配置管理 | ❌ | ✅ |

### 5. 数据库设计

#### 用户表 (Users)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('super_admin', 'user') DEFAULT 'user',
    status ENUM('active', 'inactive', 'pending', 'banned') DEFAULT 'pending',
    email_verified BOOLEAN DEFAULT FALSE,
    login_attempts INTEGER DEFAULT 0,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 用户配置表 (User_Configurations)
```sql
CREATE TABLE user_configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    config_type ENUM('data_source', 'model_params') NOT NULL,
    config_name VARCHAR(100) NOT NULL,
    config_data JSON NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, config_type, config_name)
);
```

#### 系统配置表 (System_Configurations)
```sql
CREATE TABLE system_configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSON NOT NULL,
    description TEXT,
    updated_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id)
);
```

#### 登录日志表 (Login_Logs)
```sql
CREATE TABLE login_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    email VARCHAR(100),
    ip_address VARCHAR(45),
    user_agent TEXT,
    login_status ENUM('success', 'failed', 'blocked') NOT NULL,
    failure_reason VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 验证码表 (Verification_Codes)
```sql
CREATE TABLE verification_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(100) NOT NULL,
    code VARCHAR(10) NOT NULL,
    code_type ENUM('email_verification', 'login_captcha', 'password_reset') NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 数据源表 (Data_Sources)
```sql
CREATE TABLE data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    type ENUM('csv', 'json', 'database', 'api') NOT NULL,
    file_path VARCHAR(500), -- 文件路径
    config JSON NOT NULL, -- 数据源配置
    status ENUM('active', 'error', 'processing') DEFAULT 'processing',
    file_size INTEGER, -- 文件大小
    row_count INTEGER, -- 数据行数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 模型配置表 (Model_Configurations)
```sql
CREATE TABLE model_configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    model_type ENUM('ctgan', 'tvae', 'gaussian_copula', 'custom') NOT NULL,
    config JSON NOT NULL, -- 模型配置参数
    is_default BOOLEAN DEFAULT FALSE,
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, name)
);
```

#### 合成数据任务表 (Synthetic_Tasks)
```sql
CREATE TABLE synthetic_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    data_source_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    model_config JSON NOT NULL,
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    result_config JSON, -- 生成结果配置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (data_source_id) REFERENCES data_sources(id)
);
```

#### 质量评估任务表 (Quality_Tasks)
```sql
CREATE TABLE quality_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    original_data_id INTEGER,
    synthetic_data_id INTEGER,
    task_name VARCHAR(100) NOT NULL,
    metrics_config JSON NOT NULL,
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    results JSON, -- 评估结果
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 敏感字段任务表 (Sensitive_Tasks)
```sql
CREATE TABLE sensitive_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    data_source_id INTEGER NOT NULL,
    task_name VARCHAR(100) NOT NULL,
    detection_config JSON NOT NULL,
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    results JSON, -- 检测结果
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (data_source_id) REFERENCES data_sources(id)
);
```

## 关键模块设计

### 1. 用户认证流程设计

#### 用户注册流程（可配置邀请码模式）
```
用户注册流程:
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  用户访问注册 │ -> │  检查邀请码   │ -> │  输入邮箱地址  │
│  页面        │    │  开关状态     │    │  和用户名     │
└─────────────┘    └──────────────┘    └─────────────┘
       │                   │                    │
       v                   v                    v
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  系统发送验证码│ <- │  系统发送验证码│ <- │  系统发送验证码│
│  到邮箱      │    │  到邮箱      │    │  到邮箱      │
└─────────────┘    └──────────────┘    └─────────────┘
       │                   │                    │
       v                   v                    v
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  注册成功    │ <- │  输入验证码   │ <- │  用户查收邮件 │
└─────────────┘    └──────────────┘    └─────────────┘
       │                   │                    │
       v                   v                    v
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  自动登录    │    │  图形验证码   │    │  防暴力注册  │
└─────────────┘    └──────────────┘    └─────────────┘
```

#### 详细注册步骤
1. **用户访问注册页面**：
   - 用户直接访问注册页面
   - 系统检查邀请码开关状态

2. **邀请码验证（可选）**：
   - 如果邀请码开关开启：必须输入管理员生成的邀请码
   - 如果邀请码开关关闭：跳过邀请码验证
   - 邀请码会记录绑定到哪个账号，用于统计

3. **输入基本信息**：
   - 输入邮箱地址（用于接收验证码）
   - 输入用户名
   - 输入密码（至少6位）

4. **邮箱验证**：
   - 点击"发送验证码"按钮
   - 系统发送6位数字验证码到用户邮箱
   - 用户查收邮件，输入验证码

5. **图形验证码验证**：
   - 显示图形验证码防止暴力注册
   - 用户输入图形验证码
   - 系统验证图形验证码正确性

6. **完成注册**：
   - 系统验证所有信息完整性
   - 创建用户账号并自动登录
   - 跳转到系统首页

#### 用户登录流程
```
用户登录流程:
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  访问登录页   │ -> │  输入邮箱密码  │ -> │  验证凭据    │
└─────────────┘    └──────────────┘    └─────────────┘
                           │                    │
                           v                    v
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  登录成功    │    │  登录失败    │    │  账号状态    │
└─────────────┘    └──────────────┘    └─────────────┘
       │                   │                    │
       v                   v                    v

登录失败后流程:
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  显示图形验证码│ -> │  输入验证码   │ -> │  重新验证    │
└─────────────┘    └──────────────┘    └─────────────┘
       │                   │                    │
       v                   v                    v
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  防暴力登录  │    │  记录失败次数 │    │  验证码验证  │
└─────────────┘    └──────────────┘    └─────────────┘
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  进入系统    │    │  错误提示    │    │  检查激活    │
└─────────────┘    └──────────────┘    └─────────────┘
```

### 2. 用户配置管理设计

```
用户独立配置架构:
┌─────────────────────────────────────────────────────────┐
│                用户A独立工作空间                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 独立数据源   │  │ 独立模型参数  │  │  账号信息    │     │
│  │  - 用户A的   │  │  - 用户A的   │  │  - 个人信息  │     │
│  │   CSV文件    │  │   CTGAN     │  │  - 密码修改  │     │
│  │  - 用户A的   │  │  - 用户A的   │  │  - 邮箱设置  │     │
│  │   数据库     │  │   TVAE      │  │             │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                用户B独立工作空间                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 独立数据源   │  │ 独立模型参数  │  │  账号信息    │     │
│  │  - 用户B的   │  │  - 用户B的   │  │  - 个人信息  │     │
│  │   CSV文件    │  │   CTGAN     │  │  - 密码修改  │     │
│  │  - 用户B的   │  │  - 用户B的   │  │  - 邮箱设置  │     │
│  │   API接口    │  │   TVAE      │  │             │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                                │
                                v
                    ┌─────────────────────┐
                    │   独立数据存储       │
                    │  - user_id隔离      │
                    │  - 完全独立配置     │
                    └─────────────────────┘
```

### 3. 三大工具集成设计

```
工具集成架构:
┌─────────────────────────────────────────────────────────┐
│                    用户仪表板                            │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  合成数据    │  │  质量评估    │  │  敏感字段    │     │
│  │  生成工具    │  │  工具        │  │  发现工具    │     │
│  │             │  │             │  │             │     │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │     │
│  │ │数据导入  │ │  │ │指标选择  │ │  │ │字段扫描  │ │     │
│  │ │模型配置  │ │  │ │对比分析  │ │  │ │风险评估  │ │     │
│  │ │任务执行  │ │  │ │报告生成  │ │  │ │建议生成  │ │     │
│  │ │结果导出  │ │  │ │结果导出  │ │  │ │结果导出  │ │     │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                                │
                                v
                    ┌─────────────────────┐
                    │   共享数据层         │
                    │  - 数据源           │
                    │  - 任务队列         │
                    │  - 结果存储         │
                    └─────────────────────┘
```

### 4. 管理员系统设计

```
超级管理员系统架构:
┌─────────────────────────────────────────────────────────┐
│                超级管理员控制台                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  系统管理    │  │  用户管理    │  │  工具使用    │     │
│  │  功能        │  │             │  │             │     │
│  │             │  │             │  │             │     │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │     │
│  │ │邮件配置  │ │  │ │用户列表  │ │  │ │数据源管理 │ │     │
│  │ │系统日志  │ │  │ │角色分配  │ │  │ │模型配置  │ │     │
│  │ │全局配置  │ │  │ │状态管理  │ │  │ │三大工具  │ │     │
│  │ │系统监控  │ │  │ │权限管理  │ │  │ │结果管理  │ │     │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  数据管理    │  │  配置管理    │  │  监控告警    │     │
│  │             │  │             │  │             │     │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │     │
│  │ │所有用户  │ │  │ │系统参数  │ │  │ │性能监控  │ │     │
│  │ │数据访问  │ │  │ │安全设置  │ │  │ │资源使用  │ │     │
│  │ │数据备份  │ │  │ │备份配置  │ │  │ │健康检查  │ │     │
│  │ │数据恢复  │ │  │ │更新管理  │ │  │ │告警设置  │ │     │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## 功能模块详细设计

### 1. 用户认证与权限管理

#### 功能特性
- 邮箱注册/登录/登出
- 邮箱验证机制
- 验证码验证 (登录失败触发)
- 密码重置
- 登录失败保护
- 用户数据隔离

#### API接口
```python
# 用户认证
GET  /auth/register              # 注册页面
POST /auth/register              # 注册页面处理（邮箱验证码模式）
POST /auth/login                 # 邮箱登录
POST /auth/logout                # 用户登出
GET  /auth/check-auth            # 检查认证状态

# 用户注册API
POST /api/auth/register              # 用户注册（可配置邀请码模式）
GET  /api/auth/register_config       # 获取注册配置（邀请码开关状态）

# 邀请码管理API（管理员）
POST /api/admin/invite/generate      # 生成邀请码
GET  /api/admin/invite/list          # 获取邀请码列表
DELETE /api/admin/invite/<id>        # 撤销邀请码
POST /api/admin/invite/toggle        # 开启/关闭邀请码注册模式
GET  /api/auth/verify_invite/<code>  # 验证邀请码

# 邮箱验证API
POST /api/auth/send_verification_code  # 发送邮箱验证码
POST /api/auth/verify_email            # 验证邮箱验证码

# 图形验证码API
GET  /api/captcha/generate            # 生成图形验证码
POST /api/captcha/verify              # 验证图形验证码

# 登录安全API
POST /api/auth/login_with_captcha     # 带验证码登录
GET  /api/auth/login_attempts         # 获取登录失败次数

# 扩展功能（待实现）
POST /auth/resend-verification   # 重发验证邮件
POST /auth/forgot-password       # 忘记密码
POST /auth/reset-password        # 重置密码
POST /auth/captcha               # 获取验证码

# 用户配置管理
GET  /api/user/configurations           # 获取用户配置列表
POST /api/user/configurations           # 创建用户配置
PUT  /api/user/configurations/{id}      # 更新用户配置
DELETE /api/user/configurations/{id}    # 删除用户配置
POST /api/user/configurations/{id}/set-default  # 设为默认配置

# 账号信息管理
GET  /api/user/profile                  # 获取用户个人信息
PUT  /api/user/profile                  # 更新用户个人信息
POST /api/user/change-password          # 修改密码
POST /api/user/change-email             # 修改邮箱

# 独立数据源管理
GET  /api/user/data-sources             # 获取用户个人数据源列表
POST /api/user/data-sources             # 上传/创建个人数据源
GET  /api/user/data-sources/{id}        # 获取个人数据源详情
PUT  /api/user/data-sources/{id}        # 更新个人数据源配置
DELETE /api/user/data-sources/{id}      # 删除个人数据源
POST /api/user/data-sources/{id}/preview # 个人数据预览

# 独立大模型配置管理
GET  /api/user/model-configs            # 获取用户个人模型配置列表
POST /api/user/model-configs            # 创建个人模型配置
GET  /api/user/model-configs/{id}       # 获取个人模型配置详情
PUT  /api/user/model-configs/{id}       # 更新个人模型配置
DELETE /api/user/model-configs/{id}     # 删除个人模型配置
POST /api/user/model-configs/{id}/test  # 测试个人模型配置

# 管理员功能 (超级管理员拥有所有权限)
GET  /api/admin/users                   # 获取用户列表 (管理员)
PUT  /api/admin/users/{id}              # 更新用户信息 (管理员)
POST /api/admin/users/{id}/ban          # 禁用用户 (管理员)
POST /api/admin/users/{id}/unban        # 启用用户 (管理员)
GET  /api/admin/logs                    # 获取系统日志 (管理员)
POST /api/admin/system/config           # 更新系统配置 (管理员)
GET  /api/admin/system/config           # 获取系统配置 (管理员)

# 管理员数据访问 (超级管理员可访问所有用户数据)
GET  /api/admin/all-data-sources        # 获取所有用户数据源 (管理员)
GET  /api/admin/all-model-configs       # 获取所有用户模型配置 (管理员)
GET  /api/admin/all-synthetic-tasks     # 获取所有用户合成任务 (管理员)
GET  /api/admin/all-quality-tasks       # 获取所有用户质量评估 (管理员)
GET  /api/admin/all-sensitive-tasks     # 获取所有用户敏感检测 (管理员)
GET  /api/admin/user-data/{user_id}     # 获取指定用户的所有数据 (管理员)
```

### 2. 合成数据生成模块

#### 功能特性
- 数据源配置和导入
- 模型参数配置
- 生成任务管理
- 结果下载和预览

#### 核心算法
- **CTGAN**: 基于条件GAN的表格数据生成
- **TVAE**: 变分自编码器
- **GaussianCopula**: 高斯 Copula 模型
- **Custom Models**: 自定义模型支持

#### API接口
```python
# 数据源管理
GET    /api/data-sources                   # 获取用户数据源列表
POST   /api/data-sources                   # 创建数据源
GET    /api/data-sources/{id}              # 获取数据源详情
PUT    /api/data-sources/{id}              # 更新数据源
DELETE /api/data-sources/{id}              # 删除数据源

# 合成数据生成
POST   /api/synthetic-tasks                # 创建生成任务
GET    /api/synthetic-tasks                # 获取用户任务列表
GET    /api/synthetic-tasks/{id}           # 获取任务状态
GET    /api/synthetic-tasks/{id}/result    # 下载生成结果
POST   /api/synthetic-tasks/{id}/cancel    # 取消任务
```

### 3. 质量评估模块

#### 功能特性
- 统计分布对比
- 数据质量指标计算
- 相似度分析
- 评估报告生成

#### 评估指标
- **统计指标**: 均值、方差、偏度、峰度
- **分布对比**: KS测试、卡方检验
- **相关性分析**: 皮尔逊相关系数、斯皮尔曼相关系数
- **机器学习指标**: F1分数、AUC等

#### API接口
```python
# 质量评估
POST   /api/quality-tasks                 # 创建评估任务
GET    /api/quality-tasks                 # 获取用户任务列表
GET    /api/quality-tasks/{id}            # 获取任务状态
GET    /api/quality-tasks/{id}/report     # 获取评估报告
POST   /api/quality-tasks/{id}/export     # 导出报告
```

### 4. 敏感字段发现模块

#### 功能特性
- 字段类型识别
- 敏感度评分
- 风险评估
- 建议报告

#### 检测算法
- **规则匹配**: 正则表达式、关键词匹配
- **机器学习**: 基于特征的模式识别
- **统计方法**: 异常值检测、频率分析
- **语义分析**: NLP技术识别敏感信息

#### API接口
```python
# 敏感字段检测
POST   /api/sensitive-tasks                # 创建检测任务
GET    /api/sensitive-tasks                # 获取用户任务列表
GET    /api/sensitive-tasks/{id}           # 获取任务状态
GET    /api/sensitive-tasks/{id}/report    # 获取检测报告
POST   /api/sensitive-tasks/{id}/export    # 导出报告
```

## 前端界面设计

### 1. 主要页面结构

#### 首页 (Homepage)
- 用户登录状态显示
- 三大工具入口
- 独立数据源管理入口
- 独立大模型配置入口

#### 独立数据源管理页面
- 用户个人数据源列表
- 数据源上传（CSV/JSON/数据库/API）
- 数据源配置管理
- 数据预览和验证

#### 独立大模型配置页面
- 用户个人模型参数配置
- 预设配置管理
- 配置模板库
- 配置测试和验证

#### 合成数据生成页面
- 选择用户数据源
- 选择用户模型配置
- 生成任务执行
- 结果预览和下载

#### 质量评估页面
- 选择用户数据源
- 评估指标配置
- 评估报告生成
- 结果对比分析

#### 敏感字段发现页面
- 选择用户数据源
- 检测规则配置
- 敏感度分析
- 建议报告生成

### 2. 首页布局设计

```
普通用户首页布局:
┌─────────────────────────────────────────────────────────┐
│                    顶部导航栏                            │
│  [Logo] [登录/注册] [用户菜单]                           │
└─────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────┐
│                    主要内容区                            │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 独立数据源   │  │ 独立大模型   │  │  工具中心    │     │
│  │  管理       │  │  配置       │  │             │     │
│  │             │  │             │  │             │     │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │     │
│  │ │上传数据  │ │  │ │参数配置  │ │  │ │合成数据  │ │     │
│  │ │数据列表  │ │  │ │预设管理  │ │  │ │质量评估  │ │     │
│  │ │配置管理  │ │  │ │模板库    │ │  │ │敏感检测  │ │     │
│  │ │数据预览  │ │  │ │配置测试  │ │  │ │结果导出  │ │     │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘

超级管理员首页布局:
┌─────────────────────────────────────────────────────────┐
│                    顶部导航栏                            │
│  [Logo] [管理员菜单] [系统管理] [工具使用]               │
└─────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────┐
│                    主要内容区                            │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 独立数据源   │  │ 独立大模型   │  │  工具中心    │     │
│  │  管理       │  │  配置       │  │             │     │
│  │ (所有用户)   │  │ (所有用户)   │  │             │     │
│  │             │  │             │  │             │     │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │     │
│  │ │上传数据  │ │  │ │参数配置  │ │  │ │合成数据  │ │     │
│  │ │数据列表  │ │  │ │预设管理  │ │  │ │质量评估  │ │     │
│  │ │配置管理  │ │  │ │模板库    │ │  │ │敏感检测  │ │     │
│  │ │数据预览  │ │  │ │配置测试  │ │  │ │结果导出  │ │     │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  系统管理    │  │  用户管理    │  │  监控告警    │     │
│  │             │  │             │  │             │     │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │     │
│  │ │邮件配置  │ │  │ │用户列表  │ │  │ │性能监控  │ │     │
│  │ │系统日志  │ │  │ │角色管理  │ │  │ │资源使用  │ │     │
│  │ │全局配置  │ │  │ │权限管理  │ │  │ │健康检查  │ │     │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 3. 工作流程设计

#### 普通用户工作流
```
1. 邮箱注册 → 2. 邮箱验证 → 3. 首次登录 → 4. 首页选择功能 → 5. 独立数据源管理 → 6. 独立大模型配置 → 7. 使用工具 → 8. 导出结果
```

#### 管理员工作流
```
1. 管理员登录 → 2. 管理员入口 → 3. 系统管理功能 OR 4. 使用所有工具功能
系统管理: 邮件服务配置 → 用户管理 → 系统监控 → 日志查看 → 全局配置
工具使用: 独立数据源管理 → 独立大模型配置 → 三大工具使用 → 结果导出
```

#### 验证码触发机制
```
登录流程:
正常登录: 邮箱 + 密码 → 登录成功
失败登录: 邮箱 + 密码 → 登录失败 → 触发验证码 → 验证码验证 → 登录重试
```

## 程序代码架构设计

### 1. 项目目录结构

```
web_interface/
├── app.py                          # Flask应用主入口
├── config.py                       # 配置文件
├── requirements.txt                # Python依赖
├── run.py                         # 启动脚本
├── instance/                      # 实例配置目录
│   ├── database.db               # SQLite数据库文件
│   └── config.py                 # 实例配置
├── static/                        # 静态资源目录
│   ├── css/                      # 样式文件
│   │   ├── main.css
│   │   ├── auth.css
│   │   └── components.css
│   ├── js/                       # JavaScript文件
│   │   ├── auth.js
│   │   ├── dashboard.js
│   │   └── tools.js
│   └── images/                   # 图片资源
├── templates/                     # 模板文件
│   ├── base.html                 # 基础模板
│   ├── index.html                # 首页
│   ├── auth/                     # 认证相关模板
│   │   ├── login.html
│   │   ├── register.html
│   │   └── profile.html
│   ├── tools/                    # 工具页面模板
│   │   ├── synthetic.html
│   │   ├── quality.html
│   │   └── sensitive.html
│   └── admin/                    # 管理员模板
│       ├── dashboard.html
│       └── users.html
├── models/                        # 数据模型
│   ├── __init__.py
│   ├── user.py                   # 用户模型
│   ├── data_source.py           # 数据源模型
│   ├── model_config.py          # 模型配置
│   └── tasks.py                 # 任务模型
├── services/                      # 业务服务层
│   ├── __init__.py
│   ├── auth_service.py          # 认证服务
│   ├── data_service.py          # 数据服务
│   ├── model_service.py         # 模型服务
│   ├── user_service.py          # 用户服务
│   └── admin_service.py         # 管理员服务
├── utils/                         # 工具类
│   ├── __init__.py
│   ├── database.py              # 数据库工具
│   ├── email.py                 # 邮件工具
│   ├── validators.py            # 验证工具
│   └── decorators.py            # 装饰器
├── api/                          # API路由
│   ├── __init__.py
│   ├── auth.py                  # 认证API
│   ├── data_sources.py          # 数据源API
│   ├── model_configs.py         # 模型配置API
│   ├── synthetic.py             # 合成数据API
│   ├── quality.py               # 质量评估API
│   ├── sensitive.py             # 敏感检测API
│   └── admin.py                 # 管理员API
├── core/                         # 核心功能
│   ├── __init__.py
│   ├── synthetic_generator.py   # 合成数据生成器
│   ├── quality_assessor.py      # 质量评估器
│   ├── sensitive_detector.py    # 敏感字段检测器
│   └── model_manager.py         # 模型管理器
└── tests/                        # 测试文件
    ├── __init__.py
    ├── test_auth.py
    ├── test_models.py
    └── test_api.py
```

### 2. 核心模块架构

#### 2.1 应用主入口 (app.py)
```python
# Flask应用配置和初始化
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # 配置加载
    app.config.from_object('config.Config')
    
    # 扩展初始化
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    CORS(app)
    
    # 蓝图注册
    register_blueprints(app)
    
    # 数据库初始化
    with app.app_context():
        db.create_all()
    
    return app

def register_blueprints(app):
    """注册所有蓝图"""
    from api.auth import auth_bp
    from api.user import user_bp
    from api.data_sources import data_bp
    from api.model_configs import model_bp
    from api.synthetic import synthetic_bp
    from api.quality import quality_bp
    from api.sensitive import sensitive_bp
    from api.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(data_bp, url_prefix='/api/data-sources')
    app.register_blueprint(model_bp, url_prefix='/api/model-configs')
    app.register_blueprint(synthetic_bp, url_prefix='/api/synthetic')
    app.register_blueprint(quality_bp, url_prefix='/api/quality')
    app.register_blueprint(sensitive_bp, url_prefix='/api/sensitive')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
```

#### 2.2 数据模型层 (models/)
```python
# models/user.py - 用户模型
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('super_admin', 'user'), default='user')
    status = db.Column(db.Enum('active', 'inactive', 'pending', 'banned'), default='pending')
    email_verified = db.Column(db.Boolean, default=False)
    login_attempts = db.Column(db.Integer, default=0)
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class InviteCode(db.Model):
    """推广邀请码模型"""
    __tablename__ = 'invite_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, used, revoked
    used_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(200))  # 邀请码描述
    
    # 关系
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_invites')
    user = db.relationship('User', foreign_keys=[used_by], backref='used_invite')
    
    def is_valid(self):
        """检查邀请码是否有效"""
        return self.status == 'active'
    
    def use(self, user_id):
        """使用邀请码"""
        self.status = 'used'
        self.used_by = user_id
        self.used_at = datetime.utcnow()

class CaptchaSession(db.Model):
    """图形验证码会话模型"""
    __tablename__ = 'captcha_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    captcha_code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    def is_valid(self):
        """检查验证码是否有效"""
        return not self.used and datetime.utcnow() < self.expires_at
    
    def use(self):
        """标记验证码为已使用"""
        self.used = True

class LoginAttempt(db.Model):
    """登录尝试记录模型"""
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False)
    success = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.String(500))
    
    # 关系
    data_sources = db.relationship('DataSource', backref='owner', lazy='dynamic')
    model_configs = db.relationship('ModelConfig', backref='owner', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'super_admin'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'role': self.role,
            'status': self.status,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# models/data_source.py - 数据源模型
class DataSource(db.Model):
    __tablename__ = 'data_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum('csv', 'json', 'database', 'api'), nullable=False)
    file_path = db.Column(db.String(500))
    config = db.Column(db.JSON, nullable=False)
    status = db.Column(db.Enum('active', 'error', 'processing'), default='processing')
    file_size = db.Column(db.Integer)
    row_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### 2.3 业务服务层 (services/)
```python
# services/auth_service.py - 认证服务
from flask_login import login_user, logout_user, current_user
from flask_mail import Message
from utils.email import send_email
from utils.validators import validate_email, validate_password
from models.user import User

class AuthService:
    @staticmethod
    def register_user(email, username, password):
        """用户注册"""
        # 验证输入
        if not validate_email(email):
            raise ValueError("无效的邮箱格式")
        if not validate_password(password):
            raise ValueError("密码强度不足")
        
        # 检查用户是否已存在
        if User.query.filter_by(email=email).first():
            raise ValueError("邮箱已被注册")
        
        # 创建用户
        user = User(email=email, username=username)
        user.set_password(password)
        user.status = 'pending'
        
        db.session.add(user)
        db.session.commit()
        
        # 发送验证邮件
        AuthService.send_verification_email(user)
        
        return user
    
    @staticmethod
    def login_user(email, password):
        """用户登录"""
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.status == 'banned':
                raise ValueError("账号已被禁用")
            
            login_user(user)
            user.login_attempts = 0
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            
            return user
        else:
            # 登录失败，增加尝试次数
            if user:
                user.login_attempts += 1
                if user.login_attempts >= 5:
                    user.status = 'banned'
                db.session.commit()
            raise ValueError("邮箱或密码错误")

# services/data_service.py - 数据服务
class DataService:
    @staticmethod
    def create_data_source(user_id, name, data_type, file_path, config):
        """创建数据源"""
        data_source = DataSource(
            user_id=user_id,
            name=name,
            type=data_type,
            file_path=file_path,
            config=config
        )
        
        db.session.add(data_source)
        db.session.commit()
        
        # 异步处理数据源
        DataService.process_data_source_async(data_source.id)
        
        return data_source
    
    @staticmethod
    def get_user_data_sources(user_id):
        """获取用户数据源列表"""
        return DataSource.query.filter_by(user_id=user_id).all()

# services/user_service.py - 用户服务
class UserService:
    @staticmethod
    def update_user_profile(user_id, profile_data):
        """更新用户个人信息"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        # 更新允许的字段
        allowed_fields = ['username']
        for field in allowed_fields:
            if field in profile_data:
                setattr(user, field, profile_data[field])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return user
    
    @staticmethod
    def change_password(user_id, old_password, new_password):
        """修改密码"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        if not user.check_password(old_password):
            raise ValueError("原密码错误")
        
        if not validate_password(new_password):
            raise ValueError("新密码强度不足")
        
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True
    
    @staticmethod
    def change_email(user_id, new_email, password):
        """修改邮箱"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        if not user.check_password(password):
            raise ValueError("密码错误")
        
        if not validate_email(new_email):
            raise ValueError("无效的邮箱格式")
        
        # 检查新邮箱是否已被使用
        if User.query.filter_by(email=new_email).first():
            raise ValueError("邮箱已被使用")
        
        user.email = new_email
        user.email_verified = False  # 需要重新验证
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 发送验证邮件
        AuthService.send_verification_email(user)
        
        return user
```

#### 2.4 API路由层 (api/)
```python
# api/auth.py - 认证API
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from services.auth_service import AuthService
from utils.decorators import admin_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    try:
        data = request.get_json()
        user = AuthService.register_user(
            email=data['email'],
            username=data['username'],
            password=data['password']
        )
        return jsonify({'success': True, 'message': '注册成功，请查收验证邮件'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    try:
        data = request.get_json()
        user = AuthService.login_user(data['email'], data['password'])
        return jsonify({'success': True, 'user': user.to_dict()})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 401

# api/data_sources.py - 数据源API
data_bp = Blueprint('data_sources', __name__)

@data_bp.route('/', methods=['GET'])
@login_required
def get_data_sources():
    """获取用户数据源列表"""
    data_sources = DataService.get_user_data_sources(current_user.id)
    return jsonify([ds.to_dict() for ds in data_sources])

@data_bp.route('/', methods=['POST'])
@login_required
def create_data_source():
    """创建数据源"""
    try:
        data = request.get_json()
        data_source = DataService.create_data_source(
            user_id=current_user.id,
            name=data['name'],
            data_type=data['type'],
            file_path=data.get('file_path'),
            config=data['config']
        )
        return jsonify({'success': True, 'data_source': data_source.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# api/user.py - 用户管理API
user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """获取用户个人信息"""
    return jsonify({'success': True, 'user': current_user.to_dict()})

@user_bp.route('/profile', methods=['PUT'])
@login_required
@json_required
@validate_json('username')
def update_profile():
    """更新用户个人信息"""
    try:
        data = request.get_json()
        user = UserService.update_user_profile(current_user.id, data)
        return jsonify({'success': True, 'user': user.to_dict()})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@user_bp.route('/change-password', methods=['POST'])
@login_required
@json_required
@validate_json('old_password', 'new_password')
def change_password():
    """修改密码"""
    try:
        data = request.get_json()
        UserService.change_password(
            current_user.id,
            data['old_password'],
            data['new_password']
        )
        return jsonify({'success': True, 'message': '密码修改成功'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@user_bp.route('/change-email', methods=['POST'])
@login_required
@json_required
@validate_json('new_email', 'password')
def change_email():
    """修改邮箱"""
    try:
        data = request.get_json()
        user = UserService.change_email(
            current_user.id,
            data['new_email'],
            data['password']
        )
        return jsonify({'success': True, 'message': '邮箱修改成功，请查收验证邮件'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
```

#### 2.5 核心功能层 (core/)
```python
# core/synthetic_generator.py - 合成数据生成器
import pandas as pd
from sdv.single_table import CTGANSynthesizer, TVAESynthesizer
from sdv.single_table import GaussianCopulaSynthesizer

class SyntheticDataGenerator:
    def __init__(self, model_type='ctgan'):
        self.model_type = model_type
        self.model = None
        self.fitted = False
    
    def fit(self, real_data, config=None):
        """训练模型"""
        if self.model_type == 'ctgan':
            self.model = CTGANSynthesizer(**config or {})
        elif self.model_type == 'tvae':
            self.model = TVAESynthesizer(**config or {})
        elif self.model_type == 'gaussian_copula':
            self.model = GaussianCopulaSynthesizer(**config or {})
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
        
        self.model.fit(real_data)
        self.fitted = True
    
    def generate(self, num_rows):
        """生成合成数据"""
        if not self.fitted:
            raise ValueError("模型尚未训练")
        
        return self.model.sample(num_rows)
    
    def get_quality_score(self, real_data, synthetic_data):
        """获取质量评分"""
        from core.quality_assessor import QualityAssessor
        assessor = QualityAssessor()
        return assessor.assess_quality(real_data, synthetic_data)

# core/quality_assessor.py - 质量评估器
from sklearn.metrics import f1_score, roc_auc_score
from scipy.stats import ks_2samp
import numpy as np

class QualityAssessor:
    def __init__(self):
        self.metrics = {}
    
    def assess_quality(self, real_data, synthetic_data):
        """评估数据质量"""
        scores = {}
        
        # 统计指标
        scores['statistical'] = self._statistical_similarity(real_data, synthetic_data)
        
        # 分布相似度
        scores['distribution'] = self._distribution_similarity(real_data, synthetic_data)
        
        # 相关性保持
        scores['correlation'] = self._correlation_preservation(real_data, synthetic_data)
        
        # 整体评分
        scores['overall'] = np.mean(list(scores.values()))
        
        return scores
    
    def _statistical_similarity(self, real_data, synthetic_data):
        """统计相似度评估"""
        # 计算均值、方差、偏度、峰度的相似度
        real_stats = real_data.describe()
        synth_stats = synthetic_data.describe()
        
        similarity = 1 - np.mean(np.abs(real_stats - synth_stats) / real_stats)
        return max(0, similarity)
```

### 3. 配置管理

#### 3.1 应用配置 (config.py)
```python
import os
from datetime import timedelta

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/database.db'
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
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
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
            'generator_lr': 2e-4,
            'discriminator_lr': 2e-4,
            
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

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

### 4. 工具类设计

#### 4.1 装饰器 (utils/decorators.py)
```python
from functools import wraps
from flask import jsonify, request
from flask_login import current_user

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated_function

def json_required(f):
    """JSON请求装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': '请求必须是JSON格式'}), 400
        return f(*args, **kwargs)
    return decorated_function

def validate_json(*required_fields):
    """JSON字段验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'缺少必需字段: {field}'}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

#### 4.2 验证工具 (utils/validators.py)
```python
import re
import pandas as pd

def validate_email(email):
    """邮箱格式验证"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """密码强度验证"""
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return sum([has_upper, has_lower, has_digit, has_special]) >= 3

def validate_data_source(file_path, data_type):
    """数据源验证"""
    try:
        if data_type == 'csv':
            df = pd.read_csv(file_path, nrows=100)  # 只读前100行验证
        elif data_type == 'json':
            df = pd.read_json(file_path, nrows=100)
        else:
            return True, "支持的数据类型"
        
        # 检查数据质量
        if df.empty:
            return False, "数据文件为空"
        
        if df.shape[1] < 2:
            return False, "数据至少需要2列"
        
        return True, f"数据验证通过，共{df.shape[1]}列"
    
    except Exception as e:
        return False, f"数据验证失败: {str(e)}"
```

## 技术栈

### 后端技术
- **框架**: Flask 2.3+
- **数据库**: SQLite/PostgreSQL
- **ORM**: SQLAlchemy
- **认证**: Flask-Login, JWT
- **任务队列**: Celery + Redis
- **API文档**: Flask-RESTX

### 前端技术
- **框架**: Bootstrap 5 + jQuery
- **图表**: Chart.js, D3.js
- **UI组件**: 自定义组件库
- **实时更新**: WebSocket/SSE

### 数据处理
- **机器学习**: scikit-learn, pandas, numpy
- **深度学习**: PyTorch, TensorFlow
- **数据生成**: SDV (Synthetic Data Vault)
- **评估指标**: 自定义评估框架

## 部署方案

### 开发环境
- 单机部署
- SQLite数据库
- 本地文件存储

### 生产环境
- Docker容器化
- PostgreSQL数据库
- Redis缓存
- Nginx反向代理
- 对象存储 (MinIO/AWS S3)

### 监控与日志
- 应用监控: Prometheus + Grafana
- 日志管理: ELK Stack
- 错误追踪: Sentry

## 安全考虑

### 数据安全
- 数据传输加密 (HTTPS)
- 数据存储加密
- 访问日志记录
- 数据脱敏处理

### 权限安全
- 基于角色的访问控制 (RBAC)
- API接口权限验证
- 操作审计日志
- 会话安全管理

## 扩展性设计

### 水平扩展
- 微服务架构
- 负载均衡
- 数据库分片
- 缓存集群

### 功能扩展
- 插件化架构
- 自定义算法支持
- 第三方集成接口
- 多租户支持

## 开发计划

### 第一阶段 (基础认证系统)
- 邮箱注册/登录系统
- 邮箱验证机制
- 验证码验证系统
- 用户权限管理
- 基础UI框架

### 第二阶段 (用户配置管理)
- 用户配置存储系统
- 数据源配置管理
- 大模型参数配置
- 个人偏好设置

### 第三阶段 (三大工具集成)
- 合成数据生成工具
- 质量评估工具
- 敏感字段发现工具
- 工具结果管理

### 演示数据系统设计

#### 行业演示数据
为了在没有上传数据时提供快速体验，系统内置多个行业的演示数据集：

**1. 金融行业数据**
- 银行客户数据：客户ID、年龄、收入、信用评分、贷款历史
- 股票交易数据：股票代码、价格、成交量、时间戳
- 保险理赔数据：保单号、理赔金额、事故类型、处理时间

**2. 电商行业数据**
- 用户购买数据：用户ID、商品类别、购买金额、评价分数
- 商品信息数据：商品ID、价格、库存、销量、分类
- 订单物流数据：订单号、配送地址、配送状态、时间

**3. 医疗行业数据**
- 患者病历数据：患者ID、年龄、性别、诊断结果、治疗费用
- 药品信息数据：药品名称、规格、价格、库存、副作用
- 医疗设备数据：设备ID、型号、维护记录、使用时长

**4. 教育行业数据**
- 学生成绩数据：学号、课程、成绩、出勤率、作业完成度
- 教师信息数据：教师ID、学科、教龄、学生评价、薪资
- 课程安排数据：课程ID、时间、教室、教师、学生人数

**5. 制造业数据**
- 生产设备数据：设备ID、运行状态、故障记录、维护时间
- 产品质量数据：产品ID、质检结果、缺陷类型、生产批次
- 供应链数据：供应商ID、物料类型、价格、交货时间

#### 演示数据特点
- **数据量适中**：每个数据集包含1000-5000条记录
- **字段丰富**：包含数值型、分类型、时间型等多种数据类型
- **关系完整**：支持外键关联和复杂关系
- **隐私安全**：所有数据均为合成数据，不涉及真实个人信息
- **可定制**：支持参数调整生成不同规模和特征的数据

### 系统架构图（更新版）

#### 整体架构
```
┌─────────────────────────────────────────────────────────────────┐
│                    SDG多账号控制系统架构                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   前端界面   │  │   用户认证   │  │   演示数据   │              │
│  │             │  │             │  │             │              │
│  │ - 首页控制台│  │ - 登录注册   │  │ - 金融数据   │              │
│  │ - 三大工具   │  │ - 权限管理   │  │ - 电商数据   │              │
│  │ - 数据管理   │  │ - 会话管理   │  │ - 医疗数据   │              │
│  │ - 模型配置   │  │ - 邮箱验证   │  │ - 教育数据   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│           │               │               │                     │
│           └───────────────┼───────────────┘                     │
│                           │                                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                  业务服务层                                 │ │
│  │                                                             │ │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │ │
│  │ │ 合成数据服务 │ │ 质量评估服务 │ │ 敏感检测服务 │             │ │
│  │ │             │ │             │ │             │             │ │
│  │ │ - CTGAN     │ │ - 统计相似度 │ │ - 规则匹配   │             │ │
│  │ │ - TVAE      │ │ - 分布对比   │ │ - ML检测     │             │ │
│  │ │ - Copula    │ │ - 相关性保持 │ │ - NLP分析     │             │ │
│  │ │ - DDPM      │ │ - 隐私评估   │ │ - 风险评估   │             │ │
│  │ └─────────────┘ └─────────────┘ └─────────────┘             │ │
│  │                                                             │ │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │ │
│  │ │ 用户服务     │ │ 数据服务     │ │ 模型服务     │             │ │
│  │ │             │ │             │ │             │             │ │
│  │ │ - 配置管理   │ │ - 数据源管理 │ │ - 参数配置   │             │ │
│  │ │ - 偏好设置   │ │ - 文件上传   │ │ - 模型训练   │             │ │
│  │ │ - 任务管理   │ │ - 数据预览   │ │ - 结果导出   │             │ │
│  │ └─────────────┘ └─────────────┘ └─────────────┘             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   数据存储层                                │ │
│  │                                                             │ │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │ │
│  │ │ 用户数据     │ │ 业务数据     │ │ 系统数据     │             │ │
│  │ │             │ │             │ │             │             │ │
│  │ │ - 用户信息   │ │ - 数据源     │ │ - 任务记录   │             │ │
│  │ │ - 配置信息   │ │ - 生成结果   │ │ - 系统日志   │             │ │
│  │ │ - 权限信息   │ │ - 评估报告   │ │ - 操作记录   │             │ │
│  │ └─────────────┘ └─────────────┘ └─────────────┘             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 数据流架构
```
┌─────────────────────────────────────────────────────────────────┐
│                        数据流架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户输入 ──→ 演示数据选择/文件上传 ──→ 数据预处理                │
│     │              │                    │                      │
│     │              │                    ▼                      │
│     │              │            ┌─────────────┐                 │
│     │              │            │ 数据验证     │                 │
│     │              │            │ 格式转换     │                 │
│     │              │            │ 特征分析     │                 │
│     │              │            └─────────────┘                 │
│     │              │                    │                      │
│     │              │                    ▼                      │
│     │              │            ┌─────────────┐                 │
│     │              └───────────→│ 模型选择     │                 │
│     │                           │ 参数配置     │                 │
│     │                           │ 训练执行     │                 │
│     │                           └─────────────┘                 │
│     │                                    │                      │
│     │                                    ▼                      │
│     │                            ┌─────────────┐                 │
│     │                            │ 结果生成     │                 │
│     │                            │ 质量评估     │                 │
│     │                            │ 敏感检测     │                 │
│     │                            └─────────────┘                 │
│     │                                    │                      │
│     │                                    ▼                      │
│     └────────────────────────────→ 结果展示与导出               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 用户界面优化设计

#### 首页设计（优化后）
- **未登录用户**: 
  - 系统介绍和核心功能展示
  - 三个工具的核心价值说明
  - 登录注册入口
  - 系统特色介绍
- **已登录用户**: 
  - 简洁的控制台首页
  - 直接展示三个工具入口（大卡片式设计）
  - 移除复杂的菜单导航
  - 快速操作入口

#### 控制台首页设计
```
┌─────────────────────────────────────────────────────────┐
│                    SDG多账号控制系统                     │
├─────────────────────────────────────────────────────────┤
│  欢迎回来，[用户名]！                                   │
│                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │   合成数据   │ │   质量评估   │ │  敏感字段发现│       │
│  │   生成工具   │ │   工具       │ │   工具       │       │
│  │             │ │             │ │             │       │
│  │  [开始生成]  │ │  [开始评估]  │ │  [开始检测]  │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
│                                                         │
│  快速操作: [数据源管理] [模型配置] [个人资料]           │
└─────────────────────────────────────────────────────────┘
```

#### 导航设计优化
- **简化导航**: 移除工具下拉菜单，直接从首页进入工具
- **工具入口**: 首页三个大卡片直接进入对应工具
- **快速操作**: 数据源管理、模型配置、个人资料作为快速操作入口
- **管理员入口**: 管理员用户显示管理后台入口

### 第四阶段 (管理员系统)
- 管理员控制台
- 邮件服务配置
- 用户管理功能
- 系统日志管理

### 第五阶段 (优化扩展)
- 性能优化
- 安全加固
- 功能扩展
- 监控告警

## 总结

本系统设计提供了一个完整的多账号数据生成平台，支持多用户独立工作空间、角色权限管理和数据安全。通过模块化设计，系统具有良好的可扩展性和维护性，每个用户都可以独立进行合成数据生成、质量评估和敏感字段发现等操作。
