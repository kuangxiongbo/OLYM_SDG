"""
DatetimeFormatter补丁：在convert_datetime_columns中修复被连接的日期值
"""
import pandas as pd
import numpy as np
from datetime import datetime
import re
from typing import Dict, List

# 日期格式模式
DATE_COMPACT_PATTERN = re.compile(r'\d{8}')  # YYYYMMDD格式

def fix_concatenated_datetime_value(value: str, datetime_format: str) -> str:
    """
    修复被连接的日期时间值
    
    Args:
        value: 原始值
        datetime_format: 日期时间格式
        
    Returns:
        修复后的值（如果无法修复，返回原值）
    """
    if pd.isna(value) or str(value).strip() == '':
        return value
    
    val_str = str(value).strip()
    
    # 首先检查是否是YYYYMMDD格式被连接（如 2025040120250401...）
    if len(val_str) >= 16 and val_str.isdigit():
        date_matches = DATE_COMPACT_PATTERN.findall(val_str)
        if len(date_matches) > 1:
            # 提取第一个日期（YYYYMMDD格式）
            first_date = date_matches[0]
            if len(first_date) == 8:
                year = first_date[:4]
                month = first_date[4:6]
                day = first_date[6:8]
                # 根据datetime_format转换
                if '%Y-%m-%d' in datetime_format or '%Y/%m/%d' in datetime_format:
                    return f"{year}-{month}-{day}"
                elif '%Y%m%d' in datetime_format:
                    return first_date
                else:
                    # 默认返回YYYY-MM-DD格式
                    return f"{year}-{month}-{day}"
    
    # 如果长度超过30，可能是被连接的日期时间，尝试提取第一个
    if len(val_str) > 30:
        # 尝试使用datetime_format解析第一个匹配
        # 这里需要根据实际格式来提取，暂时返回原值让SDGX处理
        pass
    
    return val_str

def patched_convert_datetime_columns(datetime_column_list: List[str], 
                                     datetime_formats: Dict[str, str], 
                                     processed_data: pd.DataFrame) -> pd.DataFrame:
    """
    修复版的convert_datetime_columns，在转换前修复被连接的值
    
    这是对SDGX的DatetimeFormatter.convert_datetime_columns的补丁
    """
    def datetime_formatter(each_value, datetime_format):
        """
        convert each single column datetime string to timestamp int value.
        """
        try:
            # 先修复被连接的值
            fixed_value = fix_concatenated_datetime_value(each_value, datetime_format)
            datetime_obj = datetime.strptime(str(fixed_value), datetime_format)
            each_stamp = datetime.timestamp(datetime_obj)
        except Exception as e:
            # 如果修复后仍然无法解析，记录警告并返回NaN
            import logging
            logger = logging.getLogger('sdgx.data_processors.formatters.datetime')
            logger.warning(
                f"An error occured when convert str to timestamp {e}, we set as mean."
            )
            logger.warning(f"Input parameters: ({str(each_value)}, {datetime_format})")
            logger.warning(f"Fixed value: {str(fixed_value)}")
            logger.warning(f"Input type: ({type(each_value)}, {type(datetime_format)})")
            each_stamp = np.nan
        return each_stamp

    # Make a copy of processed_data to avoid modifying the original data
    result_data: pd.DataFrame = processed_data.copy()

    # Convert each datetime column in datetime_column_list to timestamp
    for column in datetime_column_list:
        # 在转换前，先修复被连接的值
        # 检查是否有被连接的值
        problematic_mask = result_data[column].astype(str).apply(
            lambda x: len(str(x).strip()) >= 16 and str(x).strip().isdigit() or len(str(x).strip()) > 30
        )
        if problematic_mask.any():
            import logging
            logger = logging.getLogger('sdgx.data_processors.formatters.datetime')
            problematic_count = problematic_mask.sum()
            logger.warning(f"发现 {column} 列有 {problematic_count} 个被连接的值，正在修复...")
            
            # 修复被连接的值
            result_data.loc[problematic_mask, column] = result_data.loc[problematic_mask, column].apply(
                lambda x: fix_concatenated_datetime_value(x, datetime_formats[column])
            )
            logger.warning(f"已修复 {column} 列中的被连接值")
        
        # Convert datetime to timestamp (int)
        result_data[column] = result_data[column].apply(
            datetime_formatter, datetime_format=datetime_formats[column]
        )
        result_data[column].fillna(result_data[column].mean(), inplace=True)
    return result_data



