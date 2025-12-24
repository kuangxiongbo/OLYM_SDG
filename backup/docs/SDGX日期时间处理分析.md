# SDGX日期时间处理分析

## 一、SDGX源码中的日期时间处理机制

### 1. DatetimeFormatter的处理逻辑

**位置**: `synthetic-data-generator/sdgx/data_processors/formatters/datetime.py`

**关键代码**:
```python
def datetime_formatter(each_value, datetime_format):
    try:
        datetime_obj = datetime.strptime(str(each_value), datetime_format)
        each_stamp = datetime.timestamp(datetime_obj)
    except Exception as e:
        logger.warning(f"An error occured when convert str to timestamp {e}, we set as mean.")
        logger.warning(f"Input parameters: ({str(each_value)}, {datetime_format})")
        each_stamp = np.nan
    return each_stamp
```

**问题**:
- SDGX使用 `datetime.strptime(str(each_value), datetime_format)` 来解析日期时间
- **如果 `each_value` 是被连接的字符串（如 `'2025/4/1 9:282025/4/1 9:59...'`），`strptime` 无法解析**
- 解析失败后，SDGX会设置 `np.nan`，然后尝试用 `mean()` 填充
- **但如果值太长，可能在转换为数值类型时失败，导致错误：`Could not convert string '...' to numeric`**

### 2. CsvConnector的读取逻辑

**位置**: `synthetic-data-generator/sdgx/data_connectors/csv_connector.py`

**关键代码**:
```python
def _read(self, offset: int = 0, limit: int | None = None) -> pd.DataFrame | None:
    return pd.read_csv(
        self.path,
        sep=self.sep,
        header=self.header,
        skiprows=range(1, offset + 1),
        nrows=limit,
        **self.read_csv_kwargs,
    )
```

**特点**:
- CsvConnector**不做任何预处理**，直接使用 `pd.read_csv()` 读取文件
- 如果CSV文件本身有问题（比如某些行被错误地连接），pandas会原样读取

### 3. DataLoader的分块读取

**位置**: `synthetic-data-generator/sdgx/data_loader.py`

**关键代码**:
```python
def iter(self) -> Generator[pd.DataFrame, None, None]:
    for d in self.cacher.iter(self.chunksize, self.data_connector):
        yield d
```

**特点**:
- DataLoader使用chunksize分块读取数据
- 使用 `pd.concat()` 合并多个chunk，但这是**按行合并**，不会导致列值被连接

## 二、问题根源分析

### 可能的原因

1. **CSV文件本身有问题**
   - 如果CSV文件中的某些行被错误地连接（比如换行符丢失），pandas读取时会读取到被连接的值
   - 例如：`"2025/4/1 9:28","2025/4/1 9:59","2025/4/1 9:50"` 可能被读取为一个值

2. **pandas读取CSV时的解析问题**
   - 如果CSV格式有问题（比如引号未正确闭合），pandas可能会错误地解析值
   - 例如：`"2025/4/1 9:28"2025/4/1 9:59"` 可能被解析为一个值

3. **SDGX无法处理被连接的值**
   - SDGX的DatetimeFormatter期望的是单个日期时间字符串
   - 如果值是被连接的，`strptime` 无法解析，导致错误

## 三、解决方案

### 方案1：在读取CSV后立即修复（当前方案）

**优点**:
- 可以修复CSV文件本身的问题
- 确保传递给SDGX的数据是干净的

**实现**:
```python
# 1. 读取CSV文件
df = pd.read_csv(filepath)

# 2. 立即修复日期时间列中被连接的值
date_columns = identify_date_columns(df)
df = fix_date_columns(df, date_columns)

# 3. 使用DataFrameConnector传递给SDGX
connector = DataFrameConnector(df=df)
```

### 方案2：配置正确的datetime_format

**问题**:
- SDGX的DatetimeFormatter需要正确的 `datetime_format` 才能解析日期时间
- 如果格式不匹配，SDGX会移除该列或设置NaN

**实现**:
```python
# 为日期时间列设置正确的格式
metadata.set_datetime_format('START_TIME', '%Y/%m/%d %H:%M')
```

### 方案3：确保源文件格式正确

**建议**:
- 检查CSV文件是否包含被连接的值
- 确保CSV文件格式正确（引号正确闭合，换行符正确）

## 四、当前代码的处理流程

1. **DataPreparationService.load_data()**: 读取CSV文件为DataFrame
2. **DataPreparationService.fix_critical_issues()**: 修复被连接的日期时间值
3. **SDGXService.create_connector()**: 使用DataFrameConnector创建连接器
4. **SDGXService.create_metadata()**: SDGX自动识别字段类型
5. **SDGX的DatetimeFormatter**: 尝试解析日期时间（如果格式正确）

## 五、关键发现

**SDGX源码本身没有处理被连接日期时间值的逻辑**：
- DatetimeFormatter期望的是单个日期时间字符串
- 如果值是被连接的，`strptime` 无法解析
- 解析失败后，SDGX会设置NaN，但可能在类型转换时失败

**因此，必须在传递给SDGX之前修复被连接的值**。



