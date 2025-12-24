# 数据生成模块重构架构设计

## 问题分析

### SDGX数据处理流程
1. **DataConnector** -> 提供原始数据
2. **DataLoader** -> 加载数据
3. **Metadata.from_dataloader()** -> 自动推断数据类型（包括日期列）
4. **DataProcessors** -> 处理数据转换
   - `DatetimeFormatter`: 将日期字符串转换为时间戳（int）
   - `NumericValueTransformer`: 处理数值列
   - 其他transformers
5. **Model.fit()** -> 训练模型

### 核心问题
- `DatetimeFormatter` 在 `convert()` 方法中会调用 `datetime.strptime()` 将日期字符串转换为时间戳
- 如果日期字符串格式不正确（如被连接的字符串），转换失败
- 转换失败后，SDGX可能尝试将其转换为数值类型，导致错误

## 新架构设计

### 模块划分

#### 1. DataLoader 模块 (`data_loader.py`)
**职责**: 从各种源加载数据
- 从文件加载（CSV, Excel, JSON）
- 从模板生成数据
- 数据初步验证

#### 2. DataValidator 模块 (`data_validator.py`)
**职责**: 验证和修复数据格式
- 验证数据完整性（非空、行数、列完整性）
- 识别日期列
- 修复日期列格式（确保每个值都是独立的日期字符串）
- 处理异常值（NaN, Inf）

#### 3. DataTransformer 模块 (`data_transformer.py`)
**职责**: 将数据转换为SDGX兼容格式
- 日期列预处理（确保格式正确）
- 数据类型转换
- 列顺序调整

#### 4. SDGXAdapter 模块 (`sdgx_adapter.py`)
**职责**: 封装SDGX调用
- 创建DataConnector
- 创建Synthesizer
- 处理训练和生成流程
- 错误处理和重试

#### 5. SyntheticService 模块 (`synthetic_service.py`)
**职责**: 主服务类，协调各个模块
- 任务管理
- 进度跟踪
- 结果保存

## 数据流设计

```
原始数据源
    ↓
[DataLoader] -> 加载数据
    ↓
[DataValidator] -> 验证和修复
    ↓
[DataTransformer] -> 转换为SDGX格式
    ↓
[SDGXAdapter] -> 调用SDGX
    ↓
生成结果
```

## 关键设计原则

1. **单一职责**: 每个模块只负责一个功能
2. **数据不可变性**: 每个模块返回新的DataFrame，不修改原始数据
3. **可测试性**: 每个模块都可以独立测试
4. **错误处理**: 每个模块都有明确的错误处理机制
5. **日志记录**: 每个关键步骤都有日志记录

## 实现计划

### Phase 1: 创建模块结构
- [x] 创建架构文档
- [ ] 创建 DataLoader 模块
- [ ] 创建 DataValidator 模块
- [ ] 创建 DataTransformer 模块
- [ ] 创建 SDGXAdapter 模块

### Phase 2: 实现核心功能
- [ ] 实现数据加载逻辑
- [ ] 实现数据验证逻辑
- [ ] 实现数据转换逻辑
- [ ] 实现SDGX适配逻辑

### Phase 3: 重构主服务
- [ ] 重构 SyntheticService
- [ ] 集成新模块
- [ ] 测试完整流程

### Phase 4: 测试和优化
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化




