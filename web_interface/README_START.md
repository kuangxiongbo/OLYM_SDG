# AI 数据平台 - 启动说明

## 🚀 启动方式

### 方式一：使用启动脚本（推荐）

```bash
cd web_interface
python start.py
```

### 方式二：使用Shell脚本

```bash
cd web_interface
./启动服务器.sh
```

### 方式三：直接运行app.py

```bash
cd web_interface
python app.py
```

## 📋 访问信息

- **访问地址**: http://localhost:5000
- **登录页面**: http://localhost:5000/api/auth/login
- **健康检查**: http://localhost:5000/health

## 🔐 测试账号

- **管理员账号**: admin@sdg.com
- **密码**: admin123

## 📱 主要功能页面

- **合成数据生成**: http://localhost:5000/synthetic-data
- **质量评估**: http://localhost:5000/quality-evaluation
- **数据脱敏**: http://localhost:5000/sensitive-detection
- **任务中心**: http://localhost:5000/api/tasks
- **系统设置**: http://localhost:5000/api/settings/ai-models

## ⚙️ 环境要求

1. Python 3.8+
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境变量（可选）：
   ```bash
   cp env_template .env
   # 编辑 .env 文件配置相关参数
   ```

## 🛑 停止服务

按 `Ctrl+C` 停止服务，或使用：

```bash
pkill -f "python.*start\.py"
```

## 📝 注意事项

- 首次启动会自动创建数据库表
- 确保端口 5000 未被占用
- 如果使用虚拟环境，请先激活：`source venv/bin/activate`

