# 数据生成模块新架构使用说明

## 概述

新架构将数据生成流程重构为模块化设计，解决了日期字符串连接问题，提高了代码的可维护性和可测试性。

## 架构组成

### 核心模块

1. **DataLoader** (`data_loader.py`)
   - 负责从文件或模板加载数据
   - 确保数据满足最小行数要求

2. **DataValidator** (`data_validator.py`)
   - 识别日期列
   - 修复被连接的日期字符串
   - 验证数据完整性

3. **DataTransformer** (`data_transformer.py`)
   - 清理数据（处理NaN、空值等）
   - 转换为SDGX兼容格式

4. **SDGXAdapter** (`sdgx_adapter.py`)
   - 封装SDGX调用
   - 处理模型训练和数据生成

5. **SyntheticService** (`synthetic_service.py`)
   - 主服务类，协调各个模块
   - 支持新架构和旧架构的回退机制

## 数据流程

```
原始数据源
    ↓
[Step 1] DataLoader -> 加载数据
    ↓
[Step 2] DataValidator -> 识别日期列
    ↓
[Step 3] DataTransformer -> 清理数据
    ↓
[Step 4] DataValidator -> 修复日期列（核心修复逻辑）
    ↓
[Step 5] DataValidator -> 验证数据完整性
    ↓
[Step 6] DataTransformer -> 转换为SDGX格式
    ↓
[Step 7] SDGXAdapter -> 创建SDGX组件
    ↓
[Step 8] SDGXAdapter -> 训练模型
    ↓
[Step 9] SDGXAdapter -> 生成数据
    ↓
生成结果
```

## 关键特性

### 1. 日期列修复

**问题**: 日期字符串被连接成单个长字符串
```
'2024-12-102024-12-11'  (错误)
```

**修复**: 提取第一个日期，确保格式正确
```
'2024-12-10'  (正确)
```

### 2. 数据验证

- 验证数据不为空
- 验证数据行数（至少10行）
- 验证列完整性（无全空列）
- 处理Inf值

### 3. 向后兼容

如果新模块初始化失败，自动回退到旧逻辑，确保系统稳定性。

## 使用方法

### 自动使用

新架构已集成到 `SyntheticService` 中，会自动使用（如果可用）：

```python
from services.synthetic_service import SyntheticService

service = SyntheticService()
# 创建任务时，会自动使用新架构
task = service.create_generation_task(user_id, config)
```

### 手动测试

```bash
# 运行单元测试
python3 services/test_new_architecture.py

# 运行集成测试
python3 services/test_integration.py
```

## 日志输出

新架构会输出详细的日志，便于调试：

```
任务 {task_id}: [Step 1] 加载数据...
任务 {task_id}: [Step 2] 识别日期列...
任务 {task_id}: [Step 3] 清理数据...
任务 {task_id}: [Step 4] 修复日期列...
任务 {task_id}: [Step 5] 验证数据完整性...
任务 {task_id}: [Step 6] 转换为SDGX格式...
任务 {task_id}: [Step 7] 创建SDGX连接器和合成器...
任务 {task_id}: [Step 8] 开始训练模型...
任务 {task_id}: [Step 9] 开始生成数据...
```

## 测试结果

✅ **所有测试通过**
- 单元测试: 通过
- 集成测试: 通过
- 日期修复: 验证通过

## 注意事项

1. **日期格式**: 确保日期列格式为 `YYYY-MM-DD`（10个字符）
2. **最小行数**: 数据至少需要10行才能训练模型
3. **数据类型**: 日期列必须是 `object` 类型（字符串）

## 故障排查

### 如果新架构不可用

检查日志中的错误信息：
```
⚠️ 新模块初始化失败: {error}，将使用旧逻辑
```

系统会自动回退到旧逻辑，不会影响功能。

### 如果日期修复失败

检查日志中的日期列修复信息：
```
任务 {task_id}: [Step 4] 修复日期列...
任务 {task_id}: ⚠️ 日期列 {col} 包含被连接的日期字符串，已修复
```

如果仍有问题，检查日期列的值是否符合 `YYYY-MM-DD` 格式。

## 相关文档

- `data_generation_architecture.md` - 架构设计文档
- `模块清单.md` - 模块清单和测试计划
- `重构总结.md` - 重构总结
- `测试报告.md` - 详细测试报告




