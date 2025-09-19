# 🌐 SDG Web界面

## 📋 项目概述

SDG Web界面是一个基于Flask的Web应用程序，为SDG（Synthetic Data Generator）提供直观的图形化界面，支持：

- 📁 **数据源管理**: 上传CSV/Excel文件或使用演示数据
- ⚙️ **模型配置**: 配置CTGAN、GPT等模型的参数
- 🎯 **数据生成**: 生成高质量的合成数据
- 📊 **质量评估**: 实时评估合成数据质量
- 📥 **结果下载**: 下载生成的合成数据文件

## 🚀 快速开始

### 1. 环境准备

```bash
# 进入Web界面目录
cd SDG项目文件/Web界面/

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动应用

```bash
# 启动Web服务器
python app.py
```

### 3. 访问界面

打开浏览器访问: http://localhost:5000

## 📁 项目结构

```
Web界面/
├── app.py                 # Flask主应用
├── requirements.txt       # Python依赖
├── README.md             # 项目说明
├── static/               # 静态资源
│   ├── css/
│   │   └── style.css     # 自定义样式
│   └── js/
│       └── common.js     # 通用JavaScript函数
├── templates/            # HTML模板
│   ├── base.html         # 基础模板
│   ├── index.html        # 首页
│   ├── data_source.html  # 数据源配置
│   ├── model_config.html # 模型配置
│   └── results.html      # 结果展示
├── uploads/              # 上传文件存储
└── results/              # 生成结果存储
```

## 🎯 功能特性

### 1. 数据源配置
- ✅ 支持CSV、Excel文件上传
- ✅ 内置演示数据
- ✅ 实时数据预览
- ✅ 数据质量检查

### 2. 模型配置
- ✅ CTGAN模型参数配置
- ✅ GPT模型API配置
- ✅ 参数说明和帮助
- ✅ 实时参数验证

### 3. 数据生成
- ✅ 可视化生成进度
- ✅ 支持批量生成
- ✅ 错误处理和重试
- ✅ 生成状态监控

### 4. 质量评估
- ✅ 统计指标对比
- ✅ 分布相似性分析
- ✅ 质量分数计算
- ✅ 可视化报告

### 5. 结果管理
- ✅ 多格式下载（CSV、Excel）
- ✅ 结果预览
- ✅ 历史记录
- ✅ 分享功能

## 🔧 配置说明

### 环境变量

创建 `.env` 文件配置环境变量：

```bash
# Flask配置
FLASK_ENV=development
FLASK_DEBUG=True

# 文件上传配置
MAX_CONTENT_LENGTH=52428800  # 50MB
UPLOAD_FOLDER=uploads
RESULTS_FOLDER=results

# OpenAI API配置（可选）
OPENAI_API_KEY=your_api_key_here
OPENAI_API_URL=https://api.openai.com/v1/

# DeepSeek配置（可选）
DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_API_URL=http://localhost:8000/v1/
```

### 模型参数

#### CTGAN模型
```python
{
    "epochs": 50,                    # 训练轮数
    "batch_size": 500,               # 批次大小
    "generator_lr": 2e-4,            # 生成器学习率
    "discriminator_lr": 2e-4,        # 判别器学习率
    "generator_decay": 1e-6,         # 生成器衰减率
    "discriminator_decay": 1e-6,     # 判别器衰减率
    "generator_dim": "(256, 256)",   # 生成器维度
    "discriminator_dim": "(256, 256)" # 判别器维度
}
```

#### GPT模型
```python
{
    "openai_API_key": "sk-...",      # API密钥
    "openai_API_url": "https://api.openai.com/v1/", # API地址
    "gpt_model": "gpt-3.5-turbo",    # 模型版本
    "temperature": 0.1,               # 温度参数
    "max_tokens": 2000,               # 最大token数
    "timeout": 90,                    # 超时时间
    "query_batch": 10                 # 查询批次大小
}
```

## 📊 使用流程

### 1. 数据上传
1. 访问数据源配置页面
2. 上传CSV/Excel文件或使用演示数据
3. 查看数据预览和基本信息
4. 进行数据质量检查

### 2. 模型配置
1. 选择模型类型（CTGAN/GPT）
2. 配置模型参数
3. 设置生成数量
4. 验证配置参数

### 3. 数据生成
1. 点击生成按钮
2. 监控生成进度
3. 等待生成完成
4. 查看生成结果

### 4. 质量评估
1. 自动进行质量评估
2. 查看评估报告
3. 分析质量指标
4. 下载评估结果

## 🎨 界面特性

### 响应式设计
- 📱 支持移动端访问
- 💻 适配不同屏幕尺寸
- 🎯 触摸友好的交互

### 用户体验
- ⚡ 快速加载和响应
- 🎨 现代化UI设计
- 🔔 实时状态提示
- 📊 可视化数据展示

### 安全性
- 🔒 文件类型验证
- 📏 文件大小限制
- 🛡️ 输入参数验证
- 🚫 错误处理机制

## 🔧 开发指南

### 添加新模型

1. 在 `app.py` 中添加模型配置：
```python
elif model_type == 'new_model':
    config = {
        'param1': {'type': 'number', 'default': 100, 'description': '参数1'},
        'param2': {'type': 'text', 'default': 'value', 'description': '参数2'}
    }
```

2. 在生成函数中添加模型创建逻辑：
```python
elif model_type == 'new_model':
    model = NewModelSynthesizer(
        param1=model_config.get('param1', 100),
        param2=model_config.get('param2', 'value')
    )
```

### 自定义样式

修改 `static/css/style.css` 文件：
```css
/* 自定义主题色 */
:root {
    --primary-color: #your-color;
}

/* 自定义组件样式 */
.custom-component {
    /* 样式定义 */
}
```

### 添加新页面

1. 创建HTML模板文件
2. 在 `app.py` 中添加路由
3. 更新导航菜单

## 🐛 故障排除

### 常见问题

1. **文件上传失败**
   - 检查文件格式（仅支持CSV、Excel）
   - 检查文件大小（限制50MB）
   - 检查文件编码（建议UTF-8）

2. **模型生成失败**
   - 检查模型参数配置
   - 检查API密钥（GPT模型）
   - 检查网络连接

3. **页面加载缓慢**
   - 检查数据文件大小
   - 优化模型参数
   - 使用更小的批次大小

### 日志查看

```bash
# 查看应用日志
tail -f app.log

# 查看错误日志
grep "ERROR" app.log
```

## 📈 性能优化

### 数据优化
- 使用适当的数据类型
- 清理缺失值和异常值
- 标准化数值特征

### 模型优化
- 调整批次大小
- 优化学习率
- 使用合适的网络结构

### 系统优化
- 增加内存配置
- 使用SSD存储
- 优化网络带宽

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 📞 技术支持

- 📧 邮箱: support@example.com
- 💬 讨论: GitHub Issues
- 📖 文档: 项目Wiki

---

**版本**: 1.0.0  
**最后更新**: 2025-09-18  
**维护者**: SDG开发团队
