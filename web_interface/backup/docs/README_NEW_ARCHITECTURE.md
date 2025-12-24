# 新架构 Web 服务说明

## 概述

根据前后端架构设计文档，已重新构建了模块化的 Web 服务代码结构。

## 目录结构

```
web_interface/
├── app.py                 # 主应用文件（应用工厂模式）
├── config.py              # 配置文件
├── models/                # 数据模型层
│   ├── __init__.py
│   ├── user.py           # 用户模型
│   ├── task.py           # 任务模型
│   ├── config.py         # 系统配置模型
│   └── log.py            # 操作日志模型
├── routes/                # 路由层
│   ├── __init__.py
│   ├── auth.py           # 认证路由
│   ├── synthetic.py      # 合成数据路由
│   ├── quality.py        # 质量评估路由
│   ├── masking.py        # 数据脱敏路由
│   ├── task.py           # 任务中心路由
│   └── settings.py       # 系统设置路由
├── services/              # 业务逻辑层
│   ├── __init__.py
│   ├── email_service.py  # 邮件服务
│   ├── synthetic_service.py  # 合成数据服务
│   ├── quality_service.py   # 质量评估服务
│   └── masking_service.py   # 数据脱敏服务
└── utils/                  # 工具函数层
    ├── __init__.py
    ├── decorators.py      # 装饰器（权限、日志）
    ├── validators.py      # 数据验证
    └── helpers.py         # 辅助函数
```

## 启动方式

```bash
cd web_interface
python app.py
```

## 待完善功能

### 1. 合成数据生成服务 (synthetic_service.py)
- [ ] 实现 SDGX 模型调用
- [ ] 实现异步任务处理
- [ ] 实现结果文件生成和存储
- [ ] 实现进度更新机制

### 2. 质量评估服务 (quality_service.py)
- [ ] 实现评估指标计算
- [ ] 实现报告生成
- [ ] 实现可视化数据生成

### 3. 数据脱敏服务 (masking_service.py)
- [ ] 实现字段类型自动识别
- [ ] 实现仿真脱敏策略
- [ ] 实现遮蔽脱敏策略

### 4. 路由完善
- [ ] 完善合成数据路由的所有接口
- [ ] 完善质量评估路由的所有接口
- [ ] 完善数据脱敏路由的所有接口
- [ ] 实现文件下载接口
- [ ] 实现结果预览接口

### 5. 系统配置管理
- [ ] 实现 AI 模型配置的 CRUD
- [ ] 实现邮箱配置的 CRUD
- [ ] 实现配置加密存储

### 6. 异步任务处理
- [ ] 集成 Celery 或使用线程池
- [ ] 实现任务队列管理
- [ ] 实现进度实时更新（WebSocket 或轮询）

## 数据库初始化

首次运行会自动创建数据库表。如果需要手动初始化：

```python
from app import create_app
from models.user import db

app = create_app()
with app.app_context():
    db.create_all()
```

## 环境变量配置

创建 `.env` 文件或设置环境变量：

```bash
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///ai_data_platform.db
MAIL_SERVER=smtp.qq.com
MAIL_PORT=465
MAIL_USE_SSL=true
MAIL_USERNAME=your-email@qq.com
MAIL_PASSWORD=your-auth-code
MAIL_DEFAULT_SENDER=your-email@qq.com
```

## API 接口

所有接口遵循接口文档规范，基础路径为 `/api`。

详细接口文档请参考：`docs/开发文档/前后端接口文档.md`

## 注意事项

1. 所有模型文件需要统一使用 `db` 对象（从 `models.user` 导入）
2. 路由文件需要使用 `@login_required` 和 `@admin_required` 装饰器
3. 业务逻辑应该放在 `services` 层，路由层只负责参数验证和响应
4. 使用 `log_operation` 装饰器记录关键操作日志



