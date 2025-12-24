# 📡 SDG Web界面API文档

## 📋 概述

SDG Web界面提供完整的RESTful API接口，支持外部系统集成和自动化处理。所有API接口都返回JSON格式数据。

**基础URL**: `http://localhost:5000/api/v1`

## 🔧 通用响应格式

### 成功响应
```json
{
    "success": true,
    "data": {...},
    "message": "操作成功"
}
```

### 错误响应
```json
{
    "success": false,
    "error": "错误信息",
    "code": "ERROR_CODE"
}
```

## 🏥 健康检查

### GET /health
检查API服务状态

**响应示例**:
```json
{
    "status": "healthy",
    "timestamp": "2025-09-18T10:30:00",
    "version": "1.0.0"
}
```

## 🤖 模型管理

### GET /models
获取可用模型列表

**响应示例**:
```json
{
    "success": true,
    "models": {
        "ctgan": {
            "name": "CTGAN",
            "description": "基于GAN的表格数据生成模型",
            "suitable_for": ["数值数据", "分类数据", "混合数据"]
        },
        "gpt": {
            "name": "GPT",
            "description": "基于大语言模型的生成模型",
            "suitable_for": ["文本数据", "小数据集", "语义数据"]
        }
    }
}
```

### GET /models/{model_type}/parameters
获取模型参数配置

**参数**:
- `model_type`: 模型类型 (ctgan, gpt)

**响应示例**:
```json
{
    "success": true,
    "model_type": "ctgan",
    "parameters": {
        "epochs": {
            "type": "number",
            "default": 50,
            "min": 1,
            "max": 1000,
            "description": "训练轮数"
        }
    }
}
```

### POST /models/{model_type}/recommendations
获取模型推荐和参数建议

**请求体**:
```json
{
    "data_info": {
        "shape": [1000, 10],
        "column_types": {
            "numeric": ["age", "income"],
            "categorical": ["gender", "education"]
        }
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "model_type": "ctgan",
    "recommendations": [
        {
            "model": "ctgan",
            "score": 8,
            "reasons": ["数据量充足", "包含数值数据"],
            "confidence": "high"
        }
    ],
    "parameter_suggestions": {
        "epochs": 50,
        "batch_size": 500
    }
}
```

## 📊 数据分析

### POST /data/analyze
分析数据结构

**请求体**:
```json
{
    "data": [
        {"age": 25, "gender": "Male", "income": 50000},
        {"age": 30, "gender": "Female", "income": 60000}
    ]
}
```

**响应示例**:
```json
{
    "success": true,
    "analysis": {
        "shape": [2, 3],
        "columns": ["age", "gender", "income"],
        "dtypes": {"age": "int64", "gender": "object", "income": "int64"},
        "missing_values": {"age": 0, "gender": 0, "income": 0},
        "column_types": {
            "numeric": ["age", "income"],
            "categorical": ["gender"]
        },
        "data_quality": {
            "quality_score": 95.0,
            "recommendations": []
        }
    }
}
```

### POST /data/clean
清洗数据

**请求体**:
```json
{
    "data": [
        {"age": 25, "gender": "Male", "income": 50000},
        {"age": null, "gender": "Female", "income": 60000}
    ],
    "options": {
        "handle_missing": true,
        "missing_strategy": "fill_numeric",
        "remove_duplicates": true
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "cleaned_data": [
        {"age": 25, "gender": "Male", "income": 50000},
        {"age": 25, "gender": "Female", "income": 60000}
    ],
    "shape": [2, 3],
    "columns": ["age", "gender", "income"]
}
```

## 🎯 数据生成

### POST /synthesis/generate
生成合成数据

**请求体**:
```json
{
    "data": [
        {"age": 25, "gender": "Male", "income": 50000},
        {"age": 30, "gender": "Female", "income": 60000}
    ],
    "model_type": "ctgan",
    "model_config": {
        "epochs": 50,
        "batch_size": 500,
        "generator_lr": 0.0002
    },
    "num_samples": 100
}
```

**响应示例**:
```json
{
    "success": true,
    "session_id": "uuid-string",
    "synthetic_data": [
        {"age": 27, "gender": "Male", "income": 52000},
        {"age": 32, "gender": "Female", "income": 58000}
    ],
    "shape": [100, 3],
    "columns": ["age", "gender", "income"]
}
```

## 📈 质量评估

### POST /evaluation/evaluate
评估合成数据质量

**请求体**:
```json
{
    "session_id": "uuid-string"
}
```

或者直接提供数据:
```json
{
    "original_data": [
        {"age": 25, "gender": "Male", "income": 50000}
    ],
    "synthetic_data": [
        {"age": 27, "gender": "Male", "income": 52000}
    ]
}
```

**响应示例**:
```json
{
    "success": true,
    "evaluation_results": {
        "overall_score": 85.5,
        "metrics": {
            "statistical_similarity": {
                "score": 88.2,
                "details": {
                    "age": {
                        "mean_similarity": 0.92,
                        "std_similarity": 0.85
                    }
                }
            },
            "distribution_similarity": {
                "score": 82.1,
                "details": {...}
            }
        },
        "recommendations": [
            "质量良好，可以尝试微调参数"
        ],
        "summary": {
            "quality_level": "良好",
            "quality_color": "info",
            "best_metric": {
                "name": "statistical_similarity",
                "score": 88.2
            }
        }
    }
}
```

## 📁 会话管理

### GET /sessions
列出所有会话

