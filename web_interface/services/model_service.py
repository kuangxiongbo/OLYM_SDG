#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型服务
========

处理模型配置相关的业务逻辑
"""

from datetime import datetime
from typing import Dict, Any, List

from models import db, ModelConfig, ModelType, ModelStatus, User

class ModelService:
    """模型服务类"""
    
    @staticmethod
    def create_model_config(user_id: int, name: str, model_type: str, 
                           config: Dict[str, Any] = None) -> ModelConfig:
        """创建模型配置"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        try:
            model_type_enum = ModelType(model_type)
        except ValueError:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        model_config = ModelConfig(
            user_id=user_id,
            name=name,
            model_type=model_type_enum,
            config=config or {},
            status=ModelStatus.ACTIVE
        )
        
        db.session.add(model_config)
        db.session.commit()
        
        return model_config
    
    @staticmethod
    def get_user_model_configs(user_id: int) -> List[ModelConfig]:
        """获取用户模型配置列表"""
        return ModelConfig.query.filter_by(user_id=user_id).order_by(ModelConfig.created_at.desc()).all()
    
    @staticmethod
    def get_model_config(model_config_id: int, user_id: int) -> ModelConfig:
        """获取模型配置详情"""
        model_config = ModelConfig.query.filter_by(id=model_config_id, user_id=user_id).first()
        if not model_config:
            raise ValueError("模型配置不存在")
        return model_config

