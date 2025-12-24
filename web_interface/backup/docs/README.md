# 测试文档

## 测试结构

```
tests/
├── __init__.py                 # 测试模块初始化
├── conftest.py                 # pytest配置和fixtures
├── test_auth_service.py        # 认证服务单元测试
├── test_synthetic_service.py    # 合成数据生成服务单元测试
├── test_quality_service.py     # 数据质量评估服务单元测试
├── test_masking_service.py     # 数据脱敏服务单元测试
├── test_integration.py         # 集成测试
├── test_system.py              # 系统测试（P0/P1/P2）
├── test_performance.py         # 性能测试
└── test_security.py            # 安全测试
```

## 运行测试

### 运行所有测试

```bash
python run_tests.py
```

或使用pytest：

```bash
pytest tests/ -v
```

### 运行特定测试

```bash
# 运行单元测试
pytest tests/test_auth_service.py -v

# 运行集成测试
pytest tests/test_integration.py -v

# 运行系统测试
pytest tests/test_system.py -v

# 运行性能测试
pytest tests/test_performance.py -v

# 运行安全测试
pytest tests/test_security.py -v
```

### 生成覆盖率报告

```bash
pytest tests/ --cov=services --cov-report=html --cov-report=term-missing
```

覆盖率报告将生成在 `htmlcov/index.html`

## 测试分类

### 1. 单元测试

- **目标**: 覆盖所有服务层函数
- **覆盖率目标**: >80%
- **测试文件**:
  - `test_auth_service.py`: 认证服务测试
  - `test_synthetic_service.py`: 合成数据生成服务测试
  - `test_quality_service.py`: 数据质量评估服务测试
  - `test_masking_service.py`: 数据脱敏服务测试

### 2. 集成测试

- **目标**: 测试模块间交互
- **测试文件**: `test_integration.py`
- **测试场景**:
  - 用户注册到登录流程
  - 文件上传到合成数据生成流程
  - 数据质量评估流程
  - 数据脱敏流程
  - 任务创建到状态更新流程
  - 配置存储和检索
  - 用户数据隔离

### 3. 系统测试

- **目标**: 完整功能测试
- **测试文件**: `test_system.py`
- **优先级分类**:
  - **P0 (核心功能)**:
    - 用户登录
    - 用户注册
    - AI仿真数据生成
    - AI数据质量评估
    - AI数据脱敏
  - **P1 (重要功能)**:
    - 任务管理
    - 任务筛选
    - 系统设置
  - **P2 (辅助功能)**:
    - 操作日志
    - 数据导出
    - 任务分页

### 4. 性能测试

- **目标**: 验证系统性能指标
- **测试文件**: `test_performance.py`
- **测试指标**:
  - 登录接口响应时间: < 500ms
  - 文件上传响应时间（10MB）: < 2s
  - 任务创建响应时间: < 300ms
  - 任务状态查询响应时间: < 100ms
  - 并发登录（10个用户）: < 5s
  - 并发任务创建（5个任务）: < 2s
  - 大数据量文件处理（10000行）: < 5s
  - 数据库查询性能（100个任务）: < 500ms

### 5. 安全测试

- **目标**: 验证系统安全性
- **测试文件**: `test_security.py`
- **测试内容**:
  - SQL注入防护
  - XSS防护
  - 权限控制
  - 文件上传安全
  - 路径遍历防护
  - 密码安全
  - 输入验证

## 测试覆盖率

运行测试后，查看覆盖率报告：

```bash
# 生成HTML报告
pytest tests/ --cov=services --cov-report=html

# 在浏览器中打开
open htmlcov/index.html
```

## 注意事项

1. **测试环境**: 所有测试使用内存数据库（SQLite in-memory），不会影响生产数据
2. **临时文件**: 测试会自动创建和清理临时文件
3. **并发测试**: 性能测试中的并发测试可能需要较长时间
4. **依赖项**: 确保安装了所有测试依赖：
   ```bash
   pip install pytest pytest-cov
   ```

## 持续集成

建议在CI/CD流程中运行测试：

```yaml
# 示例 GitHub Actions 配置
- name: Run tests
  run: |
    pip install -r requirements.txt
    pip install pytest pytest-cov
    pytest tests/ --cov=services --cov-report=xml
```