**响应示例**:
```json
{
    "success": true,
    "sessions": [
        {
            "session_id": "uuid-string",
            "model_type": "ctgan",
            "created_at": "2025-09-18T10:30:00",
            "original_shape": [100, 3],
            "synthetic_shape": [100, 3]
        }
    ],
    "total": 1
}
```

### GET /sessions/{session_id}
获取会话信息

**响应示例**:
```json
{
    "success": true,
    "session": {
        "session_id": "uuid-string",
        "model_type": "ctgan",
        "model_config": {...},
        "created_at": "2025-09-18T10:30:00",
        "original_shape": [100, 3],
        "synthetic_shape": [100, 3]
    }
}
```

### GET /sessions/{session_id}/data
获取会话数据

**查询参数**:
- `type`: 数据类型 (original, synthetic)

**响应示例**:
```json
{
    "success": true,
    "data_type": "synthetic",
    "data": [
        {"age": 27, "gender": "Male", "income": 52000}
    ],
    "shape": [100, 3]
}
```

### DELETE /sessions/{session_id}
删除会话

**响应示例**:
```json
{
    "success": true,
    "message": "会话已删除"
}
```

## 🔄 批量处理

### POST /batch/process
批量处理多个数据集

**请求体**:
```json
{
    "datasets": [
        {
            "data": [
                {"age": 25, "gender": "Male", "income": 50000}
            ]
        },
        {
            "data": [
                {"age": 30, "gender": "Female", "income": 60000}
            ]
        }
    ],
    "model_type": "ctgan",
    "model_config": {
        "epochs": 50,
        "batch_size": 500
    },
    "num_samples": 100
}
```

**响应示例**:
```json
{
    "success": true,
    "results": [
        {
            "index": 0,
            "success": true,
            "synthetic_data": [...],
            "shape": [100, 3]
        },
        {
            "index": 1,
            "success": true,
            "synthetic_data": [...],
            "shape": [100, 3]
        }
    ],
    "total_processed": 2,
    "successful": 2
}
```

## 🔧 使用示例

### Python示例

```python
import requests
import json

# 基础URL
BASE_URL = "http://localhost:5000/api/v1"

# 1. 健康检查
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 2. 获取可用模型
response = requests.get(f"{BASE_URL}/models")
models = response.json()
print(models)

# 3. 分析数据
data = [
    {"age": 25, "gender": "Male", "income": 50000},
    {"age": 30, "gender": "Female", "income": 60000}
]

response = requests.post(
    f"{BASE_URL}/data/analyze",
    json={"data": data}
)
analysis = response.json()
print(analysis)

# 4. 生成合成数据
response = requests.post(
    f"{BASE_URL}/synthesis/generate",
    json={
        "data": data,
        "model_type": "ctgan",
        "model_config": {
            "epochs": 50,
            "batch_size": 500
        },
        "num_samples": 100
    }
)
result = response.json()
session_id = result["session_id"]

# 5. 评估质量
response = requests.post(
    f"{BASE_URL}/evaluation/evaluate",
    json={"session_id": session_id}
)
evaluation = response.json()
print(evaluation)
```

### JavaScript示例

```javascript
const BASE_URL = "http://localhost:5000/api/v1";

// 1. 健康检查
fetch(`${BASE_URL}/health`)
    .then(response => response.json())
    .then(data => console.log(data));

// 2. 生成合成数据
const data = [
    {age: 25, gender: "Male", income: 50000},
    {age: 30, gender: "Female", income: 60000}
];

fetch(`${BASE_URL}/synthesis/generate`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        data: data,
        model_type: "ctgan",
        model_config: {
            epochs: 50,
            batch_size: 500
        },
        num_samples: 100
    })
})
.then(response => response.json())
.then(result => {
    console.log(result);
    const sessionId = result.session_id;
    
    // 评估质量
    return fetch(`${BASE_URL}/evaluation/evaluate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({session_id: sessionId})
    });
})
.then(response => response.json())
.then(evaluation => console.log(evaluation));
```

### cURL示例

```bash
# 健康检查
curl -X GET http://localhost:5000/api/v1/health

# 获取模型列表
curl -X GET http://localhost:5000/api/v1/models

# 生成合成数据
curl -X POST http://localhost:5000/api/v1/synthesis/generate \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"age": 25, "gender": "Male", "income": 50000},
      {"age": 30, "gender": "Female", "income": 60000}
    ],
    "model_type": "ctgan",
    "model_config": {
      "epochs": 50,
      "batch_size": 500
    },
    "num_samples": 100
  }'
```

## ⚠️ 错误处理

### 常见错误码

- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

### 错误响应示例

```json
{
    "success": false,
    "error": "模型参数验证失败",
    "validation_errors": [
        "必填参数 openai_API_key 缺失"
    ]
}
```

## 🔒 安全考虑

1. **API密钥**: GPT模型需要有效的API密钥
2. **数据隐私**: 敏感数据建议在本地处理
3. **会话管理**: 会话数据存储在内存中，重启后丢失
4. **请求限制**: 建议添加请求频率限制

## 📈 性能优化

1. **批量处理**: 使用批量接口处理多个数据集
2. **会话复用**: 复用会话避免重复训练
3. **参数调优**: 根据数据特征调整模型参数
4. **数据预处理**: 预先清洗数据提高质量

---

**版本**: 1.0.0  
**最后更新**: 2025-09-18  
**维护者**: SDG开发团队
