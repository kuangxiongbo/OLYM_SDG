#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量评估器
==========

提供全面的合成数据质量评估功能
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy import stats
from scipy.stats import ks_2samp, chi2_contingency
import logging

logger = logging.getLogger(__name__)

class QualityEvaluator:
    """质量评估器类"""
    
    def __init__(self):
        self.evaluation_metrics = {
            'statistical_similarity': self._evaluate_statistical_similarity,
            'distribution_similarity': self._evaluate_distribution_similarity,
            'correlation_similarity': self._evaluate_correlation_similarity,
            'categorical_similarity': self._evaluate_categorical_similarity,
            'data_quality': self._evaluate_data_quality
        }
    
    def evaluate(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Dict[str, Any]:
        """执行完整的质量评估"""
        evaluation_results = {
            'overall_score': 0,
            'metrics': {},
            'recommendations': [],
            'summary': {}
        }
        
        try:
            # 执行各项评估
            for metric_name, metric_func in self.evaluation_metrics.items():
                try:
                    score, details = metric_func(original_df, synthetic_df)
                    evaluation_results['metrics'][metric_name] = {
                        'score': score,
                        'details': details
                    }
                except Exception as e:
                    logger.warning(f"评估指标 {metric_name} 失败: {e}")
                    evaluation_results['metrics'][metric_name] = {
                        'score': 0,
                        'details': {'error': str(e)}
                    }
            
            # 计算总体分数
            scores = [metric['score'] for metric in evaluation_results['metrics'].values() if metric['score'] > 0]
            if scores:
                evaluation_results['overall_score'] = np.mean(scores)
            
            # 生成建议
            evaluation_results['recommendations'] = self._generate_recommendations(evaluation_results)
            
            # 生成摘要
            evaluation_results['summary'] = self._generate_summary(evaluation_results)
            
        except Exception as e:
            logger.error(f"质量评估失败: {e}")
            evaluation_results['error'] = str(e)
        
        return evaluation_results
    
    def _evaluate_statistical_similarity(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """评估统计相似性"""
        numeric_cols = original_df.select_dtypes(include=[np.number]).columns
        numeric_cols = [col for col in numeric_cols if col in synthetic_df.columns]
        
        if len(numeric_cols) == 0:
            return 0, {'message': '无数值列可评估'}
        
        similarities = []
        details = {}
        
        for col in numeric_cols:
            orig_data = original_df[col].dropna()
            synth_data = synthetic_df[col].dropna()
            
            if len(orig_data) == 0 or len(synth_data) == 0:
                continue
            
            # 计算统计指标
            orig_mean = orig_data.mean()
            synth_mean = synth_data.mean()
            orig_std = orig_data.std()
            synth_std = synth_data.std()
            orig_median = orig_data.median()
            synth_median = synth_data.median()
            
            # 计算相似性分数
            mean_similarity = 1 - abs(orig_mean - synth_mean) / (abs(orig_mean) + 1e-8)
            std_similarity = 1 - abs(orig_std - synth_std) / (abs(orig_std) + 1e-8)
            median_similarity = 1 - abs(orig_median - synth_median) / (abs(orig_median) + 1e-8)
            
            col_similarity = (mean_similarity + std_similarity + median_similarity) / 3
            similarities.append(max(0, col_similarity))
            
            details[col] = {
                'mean_similarity': mean_similarity,
                'std_similarity': std_similarity,
                'median_similarity': median_similarity,
                'overall_similarity': col_similarity,
                'original_stats': {
                    'mean': orig_mean,
                    'std': orig_std,
                    'median': orig_median
                },
                'synthetic_stats': {
                    'mean': synth_mean,
                    'std': synth_std,
                    'median': synth_median
                }
            }
        
        overall_score = np.mean(similarities) * 100 if similarities else 0
        
        return overall_score, details
    
    def _evaluate_distribution_similarity(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """评估分布相似性"""
        numeric_cols = original_df.select_dtypes(include=[np.number]).columns
        numeric_cols = [col for col in numeric_cols if col in synthetic_df.columns]
        
        if len(numeric_cols) == 0:
            return 0, {'message': '无数值列可评估'}
        
        similarities = []
        details = {}
        
        for col in numeric_cols:
            orig_data = original_df[col].dropna()
            synth_data = synthetic_df[col].dropna()
            
            if len(orig_data) < 10 or len(synth_data) < 10:
                continue
            
            try:
                # Kolmogorov-Smirnov测试
                ks_statistic, ks_p_value = ks_2samp(orig_data, synth_data)
                
                # 计算分布相似性分数
                # KS统计量越小，p值越大，相似性越高
                ks_similarity = 1 - ks_statistic
                p_similarity = min(ks_p_value * 10, 1)  # 将p值转换为0-1分数
                
                distribution_similarity = (ks_similarity + p_similarity) / 2
                similarities.append(max(0, distribution_similarity))
                
                details[col] = {
                    'ks_statistic': ks_statistic,
                    'ks_p_value': ks_p_value,
                    'ks_similarity': ks_similarity,
                    'p_similarity': p_similarity,
                    'distribution_similarity': distribution_similarity
                }
                
            except Exception as e:
                logger.warning(f"分布相似性评估失败 {col}: {e}")
                continue
        
        overall_score = np.mean(similarities) * 100 if similarities else 0
        
        return overall_score, details
    
    def _evaluate_correlation_similarity(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """评估相关性相似性"""
        numeric_cols = original_df.select_dtypes(include=[np.number]).columns
        numeric_cols = [col for col in numeric_cols if col in synthetic_df.columns]
        
        if len(numeric_cols) < 2:
            return 0, {'message': '数值列数量不足，无法评估相关性'}
        
        try:
            # 计算相关性矩阵
            orig_corr = original_df[numeric_cols].corr()
            synth_corr = synthetic_df[numeric_cols].corr()
            
            # 计算相关性差异
            corr_diff = np.abs(orig_corr - synth_corr)
            
            # 排除对角线元素
            mask = np.ones_like(corr_diff, dtype=bool)
            np.fill_diagonal(mask, False)
            corr_diff_masked = corr_diff[mask]
            
            # 计算相似性分数
            correlation_similarity = 1 - np.mean(corr_diff_masked)
            overall_score = max(0, correlation_similarity) * 100
            
            details = {
                'correlation_similarity': correlation_similarity,
                'mean_correlation_difference': np.mean(corr_diff_masked),
                'max_correlation_difference': np.max(corr_diff_masked),
                'original_correlation_matrix': orig_corr.to_dict(),
                'synthetic_correlation_matrix': synth_corr.to_dict()
            }
            
        except Exception as e:
            logger.warning(f"相关性相似性评估失败: {e}")
            return 0, {'error': str(e)}
        
        return overall_score, details
    
    def _evaluate_categorical_similarity(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """评估分类相似性"""
        categorical_cols = original_df.select_dtypes(include=['object', 'category']).columns
        categorical_cols = [col for col in categorical_cols if col in synthetic_df.columns]
        
        if len(categorical_cols) == 0:
            return 0, {'message': '无分类列可评估'}
        
        similarities = []
        details = {}
        
        for col in categorical_cols:
            orig_data = original_df[col].dropna()
            synth_data = synthetic_df[col].dropna()
            
            if len(orig_data) == 0 or len(synth_data) == 0:
                continue
            
            # 计算类别分布
            orig_counts = orig_data.value_counts(normalize=True)
            synth_counts = synth_data.value_counts(normalize=True)
            
            # 获取所有类别
            all_categories = set(orig_counts.index) | set(synth_counts.index)
            
            # 计算分布差异
            total_diff = 0
            for category in all_categories:
                orig_prob = orig_counts.get(category, 0)
                synth_prob = synth_counts.get(category, 0)
                total_diff += abs(orig_prob - synth_prob)
            
            # 计算相似性分数
            categorical_similarity = 1 - total_diff / 2  # 除以2是因为最大差异为2
            similarities.append(max(0, categorical_similarity))
            
            details[col] = {
                'categorical_similarity': categorical_similarity,
                'total_difference': total_diff,
                'original_distribution': orig_counts.to_dict(),
                'synthetic_distribution': synth_counts.to_dict(),
                'unique_categories_original': len(orig_counts),
                'unique_categories_synthetic': len(synth_counts)
            }
        
        overall_score = np.mean(similarities) * 100 if similarities else 0
        
        return overall_score, details
    
    def _evaluate_data_quality(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """评估数据质量"""
        quality_metrics = {}
        
        # 检查缺失值
        orig_missing = original_df.isnull().sum().sum()
        synth_missing = synthetic_df.isnull().sum().sum()
        orig_total = original_df.shape[0] * original_df.shape[1]
        synth_total = synthetic_df.shape[0] * synthetic_df.shape[1]
        
        orig_missing_rate = orig_missing / orig_total if orig_total > 0 else 0
        synth_missing_rate = synth_missing / synth_total if synth_total > 0 else 0
        
        # 检查重复值
        orig_duplicates = original_df.duplicated().sum()
        synth_duplicates = synthetic_df.duplicated().sum()
        
        orig_duplicate_rate = orig_duplicates / original_df.shape[0] if original_df.shape[0] > 0 else 0
        synth_duplicate_rate = synth_duplicates / synthetic_df.shape[0] if synthetic_df.shape[0] > 0 else 0
        
        # 检查数据类型一致性
        dtype_consistency = 0
        for col in original_df.columns:
            if col in synthetic_df.columns:
                if original_df[col].dtype == synthetic_df[col].dtype:
                    dtype_consistency += 1
        
        dtype_consistency_rate = dtype_consistency / len(original_df.columns) if len(original_df.columns) > 0 else 0
        
        # 计算质量分数
        missing_quality = 1 - abs(orig_missing_rate - synth_missing_rate)
        duplicate_quality = 1 - abs(orig_duplicate_rate - synth_duplicate_rate)
        
        overall_quality = (missing_quality + duplicate_quality + dtype_consistency_rate) / 3
        overall_score = max(0, overall_quality) * 100
        
        quality_metrics = {
            'missing_value_quality': missing_quality,
            'duplicate_quality': duplicate_quality,
            'dtype_consistency': dtype_consistency_rate,
            'overall_quality': overall_quality,
            'original_missing_rate': orig_missing_rate,
            'synthetic_missing_rate': synth_missing_rate,
            'original_duplicate_rate': orig_duplicate_rate,
            'synthetic_duplicate_rate': synth_duplicate_rate,
            'dtype_consistency_rate': dtype_consistency_rate
        }
        
        return overall_score, quality_metrics
    
    def _generate_recommendations(self, evaluation_results: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        overall_score = evaluation_results.get('overall_score', 0)
        
        # 基于总体分数
        if overall_score < 60:
            recommendations.append("总体质量较低，建议调整模型参数或增加训练轮数")
        elif overall_score < 80:
            recommendations.append("质量良好，可以尝试微调参数以获得更好效果")
        
        # 基于各项指标
        metrics = evaluation_results.get('metrics', {})
        
        if 'statistical_similarity' in metrics:
            stat_score = metrics['statistical_similarity']['score']
            if stat_score < 70:
                recommendations.append("统计相似性较低，建议检查数值列的分布和范围")
        
        if 'distribution_similarity' in metrics:
            dist_score = metrics['distribution_similarity']['score']
            if dist_score < 70:
                recommendations.append("分布相似性较低，建议增加训练轮数或调整学习率")
        
        if 'correlation_similarity' in metrics:
            corr_score = metrics['correlation_similarity']['score']
            if corr_score < 70:
                recommendations.append("相关性相似性较低，建议使用更复杂的模型结构")
        
        if 'categorical_similarity' in metrics:
            cat_score = metrics['categorical_similarity']['score']
            if cat_score < 70:
                recommendations.append("分类相似性较低，建议检查分类变量的编码方式")
        
        if 'data_quality' in metrics:
            quality_score = metrics['data_quality']['score']
            if quality_score < 80:
                recommendations.append("数据质量需要改进，建议进行数据预处理")
        
        return recommendations
    
    def _generate_summary(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成评估摘要"""
        overall_score = evaluation_results.get('overall_score', 0)
        
        # 确定质量等级
        if overall_score >= 90:
            quality_level = "优秀"
            quality_color = "success"
        elif overall_score >= 80:
            quality_level = "良好"
            quality_color = "info"
        elif overall_score >= 70:
            quality_level = "一般"
            quality_color = "warning"
        else:
            quality_level = "需要改进"
            quality_color = "danger"
        
        # 统计各项指标
        metrics = evaluation_results.get('metrics', {})
        metric_scores = {name: metric['score'] for name, metric in metrics.items()}
        
        # 找出最强和最弱的指标
        if metric_scores:
            best_metric = max(metric_scores.items(), key=lambda x: x[1])
            worst_metric = min(metric_scores.items(), key=lambda x: x[1])
        else:
            best_metric = ("无", 0)
            worst_metric = ("无", 0)
        
        summary = {
            'overall_score': overall_score,
            'quality_level': quality_level,
            'quality_color': quality_color,
            'best_metric': {
                'name': best_metric[0],
                'score': best_metric[1]
            },
            'worst_metric': {
                'name': worst_metric[0],
                'score': worst_metric[1]
            },
            'total_metrics': len(metrics),
            'recommendations_count': len(evaluation_results.get('recommendations', []))
        }
        
        return summary
