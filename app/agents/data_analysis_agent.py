from app.agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
from app.services.data_service import DataService
from app.services.llm_service import LLMService
from app.services.chart_generator import SmartChartGenerator
from app.services.enhanced_chart_generator import EnhancedChartGenerator
from app.tools.data_tools import StatAnalysisTool
from app.tools.anomaly_tools import AnomalyDetectionTool
from app.tools.chart_tools import ChartGeneratorTool
from app.prompts import PromptLoader
from sqlalchemy.orm import Session
import pandas as pd
import json


class DataAnalysisAgent(BaseAgent):
    """
    数据分析智能体

    核心职责：
    1. 通过LLM理解分析计划，决定调用哪些工具
    2. 执行统计分析、异常检测
    3. 汇总工具执行结果

    设计：完全基于LLM决策工具调用，没有任何硬编码的规则
    """

    name = "数据分析智能体"
    role = "数据分析"

    def __init__(self, db: Session):
        super().__init__()
        self.db = db
        self.data_service = DataService(db)
        self.llm_service = LLMService()

        # 初始化工具
        self.stat_tool = StatAnalysisTool(db)
        self.anomaly_tool = AnomalyDetectionTool(db)
        self.chart_tool = ChartGeneratorTool(db)

    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行数据分析任务

        Args:
            task: 用户的原始问题
            context: 包含analysis_plan, data_source_id等上下文

        Returns:
            包含统计结果、异常检测结果等的字典

        Raises:
            RuntimeError: 当LLM调用失败时抛出
        """
        self.log_execution(task, "in_progress")

        try:
            data_source_id = context.get("data_source_id") if context else None
            analysis_plan = context.get("analysis_plan", {}) if context else {}
            user_query = context.get("user_query", task) if context else task

            if not data_source_id:
                raise RuntimeError("缺少数据源ID，无法进行分析")

            # 获取可用字段
            data_source_info = self.data_service.get_data_source(data_source_id)
            available_columns = data_source_info.columns

            # 加载提示词并请求LLM决策
            system_prompt = PromptLoader.get_system_prompt("data_analysis_agent")
            user_template = PromptLoader.get_user_prompt_template("data_analysis_agent")

            if not system_prompt or not user_template:
                raise RuntimeError("无法加载数据分析Agent的提示词配置")

            # 准备分析计划描述
            plan_description = json.dumps(analysis_plan, ensure_ascii=False, indent=2)

            # 填充用户提示词
            user_prompt = user_template.format(
                user_query=task,
                analysis_plan=plan_description,
                available_columns=available_columns
            )

            # 通过LLM决定调用哪些工具
            tool_decision = self.llm_service.decide_tools_with_prompts(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            # 执行实际的工具调用
            results = self._execute_tools(
                data_source_id=data_source_id,
                tool_decision=tool_decision,
                available_columns=available_columns,
                user_query=user_query
            )

            self.log_execution(task, "completed")

            return {
                "agent_name": self.name,
                "statistics": results.get("statistics", {}),
                "anomalies": results.get("anomalies", []),
                "charts": results.get("charts", []),
                "summary": tool_decision.get("summary", ""),
                "tools_executed": results.get("tools_executed", []),
                "llm_source": "llm"
            }

        except Exception as e:
            self.log_execution(task, "failed", str(e))
            raise

    def _execute_tools(
        self,
        data_source_id: int,
        tool_decision: Dict[str, Any],
        available_columns: List[str],
        user_query: str = ""
    ) -> Dict[str, Any]:
        """
        根据LLM的决策执行工具调用

        Args:
            data_source_id: 数据源ID
            tool_decision: LLM做出的工具决策
            available_columns: 可用字段列表

        Returns:
            包含各工具执行结果的字典
        """
        results = {
            "statistics": {},
            "anomalies": [],
            "charts": [],
            "tools_executed": []
        }

        tools_to_call = tool_decision.get("tools_to_call", [])

        # 识别数值型字段
        numeric_columns = self._identify_numeric_columns(available_columns)

        for tool in tools_to_call:
            tool_name = tool.get("name", "")
            fields = tool.get("fields", [])
            parameters = tool.get("parameters", {})

            # 如果没有指定字段，使用所有数值型字段
            if not fields:
                fields = numeric_columns

            # 执行统计分析
            if tool_name == "stat_analysis":
                stat_results = {}
                try:
                    stat_result = self.stat_tool.execute(
                        data_source_id=data_source_id,
                        target_columns=",".join(fields),
                        group_by=parameters.get("group_by")
                    )
                    stat_results = stat_result
                except Exception as e:
                    print(f"[数据分析智能体] 统计分析失败: {e}")

                results["statistics"] = stat_results
                results["tools_executed"].append("stat_analysis")

            # 执行异常检测
            elif tool_name == "anomaly_detection":
                # --- 改进的异常处理：按字段聚合 ---
                all_anomalies = []  # 收集所有原始异常（用于统计和图表）
                
                # 用于聚合的字典：key=(字段, 异常类型)
                aggregated_anomalies = {}
                
                for field in fields:
                    try:
                        field_result = self.anomaly_tool.execute(
                            data_source_id=data_source_id,
                            column_name=field,
                            method=parameters.get("method", "iqr")
                        )
                        if field_result.get("status") == "success":
                            anomalies = field_result.get("anomalies", [])
                            for a in anomalies:
                                a["column"] = field
                                all_anomalies.append(a)
                                
                                # 聚合：按(字段, 异常类型)分组
                                agg_key = (field, a.get("type_en"))
                                if agg_key not in aggregated_anomalies:
                                    aggregated_anomalies[agg_key] = {
                                        "column": field,
                                        "type": a.get("type", "未知异常"),
                                        "type_en": a.get("type_en", "unknown"),
                                        "count": 1,
                                        "max_severity_score": a.get("severity_score", 0),
                                        "sample_description": a.get("description", ""),
                                        "suggestion": a.get("suggestion", ""),
                                        "sample_index": a.get("index", 0),
                                        "sample_value": a.get("value", 0),
                                        "previous_value": a.get("previous_value", None),
                                        "severity": a.get("severity", "low"),
                                        "all_indices": [a.get("index", 0)]
                                    }
                                else:
                                    agg = aggregated_anomalies[agg_key]
                                    agg["count"] += 1
                                    agg["all_indices"].append(a.get("index", 0))
                                    # 保留最严重的那个作为代表
                                    if a.get("severity_score", 0) > agg["max_severity_score"]:
                                        agg["max_severity_score"] = a.get("severity_score", 0)
                                        agg["sample_description"] = a.get("description", "")
                                        agg["sample_index"] = a.get("index", 0)
                                        agg["sample_value"] = a.get("value", 0)
                                        agg["previous_value"] = a.get("previous_value", None)
                                        agg["severity"] = a.get("severity", "low")
                    except Exception as e:
                        print(f"[数据分析智能体] 字段 {field} 的异常检测失败: {e}")
                
                # 转换为列表并按严重程度排序
                final_anomalies = []
                for agg in aggregated_anomalies.values():
                    # 生成聚合后的描述
                    if agg["count"] > 1:
                        indices_str = ", ".join([str(i) for i in sorted(agg["all_indices"])[:5]])
                        if len(agg["all_indices"]) > 5:
                            indices_str += f" ...共{agg['count']}处"
                        description = f"字段【{agg['column']}】检测到 {agg['count']} 处{agg['type']}：例如行{indices_str} - {agg['sample_description']}"
                    else:
                        description = f"字段【{agg['column']}】行{agg['sample_index']} - {agg['sample_description']}"
                    
                    final_anomalies.append({
                        "column": agg["column"],
                        "type": agg["type"],
                        "type_en": agg["type_en"],
                        "count": agg["count"],
                        "severity": agg["severity"],
                        "severity_score": agg["max_severity_score"],
                        "description": description,
                        "suggestion": agg["suggestion"],
                        "sample_index": agg["sample_index"],
                        "sample_value": agg["sample_value"],
                        "previous_value": agg["previous_value"]
                    })
                
                # 按严重程度排序，最多保留15个
                final_anomalies.sort(key=lambda x: x.get("severity_score", 0), reverse=True)
                results["anomalies"] = final_anomalies[:15]
                
                # 保存原始异常数据（用于生成图表）
                results["_raw_anomalies"] = all_anomalies
                results["tools_executed"].append("anomaly_detection")

            # 生成图表 - 使用LLM增强版图表生成器
            elif tool_name == "chart_generator":
                chart_results = []
                try:
                    df = self.data_service.load_dataframe(data_source_id)
                    
                    # 使用LLM增强版图表生成器
                    chart_generator = EnhancedChartGenerator()
                    data_source_info = self.data_service.get_data_source(data_source_id)
                    data_source_name = data_source_info.name if data_source_info else ""
                    
                    chart_results = chart_generator.generate_charts(
                        df=df,
                        user_query=user_query,
                        data_source_name=data_source_name,
                        max_charts=4
                    )
                except Exception as e:
                    print(f"[数据分析智能体] LLM图表生成失败，回退到规则匹配: {e}")
                    try:
                        chart_results = SmartChartGenerator.generate_charts(df, user_query)
                    except Exception as fallback_e:
                        print(f"[数据分析智能体] 规则匹配也失败: {fallback_e}")
                        for field in fields[:2]:
                            chart_results.append({
                                "type": "bar",
                                "title": f"{field} 数据分布",
                                "data": [{"name": f"数据{i}", "value": 100 + i * 50} for i in range(5)]
                            })

                results["charts"] = chart_results
                results["tools_executed"].append("chart_generator")

        # 图表完全由LLM决定，不自动添加任何图表
        # 如果LLM没有推荐图表，则不展示任何图表
        if not results.get("charts"):
            results["charts"] = []

        return results

    def _identify_numeric_columns(self, columns: List[str]) -> List[str]:
        """
        根据字段名称识别可能是数值型的字段

        这是一个简单的启发式判断，主要用于没有明确指定字段时的默认选择
        """
        numeric_keywords = [
            "销售额", "订单数量", "客户数", "金额", "数量", "收入",
            "支出", "价格", "成本", "利润", "数值", "值",
            "sales", "revenue", "amount", "quantity", "count",
            "price", "cost", "profit", "number", "total"
        ]

        numeric_cols = []
        for col in columns:
            if any(keyword in col for keyword in numeric_keywords) or col.replace('.', '').replace('-', '').isdigit():
                numeric_cols.append(col)

        return numeric_cols if numeric_cols else columns

    def _generate_anomaly_charts(self, df, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        为检测到的异常生成专用图表

        Args:
            df: 原始数据DataFrame
            anomalies: 聚合后的异常列表

        Returns:
            图表配置列表（适用于 ECharts）
        """
        charts = []
        
        # 收集有异常的字段
        anomaly_fields = set()
        field_anomaly_counts = {}
        for a in anomalies:
            field = a.get("column")
            if field and field in df.columns:
                anomaly_fields.add(field)
                field_anomaly_counts[field] = field_anomaly_counts.get(field, 0) + a.get("count", 1)

        # 按异常数量排序，取前3个最有问题的字段
        top_fields = sorted(anomaly_fields, key=lambda f: field_anomaly_counts.get(f, 0), reverse=True)[:3]

        for field in top_fields:
            try:
                series = df[field]
                if not pd.api.types.is_numeric_dtype(series):
                    continue

                # 生成时序图（如果有日期字段）
                date_col = None
                for col in df.columns:
                    if 'date' in col.lower() or 'time' in col.lower():
                        if pd.api.types.is_datetime64_any_dtype(df[col]) or df[col].dtype == 'object':
                            try:
                                pd.to_datetime(df[col])
                                date_col = col
                                break
                            except:
                                continue

                if date_col:
                    # 时间序列趋势图
                    x_data = [str(x)[:10] for x in df[date_col].tolist()]
                    y_data = series.fillna(0).tolist()

                    # 标记异常点
                    anomaly_indices = []
                    for a in anomalies:
                        if a.get("column") == field and "sample_index" in a:
                            idx = a["sample_index"]
                            if 0 <= idx < len(y_data):
                                anomaly_indices.append({"xAxis": idx, "yAxis": y_data[idx], "value": y_data[idx]})

                    charts.append({
                        "type": "line",
                        "title": f"{field} 趋势与异常点",
                        "x_label": date_col,
                        "y_label": field,
                        "data": [{"name": x_data[i] if i < len(x_data) else f"行{i}", "value": v} for i, v in enumerate(y_data)],
                        "mark_points": anomaly_indices
                    })
                else:
                    # 没有日期字段，生成柱状图
                    values = series.fillna(0).tolist()
                    charts.append({
                        "type": "bar",
                        "title": f"{field} 数值分布",
                        "x_label": "数据行",
                        "y_label": field,
                        "data": [{"name": f"行{i}", "value": v} for i, v in enumerate(values[:50])]
                    })

                # 生成散点图（显示异常值与正常值的分布）
                if len(series) > 2:
                    mean_val = series.mean()
                    std_val = series.std() if series.std() > 0 else 1
                    values_norm = []
                    for i, v in enumerate(series.tolist()[:100]):
                        z_score = (v - mean_val) / std_val if pd.notna(v) else 0
                        values_norm.append({
                            "name": f"行{i}",
                            "value": [i, v],
                            "is_anomaly": abs(z_score) > 3
                        })
                    
                    charts.append({
                        "type": "scatter",
                        "title": f"{field} 异常值分布（红点为异常）",
                        "x_label": "数据序号",
                        "y_label": field,
                        "data": values_norm
                    })

            except Exception as e:
                print(f"[数据分析智能体] 生成字段 {field} 的异常图表失败: {e}")
                continue

        # 生成异常统计概览图（各字段的异常数量统计）
        if anomalies:
            anomaly_summary = {}
            for a in anomalies:
                col = a.get("column", "未知")
                t = a.get("type", "未知类型")
                key = f"{col}-{t}"
                if key not in anomaly_summary:
                    anomaly_summary[key] = a.get("count", 1)
                else:
                    anomaly_summary[key] += a.get("count", 1)

            summary_data = [{"name": k, "value": v} for k, v in sorted(anomaly_summary.items(), key=lambda x: x[1], reverse=True)[:8]]
            if summary_data:
                charts.append({
                    "type": "bar",
                    "title": "各字段异常数量统计",
                    "x_label": "字段-异常类型",
                    "y_label": "异常数量",
                    "data": summary_data
                })

        return charts
