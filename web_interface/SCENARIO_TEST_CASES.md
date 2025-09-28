# SDG多账号控制系统 - 重点场景测试用例

## 测试概述

**测试目标**: 验证用户注册场景和合成数据生成场景的完整流程  
**测试环境**: http://localhost:5000  
**测试时间**: 2025-09-27  
**邮箱服务**: kuangxiongbo@163.com  

---

## 测试场景1: 用户注册场景（邮箱验证码）

### 场景描述
验证用户通过邮箱验证码完成注册的完整流程

### 前置条件
- 系统正常运行
- 邮箱服务已配置（kuangxiongbo@163.com）
- 数据库表已创建

### 测试步骤

#### 步骤1: 发送邮箱验证码
**API**: `POST /api/auth/send_verification_code`  
**请求数据**:
```json
{
    "email": "test_new_user@example.com"
}
```

**预期结果**:
- HTTP状态码: 200
- 响应包含: `{"success": true, "message": "验证码已发送到您的邮箱"}`
- 数据库中创建EmailVerification记录
- 实际发送邮件到指定邮箱

#### 步骤2: 验证邮箱验证码
**API**: `POST /api/auth/verify_email`  
**请求数据**:
```json
{
    "email": "test_new_user@example.com",
    "code": "123456"  // 从邮件中获取的实际验证码
}
```

**预期结果**:
- HTTP状态码: 200
- 响应包含: `{"success": true, "message": "邮箱验证成功"}`
- 数据库中EmailVerification记录的verified字段为true

#### 步骤3: 完成用户注册
**API**: `POST /api/auth/register`  
**请求数据**:
```json
{
    "email": "test_new_user@example.com",
    "username": "testuser",
    "password": "test123456",
    "verification_code": "123456"
}
```

**预期结果**:
- HTTP状态码: 200
- 响应包含: `{"success": true, "message": "注册成功"}`
- 数据库中创建新用户记录
- 用户自动登录
- 返回用户信息

### 验证点
1. ✅ 邮箱验证码正确生成（6位数字）
2. ✅ 邮件成功发送到指定邮箱
3. ✅ 验证码有效期为10分钟
4. ✅ 验证码验证功能正常
5. ✅ 用户注册成功并自动登录
6. ✅ 数据库记录正确创建

---

## 测试场景2: 合成数据生成场景

### 场景描述
验证用户使用演示数据完成合成数据生成的完整流程

### 前置条件
- 用户已登录
- 演示数据服务正常运行
- 合成数据生成API可用

### 测试步骤

#### 步骤1: 获取演示行业列表
**API**: `GET /api/demo/industries`  
**认证**: 需要登录

**预期结果**:
- HTTP状态码: 200
- 返回5个行业列表
- 包含金融、电商、医疗、教育、制造业

#### 步骤2: 获取指定行业的数据集
**API**: `GET /api/demo/datasets/finance`  
**认证**: 需要登录

**预期结果**:
- HTTP状态码: 200
- 返回金融行业的3个数据集
- 包含银行客户、股票交易、保险理赔数据

#### 步骤3: 生成演示数据
**API**: `POST /api/demo/generate`  
**请求数据**:
```json
{
    "industry_id": "finance",
    "dataset_id": "bank_customers",
    "size": 100
}
```

**预期结果**:
- HTTP状态码: 200
- 返回生成的演示数据
- 数据格式正确，包含指定字段
- 数据量符合要求

#### 步骤4: 使用演示数据生成合成数据
**API**: `POST /api/synthetic/generate`  
**请求数据**:
```json
{
    "demo_data": {
        "data": [/* 步骤3返回的数据 */],
        "columns": ["customer_id", "age", "income", "credit_score", "loan_history"]
    },
    "model_type": "ctgan",
    "model_config": "default",
    "data_amount": 200,
    "similarity": 0.8
}
```

**预期结果**:
- HTTP状态码: 200
- 返回合成数据生成结果
- 包含原始数据和合成数据对比
- 包含质量评估指标
- 处理时间合理（2-5秒）

### 验证点
1. ✅ 演示数据正确生成
2. ✅ 数据格式和字段正确
3. ✅ 合成数据生成成功
4. ✅ 质量指标计算正确
5. ✅ 数据量符合要求
6. ✅ 响应时间在可接受范围内

---

## 自动化测试脚本

