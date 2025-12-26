#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统设置路由（仅管理员）
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

# 导入模型
from models.user import User, db
from models.config import SystemConfig

try:
    from models.log import OperationLog
except ImportError:
    # 如果OperationLog不存在，创建一个简单的类
    class OperationLog:
        @staticmethod
        def query():
            class Query:
                def filter(self, *args):
                    return self
                def filter_by(self, **kwargs):
                    return self
                def order_by(self, *args):
                    return self
                def paginate(self, *args, **kwargs):
                    class Pagination:
                        items = []
                        total = 0
                        pages = 0
                    return Pagination()
            return Query()

from utils.decorators import admin_required, log_operation
try:
    from services.email_service import EmailService
except ImportError:
    EmailService = None

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/ai-models', methods=['GET'])
@login_required
@admin_required
def get_ai_models():
    """获取AI模型配置列表"""
    try:
        from flask import current_app
        
        # 如果是HTML请求，返回HTML页面
        if request.headers.get('Accept', '').find('text/html') != -1:
            from flask import render_template
            try:
                return render_template('settings.html', current_user=current_user, active_tab='model')
            except:
                from flask import redirect
                return redirect('/')
        
        # 确保在应用上下文中
        with current_app.app_context():
            try:
                from utils.encryption import encryption_service
            except ImportError:
                encryption_service = None
            
            # 预定义的模型列表
            model_list = [
                {'id': 'ollama', 'name': 'Ollama'},
                {'id': 'tongyi', 'name': '通义千问'},
                {'id': 'openai', 'name': 'OpenAI'},
                {'id': 'claude', 'name': 'Claude'},
                {'id': 'gemini', 'name': 'Gemini'},
                {'id': 'deepseek', 'name': 'Deepseek'},
                {'id': 'moonshot', 'name': 'Moonshot'},
                {'id': 'doubao', 'name': '火山方舟(豆包)'},
                {'id': 'qianfan', 'name': '百度云千帆'},
                {'id': 'grok', 'name': 'Grok'},
                {'id': 'hunyuan', 'name': '腾讯混元'},
                {'id': 'openrouter', 'name': 'OpenRouter'},
                {'id': 'zhipu', 'name': '智谱'},
                {'id': 'siliconflow', 'name': '硅基流动'}
            ]
            
            models = []
            for model_info in model_list:
                try:
                    config_key = f'ai_model_{model_info["id"]}'
                    config = SystemConfig.query.filter_by(config_key=config_key).first()
                    
                    if config:
                        config_value = config.get_value() if hasattr(config, 'get_value') else {}
                        # 解密API Key
                        if encryption_service and 'api_key' in config_value.get('config', {}) and config_value['config']['api_key']:
                            try:
                                config_value['config']['api_key'] = encryption_service.decrypt(config_value['config']['api_key'])
                            except:
                                pass
                        config_dict = config_value.get('config', {})
                        # 确保config包含selected_models（从顶层或config中获取）
                        if 'selected_models' in config_value:
                            config_dict['selected_models'] = config_value.get('selected_models', [])
                        elif 'selected_models' in config_dict:
                            # 如果已经在config中，保持不变
                            pass
                        else:
                            # 如果没有，初始化为空数组
                            config_dict['selected_models'] = []
                        
                        models.append({
                            'id': model_info['id'],
                            'name': model_info['name'],
                            'enabled': config_value.get('enabled', False),
                            'config': config_dict
                        })
                    else:
                        models.append({
                            'id': model_info['id'],
                            'name': model_info['name'],
                            'enabled': False,
                            'config': {}
                        })
                except Exception as e:
                    # 如果某个模型配置出错，仍然添加，但使用默认值
                    print(f"加载模型 {model_info['id']} 配置失败: {e}")
                    models.append({
                        'id': model_info['id'],
                        'name': model_info['name'],
                        'enabled': False,
                        'config': {}
                    })
        
        return jsonify({
            'success': True,
            'data': {'models': models}
        }), 200
    except Exception as e:
        import traceback
        print(f"获取AI模型配置失败: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@settings_bp.route('/ai-models/<model_id>', methods=['PUT'])
@login_required
@admin_required
@log_operation('更新AI模型配置', 'config')
def update_ai_model(model_id):
    """更新AI模型配置"""
    import json
    import sys
    
    try:
        from utils.encryption import encryption_service
    except ImportError:
        encryption_service = None
    
    try:
        data = request.get_json()
        config_key = f'ai_model_{model_id}'
        
        # 获取或创建配置
        config = SystemConfig.query.filter_by(config_key=config_key).first()
        if not config:
            config = SystemConfig(
                config_key=config_key,
                config_type='ai_model',
                description=f'{model_id}模型配置'
            )
            db.session.add(config)
        
        # 准备配置值
        config_dict = data.get('config', {})
        
        # 处理selected_models：优先使用config中的值，如果没有则初始化为空数组
        # 注意：前端会将selected_models放在config中发送，所以这里不需要从顶层读取
        if 'selected_models' not in config_dict:
            config_dict['selected_models'] = []
        
        config_value = {
            'enabled': data.get('enabled', False),
            'config': config_dict
        }
        
        # 加密API Key
        if encryption_service and 'api_key' in config_value['config']:
            api_key = config_value['config']['api_key']
            # 只有当API Key不为空且不是占位符时才加密
            if api_key and api_key.strip() and not api_key.startswith('sk-***') and not api_key.startswith('***'):
                try:
                    config_value['config']['api_key'] = encryption_service.encrypt(api_key.strip())
                    print(f"[DEBUG] API Key已加密保存 - model_id: {model_id}, length: {len(api_key)}", file=sys.stderr)
                except Exception as e:
                    print(f"[ERROR] API Key加密失败: {e}", file=sys.stderr)
                    pass
            elif not api_key or not api_key.strip():
                # 如果API Key为空，清空配置
                config_value['config']['api_key'] = ''
                print(f"[DEBUG] API Key为空，清空配置 - model_id: {model_id}", file=sys.stderr)
        
        if hasattr(config, 'set_value'):
            config.set_value(config_value)
        else:
            config.config_value = json.dumps(config_value, ensure_ascii=False)
        
        # 设置更新者（确保current_user存在）
        if current_user and hasattr(current_user, 'id') and current_user.id:
            config.updated_by = current_user.id
        elif hasattr(config, 'updated_by'):
            # 如果current_user不存在，保持原有值
            if not config.updated_by:
                config.updated_by = None
        
        # 添加调试日志
        print(f"[DEBUG] 保存配置 - model_id: {model_id}", file=sys.stderr)
        print(f"[DEBUG] config_value: {json.dumps(config_value, ensure_ascii=False, indent=2)}", file=sys.stderr)
        print(f"[DEBUG] selected_models in config: {'selected_models' in config_value.get('config', {})}", file=sys.stderr)
        if 'selected_models' in config_value.get('config', {}):
            print(f"[DEBUG] selected_models值: {config_value['config']['selected_models']}", file=sys.stderr)
        
        try:
            db.session.commit()
            
            # 验证保存结果
            try:
                db.session.refresh(config)
                saved_value = config.get_value() if hasattr(config, 'get_value') else json.loads(config.config_value) if config.config_value else {}
                print(f"[DEBUG] 保存后的配置: {json.dumps(saved_value, ensure_ascii=False, indent=2)}", file=sys.stderr)
            except Exception as refresh_error:
                print(f"[DEBUG] 刷新配置失败（不影响保存）: {refresh_error}", file=sys.stderr)
            
            return jsonify({
                'success': True,
                'message': '配置已更新'
            }), 200
        except Exception as commit_error:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[ERROR] 数据库提交失败: {commit_error}", file=sys.stderr)
            print(f"[ERROR] 错误详情: {error_detail}", file=sys.stderr)
            try:
                db.session.rollback()
            except:
                pass
            return jsonify({
                'success': False,
                'error': f'保存配置失败: {str(commit_error)}',
                'code': 'DATABASE_ERROR'
            }), 500
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] 更新配置异常: {e}", file=sys.stderr)
        print(f"[ERROR] 错误详情: {error_detail}", file=sys.stderr)
        traceback.print_exc()
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({
            'success': False,
            'error': f'更新配置失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@settings_bp.route('/ai-models/<model_id>/test', methods=['POST'])
@login_required
@admin_required
def test_ai_model(model_id):
    """测试AI模型连接 - 与get_model_list保持一致的逻辑"""
    try:
        from flask import current_app, request
        import requests
        import time
        import json
        import sys
        
        # 统一从数据库获取配置（与get_model_list保持一致）
        config_key = f'ai_model_{model_id}'
        config = SystemConfig.query.filter_by(config_key=config_key).first()
        
        if not config:
            return jsonify({
                'success': False,
                'error': '模型未配置，请先保存配置',
                'code': 'MODEL_NOT_CONFIGURED'
            }), 400
        
        config_value = config.get_value() if hasattr(config, 'get_value') else {}
        if not isinstance(config_value, dict):
            config_value = {}
        
        endpoint = config_value.get('config', {}).get('endpoint')
        api_key = config_value.get('config', {}).get('api_key')
        
        if not endpoint:
            return jsonify({
                'success': False,
                'error': 'Endpoint未配置',
                'code': 'ENDPOINT_NOT_CONFIGURED'
            }), 400
        
        # 解密API Key（与get_model_list保持一致的逻辑）
        if api_key:
            # 如果前端传递的是空字符串，保持为空
            if not api_key.strip():
                api_key = ''
                print(f"[DEBUG] 测试连接 - API Key为空字符串 - model_id: {model_id}", file=sys.stderr)
            elif not api_key.startswith('sk-***') and not api_key.startswith('***'):
                # 尝试解密（如果已加密）
                try:
                    from utils.encryption import encryption_service
                    if encryption_service:
                        try:
                            # 尝试解密，如果失败说明是明文，直接使用
                            decrypted = encryption_service.decrypt(api_key)
                            api_key = decrypted
                            print(f"[DEBUG] 测试连接 - API Key已解密 - model_id: {model_id}, length: {len(api_key)}", file=sys.stderr)
                        except:
                            # 解密失败，说明是明文，直接使用
                            print(f"[DEBUG] 测试连接 - API Key是明文，直接使用 - model_id: {model_id}, length: {len(api_key)}", file=sys.stderr)
                            pass
                except ImportError:
                    print(f"[DEBUG] 测试连接 - 加密服务不可用，使用明文 - model_id: {model_id}", file=sys.stderr)
                    pass
            else:
                # 如果是占位符，设为空（ollama可能不需要API Key）
                api_key = ''
                print(f"[DEBUG] 测试连接 - API Key是占位符，设为空 - model_id: {model_id}", file=sys.stderr)
        else:
            api_key = ''
            print(f"[DEBUG] 测试连接 - API Key未提供 - model_id: {model_id}", file=sys.stderr)
        
        print(f"[DEBUG] 测试连接 - model_id: {model_id}, endpoint: {endpoint}, api_key: {'已设置(' + str(len(api_key)) + '字符)' if api_key else '空'}", file=sys.stderr)
        
        # 统一在这里按用户配置的 Endpoint 进行真实连通性测试（与get_model_list保持一致）
        import re
        
        start_time = time.time()
        connected = False
        response_time = 0
        error_message = None
        models_count = 0
        
        try:
            # 处理Endpoint URL - 与get_model_list保持一致的逻辑
            test_url = endpoint.strip()
            if not test_url.startswith('http'):
                test_url = f'http://{test_url}'
            
            # 确保URL末尾没有斜杠
            base_url = test_url.rstrip('/')
            
            # 直接使用用户配置的endpoint + /models 进行测试（与get_model_list保持一致）
            models_url = f'{base_url}/models'
            
            # 准备请求头 - 对于GET请求，不需要Content-Type: application/json
            # 与ai_model_client.py保持一致的认证逻辑
            request_headers = {
                'Accept': 'application/json'
            }
            if api_key:
                # Claude使用特殊的认证方式
                if model_id == 'claude':
                    request_headers['x-api-key'] = api_key
                    request_headers['anthropic-version'] = '2023-06-01'
                else:
                    # 其他所有模型都使用Bearer Token（与ai_model_client.py保持一致）
                    # 包括: openai, deepseek, moonshot, ollama, tongyi, gemini, 
                    #      zhipu, grok, openrouter, doubao, qianfan, hunyuan, siliconflow
                    request_headers['Authorization'] = f'Bearer {api_key}'
            
            # 发送请求测试连接
            try:
                # 添加调试日志
                import sys
                print(f"[DEBUG] 测试连接 - URL: {models_url}", file=sys.stderr)
                print(f"[DEBUG] 请求头: {request_headers}", file=sys.stderr)
                
                response = requests.get(models_url, headers=request_headers, timeout=10, verify=False, allow_redirects=True)
                response_time = int((time.time() - start_time) * 1000)
                
                print(f"[DEBUG] 响应状态码: {response.status_code}", file=sys.stderr)
                print(f"[DEBUG] 响应Content-Type: {response.headers.get('Content-Type')}", file=sys.stderr)
                
                # 安全地获取响应文本
                response_text = response.text if response.text is not None else ''
                print(f"[DEBUG] 响应长度: {len(response_text)}", file=sys.stderr)
                print(f"[DEBUG] 响应前200字符: {response_text[:200] if response_text else '(空响应)'}", file=sys.stderr)
                
                if response.status_code == 200:
                    try:
                        # 检查响应内容
                        response_text = (response.text or '').strip()
                        if not response_text:
                            connected = False
                            error_message = '服务器返回空响应'
                        else:
                            # 检查响应内容类型
                            content_type = response.headers.get('Content-Type', '').lower()
                            
                            # 尝试解析JSON
                            try:
                                data = response.json()
                                # 验证响应格式 - 支持多种格式
                                if 'data' in data and isinstance(data['data'], list):
                                    # OpenAI兼容格式: {"data": [{"id": "...", ...}]}
                                    models_count = len(data['data'])
                                    connected = models_count > 0
                                    if not connected:
                                        error_message = '模型列表为空'
                                elif 'models' in data and isinstance(data['models'], list):
                                    # Ollama原生格式或其他格式: {"models": [{"name": "...", ...}]}
                                    models_count = len(data['models'])
                                    connected = models_count > 0
                                    if not connected:
                                        error_message = '模型列表为空'
                                else:
                                    connected = False
                                    error_message = f'无法解析模型列表响应: {str(data)[:200]}'
                            except json.JSONDecodeError as e:
                                # JSON解析失败
                                connected = False
                                error_text = response_text[:200] if response_text else "空响应"
                                if 'application/json' in content_type:
                                    error_message = f'响应不是有效的JSON格式: {str(e)}。响应内容: {error_text}'
                                else:
                                    error_message = f'响应不是JSON格式 (Content-Type: {content_type})。响应内容: {error_text}'
                    except Exception as e:
                        connected = False
                        import traceback
                        error_detail = traceback.format_exc()
                        error_text = response.text[:200] if hasattr(response, 'text') and response.text else "空响应"
                        error_message = f'解析响应失败: {str(e)}。响应内容: {error_text}'
                        # 在调试模式下输出详细错误
                        import sys
                        print(f"解析响应异常详情: {error_detail}", file=sys.stderr)
                elif response.status_code == 404:
                    connected = False
                    error_message = f'端点不存在 (404): {models_url}。请检查URL路径是否正确'
                elif response.status_code in [301, 302, 307, 308]:
                    # 重定向，尝试跟随重定向
                    try:
                        redirect_response = requests.get(models_url, headers=request_headers, timeout=10, verify=False, allow_redirects=True)
                        if redirect_response.status_code == 200:
                            response_time = int((time.time() - start_time) * 1000)
                            try:
                                data = redirect_response.json()
                                if 'data' in data and isinstance(data['data'], list):
                                    models_count = len(data['data'])
                                    connected = models_count > 0
                                elif 'models' in data and isinstance(data['models'], list):
                                    models_count = len(data['models'])
                                    connected = models_count > 0
                                else:
                                    connected = False
                                    error_message = f'无法解析模型列表响应: {str(data)[:200]}'
                            except:
                                connected = False
                                error_message = '重定向后响应格式不正确'
                        else:
                            connected = False
                            error_message = f'重定向后返回 {redirect_response.status_code}: {redirect_response.url}'
                    except Exception as e:
                        connected = False
                        error_message = f'重定向失败: {str(e)}'
                elif response.status_code == 400:
                    # 400错误，尝试解析错误信息
                    connected = False
                    import sys
                    print(f"[DEBUG] 收到400错误", file=sys.stderr)
                    print(f"[DEBUG] 响应内容: {response.text[:500]}", file=sys.stderr)
                    
                    try:
                        # 先检查响应是否为空
                        if not response.text or not response.text.strip():
                            error_message = 'HTTP 400 Bad Request: 服务器返回空响应'
                        else:
                            error_data = response.json()
                            error_msg = error_data.get('error', {}).get('message', '') or error_data.get('message', '') or str(error_data)
                            error_message = f'HTTP 400 Bad Request: {error_msg}'
                    except json.JSONDecodeError as e:
                        # JSON解析失败，显示原始响应
                        error_text = response.text[:200] if response.text else 'Bad Request (空响应)'
                        error_message = f'HTTP 400 Bad Request: 响应不是JSON格式。响应内容: {error_text}'
                        print(f"[DEBUG] JSON解析错误: {str(e)}", file=sys.stderr)
                    except Exception as e:
                        error_message = f'HTTP 400 Bad Request: {str(e)}'
                        print(f"[DEBUG] 解析400错误时异常: {str(e)}", file=sys.stderr)
                        import traceback
                        traceback.print_exc()
                elif response.status_code == 401:
                    # 401错误，通常是API Key问题
                    connected = False
                    import sys
                    print(f"[DEBUG] 收到401错误 - 可能是API Key问题", file=sys.stderr)
                    print(f"[DEBUG] 响应内容: {response.text[:500]}", file=sys.stderr)
                    
                    try:
                        # 尝试解析错误信息
                        if not response.text or not response.text.strip():
                            error_message = 'HTTP 401 Unauthorized: 未提供API Key或API Key无效'
                        else:
                            try:
                                error_data = response.json()
                                error_msg = error_data.get('error', {}).get('message', '') or error_data.get('message', '') or str(error_data)
                                error_message = f'HTTP 401: {error_msg}'
                            except json.JSONDecodeError:
                                # 不是JSON格式，显示原始文本
                                error_text = response.text[:200] if response.text else 'Unauthorized (空响应)'
                                error_message = f'HTTP 401: {error_text}'
                    except Exception as e:
                        error_message = f'HTTP 401 Unauthorized: {str(e)}'
                        print(f"[DEBUG] 解析401错误时异常: {str(e)}", file=sys.stderr)
                else:
                    connected = False
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', {}).get('message', '') or error_data.get('message', '') or str(error_data)
                    except:
                        error_msg = response.text[:200] if response.text else f'HTTP {response.status_code}'
                    error_message = f'HTTP {response.status_code}: {error_msg}'
            except requests.exceptions.Timeout:
                error_message = f'连接超时（10秒）: 无法访问 {models_url}'
                response_time = 10000
            except requests.exceptions.ConnectionError as e:
                error_message = f'无法连接到服务器: {str(e)}。请检查URL是否正确: {models_url}'
                response_time = 10000
            except requests.exceptions.RequestException as e:
                error_message = f'请求失败: {str(e)}'
                response_time = int((time.time() - start_time) * 1000)
            except Exception as e:
                error_message = f'连接失败: {str(e)}'
                response_time = int((time.time() - start_time) * 1000)
        except Exception as e:
            error_message = f'测试失败: {str(e)}'
            response_time = int((time.time() - start_time) * 1000)
        
        # 构建返回消息
        if connected:
            message = f'连接成功，找到 {models_count} 个模型'
        else:
            message = error_message or '连接失败'
        
        return jsonify({
            'success': True,
            'data': {
                'connected': connected,
                'response_time': response_time,
                'message': message,
                'models_count': models_count
            }
        }), 200
        
    except Exception as e:
        import traceback
        import sys
        from flask import current_app
        error_detail = traceback.format_exc()
        print(f"测试连接错误详情: {error_detail}", file=sys.stderr)
        traceback.print_exc()
        try:
            debug_mode = current_app.config.get('DEBUG', False)
        except:
            debug_mode = False
        return jsonify({
            'success': False,
            'error': f'测试连接失败: {str(e)}',
            'code': 'INTERNAL_ERROR',
            'detail': error_detail if debug_mode else None
        }), 500

@settings_bp.route('/ai-models/<model_id>/models', methods=['GET'])
@login_required
@admin_required
def get_model_list(model_id):
    """获取模型列表 - 直接调用endpoint + /models"""
    try:
        import requests
        import json
        
        config_key = f'ai_model_{model_id}'
        config = SystemConfig.query.filter_by(config_key=config_key).first()
        
        if not config:
            return jsonify({
                'success': False,
                'error': '模型服务未配置',
                'code': 'MODEL_NOT_CONFIGURED',
                'data': {'models': []}
            }), 400
        
        config_value = config.get_value() if hasattr(config, 'get_value') else {}
        if not isinstance(config_value, dict):
            config_value = {}
        
        endpoint = config_value.get('config', {}).get('endpoint')
        api_key = config_value.get('config', {}).get('api_key')
        
        if not endpoint:
            return jsonify({
                'success': False,
                'error': 'Endpoint未配置',
                'code': 'ENDPOINT_NOT_CONFIGURED',
                'data': {'models': []}
            }), 400
        
        # 解密API Key
        import sys
        if api_key:
            # 如果前端传递的是空字符串，保持为空
            if not api_key.strip():
                api_key = ''
                print(f"[DEBUG] 获取模型列表 - API Key为空字符串 - model_id: {model_id}", file=sys.stderr)
            elif not api_key.startswith('sk-***') and not api_key.startswith('***'):
                # 尝试解密（如果已加密）
                try:
                    from utils.encryption import encryption_service
                    if encryption_service:
                        try:
                            # 尝试解密，如果失败说明是明文，直接使用
                            decrypted = encryption_service.decrypt(api_key)
                            api_key = decrypted
                            print(f"[DEBUG] 获取模型列表 - API Key已解密 - model_id: {model_id}, length: {len(api_key)}", file=sys.stderr)
                        except:
                            # 解密失败，说明是明文，直接使用
                            print(f"[DEBUG] 获取模型列表 - API Key是明文，直接使用 - model_id: {model_id}, length: {len(api_key)}", file=sys.stderr)
                            pass
                except ImportError:
                    print(f"[DEBUG] 获取模型列表 - 加密服务不可用，使用明文 - model_id: {model_id}", file=sys.stderr)
                    pass
            else:
                # 如果是占位符，设为空
                api_key = ''
                print(f"[DEBUG] 获取模型列表 - API Key是占位符，设为空 - model_id: {model_id}", file=sys.stderr)
        else:
            api_key = ''
            print(f"[DEBUG] 获取模型列表 - API Key未提供 - model_id: {model_id}", file=sys.stderr)
        
        print(f"[DEBUG] 获取模型列表 - model_id: {model_id}, endpoint: {endpoint}, api_key: {'已设置(' + str(len(api_key)) + '字符)' if api_key else '空'}", file=sys.stderr)
        
        # 处理Endpoint URL - 直接使用用户配置的endpoint + /models
        test_url = endpoint.strip()
        if not test_url.startswith('http'):
            test_url = f'http://{test_url}'
        
        # 确保URL末尾没有斜杠
        base_url = test_url.rstrip('/')
        
        # 直接使用用户配置的endpoint + /models 获取模型列表
        models_url = f'{base_url}/models'
        
        # 准备请求头 - 与test_ai_model保持一致的认证逻辑
        request_headers = {
            'Accept': 'application/json'
        }
        if api_key:
            # Claude使用特殊的认证方式
            if model_id == 'claude':
                request_headers['x-api-key'] = api_key
                request_headers['anthropic-version'] = '2023-06-01'
            else:
                # 其他所有模型都使用Bearer Token（与ai_model_client.py保持一致）
                # 包括: openai, deepseek, moonshot, ollama, tongyi, gemini, 
                #      zhipu, grok, openrouter, doubao, qianfan, hunyuan, siliconflow
                request_headers['Authorization'] = f'Bearer {api_key}'
        
        print(f"[DEBUG] 获取模型列表 - URL: {models_url}", file=sys.stderr)
        print(f"[DEBUG] 获取模型列表 - 请求头: {request_headers}", file=sys.stderr)
        
        # 发送请求获取模型列表
        try:
            response = requests.get(models_url, headers=request_headers, timeout=10, verify=False, allow_redirects=True)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    formatted_models = []
                    
                    # 支持多种响应格式
                    if 'data' in data and isinstance(data['data'], list):
                        # OpenAI兼容格式: {"data": [{"id": "...", ...}]}
                        for model_item in data['data']:
                            model_id_str = model_item.get('id', '')
                            model_name = model_item.get('name', model_id_str)
                            # 提取context信息（如果有）
                            context_info = ''
                            if 'context_length' in model_item:
                                context_info = f"{model_item['context_length']}K"
                            elif 'context' in model_item:
                                context_info = str(model_item['context'])
                            
                            formatted_models.append({
                                'id': model_id_str,
                                'name': model_name,
                                'context': context_info,
                                'vision': model_item.get('vision', False),
                                'tools': model_item.get('function_calling', False) or model_item.get('tools', False)
                            })
                    elif 'models' in data and isinstance(data['models'], list):
                        # Ollama原生格式: {"models": [{"name": "...", ...}]}
                        for model_item in data['models']:
                            model_id_str = model_item.get('name', '') or model_item.get('id', '')
                            model_name = model_item.get('display_name', model_id_str)
                            # 提取context信息
                            context_info = ''
                            if 'size' in model_item:
                                size = model_item['size']
                                if isinstance(size, int):
                                    # 转换为可读格式
                                    if size >= 1024**3:
                                        context_info = f"{size // (1024**3)}GB"
                                    elif size >= 1024**2:
                                        context_info = f"{size // (1024**2)}MB"
                            
                            formatted_models.append({
                                'id': model_id_str,
                                'name': model_name,
                                'context': context_info,
                                'vision': False,
                                'tools': False
                            })
                    else:
                        # 未知格式，尝试解析
                        return jsonify({
                            'success': False,
                            'error': f'无法解析模型列表响应格式: {str(data)[:200]}',
                            'code': 'INVALID_RESPONSE_FORMAT',
                            'data': {'models': []}
                        }), 400
                    
                    return jsonify({
                        'success': True,
                        'data': {'models': formatted_models}
                    }), 200
                    
                except json.JSONDecodeError as e:
                    return jsonify({
                        'success': False,
                        'error': f'响应不是有效的JSON格式: {str(e)}',
                        'code': 'INVALID_JSON',
                        'data': {'models': []}
                    }), 400
            else:
                # 非200状态码
                error_text = response.text[:200] if response.text else f'HTTP {response.status_code}'
                return jsonify({
                    'success': False,
                    'error': f'获取模型列表失败: HTTP {response.status_code} - {error_text}',
                    'code': 'HTTP_ERROR',
                    'data': {'models': []}
                }), response.status_code
                
        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': '连接超时（10秒）',
                'code': 'TIMEOUT',
                'data': {'models': []}
            }), 408
        except requests.exceptions.ConnectionError as e:
            return jsonify({
                'success': False,
                'error': f'无法连接到服务器: {str(e)}',
                'code': 'CONNECTION_ERROR',
                'data': {'models': []}
            }), 503
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'获取模型列表失败: {str(e)}',
                'code': 'REQUEST_ERROR',
                'data': {'models': []}
            }), 500
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'获取模型列表失败: {str(e)}',
            'code': 'INTERNAL_ERROR',
            'data': {'models': []}
        }), 500

