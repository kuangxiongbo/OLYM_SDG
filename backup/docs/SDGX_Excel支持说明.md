# SDGX Excel 文件支持说明

## 结论

**SDGX 不支持 Excel 文件（.xlsx/.xls），只支持 CSV 文件。**

## 原因

从 SDGX 源码检查结果：

1. **只有 `CsvConnector`**：
   - SDGX 只提供了 `CsvConnector` 用于读取 CSV 文件
   - 没有 `ExcelConnector` 或 `XlsxConnector`

2. **示例代码只使用 CSV**：
   - 所有 SDGX 示例代码都使用 CSV 文件
   - 没有 Excel 文件的示例

## 解决方案

### 方案 1：使用 DataFrameConnector（当前方案）

对于 Excel 文件，我们的系统会：
1. 使用 `pandas.read_excel()` 读取 Excel 文件
2. 转换为 DataFrame
3. 使用 `DataFrameConnector` 传递给 SDGX

```python
# 当前实现
if source_file_path and source_file_path.endswith('.csv'):
    # 使用 CsvConnector（直接读取源文件）
    data_connector = CsvConnector(path=source_file_path)
else:
    # 使用 DataFrameConnector（Excel 文件需要先读取为 DataFrame）
    data_connector = DataFrameConnector(df=df_for_sdgx)
```

### 方案 2：转换为 CSV（可选）

如果需要完全按照 SDGX 示例代码的方式，可以：
1. 将 Excel 文件转换为 CSV
2. 使用 `CsvConnector` 读取

```python
# 可选实现
if source_file_path.endswith('.xlsx') or source_file_path.endswith('.xls'):
    # 转换为 CSV
    df = pd.read_excel(source_file_path)
    csv_path = source_file_path.replace('.xlsx', '.csv').replace('.xls', '.csv')
    df.to_csv(csv_path, index=False)
    # 使用 CsvConnector
    data_connector = CsvConnector(path=csv_path)
```

## 当前状态

- ✅ **CSV 文件**：支持直接使用 `CsvConnector`（完全按照 SDGX 示例）
- ⚠️ **Excel 文件**：使用 `DataFrameConnector`（需要预处理）

## 日期列被连接的问题

即使使用 `DataFrameConnector`，日期列仍然可能被连接成长字符串。这需要在传递给 SDGX 之前修复。

**修复逻辑**：
1. 检查日期列是否有长度超过 10 的值
2. 使用正则表达式提取第一个日期（YYYY-MM-DD 格式）
3. 确保所有日期值都是 10 个字符




