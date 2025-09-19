#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接器
============

提供各种数据库的连接和查询功能
"""

import pandas as pd
import pymysql
import psycopg2
import cx_Oracle
import pymongo
import pyodbc
import sqlite3
from sqlalchemy import create_engine, text
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseConnector:
    """数据库连接器类"""
    
    def __init__(self):
        self.connections = {}
    
    def get_connection_string(self, config: Dict[str, Any]) -> str:
        """根据配置生成数据库连接字符串"""
        db_type = config.get('type', '').lower()
        
        if db_type == 'mysql':
            return f"mysql+pymysql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        elif db_type == 'postgresql':
            return f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        elif db_type == 'oracle':
            return f"oracle+cx_oracle://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        elif db_type == 'sqlserver':
            return f"mssql+pyodbc://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?driver=ODBC+Driver+17+for+SQL+Server"
        elif db_type == 'sqlite':
            return f"sqlite:///{config['database']}"
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """测试数据库连接"""
        try:
            db_type = config.get('type', '').lower()
            
            if db_type == 'mysql':
                connection = pymysql.connect(
                    host=config['host'],
                    port=int(config['port']),
                    user=config['username'],
                    password=config['password'],
                    database=config['database'],
                    charset='utf8mb4'
                )
                connection.close()
                
            elif db_type == 'postgresql':
                connection = psycopg2.connect(
                    host=config['host'],
                    port=int(config['port']),
                    user=config['username'],
                    password=config['password'],
                    database=config['database']
                )
                connection.close()
                
            elif db_type == 'oracle':
                dsn = cx_Oracle.makedsn(config['host'], int(config['port']), service_name=config['database'])
                connection = cx_Oracle.connect(config['username'], config['password'], dsn)
                connection.close()
                
            elif db_type == 'sqlserver':
                connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config['host']},{config['port']};DATABASE={config['database']};UID={config['username']};PWD={config['password']}"
                connection = pyodbc.connect(connection_string)
                connection.close()
                
            elif db_type == 'sqlite':
                connection = sqlite3.connect(config['database'])
                connection.close()
                
            elif db_type == 'mongodb':
                client = pymongo.MongoClient(
                    f"mongodb://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
                )
                client.admin.command('ping')
                client.close()
                
            else:
                return {
                    'success': False,
                    'error': f'不支持的数据库类型: {db_type}'
                }
            
            return {
                'success': True,
                'message': '连接成功'
            }
            
        except Exception as e:
            logger.error(f"数据库连接测试失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_tables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """获取数据库中的表列表"""
        try:
            db_type = config.get('type', '').lower()
            tables = []
            
            if db_type == 'mysql':
                connection = pymysql.connect(
                    host=config['host'],
                    port=int(config['port']),
                    user=config['username'],
                    password=config['password'],
                    database=config['database'],
                    charset='utf8mb4'
                )
                cursor = connection.cursor()
                cursor.execute("SHOW TABLES")
                table_names = cursor.fetchall()
                
                for table_name in table_names:
                    table_name = table_name[0]
                    # 获取表的行数和列数
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    row_count = cursor.fetchone()[0]
                    
                    cursor.execute(f"DESCRIBE `{table_name}`")
                    columns = cursor.fetchall()
                    col_count = len(columns)
                    
                    tables.append({
                        'name': table_name,
                        'description': f'{table_name}表',
                        'rows': row_count,
                        'columns': col_count
                    })
                
                cursor.close()
                connection.close()
                
            elif db_type == 'postgresql':
                connection = psycopg2.connect(
                    host=config['host'],
                    port=int(config['port']),
                    user=config['username'],
                    password=config['password'],
                    database=config['database']
                )
                cursor = connection.cursor()
                
                # 获取表列表
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """)
                table_names = cursor.fetchall()
                
                for table_name in table_names:
                    table_name = table_name[0]
                    # 获取表的行数和列数
                    cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
                    row_count = cursor.fetchone()[0]
                    
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}' AND table_schema = 'public'
                    """)
                    col_count = cursor.fetchone()[0]
                    
                    tables.append({
                        'name': table_name,
                        'description': f'{table_name}表',
                        'rows': row_count,
                        'columns': col_count
                    })
                
                cursor.close()
                connection.close()
                
            elif db_type == 'oracle':
                dsn = cx_Oracle.makedsn(config['host'], int(config['port']), service_name=config['database'])
                connection = cx_Oracle.connect(config['username'], config['password'], dsn)
                cursor = connection.cursor()
                
                # 获取表列表
                cursor.execute("""
                    SELECT table_name 
                    FROM user_tables 
                    ORDER BY table_name
                """)
                table_names = cursor.fetchall()
                
                for table_name in table_names:
                    table_name = table_name[0]
                    # 获取表的行数和列数
                    cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
                    row_count = cursor.fetchone()[0]
                    
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM user_tab_columns 
                        WHERE table_name = '{table_name}'
                    """)
                    col_count = cursor.fetchone()[0]
                    
                    tables.append({
                        'name': table_name,
                        'description': f'{table_name}表',
                        'rows': row_count,
                        'columns': col_count
                    })
                
                cursor.close()
                connection.close()
                
            elif db_type == 'sqlserver':
                connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config['host']},{config['port']};DATABASE={config['database']};UID={config['username']};PWD={config['password']}"
                connection = pyodbc.connect(connection_string)
                cursor = connection.cursor()
                
                # 获取表列表
                cursor.execute("""
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_TYPE = 'BASE TABLE'
                """)
                table_names = cursor.fetchall()
                
                for table_name in table_names:
                    table_name = table_name[0]
                    # 获取表的行数和列数
                    cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                    row_count = cursor.fetchone()[0]
                    
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_NAME = '{table_name}'
                    """)
                    col_count = cursor.fetchone()[0]
                    
                    tables.append({
                        'name': table_name,
                        'description': f'{table_name}表',
                        'rows': row_count,
                        'columns': col_count
                    })
                
                cursor.close()
                connection.close()
                
            elif db_type == 'sqlite':
                connection = sqlite3.connect(config['database'])
                cursor = connection.cursor()
                
                # 获取表列表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                table_names = cursor.fetchall()
                
                for table_name in table_names:
                    table_name = table_name[0]
                    # 获取表的行数和列数
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    row_count = cursor.fetchone()[0]
                    
                    cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                    columns = cursor.fetchall()
                    col_count = len(columns)
                    
                    tables.append({
                        'name': table_name,
                        'description': f'{table_name}表',
                        'rows': row_count,
                        'columns': col_count
                    })
                
                cursor.close()
                connection.close()
                
            elif db_type == 'mongodb':
                client = pymongo.MongoClient(
                    f"mongodb://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
                )
                db = client[config['database']]
                collections = db.list_collection_names()
                
                for collection_name in collections:
                    collection = db[collection_name]
                    doc_count = collection.count_documents({})
                    
                    # 获取一个样本文档来估算字段数
                    sample_doc = collection.find_one()
                    field_count = len(sample_doc) if sample_doc else 0
                    
                    tables.append({
                        'name': collection_name,
                        'description': f'{collection_name}集合',
                        'rows': doc_count,
                        'columns': field_count
                    })
                
                client.close()
                
            else:
                return {
                    'success': False,
                    'error': f'不支持的数据库类型: {db_type}'
                }
            
            return {
                'success': True,
                'tables': tables
            }
            
        except Exception as e:
            logger.error(f"获取表列表失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_table_data(self, config: Dict[str, Any], table_name: str, limit: int = 100) -> Dict[str, Any]:
        """获取表数据"""
        try:
            db_type = config.get('type', '').lower()
            
            if db_type == 'mysql':
                connection = pymysql.connect(
                    host=config['host'],
                    port=int(config['port']),
                    user=config['username'],
                    password=config['password'],
                    database=config['database'],
                    charset='utf8mb4'
                )
                df = pd.read_sql(f"SELECT * FROM `{table_name}` LIMIT {limit}", connection)
                connection.close()
                
            elif db_type == 'postgresql':
                connection = psycopg2.connect(
                    host=config['host'],
                    port=int(config['port']),
                    user=config['username'],
                    password=config['password'],
                    database=config['database']
                )
                df = pd.read_sql(f'SELECT * FROM "{table_name}" LIMIT {limit}', connection)
                connection.close()
                
            elif db_type == 'oracle':
                dsn = cx_Oracle.makedsn(config['host'], int(config['port']), service_name=config['database'])
                connection = cx_Oracle.connect(config['username'], config['password'], dsn)
                df = pd.read_sql(f'SELECT * FROM "{table_name}" WHERE ROWNUM <= {limit}', connection)
                connection.close()
                
            elif db_type == 'sqlserver':
                connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config['host']},{config['port']};DATABASE={config['database']};UID={config['username']};PWD={config['password']}"
                connection = pyodbc.connect(connection_string)
                df = pd.read_sql(f"SELECT TOP {limit} * FROM [{table_name}]", connection)
                connection.close()
                
            elif db_type == 'sqlite':
                connection = sqlite3.connect(config['database'])
                df = pd.read_sql(f"SELECT * FROM `{table_name}` LIMIT {limit}", connection)
                connection.close()
                
            elif db_type == 'mongodb':
                client = pymongo.MongoClient(
                    f"mongodb://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
                )
                db = client[config['database']]
                collection = db[table_name]
                
                # 获取数据并转换为DataFrame
                data = list(collection.find().limit(limit))
                if data:
                    df = pd.DataFrame(data)
                    # 移除MongoDB的_id字段
                    if '_id' in df.columns:
                        df = df.drop('_id', axis=1)
                else:
                    df = pd.DataFrame()
                
                client.close()
                
            else:
                return {
                    'success': False,
                    'error': f'不支持的数据库类型: {db_type}'
                }
            
            # 转换为列表格式
            data_list = [df.columns.tolist()] + df.values.tolist()
            
            return {
                'success': True,
                'data': data_list,
                'columns': df.columns.tolist(),
                'rows': len(df)
            }
            
        except Exception as e:
            logger.error(f"获取表数据失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
