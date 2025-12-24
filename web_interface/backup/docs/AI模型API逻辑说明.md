# AI模型API逻辑处理说明

## 概述

系统支持多种AI模型提供商，每个提供商有不同的API格式、认证方式和端点结构。本文档说明系统如何统一处理这些差异。

## 支持的模型提供商

| 提供商ID | 名称 | 默认端点 | 认证方式 |
|---------|------|---------|---------|
| ollama | Ollama | http://localhost:11434/v1 | Bearer Token (可选) |
| openai | OpenAI | https://api.openai.com/v1 | Bearer Token |
| claude | Claude | https://api.anthropic.com/v1 | x-api-key |
| tongyi | 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1 | Bearer Token |
| gemini | Gemini | https://generativelanguage.googleapis.com/v1 | Bearer Token |
| deepseek | Deepseek | https://api.deepseek.com/v1 | Bearer Token |
| moonshot | Moonshot | https://api.moonshot.cn/v1 | Bearer Token |
| doubao | 火山方舟(豆包) | https://ark.cn-beijing.volces.com/api/v3 | Bearer Token |
| qianfan | 百度云千帆 | https://aip.baidubce.com/rpc/2.0/ai_custom/v1 | Bearer Token |
| hunyuan | 腾讯混元 | https://hunyuan.tencentcloudapi.com | Bearer Token |
| zhipu | 智谱 | https://open.bigmodel.cn/api/paas/v4 | Bearer Token |
| grok | Grok | - | Bearer Token |
| openrouter | OpenRouter | - | Bearer Token |

## 统一API客户端

系统提供了统一的`AIModelClient`类（`services/ai_model_client.py`）来处理所有模型的API调用。

### 主要功能

1. **统一认证处理**：根据不同的提供商自动设置正确的认证头
2. **端点格式化**：自动生成正确的API端点URL
3. **请求格式化**：根据提供商格式化请求体
4. **响应解析**：统一解析不同提供商的响应格式

## 认证方式处理

### Bearer Token认证（大多数提供商）

```python
headers['Authorization'] = f'Bearer {api_key}'
```

适用于：OpenAI、Deepseek、Moonshot、Ollama、通义千问、Gemini、智谱、Grok、OpenRouter、火山方舟、百度千帆、腾讯混元

### Claude特殊认证

```python
headers['x-api-key'] = api_key
headers['anthropic-version'] = '2023-06-01'
```

## 端点处理

### 聊天完成端点

不同提供商的聊天完成端点格式：

| 提供商 | 端点格式 |
|--------|---------|
| Ollama | `{endpoint}/api/chat` |
| Claude | `{endpoint}/v1/messages` |
| Gemini | `{endpoint}/models/gemini-pro:generateContent` |
| 火山方舟 | `{endpoint}/chat/completions` |
| 其他 | `{endpoint}/v1/chat/completions` 或 `{endpoint}/chat/completions` |

### 测试连接端点

| 提供商 | 测试端点 |
|--------|---------|
| Ollama | `/api/tags`, `/api/version`, `/api/health` |
| Claude | `/v1/models` |
| Gemini | `/models` |
| 其他 | `/v1/models`, `/models`, `/health` |

## 请求格式处理

### OpenAI兼容格式（大多数提供商）

```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### Claude格式

```json
{
  "model": "claude-3-5-sonnet-20241022",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "max_tokens": 4096
}
```

### Gemini格式

```json
{
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "Hello"}]
    }
  ]
}
```

### Ollama格式

```json
{
  "model": "llama2",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "stream": false
}
```

## 响应格式处理

### OpenAI兼容格式

```json
{
  "choices": [
    {
      "message": {
        "content": "Hello! How can I help you?"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 8,
    "total_tokens": 18
  }
}
```

### Claude格式

```json
{
  "content": [
    {
      "text": "Hello! How can I help you?"
    }
  ],
  "usage": {
    "input_tokens": 10,
    "output_tokens": 8
  }
}
```

### Gemini格式

```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "Hello! How can I help you?"
          }
        ]
      }
    }
  ]
}
```

### Ollama格式

```json
{
  "message": {
    "content": "Hello! How can I help you?"
  },
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 8
  }
}
```

## 使用示例

### 创建客户端

```python
from services.ai_model_client import create_model_client