### 测试执行脚本
```bash
#!/bin/bash

echo "=== SDG系统重点场景自动化测试 ==="
echo "测试时间: $(date)"
echo ""

# 设置测试环境
BASE_URL="http://localhost:5000"
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_USERNAME="testuser_$(date +%s)"
TEST_PASSWORD="test123456"

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_status="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo "🧪 执行测试: $test_name"
    
    # 执行测试命令
    result=$(eval "$test_command")
    actual_status=$?
    
    if [ "$actual_status" -eq "$expected_status" ]; then
        echo "✅ 测试通过: $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo "❌ 测试失败: $test_name"
        echo "   预期状态码: $expected_status, 实际状态码: $actual_status"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# 测试1: 发送邮箱验证码
echo "📧 测试场景1: 用户注册场景（邮箱验证码）"
echo ""

run_test "发送邮箱验证码" \
    "curl -s -X POST $BASE_URL/api/auth/send_verification_code -H 'Content-Type: application/json' -d '{\"email\":\"$TEST_EMAIL\"}' | grep -q 'success.*true'" \
    0

if [ $? -eq 0 ]; then
    echo "📬 验证码已发送到: $TEST_EMAIL"
    echo "⏳ 请检查邮箱并输入验证码..."
    read -p "请输入收到的验证码: " VERIFICATION_CODE
    
    # 测试2: 验证邮箱验证码
    run_test "验证邮箱验证码" \
        "curl -s -X POST $BASE_URL/api/auth/verify_email -H 'Content-Type: application/json' -d '{\"email\":\"$TEST_EMAIL\",\"code\":\"$VERIFICATION_CODE\"}' | grep -q 'success.*true'" \
        0
    
    if [ $? -eq 0 ]; then
        # 测试3: 用户注册
        run_test "用户注册" \
            "curl -s -X POST $BASE_URL/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"$TEST_EMAIL\",\"username\":\"$TEST_USERNAME\",\"password\":\"$TEST_PASSWORD\",\"verification_code\":\"$VERIFICATION_CODE\"}' | grep -q 'success.*true'" \
            0
    fi
fi

echo ""
echo "🔬 测试场景2: 合成数据生成场景"
echo ""

# 测试4: 获取演示行业列表
run_test "获取演示行业列表" \
    "curl -s -b cookies.txt $BASE_URL/api/demo/industries | grep -q 'success.*true'" \
    0

# 测试5: 获取金融行业数据集
run_test "获取金融行业数据集" \
    "curl -s -b cookies.txt $BASE_URL/api/demo/datasets/finance | grep -q 'success.*true'" \
    0

# 测试6: 生成演示数据
run_test "生成演示数据" \
    "curl -s -b cookies.txt -X POST $BASE_URL/api/demo/generate -H 'Content-Type: application/json' -d '{\"industry_id\":\"finance\",\"dataset_id\":\"bank_customers\",\"size\":50}' | grep -q 'success.*true'" \
    0

# 测试7: 生成合成数据
run_test "生成合成数据" \
    "curl -s -b cookies.txt -X POST $BASE_URL/api/synthetic/generate -H 'Content-Type: application/json' -d '{\"demo_data\":{\"data\":[],\"columns\":[\"customer_id\",\"age\",\"income\"]},\"model_type\":\"ctgan\",\"data_amount\":100}' | grep -q 'success.*true'" \
    0

# 输出测试结果
echo ""
echo "=== 测试结果汇总 ==="
echo "总测试数: $TOTAL_TESTS"
echo "通过测试: $PASSED_TESTS"
echo "失败测试: $FAILED_TESTS"
echo "通过率: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"

if [ $FAILED_TESTS -eq 0 ]; then
    echo ""
    echo "🎉 所有测试通过！系统功能正常！"
    exit 0
else
    echo ""
    echo "⚠️  存在失败的测试，请检查系统配置"
    exit 1
fi
```

---

## 测试执行计划

### 自动执行测试
1. **启动系统**: 确保应用正常运行
2. **执行测试脚本**: 运行自动化测试脚本
3. **监控结果**: 实时查看测试进度
4. **自动修复**: 发现问题时自动尝试修复
5. **生成报告**: 输出详细的测试报告

### 手动验证步骤
1. **邮箱验证**: 检查实际收到的验证码邮件
2. **数据质量**: 验证生成的合成数据质量
3. **用户体验**: 确认界面操作流畅
4. **性能表现**: 监控响应时间和资源使用

---

## 预期测试结果

### 成功标准
- ✅ 所有API接口正常响应
- ✅ 邮箱验证码功能完整
- ✅ 用户注册流程顺畅
- ✅ 演示数据生成正确
- ✅ 合成数据生成成功
- ✅ 数据质量指标合理
- ✅ 系统性能表现良好

### 失败处理
- 🔧 自动检测配置问题
- 🔧 自动修复常见错误
- 🔧 提供详细的错误信息
- 🔧 建议解决方案

---

**测试用例创建时间**: 2025-09-27  
**版本**: 1.0  
**维护者**: AI Assistant

