#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI模型API客户端
统一处理不同AI模型的API调用逻辑
"""

import requests
import json
import time
from typing import Dict, Any, Optional, List
from enum import Enum


class ModelProvider(str, Enum):
    """模型提供商枚举"""
    OLLAMA = 'ollama'
    OPENAI = 'openai'
    CLAUDE = 'claude'
    TONGYI = 'tongyi'
    GEMINI = 'gemini'
    DEEPSEEK = 'deepseek'
    MOONSHOT = 'moonshot'
    DOUBAO = 'doubao'
    QIANFAN = 'qianfan'
    HUNYUAN = 'hunyuan'
    ZHIPU = 'zhipu'
    GROK = 'grok'
    OPENROUTER = 'openrouter'


class AIModelClient:
    """AI模型API客户端"""
    
    def __init__(self, provider: str, endpoint: str, api_key: Optional[str] = None):
        """
        初始化AI模型客户端
        
        Args:
            provider: 模型提供商ID
            endpoint: API端点URL
            api_key: API密钥（可选）
        """
        self.provider = provider.lower()
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.timeout = 30
        
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        if not self.api_key:
            return headers
        
        # 根据不同的提供商设置不同的认证头
        if self.provider in [ModelProvider.OPENAI, ModelProvider.DEEPSEEK, 
                            ModelProvider.MOONSHOT, ModelProvider.OLLAMA,
                            ModelProvider.TONGYI, ModelProvider.GEMINI,
                            ModelProvider.ZHIPU, ModelProvider.GROK,
                            ModelProvider.OPENROUTER]:
            headers['Authorization'] = f'Bearer {self.api_key}'
        elif self.provider == ModelProvider.CLAUDE:
            headers['x-api-key'] = self.api_key
            headers['anthropic-version'] = '2023-06-01'
        elif self.provider == ModelProvider.DOUBAO:
            headers['Authorization'] = f'Bearer {self.api_key}'
        elif self.provider == ModelProvider.QIANFAN:
            # 百度千帆使用特殊的认证方式
            headers['Authorization'] = f'Bearer {self.api_key}'
        elif self.provider == ModelProvider.HUNYUAN:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers
    
    def _get_chat_endpoint(self) -> str:
        """获取聊天完成端点"""
        if self.provider == ModelProvider.OLLAMA:
            # Ollama: 完全按配置的 endpoint 来拼接，不做 /v1 等版本号假设
            base = self.endpoint.rstrip('/')
            return f'{base}/chat/completions'
        elif self.provider == ModelProvider.CLAUDE:
            # Claude使用 /v1/messages 端点
            return f'{self.endpoint}/v1/messages'
        elif self.provider == ModelProvider.GEMINI:
            # Gemini使用特殊的端点格式
            return f'{self.endpoint}/models/gemini-pro:generateContent'
        elif self.provider == ModelProvider.DOUBAO:
            # 火山方舟使用 /api/v3/chat/completions
            return f'{self.endpoint}/chat/completions'
        elif self.provider == ModelProvider.QIANFAN:
            # 百度千帆使用 /chat/completions
            return f'{self.endpoint}/chat/completions'
        elif self.provider == ModelProvider.HUNYUAN:
            # 腾讯混元使用 /chat/completions
            return f'{self.endpoint}/chat/completions'
        elif self.provider == ModelProvider.ZHIPU:
            # 智谱使用 /chat/completions
            return f'{self.endpoint}/chat/completions'
        else:
            # OpenAI兼容格式：/v1/chat/completions
            if '/v1' in self.endpoint:
                return f'{self.endpoint}/chat/completions'
            else:
                return f'{self.endpoint}/v1/chat/completions'
    
    def _format_messages_for_provider(self, messages: List[Dict[str, str]], 
                                     model: str) -> Dict[str, Any]:
        """根据提供商格式化消息"""
        if self.provider == ModelProvider.CLAUDE:
            # Claude使用messages格式
            return {
                'model': model,
                'messages': messages,
                'max_tokens': 4096
            }
        elif self.provider == ModelProvider.GEMINI:
            # Gemini使用特殊的格式
            contents = []
            for msg in messages:
                role = 'user' if msg['role'] == 'user' else 'model'
                contents.append({
                    'role': role,
                    'parts': [{'text': msg['content']}]
                })
            return {
                'contents': contents
            }
        elif self.provider == ModelProvider.OLLAMA:
            # Ollama使用messages格式
            return {
                'model': model,
                'messages': messages,
                'stream': False
            }
        else:
            # OpenAI兼容格式
            return {
                'model': model,
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 2000
            }
    
    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """解析响应"""
        try:
            data = response.json()
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': f'无效的JSON响应: {response.text[:200]}'
            }
        
        if response.status_code >= 400:
            error_msg = data.get('error', {}).get('message', '未知错误') if isinstance(data.get('error'), dict) else str(data.get('error', '未知错误'))
            return {
                'success': False,
                'error': error_msg,
                'status_code': response.status_code
            }
        
        # 根据不同提供商解析响应
        if self.provider == ModelProvider.CLAUDE:
            # Claude响应格式
            content = data.get('content', [])
            if content and len(content) > 0:
                text = content[0].get('text', '')
            else:
                text = ''
            return {
                'success': True,
                'content': text,
                'usage': data.get('usage', {})
            }
        elif self.provider == ModelProvider.GEMINI:
            # Gemini响应格式
            candidates = data.get('candidates', [])
            if candidates and len(candidates) > 0:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                text = parts[0].get('text', '') if parts else ''
            else:
                text = ''
            return {
                'success': True,
                'content': text
            }
        elif self.provider == ModelProvider.OLLAMA:
            # Ollama响应格式
            return {
                'success': True,
                'content': data.get('message', {}).get('content', ''),
                'usage': data.get('usage', {})
            }
        else:
            # OpenAI兼容格式
            choices = data.get('choices', [])
            if choices and len(choices) > 0:
                text = choices[0].get('message', {}).get('content', '')
            else:
                text = ''
            return {
                'success': True,
                'content': text,
                'usage': data.get('usage', {})
            }
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       model: Optional[str] = None,
                       **kwargs) -> Dict[str, Any]:
        """
        发送聊天完成请求
        
        Args:
            messages: 消息列表，格式：[{'role': 'user', 'content': '...'}]
            model: 模型名称（可选，某些提供商需要）
            **kwargs: 其他参数
        
        Returns:
            包含success、content、usage等字段的字典
        """
        try:
            # 获取端点
            url = self._get_chat_endpoint()
            
            # 格式化请求体
            request_data = self._format_messages_for_provider(messages, model or 'default')
            
            # 合并额外参数
            request_data.update(kwargs)
            
            # 发送请求
            headers = self._get_headers()
            response = requests.post(
                url,
                headers=headers,
                json=request_data,
                timeout=self.timeout,
                verify=False  # 对于自签名证书，允许不验证
            )
            
            # 解析响应
            return self._parse_response(response)
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': '请求超时'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': '无法连接到服务器'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试连接
        
        Returns:
            包含connected、response_time、message等字段的字典
        """
        start_time = time.time()
        
        try:
            # 根据不同提供商选择测试端点
            if self.provider == ModelProvider.OLLAMA:
                # Ollama测试端点：先尝试/v1/models（OpenAI兼容），再尝试/api/tags
                base_url = self.endpoint.rstrip('/')
                if base_url.endswith('/v1'):
                    test_urls = [
                        f'{base_url}/models',
                        f'{base_url}/chat/completions',
                        base_url
                    ]
                else:
                    # 如果没有/v1，尝试/api端点
                    test_urls = [
                        f'{base_url}/v1/models',
                        f'{base_url}/api/tags',
                        f'{base_url}/api/version'
                    ]
            elif self.provider == ModelProvider.CLAUDE:
                test_urls = [
                    f'{self.endpoint}/v1/models'
                ]
            elif self.provider == ModelProvider.GEMINI:
                test_urls = [
                    f'{self.endpoint}/models'
                ]
            else:
                # OpenAI兼容格式
                test_urls = [
                    f'{self.endpoint}/v1/models',
                    f'{self.endpoint}/models',
                    f'{self.endpoint}/health'
                ]
            
            connected = False
            error_message = None
            models_count = 0
            
            for url in test_urls:
                try:
                    headers = self._get_headers()
                    response = requests.get(
                        url,
                        headers=headers,
                        timeout=10,
                        verify=False
                    )
                    
                    response_time = int((time.time() - start_time) * 1000)
                    
                    # 判断是否连接成功，并验证响应内容
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            # 验证响应格式，确保可以获取模型列表
                            if self.provider == ModelProvider.OLLAMA:
                                # Ollama OpenAI兼容格式: {"data": [{"id": "...", ...}]}
                                # 或 Ollama原生格式: {"models": [...]}
                                if 'data' in data and isinstance(data['data'], list):
                                    models_count = len(data['data'])
                                    connected = models_count > 0
                                    if not connected:
                                        error_message = '模型列表为空'
                                elif 'models' in data and isinstance(data['models'], list):
                                    models_count = len(data['models'])
                                    connected = models_count > 0
                                    if not connected:
                                        error_message = '模型列表为空'
                                else:
                                    # 如果不是模型列表格式，继续尝试下一个URL
                                    continue
                            else:
                                # OpenAI兼容格式: {"data": [{"id": "...", ...}]}
                                if 'data' in data and isinstance(data['data'], list):
                                    models_count = len(data['data'])
                                    connected = models_count > 0
                                    if not connected:
                                        error_message = '模型列表为空'
                                else:
                                    # 如果不是模型列表格式，继续尝试下一个URL
                                    continue
                        except json.JSONDecodeError:
                            # 响应不是JSON，继续尝试下一个URL
                            continue
                    elif response.status_code < 500:
                        connected = True
                        break
                    else:
                        error_message = f'HTTP {response.status_code}'
                        
                except requests.exceptions.Timeout:
                    error_message = '连接超时（10秒）'
                except requests.exceptions.ConnectionError:
                    error_message = '无法连接到服务器，请检查URL是否正确'
                except Exception as e:
                    error_message = f'连接失败: {str(e)}'
            
            response_time = int((time.time() - start_time) * 1000)
            
            # 构建返回消息
            if connected:
                message = f'连接成功，找到 {models_count} 个模型'
            else:
                message = error_message or '连接失败'
            
            return {
                'connected': connected,
                'response_time': response_time,
                'message': message,
                'models_count': models_count
            }
            
        except Exception as e:
            return {
                'connected': False,
                'response_time': int((time.time() - start_time) * 1000),
                'message': f'连接失败: {str(e)}'
            }
    
    def list_models(self) -> Dict[str, Any]:
        """
        列出可用的模型
        
        Returns:
            包含success、models等字段的字典
        """
        try:
            base = self.endpoint.rstrip('/')
            if self.provider == ModelProvider.OLLAMA:
                # Ollama:
                # - 如果 Endpoint 已经是 OpenAI 兼容形式（以 /vX 结尾），按 OpenAI 规范请求 /models
                #   例如: http://host:11434/v1  -> http://host:11434/v1/models
                # - 否则按 Ollama 原生接口请求 /api/tags
                import re
                if re.search(r'/v\d+$', base):
                    url = f'{base}/models'
                else:
                    url = f'{base}/api/tags'
            elif self.provider == ModelProvider.CLAUDE:
                url = f'{base}/v1/models'
            elif self.provider == ModelProvider.GEMINI:
                url = f'{base}/models'
            else:
                # OpenAI兼容格式
                url = f'{base}/v1/models'
            
            headers = self._get_headers()
            response = requests.get(
                url,
                headers=headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code >= 400:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'models': []
                }
            
            data = response.json()
            
            # 解析模型列表
            if self.provider == ModelProvider.OLLAMA:
                models = [m.get('name', '') for m in data.get('models', [])]
            elif self.provider == ModelProvider.CLAUDE:
                models = [m.get('id', '') for m in data.get('data', [])]
            elif self.provider == ModelProvider.GEMINI:
                models = [m.get('name', '').split('/')[-1] for m in data.get('models', [])]
            else:
                # OpenAI兼容格式
                models = [m.get('id', '') for m in data.get('data', [])]
            
            return {
                'success': True,
                'models': models
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'models': []
            }


def create_model_client(provider: str, endpoint: str, 
                       api_key: Optional[str] = None) -> AIModelClient:
    """
    创建AI模型客户端
    
    Args:
        provider: 模型提供商ID
        endpoint: API端点URL
        api_key: API密钥（可选）
    
    Returns:
        AIModelClient实例
    """
    return AIModelClient(provider, endpoint, api_key)