# 创建Ollama客户端
client = create_model_client(
    provider='ollama',
    endpoint='http://192.168.210.209:11434/v1',
    api_key=None  # Ollama通常不需要API Key
)

# 创建OpenAI客户端
client = create_model_client(
    provider='openai',
    endpoint='https://api.openai.com/v1',
    api_key='sk-...'
)
```

### 测试连接

```python
result = client.test_connection()
if result['connected']:
    print(f"连接成功！响应时间: {result['response_time']}ms")
else:
    print(f"连接失败: {result['message']}")
```

### 发送聊天请求

```python
messages = [
    {'role': 'user', 'content': '你好，请介绍一下自己'}
]

result = client.chat_completion(
    messages=messages,
    model='llama2'  # 对于Ollama
)

if result['success']:
    print(f"回复: {result['content']}")
    print(f"使用量: {result.get('usage', {})}")
else:
    print(f"错误: {result['error']}")
```

### 列出可用模型

```python
result = client.list_models()
if result['success']:
    print(f"可用模型: {result['models']}")
else:
    print(f"错误: {result['error']}")
```

## 在系统设置中使用

系统设置页面（`routes/settings.py`）已经集成了统一的API客户端：

```python
from services.ai_model_client import create_model_client

# 在test_ai_model路由中
client = create_model_client(model_id, endpoint, api_key)
result = client.test_connection()
```

## 特殊处理说明

### Ollama

- **端点协议**：默认使用HTTP（不是HTTPS）
- **API Key**：通常不需要，但某些配置可能需要
- **测试端点**：使用`/api/tags`或`/api/version`
- **聊天端点**：使用`/api/chat`（不是`/chat/completions`）

### Claude

- **认证头**：使用`x-api-key`而不是`Authorization`
- **版本头**：需要`anthropic-version: 2023-06-01`
- **端点**：使用`/v1/messages`而不是`/chat/completions`

### Gemini

- **请求格式**：使用`contents`数组而不是`messages`
- **响应格式**：使用`candidates`数组

### 国内服务商

- **通义千问**：使用OpenAI兼容格式
- **百度千帆**：使用OpenAI兼容格式，但认证可能有特殊要求
- **腾讯混元**：使用OpenAI兼容格式
- **智谱**：使用OpenAI兼容格式
- **火山方舟**：使用OpenAI兼容格式

## 错误处理

统一客户端会处理以下错误：

1. **连接超时**：返回`{'success': False, 'error': '请求超时'}`
2. **连接错误**：返回`{'success': False, 'error': '无法连接到服务器'}`
3. **HTTP错误**：解析响应中的错误信息
4. **JSON解析错误**：返回`{'success': False, 'error': '无效的JSON响应'}`

## 扩展新模型

要添加新的模型提供商：

1. 在`ModelProvider`枚举中添加新的提供商ID
2. 在`_get_headers()`方法中添加认证逻辑
3. 在`_get_chat_endpoint()`方法中添加端点格式
4. 在`_format_messages_for_provider()`方法中添加请求格式化逻辑
5. 在`_parse_response()`方法中添加响应解析逻辑
6. 在`test_connection()`和`list_models()`方法中添加测试端点

## 注意事项

1. **API Key加密**：系统会自动加密存储API Key，调用时会自动解密
2. **SSL验证**：对于自签名证书，客户端会跳过SSL验证（`verify=False`）
3. **超时设置**：默认超时时间为30秒（聊天请求）和5秒（测试连接）
4. **端点格式**：系统会自动处理端点URL的格式（添加/移除尾部斜杠）

## 测试建议

1. **连接测试**：在系统设置页面使用"测试连接"功能
2. **模型列表**：使用`list_models()`方法获取可用模型
3. **聊天测试**：使用`chat_completion()`方法发送测试消息
4. **错误处理**：测试各种错误情况（无效端点、错误API Key等）

