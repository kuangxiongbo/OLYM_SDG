# SDGX 字段识别机制说明

## 为什么示例代码可以直接传源文件？

### 1. SDGX 的自动化设计理念

SDGX 的设计理念是**"自动化"**，不需要手动识别字段类型。框架会自动处理类型推断。

### 2. 示例代码的完整流程

```python
# Step 1: 直接使用源文件创建连接器（不需要预处理）
data_connector = CsvConnector(path="data.csv")

# Step 2: 创建数据加载器
data_loader = DataLoader(data_connector)

# Step 3: 自动创建元数据（关键！）
# Metadata.from_dataloader 会自动使用 Inspectors 识别字段类型
loan_metadata = Metadata.from_dataloader(data_loader)

# Step 4: 创建合成器（会自动使用元数据）
synthesizer = Synthesizer(
    metadata=loan_metadata,  # 使用自动识别的元数据
    model=CTGANSynthesizerModel(epochs=128),
    data_connector=data_connector,
)
```

### 3. Metadata.from_dataloader 的自动识别机制

在 `Metadata.from_dataloader` 中，SDGX 会：

1. **自动加载 Inspectors**（检查器）：
   - `NumericInspector` - 识别数值类型（int, float）
   - `IDInspector` - 识别ID类型
   - `DatetimeInspector` - 识别日期时间类型
   - `DiscreteInspector` - 识别离散类型
   - 等等...

2. **扫描数据样本**：
   ```python
   for i, chunk in enumerate(dataloader.iter()):
       for inspector in inspectors:
           if not inspector.ready:
               inspector.fit(chunk)  # 让检查器学习数据特征
   ```

3. **自动标注字段类型**：
   ```python
   for inspector in inspectors:
       inspect_res = inspector.inspect()  # 获取识别结果
       metadata.update(inspect_res)  # 更新元数据
   ```

### 4. 为什么示例代码可以直接传源文件？

**因为 SDGX 会在内部自动处理：**

- ✅ **自动类型推断**：通过 Inspectors 自动识别每个列的类型
- ✅ **自动处理空值**：通过 `NonValueTransformer` 自动处理 NaN
- ✅ **自动格式化**：通过各种 Formatters 自动格式化数据
- ✅ **自动处理异常值**：通过 `OutlierTransformer` 自动处理异常值

### 5. 我们的数据源为什么需要预处理？

虽然 SDGX 有自动识别机制，但我们的数据源有一些**特殊情况**：

1. **混合类型问题**：
   - `CALL_REFNUM` 列是 object 类型，但包含整数和字符串
   - PyArrow 期望 object 列的值都是字符串（bytes）
   - 导致 `Expected bytes, got a 'int' object` 错误

2. **空值字符串问题**：
   - 数据源中可能包含 `'NAN_VALUE'` 字符串
   - SDGX 的 `NonValueTransformer` 会将 NaN 填充为 `'NAN_VALUE'`
   - 如果该列后来被识别为 int 类型，会导致转换错误

3. **类型推断错误**：
   - 如果 object 列包含整数，SDGX 可能错误地将其识别为 int 类型
   - 但该列实际上应该保持为 object 类型（因为包含字符串）

### 6. 解决方案

我们有两个选择：

#### 方案 A：完全按照示例代码（推荐测试）

直接使用源文件，让 SDGX 自己处理：

```python
# 直接使用源文件
data_connector = CsvConnector(path=source_file_path)
synthesizer = Synthesizer(
    model=model,
    data_connector=data_connector,
    # 不提供 metadata，让 SDGX 自动创建
)
```

**优点**：
- 完全按照示例代码
- 让 SDGX 自己处理所有问题
- 代码简单

**缺点**：
- 如果数据源有问题，可能会失败
- 无法控制类型推断结果

#### 方案 B：预处理后使用（当前方案）

在传入 SDGX 之前，先处理特殊情况：

```python
# 预处理：统一 object 列的类型
for col in df.columns:
    if df[col].dtype == 'object':
        # 确保所有值都是字符串类型
        df[col] = df[col].astype(str)
```

**优点**：
- 可以处理特殊情况
- 更可控

**缺点**：
- 需要额外的预处理步骤
- 可能改变原始数据

### 7. 建议

**最佳实践**：

1. **先尝试方案 A**（直接使用源文件）：
   - 如果数据源是干净的，应该可以直接使用
   - 如果失败，再考虑预处理

2. **如果方案 A 失败，使用方案 B**：
   - 只处理必要的特殊情况
   - 保持预处理最小化

3. **关键原则**：
   - **让 SDGX 自己处理**，除非有明确的错误
   - **最小化预处理**，只处理真正的问题
   - **保持数据源干净**，避免引入特殊值（如 'NAN_VALUE'）