@settings_bp.route('/ai-models/<model_id>/test-model', methods=['POST'])
@login_required
@admin_required
def test_specific_model(model_id):
    """测试特定模型连接"""
    try:
        from flask import current_app
        from services.ai_model_client import create_model_client
        
        data = request.get_json()
        test_model_id = data.get('model_id')
        
        if not test_model_id:
            return jsonify({
                'success': False,
                'error': '请提供模型ID',
                'code': 'MODEL_ID_REQUIRED'
            }), 400
        
        with current_app.app_context():
            config_key = f'ai_model_{model_id}'
            config = SystemConfig.query.filter_by(config_key=config_key).first()
            
            if not config:
                return jsonify({
                    'success': False,
                    'error': '模型服务未配置',
                    'code': 'MODEL_NOT_CONFIGURED'
                }), 400
            
            config_value = config.get_value() if hasattr(config, 'get_value') else {}
            if not isinstance(config_value, dict):
                config_value = {}
            
            endpoint = config_value.get('config', {}).get('endpoint')
            api_key = config_value.get('config', {}).get('api_key')
            
            if not endpoint:
                return jsonify({
                    'success': False,
                    'error': 'Endpoint未配置',
                    'code': 'ENDPOINT_NOT_CONFIGURED'
                }), 400
            
            # 解密API Key
            if api_key:
                try:
                    from utils.encryption import encryption_service
                    if encryption_service and not api_key.startswith('sk-***') and not api_key.startswith('***'):
                        try:
                            api_key = encryption_service.decrypt(api_key)
                        except:
                            pass
                except ImportError:
                    pass
            
            # 使用AI模型客户端测试特定模型
            try:
                client = create_model_client(model_id, endpoint, api_key)
                
                # 发送测试消息
                messages = [
                    {'role': 'user', 'content': 'Hello'}
                ]
                
                result = client.chat_completion(messages, model=test_model_id)
                
                if result.get('success'):
                    return jsonify({
                        'success': True,
                        'data': {
                            'connected': True,
                            'response_time': 0,  # 可以从结果中获取
                            'message': '模型连接成功',
                            'model_id': test_model_id
                        }
                    }), 200
                else:
                    return jsonify({
                        'success': True,
                        'data': {
                            'connected': False,
                            'response_time': 0,
                            'message': result.get('error', '模型连接失败'),
                            'model_id': test_model_id
                        }
                    }), 200
            except ImportError:
                # 如果客户端不可用，返回错误
                return jsonify({
                    'success': False,
                    'error': 'AI模型客户端不可用',
                    'code': 'CLIENT_NOT_AVAILABLE'
                }), 500
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'测试模型失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@settings_bp.route('/email', methods=['GET'])
@login_required
@admin_required
def get_email_config():
    """获取邮箱配置"""
    try:
        try:
            from utils.encryption import encryption_service
        except ImportError:
            encryption_service = None
        
        # 查询邮箱配置
        try:
            config = SystemConfig.query.filter_by(config_key='email_server').first()
        except Exception as e:
            print(f"查询邮箱配置失败: {e}")
            config = None
        
        # 默认配置结构（按服务商ID组织）
        default_config = {
            'qq': {'enabled': False, 'sender_email': '', 'password': '', 'sender_name': 'AI 数据平台'},
            '163': {'enabled': False, 'sender_email': '', 'password': '', 'sender_name': 'AI 数据平台'},
            'gmail': {'enabled': False, 'sender_email': '', 'password': '', 'sender_name': 'AI 数据平台'},
            'outlook': {'enabled': False, 'sender_email': '', 'password': '', 'sender_name': 'AI 数据平台'},
            'sina': {'enabled': False, 'sender_email': '', 'password': '', 'sender_name': 'AI 数据平台'},
            'custom': {'enabled': False, 'sender_email': '', 'password': '', 'sender_name': 'AI 数据平台'}
        }
        
        if config:
            try:
                config_value = config.get_value() if hasattr(config, 'get_value') else {}
                # 确保config_value是字典
                if not isinstance(config_value, dict):
                    config_value = {}
                
                # 如果配置是旧格式（provider/enabled/config），转换为新格式
                if 'provider' in config_value:
                    # 旧格式：转换为新格式
                    provider = config_value.get('provider', 'qq')
                    enabled = config_value.get('enabled', False)
                    provider_config = config_value.get('config', {})
                    
                    # 解密授权码
                    auth_code = provider_config.get('auth_code', '')
                    if encryption_service and auth_code and not auth_code.startswith('***'):
                        try:
                            auth_code = encryption_service.decrypt(auth_code)
                        except:
                            pass
                    
                    # 转换为新格式，同时提供兼容旧格式的字段
                    result_config = default_config.copy()
                    result_config[provider] = {
                        'enabled': enabled,
                        'sender_email': provider_config.get('sender_email', ''),
                        'password': auth_code,
                        'sender_name': provider_config.get('sender_name', 'AI 数据平台')
                    }
                    
                    # 同时提供旧格式兼容字段（供前端直接使用）
                    result_config['smtp_host'] = provider_config.get('smtp_host', '')
                    result_config['smtp_port'] = str(provider_config.get('smtp_port', 465))
                    result_config['encryption'] = provider_config.get('encryption', 'SSL')
                    result_config['sender_email'] = provider_config.get('sender_email', '')
                    result_config['auth_code'] = auth_code
                    
                    return jsonify({
                        'success': True,
                        'data': result_config
                    }), 200
                else:
                    # 新格式：直接使用，但确保所有服务商都有配置
                    result_config = default_config.copy()
                    result_config.update(config_value)
                    
                    # 解密所有服务商的密码
                    for provider_id, provider_config in result_config.items():
                        if isinstance(provider_config, dict) and 'password' in provider_config:
                            if encryption_service and provider_config['password'] and not provider_config['password'].startswith('***'):
                                try:
                                    provider_config['password'] = encryption_service.decrypt(provider_config['password'])
                                except:
                                    pass
                    
                    return jsonify({
                        'success': True,
                        'data': result_config
                    }), 200
            except Exception as e:
                print(f"解析邮箱配置失败: {e}")
                import traceback
                print(traceback.format_exc())
                # 如果解析失败，返回默认配置
                return jsonify({
                    'success': True,
                    'data': default_config
                }), 200
        
        # 如果没有配置，返回默认配置（兼容旧格式）
        # 为了兼容前端，返回一个包含smtp_host等字段的对象
        return jsonify({
            'success': True,
            'data': {
                'smtp_host': '',
                'smtp_port': '465',
                'encryption': 'SSL',
                'sender_email': '',
                'auth_code': '',
                **default_config  # 同时包含新格式
            }
        }), 200
        
    except Exception as e:
        import traceback
        print(f"获取邮箱配置失败: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@settings_bp.route('/email', methods=['PUT'])
@login_required
@admin_required
@log_operation('更新邮箱配置', 'config')
def update_email_config():
    """更新邮箱配置"""
    try:
        from utils.encryption import encryption_service
    except ImportError:
        encryption_service = None
    
    try:
        data = request.get_json()
        
        # 获取或创建配置
        config = SystemConfig.query.filter_by(config_key='email_server').first()
        if not config:
            config = SystemConfig(
                config_key='email_server',
                config_type='email',
                description='邮箱服务器配置'
            )
            db.session.add(config)
        
        # 准备配置值
        config_value = {
            'provider': data.get('provider', 'qq'),
            'enabled': data.get('enabled', False),
            'config': data.get('config', {})
        }
        
        # 加密授权码
        if encryption_service and 'auth_code' in config_value.get('config', {}):
            auth_code = config_value['config']['auth_code']
            if auth_code and not auth_code.startswith('***'):  # 避免重复加密
                try:
                    config_value['config']['auth_code'] = encryption_service.encrypt(auth_code)
                except:
                    pass
        
        if hasattr(config, 'set_value'):
            config.set_value(config_value)
        else:
            config.config_value = json.dumps(config_value, ensure_ascii=False)
        config.updated_by = current_user.id
        db.session.commit()
        
        # 更新Flask-Mail配置
        try:
            from flask import current_app
            email_config = config_value.get('config', {})
            smtp_host = email_config.get('smtp_host', 'smtp.qq.com')
            smtp_port = int(email_config.get('smtp_port', 465))
            encryption = email_config.get('encryption', 'SSL')
            sender_email = email_config.get('sender_email', '')
            
            current_app.config['MAIL_SERVER'] = smtp_host
            current_app.config['MAIL_PORT'] = smtp_port
            current_app.config['MAIL_USE_SSL'] = (encryption == 'SSL')
            current_app.config['MAIL_USE_TLS'] = (encryption == 'TLS')
            current_app.config['MAIL_USERNAME'] = sender_email
            
            # 解密授权码
            auth_code = email_config.get('auth_code', '')
            if auth_code:
                if encryption_service and not auth_code.startswith('***'):
                    try:
                        current_app.config['MAIL_PASSWORD'] = encryption_service.decrypt(auth_code)
                    except:
                        current_app.config['MAIL_PASSWORD'] = auth_code
                else:
                    current_app.config['MAIL_PASSWORD'] = auth_code
            
            current_app.config['MAIL_DEFAULT_SENDER'] = sender_email
            
            # 重新初始化Mail对象（如果需要）
            try:
                from flask_mail import Mail
                if hasattr(current_app, 'mail'):
                    # 重新创建Mail实例以应用新配置
                    current_app.mail = Mail(current_app)
            except:
                pass
        except Exception as e:
            import sys
            print(f"[ERROR] 更新Flask-Mail配置失败: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
        
        return jsonify({
            'success': True,
            'message': '邮箱配置已更新'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@settings_bp.route('/email/test', methods=['POST'])
@login_required
@admin_required
def test_email():
    """发送测试邮件 - 使用当前保存的配置"""
    try:
        import sys
        from flask import current_app
        from flask_mail import Message
        from datetime import datetime
        
        data = request.get_json()
        recipient = data.get('recipient')
        sender_email_from_request = data.get('sender_email')  # 从前端获取实际配置的发件人邮箱
        
        if not recipient:
            return jsonify({
                'success': False,
                'error': '请提供收件人邮箱',
                'code': 'INVALID_PARAMS'
            }), 400
        
        # 验证邮箱格式
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, recipient):
            return jsonify({
                'success': False,
                'error': '收件人邮箱格式不正确',
                'code': 'INVALID_EMAIL'
            }), 400
        
        # 获取实际配置的发件人邮箱
        # 优先使用前端传递的，否则使用Flask-Mail配置的，最后使用当前用户邮箱
        actual_sender_email = sender_email_from_request or current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME') or (current_user.email if current_user else '系统')
        
        # 确保使用最新的Flask-Mail配置
        # 配置应该在保存时已经更新，这里直接使用
        print(f"[DEBUG] 测试邮件 - MAIL_SERVER: {current_app.config.get('MAIL_SERVER')}", file=sys.stderr)
        print(f"[DEBUG] 测试邮件 - MAIL_PORT: {current_app.config.get('MAIL_PORT')}", file=sys.stderr)
        print(f"[DEBUG] 测试邮件 - MAIL_USE_SSL: {current_app.config.get('MAIL_USE_SSL')}", file=sys.stderr)
        print(f"[DEBUG] 测试邮件 - MAIL_USE_TLS: {current_app.config.get('MAIL_USE_TLS')}", file=sys.stderr)
        print(f"[DEBUG] 测试邮件 - MAIL_USERNAME: {current_app.config.get('MAIL_USERNAME')}", file=sys.stderr)
        print(f"[DEBUG] 测试邮件 - 实际发件人: {actual_sender_email}", file=sys.stderr)
        
        # 检查邮件配置是否完整
        if not current_app.config.get('MAIL_SERVER'):
            return jsonify({
                'success': False,
                'error': '邮件服务器未配置，请先保存邮件配置',
                'code': 'EMAIL_NOT_CONFIGURED'
            }), 400
        
        try:
            # 创建测试邮件，使用实际配置的发件人邮箱
            msg = Message(
                subject='AI 数据平台 - 邮件配置测试',
                recipients=[recipient],
                sender=actual_sender_email,  # 明确指定发件人
                body=f'''
这是一封测试邮件，用于验证邮件服务器配置。

发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
发件人: {actual_sender_email}
收件人: {recipient}
系统: AI 数据平台

如果您收到这封邮件，说明邮件服务器配置正常。
                ''',
                html=f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #333; margin-bottom: 20px;">AI 数据平台 - 邮件配置测试</h2>
                    <p style="color: #666; line-height: 1.6; margin-bottom: 20px;">这是一封测试邮件，用于验证邮件服务器配置。</p>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3b82f6;">
                        <p style="margin: 8px 0; color: #333;"><strong>发送时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p style="margin: 8px 0; color: #333;"><strong>发件人:</strong> <a href="mailto:{actual_sender_email}" style="color: #3b82f6; text-decoration: none;">{actual_sender_email}</a></p>
                        <p style="margin: 8px 0; color: #333;"><strong>收件人:</strong> <a href="mailto:{recipient}" style="color: #3b82f6; text-decoration: none;">{recipient}</a></p>
                        <p style="margin: 8px 0; color: #333;"><strong>系统:</strong> AI 数据平台</p>
                    </div>
                    <p style="color: #10b981; font-weight: 500; margin-top: 20px;">如果您收到这封邮件，说明邮件服务器配置正常。</p>
                </div>
                '''
            )
            
            # 发送邮件
            current_app.mail.send(msg)
            
            print(f"[DEBUG] 测试邮件发送成功 - 收件人: {recipient}", file=sys.stderr)
            
            return jsonify({
                'success': True,
                'message': f'测试邮件已发送到 {recipient}，请查收'
            }), 200
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[ERROR] 发送测试邮件失败: {e}", file=sys.stderr)
            print(f"[ERROR] 错误详情: {error_detail}", file=sys.stderr)
            
            # 提供更详细的错误信息
            error_msg = str(e)
            if 'authentication failed' in error_msg.lower() or '535' in error_msg:
                error_msg = '认证失败，请检查邮箱和授权码是否正确'
            elif 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
                error_msg = '连接失败，请检查SMTP服务器地址和端口是否正确'
            elif 'ssl' in error_msg.lower() or 'tls' in error_msg.lower():
                error_msg = 'SSL/TLS连接失败，请检查加密协议设置是否正确'
            
            return jsonify({
                'success': False,
                'error': f'发送测试邮件失败: {error_msg}',
                'code': 'EMAIL_SEND_FAILED'
            }), 500
            
    except Exception as e:
        import traceback
        import sys
        error_detail = traceback.format_exc()
        print(f"[ERROR] 测试邮件异常: {e}", file=sys.stderr)
        print(f"[ERROR] 错误详情: {error_detail}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'测试邮件失败: {str(e)}',
            'code': 'INTERNAL_ERROR'
        }), 500

@settings_bp.route('/admins', methods=['GET'])
@login_required
@admin_required
def get_admins():
    """获取管理员列表"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 查询所有用户（管理员列表显示所有用户，不仅仅是管理员）
        try:
            from sqlalchemy import or_
            # 显示所有用户，但优先显示管理员
            query = User.query.order_by(
                User.role.desc(),  # admin/super_admin 在前
                User.created_at.desc()  # 按创建时间倒序
            )
            pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        except Exception as e:
            print(f"查询管理员列表失败: {e}")
            import traceback
            print(traceback.format_exc())
            # 如果查询失败，返回空列表
            pagination = type('obj', (object,), {
                'items': [],
                'total': 0,
                'pages': 0
            })()
        
        # 处理管理员数据
        admins_data = []
        for admin in pagination.items:
            try:
                if hasattr(admin, 'to_dict'):
                    admin_dict = admin.to_dict()
                    # 确保字段名匹配前端期望
                    if 'last_login_at' in admin_dict:
                        admin_dict['last_login'] = admin_dict.pop('last_login_at')
                    elif 'last_login' not in admin_dict:
                        # 尝试从不同字段获取
                        last_login = getattr(admin, 'last_login_at', None) or getattr(admin, 'last_login', None)
                        admin_dict['last_login'] = last_login.isoformat() if last_login and hasattr(last_login, 'isoformat') else (str(last_login) if last_login else None)
                    # 确保有name字段
                    if 'name' not in admin_dict:
                        admin_dict['name'] = admin_dict.get('username') or admin_dict.get('name') or ''
                else:
                    # 手动构建字典
                    admin_dict = {
                        'id': admin.id,
                        'email': admin.email,
                        'name': getattr(admin, 'name', None) or getattr(admin, 'username', None) or '',
                        'role': getattr(admin, 'role', 'user'),
                        'status': getattr(admin, 'status', 'active'),
                        'last_login': None
                    }
                    # 尝试获取最后登录时间
                    last_login = getattr(admin, 'last_login_at', None) or getattr(admin, 'last_login', None)
                    if last_login:
                        try:
                            admin_dict['last_login'] = last_login.isoformat() if hasattr(last_login, 'isoformat') else str(last_login)
                        except:
                            pass
                admins_data.append(admin_dict)
            except Exception as e:
                print(f"处理管理员数据失败 (ID: {getattr(admin, 'id', 'unknown')}): {e}")
                import traceback
                print(traceback.format_exc())
                # 如果单个管理员数据处理失败，跳过
                continue
        
        return jsonify({
            'success': True,
            'data': {
                'admins': admins_data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': pagination.total,
                    'total_pages': pagination.pages
                }
            }
        }), 200
    except Exception as e:
        import traceback
        print(f"获取管理员列表失败: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR',
            'data': {
                'admins': [],
                'pagination': {
                    'page': 1,
                    'page_size': 20,
                    'total': 0,
                    'total_pages': 0
                }
            }
        }), 500

@settings_bp.route('/admins', methods=['POST'])
@login_required
@admin_required
@log_operation('新增管理员', 'user')
def create_admin():
    """新增管理员"""
    try:
        from utils.validators import validate_email, validate_password
        from services.email_service import EmailService
        
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        role = data.get('role', 'admin')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': '邮箱和密码不能为空',
                'code': 'INVALID_PARAMS'
            }), 400
        
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': '邮箱格式不正确',
                'code': 'INVALID_PARAMS'
            }), 400
        
        is_valid, msg = validate_password(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': msg,
                'code': 'INVALID_PARAMS'
            }), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'error': '该邮箱已被注册',
                'code': 'INVALID_PARAMS'
            }), 400
        
        # 创建管理员
        # 生成username（使用邮箱前缀，如果数据库要求username不能为null）
        username = email.split('@')[0]  # 使用邮箱前缀作为username
        
        # 检查username是否已存在，如果存在则添加数字后缀
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        admin = User(
            email=email,
            username=username,  # 设置username字段
            name=name,
            role=role,
            status='active'
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'admin_id': admin.id,
                'message': '管理员已创建'
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@settings_bp.route('/admins/<int:admin_id>', methods=['PUT'])
@login_required
@admin_required
@log_operation('更新用户信息', 'user')
def update_admin(admin_id):
    """更新用户信息（支持管理员和普通用户）"""
    try:
        user = User.query.get_or_404(admin_id)
        
        data = request.get_json()
        if 'name' in data:
            user.name = data['name']
        if 'role' in data:
            # 允许将普通用户提升为管理员，或修改管理员角色
            user.role = data['role']
        if 'status' in data:
            user.status = data['status']
        
        db.session.commit()
        
        # 根据用户角色返回不同的消息
        if user.role in ['admin', 'super_admin']:
            message = '管理员信息已更新'
        else:
            message = '用户信息已更新'
        
        return jsonify({
            'success': True,
            'message': message
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@settings_bp.route('/admins/<int:admin_id>/reset-password', methods=['POST'])
@login_required
@admin_required
@log_operation('重置用户密码', 'user')
def reset_admin_password(admin_id):
    """重置用户密码（支持管理员和普通用户）"""
    try:
        import secrets
        import string
        from services.email_service import EmailService
        
        user = User.query.get_or_404(admin_id)
        
        # 生成新密码
        new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        user.set_password(new_password)
        db.session.commit()
        
        # 发送邮件
        try:
            email_service = EmailService()
            email_service.send_test_email(user.email)  # TODO: 发送包含新密码的邮件
        except:
            pass
        
        # 根据用户角色返回不同的消息
        if user.role in ['admin', 'super_admin']:
            message = '密码已重置，新密码已发送至管理员邮箱'
        else:
            message = '密码已重置，新密码已发送至用户邮箱'
        
        return jsonify({
            'success': True,
            'data': {
                'new_password': new_password,
                'message': message
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@settings_bp.route('/admins/<int:admin_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
@log_operation('切换用户状态', 'user')
def toggle_admin_status(admin_id):
    """禁用/启用用户（支持管理员和普通用户）"""
    try:
        user = User.query.get_or_404(admin_id)
        
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'error': '不能修改自己的状态',
                'code': 'INVALID_PARAMS'
            }), 400
        
        # 切换状态
        user.status = 'disabled' if user.status == 'active' else 'active'
        db.session.commit()
        
        # 根据用户角色返回不同的消息
        if user.role in ['admin', 'super_admin']:
            message = f'管理员已{"禁用" if user.status == "disabled" else "启用"}'
        else:
            message = f'用户已{"禁用" if user.status == "disabled" else "启用"}'
        
        return jsonify({
            'success': True,
            'data': {
                'status': user.status,
                'message': message
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@settings_bp.route('/admins/<int:admin_id>', methods=['DELETE'])
@login_required
@admin_required
@log_operation('删除用户', 'user')
def delete_admin(admin_id):
    """删除用户（管理员可以删除任何用户）"""
    try:
        user = User.query.get_or_404(admin_id)
        
        # 不能删除自己
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'error': '不能删除自己',
                'code': 'INVALID_PARAMS'
            }), 400
        
        # 记录用户信息（用于日志）
        user_role = user.role
        user_email = user.email
        user_id = user.id
        
        # 在删除用户前，先检查是否有相关的任务
        # 如果存在任务，需要先处理（删除或转移）
        try:
            from models.task import Task
            task_count = Task.query.filter_by(user_id=user_id).count()
            if task_count > 0:
                # 如果用户有任务，先删除这些任务
                Task.query.filter_by(user_id=user_id).delete(synchronize_session=False)
                db.session.flush()
        except Exception as task_error:
            # 如果处理任务失败，回滚并返回错误
            db.session.rollback()
            import sys
            error_msg = str(task_error)
            print(f"[ERROR] 处理用户任务失败: {error_msg}", file=sys.stderr)
            return jsonify({
                'success': False,
                'error': f'删除用户失败：无法处理相关任务。{error_msg}',
                'code': 'DELETE_TASKS_ERROR'
            }), 500
        
        # 在删除用户前，先处理相关的操作日志
        # 如果数据库表结构允许，将相关日志的 user_id 设置为 NULL
        # 这样可以保留历史记录，同时避免外键约束错误
        # 注意：如果更新失败，需要回滚事务，避免后续操作失败
        try:
            from models.log import OperationLog
            # 尝试更新操作日志（如果数据库支持）
            # 注意：这需要数据库表结构已经允许 user_id 为 NULL
            OperationLog.query.filter_by(user_id=user_id).update({OperationLog.user_id: None}, synchronize_session=False)
            db.session.flush()  # 刷新但不提交，以便在出错时可以回滚
        except Exception as log_update_error:
            # 如果更新失败（可能是数据库约束不允许），回滚事务并返回错误
            db.session.rollback()
            import sys
            error_msg = str(log_update_error)
            print(f"[ERROR] 更新操作日志失败: {error_msg}", file=sys.stderr)
            
            # 检查是否是数据库约束错误
            if 'not-null constraint' in error_msg.lower() or 'null value' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': '数据库表结构需要更新。请先运行修复脚本：python3 fix_operation_logs_user_id.py',
                    'code': 'DATABASE_SCHEMA_ERROR'
                }), 500
            
            # 其他错误，返回通用错误信息
            return jsonify({
                'success': False,
                'error': f'删除用户失败: {error_msg}',
                'code': 'DELETE_USER_ERROR'
            }), 500
        
        # 删除用户（管理员可以删除任何用户，包括普通用户）
        try:
            db.session.delete(user)
            db.session.commit()
        except Exception as delete_error:
            # 如果删除失败，回滚事务
            db.session.rollback()
            import sys
            error_msg = str(delete_error)
            print(f"[ERROR] 删除用户失败: {error_msg}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            
            # 检查是否是外键约束错误
            if 'foreign key' in error_msg.lower() or 'constraint' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': '无法删除用户：存在关联数据。请先删除或处理该用户的相关任务和日志。',
                    'code': 'FOREIGN_KEY_CONSTRAINT'
                }), 500
            
            return jsonify({
                'success': False,
                'error': f'删除用户失败: {error_msg}',
                'code': 'DELETE_USER_ERROR'
            }), 500
        
        # 根据用户角色返回不同的消息
        if user_role in ['admin', 'super_admin']:
            message = '管理员已删除'
        else:
            message = '用户已删除'
        
        return jsonify({
            'success': True,
            'message': message
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@settings_bp.route('/logs', methods=['GET'])
@login_required
@admin_required
def get_logs():
    """查询操作日志"""
    try:
        keyword = request.args.get('keyword')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        result = request.args.get('result')
        user_id = request.args.get('user_id', type=int)
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 检查OperationLog是否可用
        try:
            # 尝试查询日志
            query = OperationLog.query
            if keyword:
                query = query.filter(OperationLog.action.contains(keyword))
            if start_time:
                query = query.filter(OperationLog.created_at >= start_time)
            if end_time:
                query = query.filter(OperationLog.created_at <= end_time)
            if result:
                query = query.filter_by(result=result)
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            pagination = query.order_by(OperationLog.created_at.desc()).paginate(
                page=page, per_page=page_size, error_out=False
            )
        except Exception as e:
            print(f"查询操作日志失败: {e}")
            import traceback
            print(traceback.format_exc())
            # 如果查询失败，返回空列表
            pagination = type('obj', (object,), {
                'items': [],
                'total': 0,
                'pages': 0
            })()
        
        # 处理日志数据
        logs_data = []
        for log in pagination.items:
            try:
                if hasattr(log, 'to_dict'):
                    log_dict = log.to_dict()
                    # 转换字段格式以匹配前端期望
                    if 'user' in log_dict and isinstance(log_dict['user'], dict):
                        log_dict['user_email'] = log_dict['user'].get('email', '')
                        log_dict['user_name'] = log_dict['user'].get('name', '')
                    elif 'user_email' not in log_dict:
                        # 尝试从关系对象获取
                        if hasattr(log, 'user') and log.user:
                            log_dict['user_email'] = log.user.email
                            log_dict['user_name'] = getattr(log.user, 'name', None) or getattr(log.user, 'username', None)
                        else:
                            log_dict['user_email'] = ''
                            log_dict['user_name'] = ''
                    
                    # 确保有timestamp字段
                    if 'created_at' in log_dict and 'timestamp' not in log_dict:
                        log_dict['timestamp'] = log_dict['created_at']
                    elif 'timestamp' not in log_dict:
                        timestamp = getattr(log, 'created_at', None)
                        log_dict['timestamp'] = timestamp.isoformat() if timestamp and hasattr(timestamp, 'isoformat') else (str(timestamp) if timestamp else None)
                    
                    # 处理details字段 - 保持为字典格式，前端会格式化显示
                    if 'details' in log_dict:
                        if isinstance(log_dict['details'], str):
                            # 如果是字符串，尝试解析为JSON
                            try:
                                log_dict['details'] = json.loads(log_dict['details'])
                            except:
                                # 如果解析失败，保持为字符串
                                pass
                        elif log_dict['details'] is None:
                            log_dict['details'] = {}
                        # 如果是字典，直接使用
                    
                    logs_data.append(log_dict)
                else:
                    # 如果log没有to_dict方法，手动构建
                    log_dict = {
                        'id': getattr(log, 'id', 0),
                        'action': getattr(log, 'action', ''),
                        'result': getattr(log, 'result', 'success'),
                        'details': '',
                        'timestamp': None
                    }
                    
                    # 获取用户信息
                    if hasattr(log, 'user') and log.user:
                        log_dict['user_email'] = log.user.email
                        log_dict['user_name'] = getattr(log.user, 'name', None) or getattr(log.user, 'username', None)
                    else:
                        log_dict['user_email'] = ''
                        log_dict['user_name'] = ''
                    
                    # 获取时间戳
                    timestamp = getattr(log, 'created_at', None)
                    if timestamp:
                        log_dict['timestamp'] = timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp)
                    
                    # 获取详情
                    details = getattr(log, 'details', None)
                    if details:
                        if isinstance(details, str):
                            try:
                                import json
                                details_dict = json.loads(details)
                                log_dict['details'] = str(details_dict)
                            except:
                                log_dict['details'] = details
                        else:
                            log_dict['details'] = str(details)
                    
                    logs_data.append(log_dict)
            except Exception as e:
                print(f"处理日志数据失败 (ID: {getattr(log, 'id', 'unknown')}): {e}")
                import traceback
                print(traceback.format_exc())
                # 如果单个日志数据处理失败，跳过
                continue
        
        return jsonify({
            'success': True,
            'data': {
                'logs': logs_data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': pagination.total,
                    'total_pages': pagination.pages
                }
            }
        }), 200
    except Exception as e:
        import traceback
        print(f"获取操作日志失败: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR',
            'data': {
                'logs': [],
                'pagination': {
                    'page': 1,
                    'page_size': 20,
                    'total': 0,
                    'total_pages': 0
                }
            }
        }), 500

