# 🎯 SDG (Synthetic Data Generator) 项目

## 📋 项目概述

SDG是一个强大的合成数据生成器，支持多种生成模型和Web界面，可以生成高质量的合成数据用于机器学习、数据分析和隐私保护等场景。

## 🏗️ 项目结构

```
SDG项目/
├── 📁 synthetic-data-generator/     # SDG核心模块
│   ├── sdgx/                       # 主要代码包
│   ├── examples/                   # 使用示例
│   ├── tests/                      # 测试文件
│   └── requirements.txt            # 核心依赖
├── 📁 web_interface/               # Web界面
│   ├── app.py                      # 完整版应用
│   ├── app_simple.py               # 简化版应用
│   ├── templates/                  # HTML模板
│   ├── static/                     # 静态资源
│   ├── utils/                      # 工具类
│   └── requirements.txt            # Web依赖
├── 📁 SDG项目文件/                 # 项目文档和示例
│   ├── 基础示例/                   # 基础使用示例
│   ├── 话单数据合成/               # 话单数据合成
│   ├── 质量评估/                   # 数据质量评估
│   ├── 大模型配置/                 # 大模型配置
│   └── DeepSeek本地部署/           # 本地部署指南
├── 📁 dataset/                     # 数据集
├── 🚀 start_web.sh                 # Web界面启动脚本
└── 📖 README.md                    # 项目说明
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd SDG项目

# 安装SDG核心模块
cd synthetic-data-generator
pip install -e .
cd ..
```

### 2. 启动Web界面

```bash
# 使用启动脚本（推荐）
./start_web.sh

# 或手动启动
cd web_interface
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app_simple.py  # 简化版
# 或
python app.py         # 完整版
```

### 3. 访问界面

打开浏览器访问: **http://localhost:5000**

## 🎯 主要功能

### 1. 数据源管理
- ✅ 支持CSV、Excel文件上传
- ✅ 内置演示数据
- ✅ 实时数据预览和统计
- ✅ 数据质量检查

### 2. 模型支持
- ✅ **CTGAN**: 基于GAN的表格数据生成
- ✅ **GPT**: 基于大语言模型的生成
- ✅ **GLM**: 支持GLM模型
- ✅ **DeepSeek**: 支持本地DeepSeek部署

### 3. 数据生成
- ✅ 可视化生成进度
- ✅ 支持批量生成
- ✅ 错误处理和重试
- ✅ 生成状态监控

### 4. 质量评估
- ✅ 多维度质量评估
- ✅ 统计相似性分析
- ✅ 分布相似性测试
- ✅ 相关性分析
- ✅ 质量分数计算

### 5. Web界面特性
- ✅ 响应式设计
- ✅ 现代化UI
- ✅ 实时状态提示
- ✅ 批量处理功能
- ✅ RESTful API接口

## 🔧 使用方式

### 方式1: Web界面（推荐）

1. 启动Web服务: `./start_web.sh`
2. 访问: http://localhost:5000
3. 上传数据或使用演示数据
4. 配置模型参数
5. 生成合成数据
6. 查看质量评估
7. 下载结果

### 方式2: Python API

```python
from sdgx.data_connectors.csv_connector import CsvConnector
from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
from sdgx.synthesizer import Synthesizer

# 创建数据连接器
data_connector = CsvConnector(path="your_data.csv")

# 创建模型
model = CTGANSynthesizerModel(epochs=50, batch_size=500)

# 创建合成器
synthesizer = Synthesizer(
    model=model,
    data_connector=data_connector
)

# 训练和生成
synthesizer.fit()
synthetic_data = synthesizer.sample(1000)
```

### 方式3: RESTful API

```bash
# 健康检查
curl http://localhost:5000/api/v1/health

# 生成合成数据
curl -X POST http://localhost:5000/api/v1/synthesis/generate \
  -H "Content-Type: application/json" \
  -d '{
    "data": [...],
    "model_type": "ctgan",
    "model_config": {...},
    "num_samples": 100
  }'
```

## 📊 支持的数据类型

- **数值数据**: 整数、浮点数
- **分类数据**: 字符串、枚举值
- **日期时间**: 时间戳、日期
- **文本数据**: 短文本、长文本
- **混合数据**: 包含多种类型的表格

## 🎨 界面预览

### 主页
- 功能模块导航
- 快速开始指南
- 系统状态显示

### 数据源配置
- 文件上传界面
- 数据预览表格
- 数据质量检查

### 模型配置
- 参数配置界面
- 实时参数验证
- 模型推荐功能

### 结果展示
- 合成数据预览
- 质量评估报告
- 结果下载功能

## 🔧 配置说明

### 环境变量

```bash
# Flask配置
export FLASK_ENV=development
export FLASK_DEBUG=True

# 文件上传配置
export MAX_CONTENT_LENGTH=52428800  # 50MB

# API配置
export OPENAI_API_KEY=your_key_here
export DEEPSEEK_API_KEY=your_key_here
```

### 模型参数

#### CTGAN参数
```python
{
    "epochs": 50,                    # 训练轮数
    "batch_size": 500,               # 批次大小
    "generator_lr": 2e-4,            # 生成器学习率
    "discriminator_lr": 2e-4,        # 判别器学习率
}
```

#### GPT参数
```python
{
    "openai_API_key": "sk-...",      # API密钥
    "gpt_model": "gpt-3.5-turbo",    # 模型版本
    "temperature": 0.1,               # 温度参数
    "max_tokens": 2000,               # 最大token数
}
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

## 🐛 故障排除

### 常见问题

1. **依赖安装失败**
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

2. **SDG模块导入失败**
   ```bash
   cd synthetic-data-generator
   pip install -e .
   ```

3. **Web界面启动失败**
   ```bash
   # 使用简化版
   python app_simple.py
   ```

4. **内存不足**
   - 减少批次大小
   - 使用更小的数据集
   - 增加系统内存

### 日志查看

```bash
# 查看应用日志
tail -f web_interface/app.log

# 查看错误日志
grep "ERROR" web_interface/app.log
```

## 📚 文档资源

- **Web界面使用指南**: `web_interface/README.md`
- **API文档**: `web_interface/API文档.md`
- **部署指南**: `web_interface/部署指南.md`
- **项目示例**: `SDG项目文件/` 目录下的各种示例

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 📞 技术支持

- **GitHub Issues**: 项目问题反馈
- **邮箱**: support@example.com
- **文档**: 项目Wiki

## 🎉 更新日志

### v1.0.0 (2025-09-18)
- ✅ 完整的Web界面
- ✅ 支持CTGAN和GPT模型
- ✅ 数据质量评估
- ✅ 批量处理功能
- ✅ RESTful API接口
- ✅ 响应式设计
- ✅ 部署指南

---

**版本**: 1.0.0  
**最后更新**: 2025-09-18  
**维护者**: SDG开发团队
