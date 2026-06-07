"""
智能图表生成器（LLM增强版）
结合LLM语义分析和传统规则匹配，实现智能图表选择

核心原则：
1. 图表不是"必选项"，而是"辅助理解的工具"
2. 由LLM基于用户问题和数据特征决定是否需要图表
3. 图表类型和内容由LLM决定，而非固定规则
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from app.services.llm_chart_selector import LLMChartSelector

class EnhancedChartGenerator:
    """
    增强版图表生成器 - 结合LLM和规则匹配
    
    核心策略：
    1. 优先使用LLM分析用户意图和数据结构（包括异常数据）
    2. LLM会智能判断：是否需要图表、需要什么类型的图表
    3. 如果LLM分析失败或返回结果不可用，回退到简单规则匹配
    4. 确保生成的图表配置可以被前端ECharts渲染
    """
    
    def __init__(self):
        self.llm_selector = LLMChartSelector()
        
    def generate_charts(
        self,
        df: pd.DataFrame,
        user_query: str = '',
        data_source_name: str = '',
        max_charts: int = 5,
        analysis_results: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        生成图表配置（完全由LLM智能决定）
        
        核心原则：
        - 图表完全由LLM决定，不自动添加任何图表
        - 如果LLM没有推荐图表，则不展示任何图表
        - 异常数据信息已包含在data_summary中，供LLM决策使用
        
        Args:
            df: 数据框
            user_query: 用户问题
            data_source_name: 数据源名称
            max_charts: 最大图表数量
            analysis_results: 分析结果（包含statistics统计和anomalies异常数据）
            
        Returns:
            图表配置列表（ECharts格式）- 仅包含LLM推荐的图表
        """
        # 步骤1：生成数据摘要（包含异常信息），供LLM分析使用
        data_summary = self._generate_data_summary(df, data_source_name, analysis_results)
        
        # 步骤2：LLM分析 - 让LLM决定是否需要图表、需要什么类型的图表
        # 这是关键：LLM会基于用户的问题和数据特征，智能决策
        llm_charts = self.llm_selector.analyze_and_select_charts(
            user_query=user_query,
            data_summary=data_summary,
            max_charts=max_charts
        )
        
        # 步骤3：如果LLM返回了有效结果，使用LLM的结果并填充数据
        if llm_charts and len(llm_charts) > 0:
            try:
                filled_charts = self._fill_chart_data(df, llm_charts)
                print(f"[增强图表生成器] LLM推荐了 {len(filled_charts)} 个图表")
                return filled_charts
            except Exception as e:
                print(f"[增强图表生成器] LLM图表数据填充失败: {e}")
        
        # 如果LLM没有推荐图表，返回空列表（不展示任何图表）
        print(f"[增强图表生成器] LLM未推荐任何图表")
        return []
    
    def _generate_data_summary(self, df: pd.DataFrame, name: str, 
                                analysis_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成数据摘要供LLM分析 - 包含异常信息，帮助LLM做出更智能的图表决策
        
        Args:
            df: 数据框
            name: 数据源名称
            analysis_results: 分析结果（包含statistics统计和anomalies异常数据）
            
        Returns:
            数据摘要字典（包含异常信息和统计信息）
        """
        fields = []
        
        for col in df.columns[:10]:
            sample_values = df[col].dropna().head(3).tolist()
            sample_str = ", ".join([str(v)[:20] for v in sample_values])
            
            # 字段类型使用英文，便于LLM理解
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                field_type = "datetime"
            elif pd.api.types.is_numeric_dtype(df[col]):
                field_type = "numeric"
            elif df[col].nunique() < 20:
                field_type = "category"
            else:
                field_type = "text"
            
            fields.append({
                "name": col,
                "type": field_type,
                "sample": sample_str
            })
        
        summary = {
            "name": name,
            "row_count": len(df),
            "fields": fields
        }
        
        # 关键改进：如果有分析结果，将异常和统计信息也加入摘要
        # 这样LLM就能知道：哪些字段有异常？有多少个异常？异常类型是什么？
        if analysis_results:
            # 异常数据摘要
            anomalies = analysis_results.get("anomalies", [])
            if anomalies and isinstance(anomalies, list):
                anomaly_fields = list(set([a.get("column", "") for a in anomalies if a.get("column")]))
                anomaly_types = list(set([a.get("type", "") for a in anomalies if a.get("type")]))
                
                summary["anomalies_summary"] = {
                    "total_count": len(anomalies),
                    "fields_with_anomalies": anomaly_fields[:5],  # 最多5个字段
                    "anomaly_types": anomaly_types[:5],  # 最多5种异常类型
                    "sample_anomalies": anomalies[:3]  # 3个示例异常
                }
            
            # 统计数据摘要
            statistics = analysis_results.get("statistics", {})
            if statistics and isinstance(statistics, dict):
                stat_fields = list(statistics.keys())[:5]
                summary["statistics_summary"] = {
                    "fields_with_statistics": stat_fields,
                    "has_distribution": any("count" in str(statistics.get(f, {})) for f in stat_fields if f in statistics)
                }
        
        return summary
    
    def _generate_anomaly_visualization_charts(self, df: pd.DataFrame, 
                                               analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        为异常数据生成可视化图表（优化版）
        
        策略：
        1. 优先生成时间序列图（如果有时间字段，对每个异常字段生成时序图，标记异常点）
        2. 生成异常类型分布图（聚合统计，最直观的汇总图）
        3. 其次生成散点图（展示异常值偏离程度）
        
        关键改进：
        - 确保异常类型分布图总是被包含
        - 确保每个异常字段的时间序列图被生成
        - numpy 类型转换为 Python 原生类型
        - 调整返回数量限制为 5 个
        
        Args:
            df: 原始数据
            analysis_results: 分析结果（包含anomalies）
            
        Returns:
            图表配置列表
        """
        charts = []
        anomalies = analysis_results.get("anomalies", [])
        
        if not anomalies or not isinstance(anomalies, list):
            return charts
        
        # 提取有异常的字段（去重）
        anomaly_fields = []
        seen = set()
        for a in anomalies:
            field = a.get("column")
            if field and field not in seen and field in df.columns and pd.api.types.is_numeric_dtype(df[field]):
                seen.add(field)
                anomaly_fields.append(field)
        
        if not anomaly_fields:
            return charts
        
        # ========================================================
        # 步骤1：检测时间字段（全局检测，避免在循环中重复检测）
        # ========================================================
        date_col = None
        for col in df.columns:
            if "date" in col.lower() or "time" in col.lower() or "日期" in col:
                try:
                    pd.to_datetime(df[col].head(5))
                    date_col = col
                    break
                except:
                    continue
        
        # ========================================================
        # 步骤2：为每个异常字段生成时间序列图（优先，最有价值）
        # ========================================================
        for field in anomaly_fields:
            try:
                series = df[field].dropna()
                if len(series) == 0:
                    continue
                
                mean_val = float(series.mean())
                std_val = float(series.std()) if series.std() > 0 else 1.0
                
                if date_col:
                    temp_df = df[[date_col, field]].dropna().head(100)
                    if len(temp_df) > 5:
                        x_data = [str(x)[:10] for x in temp_df[date_col].tolist()]
                        y_data = [float(v) for v in temp_df[field].tolist()]
                        
                        # 标记异常点（z-score > 2.5）
                        mark_points = []
                        for i, (idx, row) in enumerate(temp_df.iterrows()):
                            value = float(row[field])
                            z_score = abs((value - mean_val) / std_val) if std_val > 0 else 0
                            if z_score > 2.5:
                                mark_points.append({
                                    "xAxis": int(i),
                                    "yAxis": float(value),
                                    "value": float(value)
                                })
                        
                        # 生成图表配置（即使没有标记点也生成，展示整体趋势）
                        line_data = []
                        for i in range(len(y_data)):
                            line_data.append({
                                "name": x_data[i] if i < len(x_data) else f"记录{i}",
                                "value": y_data[i]
                            })
                        
                        chart_config = {
                            "type": "line",
                            "title": f"{field} 时间序列（含异常点标记）",
                            "x_label": date_col,
                            "y_label": field,
                            "data": line_data,
                            "mark_points": mark_points if mark_points else []
                        }
                        charts.append(chart_config)
            except Exception as e:
                print(f"[增强图表生成器] 生成字段 {field} 的时间序列图失败: {e}")
                continue
        
        # ========================================================
        # 步骤3：生成异常类型分布图（必须包含，最重要的汇总图表）
        # ========================================================
        try:
            anomaly_types = {}
            for a in anomalies:
                t = a.get("type", "未知类型")
                if t:
                    anomaly_types[t] = int(anomaly_types.get(t, 0) + int(a.get("count", 1)))
            
            if anomaly_types:
                anomaly_chart_data = []
                for k, v in sorted(anomaly_types.items(), key=lambda x: x[1], reverse=True)[:8]:
                    anomaly_chart_data.append({
                        "name": str(k),
                        "value": int(v)
                    })
                
                chart_config = {
                    "type": "bar",
                    "title": "异常类型分布",
                    "x_label": "异常类型",
                    "y_label": "异常数量",
                    "data": anomaly_chart_data
                }
                charts.append(chart_config)
        except Exception as e:
            print(f"[增强图表生成器] 生成异常类型分布图失败: {e}")
        
        # ========================================================
        # 步骤4：为每个异常字段生成散点图（直观展示异常分布）
        # ========================================================
        for field in anomaly_fields:
            try:
                series = df[field].dropna()
                if len(series) == 0:
                    continue
                
                mean_val = float(series.mean())
                std_val = float(series.std()) if series.std() > 0 else 1.0
                
                # 计算哪些数据点是异常值（z-score > 3）
                data_points = []
                for i, (idx, value) in enumerate(series.head(50).items()):
                    z_score = abs((value - mean_val) / std_val) if std_val > 0 else 0
                    is_anomaly = bool(z_score > 3)
                    data_points.append({
                        "name": f"记录{idx}",
                        "value": [int(i), float(value)],
                        "is_anomaly": is_anomaly
                    })
                
                if len(data_points) >= 5:
                    chart_config = {
                        "type": "scatter",
                        "title": f"{field} 异常值分布（红点为异常）",
                        "x_label": "数据序号",
                        "y_label": field,
                        "data": data_points
                    }
                    charts.append(chart_config)
            except Exception as e:
                print(f"[增强图表生成器] 生成字段 {field} 的散点图失败: {e}")
                continue
        
        # 调整返回数量限制：最多返回 5 个图表（确保重要图表不被截断）
        return charts[:5]
    
    def _fill_chart_data(self, df: pd.DataFrame, chart_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为LLM推荐的图表配置填充实际数据"""
        result = []
        
        for config in chart_configs:
            chart_type = config.get('type')
            x_field = config.get('x_field')
            y_field = config.get('y_field')
            
            if x_field not in df.columns or y_field not in df.columns:
                continue
            
            try:
                chart_data = self._create_chart_with_data(df, chart_type, x_field, y_field)
                if chart_data:
                    chart_data['purpose'] = config.get('purpose', '')
                    chart_data['analysis_goal'] = config.get('analysis_goal', '')
                    result.append(chart_data)
            except Exception as e:
                print(f"[增强图表生成器] 填充图表数据失败 {chart_type}: {e}")
        
        return result
    
    def _create_chart_with_data(self, df: pd.DataFrame, chart_type: str, 
                                x_field: str, y_field: str) -> Dict[str, Any]:
        """根据类型和字段创建图表数据"""
        if chart_type == 'bar':
            return self._create_bar_chart_data(df, x_field, y_field)
        elif chart_type == 'line':
            return self._create_line_chart_data(df, x_field, y_field)
        elif chart_type == 'pie':
            return self._create_pie_chart_data(df, x_field, y_field)
        elif chart_type == 'scatter':
            return self._create_scatter_chart_data(df, x_field, y_field)
        elif chart_type == 'area':
            return self._create_area_chart_data(df, x_field, y_field)
        elif chart_type == 'histogram':
            return self._create_histogram_data(df, y_field)
        return None
    
    def _create_bar_chart_data(self, df: pd.DataFrame, x_field: str, y_field: str) -> Dict[str, Any]:
        """创建柱状图数据"""
        if not pd.api.types.is_numeric_dtype(df[y_field]):
            return None
        
        grouped = df.groupby(x_field)[y_field].sum().sort_values(ascending=False).head(10)
        return {
            'type': 'bar',
            'title': f'{x_field} - {y_field} 分布',
            'x_label': x_field,
            'y_label': y_field,
            'data': [{'name': str(k), 'value': float(v)} for k, v in grouped.items()]
        }
    
    def _create_line_chart_data(self, df: pd.DataFrame, x_field: str, y_field: str) -> Dict[str, Any]:
        """创建折线图数据"""
        temp_df = df.copy()
        try:
            temp_df[x_field] = pd.to_datetime(temp_df[x_field])
            temp_df['period'] = temp_df[x_field].dt.strftime('%Y-%m-%d')
        except:
            temp_df['period'] = temp_df[x_field].astype(str)
        
        grouped = temp_df.groupby('period')[y_field].sum().sort_index().head(30)
        return {
            'type': 'line',
            'title': f'{y_field} 趋势变化',
            'x_label': x_field,
            'y_label': y_field,
            'data': [{'name': str(k), 'value': float(v)} for k, v in grouped.items()]
        }
    
    def _create_pie_chart_data(self, df: pd.DataFrame, x_field: str, y_field: str) -> Dict[str, Any]:
        """创建饼图数据"""
        if pd.api.types.is_numeric_dtype(df[y_field]):
            grouped = df.groupby(x_field)[y_field].sum().sort_values(ascending=False).head(8)
        else:
            grouped = df[x_field].value_counts().head(8)
        
        return {
            'type': 'pie',
            'title': f'{x_field} 占比分布',
            'data': [{'name': str(k), 'value': float(v)} for k, v in grouped.items()]
        }
    
    def _create_scatter_chart_data(self, df: pd.DataFrame, x_field: str, y_field: str) -> Dict[str, Any]:
        """创建散点图数据"""
        if not (pd.api.types.is_numeric_dtype(df[x_field]) and pd.api.types.is_numeric_dtype(df[y_field])):
            return None
        
        sample_df = df[[x_field, y_field]].dropna().head(100)
        return {
            'type': 'scatter',
            'title': f'{x_field} vs {y_field}',
            'x_label': x_field,
            'y_label': y_field,
            'data': [{'name': f'点{i}', 'value': [float(row[x_field]), float(row[y_field])]} 
                     for i, (_, row) in enumerate(sample_df.iterrows())]
        }
    
    def _create_area_chart_data(self, df: pd.DataFrame, x_field: str, y_field: str) -> Dict[str, Any]:
        """创建面积图数据"""
        chart_data = self._create_line_chart_data(df, x_field, y_field)
        if chart_data:
            chart_data['type'] = 'area'
            chart_data['title'] = f'{y_field} 累积趋势'
        return chart_data
    
    def _create_histogram_data(self, df: pd.DataFrame, field: str) -> Dict[str, Any]:
        """创建直方图数据"""
        if not pd.api.types.is_numeric_dtype(df[field]):
            return None
        
        data = df[field].dropna().values
        if len(data) == 0:
            return None
        
        counts, bins = pd.cut(data, bins=10, retbins=True, include_lowest=True)
        bin_counts = counts.value_counts().sort_index()
        
        return {
            'type': 'bar',
            'title': f'{field} 数值分布',
            'x_label': field,
            'y_label': '频数',
            'data': [{'name': str(b), 'value': int(v)} for b, v in bin_counts.items()]
        }
    
    def _fallback_to_rules(self, df: pd.DataFrame, user_query: str, max_charts: int) -> List[Dict[str, Any]]:
        """回退到传统规则匹配"""
        from app.services.chart_generator import SmartChartGenerator
        return SmartChartGenerator.generate_charts(df, user_query)[:max_charts]
