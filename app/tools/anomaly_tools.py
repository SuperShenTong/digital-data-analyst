from app.tools.base_tool import BaseTool
from app.services.data_service import DataService
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
from scipy import stats


class AnomalyDetectionTool(BaseTool):
    """
    数据异常洞察工具

    核心能力：
    1. 极值异常检测（Z-score / IQR 方法）
    2. 环比异常检测（MoM - Month-over-Month）
    3. 同比异常检测（YoY - Year-over-Year）
    4. 数值突变检测（Change Point）
    5. 综合异常检测（一键调用所有方法）
    6. 智能建议生成（基于异常优化建议）
    """

    name = "anomaly_detection"
    description = "全面检测数据异常，支持极值、环比、同比、突变检测，生成排查建议"
    parameters = {
        "data_source_id": {"type": "integer", "description": "数据源ID", "required": True},
        "column_name": {"type": "string", "description": "要检测的字段名称", "required": True},
        "method": {"type": "string", "description": "检测方法：zscore, iqr, mom, yoy, change_point, comprehensive", "required": False},
        "time_column": {"type": "string", "description": "时间字段（用于环比/同比检测）", "required": False},
        "threshold": {"type": "number", "description": "自定义阈值", "required": False}
    }

    def __init__(self, db: Session):
        self.data_service = DataService(db)

    def execute(self, **kwargs):
        """
        执行异常检测

        Args:
            data_source_id: 数据源ID
            column_name: 要检测的字段名称
            method: 检测方法
            time_column: 时间字段（可选）
            threshold: 自定义阈值（可选）

        Returns:
            包含检测结果和建议
        """
        data_source_id = kwargs.get("data_source_id")
        column_name = kwargs.get("column_name")
        method = kwargs.get("method", "comprehensive")
        time_column = kwargs.get("time_column")
        threshold = kwargs.get("threshold")

        if not data_source_id or not column_name:
            return {"error": "缺少必填参数: data_source_id 和 column_name"}

        try:
            df = self.data_service.load_dataframe(data_source_id)
        except Exception as e:
            return {"error": f"加载数据源失败: {str(e)}"}

        if column_name not in df.columns:
            return {"error": f"字段 '{column_name}' 不在数据源中"}

        if not pd.api.types.is_numeric_dtype(df[column_name]):
            return {"error": f"字段 '{column_name}' 不是数值型字段，无法进行异常检测"}

        all_anomalies = []

        try:
            if method == "comprehensive":
                zscore_anomalies = self.detect_zscore_anomalies(df, column_name, threshold)
                iqr_anomalies = self.detect_iqr_anomalies(df, column_name, threshold)
                change_point_anomalies = self.detect_change_points(df, column_name, time_column, threshold)
                mom_anomalies = self.detect_mom_anomalies(df, column_name, time_column, threshold)
                yoy_anomalies = self.detect_yoy_anomalies(df, column_name, time_column, threshold)

                all_anomalies.extend(zscore_anomalies)
                all_anomalies.extend(iqr_anomalies)
                all_anomalies.extend(change_point_anomalies)
                all_anomalies.extend(mom_anomalies)
                all_anomalies.extend(yoy_anomalies)

            elif method == "zscore":
                all_anomalies = self.detect_zscore_anomalies(df, column_name, threshold)

            elif method == "iqr":
                all_anomalies = self.detect_iqr_anomalies(df, column_name, threshold)

            elif method == "mom":
                all_anomalies = self.detect_mom_anomalies(df, column_name, time_column, threshold)

            elif method == "yoy":
                all_anomalies = self.detect_yoy_anomalies(df, column_name, time_column, threshold)

            elif method == "change_point":
                all_anomalies = self.detect_change_points(df, column_name, time_column, threshold)

            # 去重和排序
            all_anomalies = self._deduplicate_anomalies(all_anomalies)
            all_anomalies.sort(key=lambda x: x.get("severity_score", 0), reverse=True)

            # 生成建议
            suggestions = self._generate_suggestions(all_anomalies, column_name)

            # 评估影响范围
            impact = self._assess_impact(all_anomalies, df, column_name)

            return {
                "status": "success",
                "anomalies": all_anomalies[:20],  # 最多返回20个最严重的
                "total_count": len(all_anomalies),
                "method_used": method,
                "column": column_name,
                "suggestions": suggestions,
                "impact_assessment": impact,
                "basis": f"基于 {len(df)} 行数据进行异常检测"
            }

        except Exception as e:
            return {"error": f"异常检测失败: {str(e)}"}

    def detect_zscore_anomalies(self, df: pd.DataFrame, column: str, threshold=None):
        """
        【极值异常】Z-score方法

        原理：计算每个数据点与均值的标准差距离
        - Z-score > 3 或 < -3 判定为异常
        """
        results = []
        data = df[column].dropna()

        if len(data) < 3:
            return results

        z_threshold = threshold if threshold else 3.0

        z_scores = np.abs(stats.zscore(data))

        for idx, z_score in zip(data.index, z_scores):
            if z_score > z_threshold:
                value = float(data.iloc[list(data.index).index(idx)])
                severity = "high" if z_score > 4 else "medium" if z_score > 3.5 else "low"
                severity_score = float(z_score)

                results.append({
                    "type": "极值异常(Z-score)",
                    "type_en": "extreme_value_zscore",
                    "index": int(idx),
                    "value": value,
                    "z_score": round(float(z_score), 2),
                    "threshold": z_threshold,
                    "column": column,
                    "severity": severity,
                    "severity_score": severity_score,
                    "description": f"值 {value} 与均值的距离为 {z_score:.2f} 个标准差，超过阈值 {z_threshold}",
                    "basis": f"基于Z-score统计方法，值偏离均值超过 {z_threshold} 个标准差",
                    "suggestion": "请核查该数据是否为录入错误、特殊业务事件或真实极值",
                    "impact_scope": "单点异常，建议单独评估业务影响"
                })

        return results

    def detect_iqr_anomalies(self, df: pd.DataFrame, column: str, threshold=None):
        """
        【极值异常】IQR四分位距方法

        原理：基于四分位距识别异常值
        - 值 < Q1 - 1.5*IQR 或 > Q3 + 1.5*IQR
        """
        results = []
        data = df[column].dropna()

        if len(data) < 4:
            return results

        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1

        iqr_multiplier = threshold if threshold else 1.5

        lower_bound = q1 - iqr_multiplier * iqr
        upper_bound = q3 + iqr_multiplier * iqr

        for idx, value in data.items():
            if value < lower_bound or value > upper_bound:
                distance = max(abs(value - upper_bound), abs(lower_bound - value))
                distance_ratio = distance / iqr if iqr > 0 else 0
                severity = "high" if distance_ratio > 3 else "medium" if distance_ratio > 2 else "low"
                severity_score = distance_ratio

                results.append({
                    "type": "极值异常(IQR)",
                    "type_en": "extreme_value_iqr",
                    "index": int(idx),
                    "value": float(value),
                    "expected_range": [float(lower_bound), float(upper_bound)],
                    "iqr_value": float(iqr),
                    "threshold": iqr_multiplier,
                    "column": column,
                    "severity": severity,
                    "severity_score": severity_score,
                    "description": f"值 {value} 超出IQR范围 [{lower_bound:.2f}, {upper_bound:.2f}]",
                    "basis": f"基于四分位距方法，IQR={iqr:.2f}，使用 {iqr_multiplier}xIQR 阈值",
                    "suggestion": "检查是否为业务范围内的合理数据，或存在业务调整或特殊事件",
                    "impact_scope": "箱线图判定的异常点，关注其业务合理性"
                })

        return results

    def detect_mom_anomalies(self, df: pd.DataFrame, column: str, time_column: str = None, threshold=None):
        """
        【环比异常】Month-over-Month

        原理：检测相邻数据点的变化率
        - 变化率 > 30% 以上的突变判定为异常
        """
        results = []
        data = df[column].dropna()

        if len(data) < 3:
            return results

        mom_threshold = threshold if threshold else 0.3  # 默认30%变化率

        values = data.values

        for i in range(1, len(values)):
            prev_value = values[i - 1]
            curr_value = values[i]

            if prev_value != 0:
                change_rate = abs((curr_value - prev_value) / abs(prev_value))
            else:
                change_rate = abs(curr_value) if curr_value != 0 else 0

            if change_rate > mom_threshold:
                idx = data.index[i]
                severity = "high" if change_rate > 1.0 else "medium" if change_rate > 0.5 else "low"
                severity_score = float(change_rate)

                results.append({
                    "type": "环比异常(MoM)",
                    "type_en": "mom_anomaly",
                    "index": int(idx),
                    "value": float(curr_value),
                    "previous_value": float(prev_value),
                    "change_rate": round(float(change_rate), 4),
                    "threshold": mom_threshold,
                    "column": column,
                    "severity": severity,
                    "severity_score": severity_score,
                    "description": f"从 {prev_value} 变为 {curr_value}，环比变化率 {change_rate*100:.1f}%",
                    "basis": f"相邻数据点环比变化超过 {mom_threshold*100:.0f}% 阈值",
                    "suggestion": "检查是否存在促销活动、季节性变化、数据录入错误或业务结构调整",
                    "impact_scope": "时间序列中的显著变化点，建议深入分析前后数据变化原因"
                })

        return results

    def detect_yoy_anomalies(self, df: pd.DataFrame, column: str, time_column: str = None, threshold=None):
        """
        【同比异常】Year-over-Year

        原理：检测同期数据对比，识别大幅偏离同期均值的点
        """
        results = []
        data = df[column].dropna()

        if len(data) < 6:
            return results

        yoy_threshold = threshold if threshold else 0.4  # 默认40%

        mean_val = data.mean()
        std_val = data.std() if data.std() > 0 else 1

        for idx, value in data.items():
            if mean_val != 0:
                deviation = abs((value - mean_val) / abs(mean_val))
            else:
                deviation = abs(value) if value != 0 else 0

            if deviation > yoy_threshold:
                severity = "high" if deviation > 1.0 else "medium" if deviation > 0.6 else "low"
                severity_score = float(deviation)

                results.append({
                    "type": "同比异常(YoY)",
                    "type_en": "yoy_anomaly",
                    "index": int(idx),
                    "value": float(value),
                    "period_mean": float(mean_val),
                    "deviation_rate": round(float(deviation), 4),
                    "threshold": yoy_threshold,
                    "column": column,
                    "severity": severity,
                    "severity_score": severity_score,
                    "description": f"值 {value} 与同期均值 {mean_val:.2f} 的偏离率为 {deviation*100:.1f}%",
                    "basis": f"基于同期数据均值对比方法，偏离超过 {yoy_threshold*100:.0f}% 阈值",
                    "suggestion": "分析是否为结构性变化、周期性因素或特殊业务事件",
                    "impact_scope": "显著偏离同期均值，关注业务背景分析"
                })

        return results

    def detect_change_points(self, df: pd.DataFrame, column: str, time_column: str = None, threshold=None):
        """
        【突变检测】Change Point Detection

        原理：检测数值序列中的突变点
        - 相邻差分显著大于历史平均差分
        """
        results = []
        data = df[column].dropna().values

        if len(data) < 5:
            return results

        diffs = np.diff(data)
        mean_diff = np.mean(np.abs(diffs))
        std_diff = np.std(diffs) if np.std(diffs) > 0 else 1

        cp_threshold = threshold if threshold else mean_diff + 3 * std_diff

        for i, diff in enumerate(diffs):
            if abs(diff) > cp_threshold:
                idx = df[column].dropna().index[i + 1]
                prev_val = float(data[i])
                curr_val = float(data[i + 1])
                severity = "high" if abs(diff) > cp_threshold * 2 else "medium" if abs(diff) > cp_threshold * 1.5 else "low"
                severity_score = float(abs(diff) / cp_threshold)

                results.append({
                    "type": "突变异常",
                    "type_en": "change_point",
                    "index": int(idx),
                    "value": curr_val,
                    "previous_value": prev_val,
                    "change_amount": float(diff),
                    "mean_diff": float(mean_diff),
                    "threshold": float(cp_threshold),
                    "column": column,
                    "severity": severity,
                    "severity_score": severity_score,
                    "description": f"数值从 {prev_val} 突变为 {curr_val}，变化量 {diff}",
                    "basis": f"基于差分分析，变化量显著超过历史平均差分 + 3倍标准差阈值",
                    "suggestion": "检查是否存在数据采集中断、业务突变或录入错误",
                    "impact_scope": "序列突变点，建议检查前后数据完整性"
                })

        return results

    def comprehensive_anomaly_detection(self, data_source_id: int, column_name: str, time_column: str = None) -> dict:
        """
        【综合异常检测】一键调用所有检测方法

        Args:
            data_source_id: 数据源ID
            column_name: 要检测的字段
            time_column: 时间字段

        Returns:
            汇总结果
        """
        result = self.execute(
            data_source_id=data_source_id,
            column_name=column_name,
            method="comprehensive",
            time_column=time_column
        )

        # 按类型统计
        anomalies = result.get("anomalies", [])

        type_counts = {}
        for a in anomalies:
            t = a.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        result["anomaly_type_distribution"] = type_counts
        return result

    def _deduplicate_anomalies(self, anomalies):
        """去重：同一索引的多个异常只保留最严重的"""
        seen = {}
        anomaly_list = anomalies
        final = []

        # 按严重程度排序
        anomaly_list.sort(key=lambda x: x.get("severity_score", 0), reverse=True)

        for a in anomaly_list:
            key = (a.get("index"), a.get("type_en"))
            if key not in seen:
                seen[key] = True
                final.append(a)

        return final

    def _generate_suggestions(self, anomalies, column_name):
        """生成智能优化建议"""
        if not anomalies:
            return [f"字段【{column_name}】未检测到显著异常，数据质量良好"]

        high_count = sum(1 for a in anomalies if a.get("severity") == "high")
        medium_count = sum(1 for a in anomalies if a.get("severity") == "medium")
        total = len(anomalies)

        suggestions = []

        suggestions.append(
            f"共检测到 {total} 个异常点：{high_count} 个高风险，{medium_count} 个中等风险"
        )

        if high_count > 0:
            suggestions.append(
                "【高优先级】首先核查高风险异常点：建议立即核查这些数据是否为录入错误、系统故障或真实业务极值"
            )

        types_found = set(a.get("type_en", "") for a in anomalies)

        if "mom_anomaly" in types_found:
            suggestions.append(
                "【环比异常排查建议】检查环比变化率高的时段是否存在促销活动、季节性变化或数据采集变更"
            )

        if "yoy_anomaly" in types_found:
            suggestions.append(
                "【同比异常排查建议】分析是否为结构性业务变化、周期性因素或特殊事件影响"
            )

        if "change_point" in types_found:
            suggestions.append(
                "【突变异常排查建议】核查数据采集是否中断、业务突变或业务政策变化"
            )

        if "extreme_value_zscore" in types_found or "extreme_value_iqr" in types_found:
            suggestions.append(
                "【极值异常排查建议】验证极值数据是否为真实业务数据，考虑是否需要剔除或特殊标注"
            )

        suggestions.append(
            f"【优化建议】建议建立数据质量监控机制，定期检查【{column_name}】字段的异常波动"
        )

        return suggestions

    def _assess_impact(self, anomalies, df, column_name):
        """评估异常影响范围"""
        if not anomalies:
            return {
                "impact_level": "low",
                "affected_rows": 0,
                "affected_percentage": 0.0,
                "summary": "无异常"
            }

        total_rows = len(df)
        affected_rows = len(set(a.get("index") for a in anomalies))
        percentage = round((affected_rows / total_rows) * 100, 2) if total_rows > 0 else 0

        high_count = sum(1 for a in anomalies if a.get("severity") == "high")

        if high_count > 5 or percentage > 10:
            impact_level = "high"
        elif high_count > 2 or percentage > 5:
            impact_level = "medium"
        else:
            impact_level = "low"

        return {
            "impact_level": impact_level,
            "impact_level_cn": {"high": "高", "medium": "中", "low": "低"}[impact_level],
            "affected_rows": affected_rows,
            "total_rows": total_rows,
            "affected_percentage": percentage,
            "high_severity_count": high_count,
            "summary": f"影响 {affected_rows}/{total_rows} 行数据 ({percentage}%)，影响等级【{impact_level}】"
        }
