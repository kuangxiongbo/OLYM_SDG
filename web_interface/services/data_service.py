#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据服务
========

处理数据源管理相关的业务逻辑
"""

import os
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from werkzeug.utils import secure_filename

from models import db, DataSource, DataSourceType, DataSourceStatus, User

class DataService:
    """数据服务类"""
    
    @staticmethod
    def create_data_source(user_id: int, name: str, data_type: str, 
                          file_path: Optional[str] = None, 
                          config: Optional[Dict[str, Any]] = None) -> DataSource:
        """创建数据源"""
        # 验证用户
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        # 验证数据源类型
        try:
            data_source_type = DataSourceType(data_type)
        except ValueError:
            raise ValueError(f"不支持的数据源类型: {data_type}")
        
        # 验证文件
        if file_path and not os.path.exists(file_path):
            raise ValueError("文件不存在")
        
        # 创建数据源记录
        data_source = DataSource(
            user_id=user_id,
            name=name,
            type=data_source_type,
            file_path=file_path,
            config=config or {},
            status=DataSourceStatus.PROCESSING
        )
        
        db.session.add(data_source)
        db.session.commit()
        
        # 异步处理数据源
        DataService._process_data_source_async(data_source.id)
        
        return data_source
    
    @staticmethod
    def get_user_data_sources(user_id: int) -> List[DataSource]:
        """获取用户数据源列表"""
        return DataSource.query.filter_by(user_id=user_id).order_by(DataSource.created_at.desc()).all()
    
    @staticmethod
    def get_data_source(data_source_id: int, user_id: int) -> DataSource:
        """获取数据源详情"""
        data_source = DataSource.query.filter_by(id=data_source_id, user_id=user_id).first()
        if not data_source:
            raise ValueError("数据源不存在")
        return data_source
    
    @staticmethod
    def update_data_source(data_source_id: int, user_id: int, 
                          update_data: Dict[str, Any]) -> DataSource:
        """更新数据源"""
        data_source = DataSource.query.filter_by(id=data_source_id, user_id=user_id).first()
        if not data_source:
            raise ValueError("数据源不存在")
        
        # 更新允许的字段
        allowed_fields = ['name', 'description', 'config']
        for field in allowed_fields:
            if field in update_data:
                setattr(data_source, field, update_data[field])
        
        data_source.updated_at = datetime.utcnow()
        db.session.commit()
        
        return data_source
    
    @staticmethod
    def delete_data_source(data_source_id: int, user_id: int) -> bool:
        """删除数据源"""
        data_source = DataSource.query.filter_by(id=data_source_id, user_id=user_id).first()
        if not data_source:
            raise ValueError("数据源不存在")
        
        # 删除文件
        if data_source.file_path and os.path.exists(data_source.file_path):
            try:
                os.remove(data_source.file_path)
            except OSError:
                pass  # 忽略文件删除错误
        
        db.session.delete(data_source)
        db.session.commit()
        
        return True
    
    @staticmethod
    def preview_data_source(data_source_id: int, user_id: int, 
                           limit: int = 100) -> Dict[str, Any]:
        """预览数据源"""
        data_source = DataSource.query.filter_by(id=data_source_id, user_id=user_id).first()
        if not data_source:
            raise ValueError("数据源不存在")
        
        if not data_source.file_path or not os.path.exists(data_source.file_path):
            raise ValueError("数据文件不存在")
        
        try:
            # 根据类型读取数据
            if data_source.type == DataSourceType.CSV:
                df = pd.read_csv(data_source.file_path, nrows=limit)
            elif data_source.type == DataSourceType.JSON:
                df = pd.read_json(data_source.file_path, nrows=limit)
            else:
                raise ValueError("不支持预览此类型的数据源")
            
            return {
                'columns': df.columns.tolist(),
                'dtypes': df.dtypes.astype(str).to_dict(),
                'data': df.head(10).to_dict('records'),
                'shape': df.shape,
                'null_counts': df.isnull().sum().to_dict()
            }
        except Exception as e:
            raise ValueError(f"数据预览失败: {str(e)}")
    
    @staticmethod
    def validate_data_source(file_path: str, data_type: str) -> Tuple[bool, str]:
        """验证数据源"""
        try:
            if not os.path.exists(file_path):
                return False, "文件不存在"
            
            if data_type == 'csv':
                df = pd.read_csv(file_path, nrows=100)  # 只读前100行验证
            elif data_type == 'json':
                df = pd.read_json(file_path, nrows=100)
            else:
                return True, "支持的数据类型"
            
            # 检查数据质量
            if df.empty:
                return False, "数据文件为空"
            
            if df.shape[1] < 2:
                return False, "数据至少需要2列"
            
            return True, f"数据验证通过，共{df.shape[1]}列，{df.shape[0]}行"
        
        except Exception as e:
            return False, f"数据验证失败: {str(e)}"
    
    @staticmethod
    def upload_file(file, upload_folder: str) -> str:
        """上传文件"""
        if file and file.filename:
            # 生成安全的文件名
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            filename = f"{timestamp}_{name}{ext}"
            
            # 确保上传目录存在
            os.makedirs(upload_folder, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            return file_path
        
        raise ValueError("无效的文件")
    
    @staticmethod
    def _process_data_source_async(data_source_id: int):
        """异步处理数据源"""
        # 这里应该实现异步处理逻辑
        # 例如使用Celery任务队列
        data_source = DataSource.query.get(data_source_id)
        if data_source:
            try:
                # 模拟处理过程
                if data_source.file_path and os.path.exists(data_source.file_path):
                    df = pd.read_csv(data_source.file_path) if data_source.type.value == 'csv' else pd.read_json(data_source.file_path)
                    data_source.row_count = len(df)
                    data_source.column_count = len(df.columns)
                    data_source.file_size = os.path.getsize(data_source.file_path)
                    data_source.status = DataSourceStatus.ACTIVE
                else:
                    data_source.status = DataSourceStatus.ERROR
                
                db.session.commit()
            except Exception as e:
                data_source.status = DataSourceStatus.ERROR
                db.session.commit()
                print(f"处理数据源失败: {e}")

