from app.agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
from app.services.data_service import DataService
from app.services.llm_service import LLMService
from app.tools.data_tools import StatAnalysisTool
from app.tools.anomaly_tools import AnomalyDetectionTool
from app.tools.chart_tools import ChartGeneratorTool
from app.prompts import PromptLoader
from sqlalchemy.orm import Session
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
                available_columns=available_columns
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
        available_columns: List[str]
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
                anomaly_results = []
                for field in fields:
                    try:
                        field_result = self.anomaly_tool.execute(
                            data_source_id=data_source_id,
                            column_name=field,
                            method=parameters.get("method", "iqr")
                        )
                        if field_result.get("status") == "success":
                            field_anomalies = field_result.get("anomalies", [])
                            for a in field_anomalies:
                                a["column"] = field
                            anomaly_results.extend(field_anomalies)
                    except Exception as e:
                        print(f"[数据分析智能体] 字段 {field} 的异常检测失败: {e}")

                results["anomalies"] = anomaly_results
                results["tools_executed"].append("anomaly_detection")

            # 生成图表
            elif tool_name == "chart_generator":
                chart_results = []
                for field in fields[:2]:  # 最多生成2个图表避免过多
                    try:
                        # 生成柱状图
                        bar_chart = self.chart_tool.execute(
                            data_source_id=data_source_id,
                            chart_type=parameters.get("chart_type", "bar"),
                            x_column=field,
                            y_column=field,
                            title=f"{field}数据分布"
                        )
                        if "url" in bar_chart:
                            chart_results.append(bar_chart)

                        # 生成折线图
                        line_chart = self.chart_tool.execute(
                            data_source_id=data_source_id,
                            chart_type="line",
                            x_column=field,
                            y_column=field,
                            title=f"{field}趋势变化"
                        )
                        if "url" in line_chart:
                            chart_results.append(line_chart)
                    except Exception as e:
                        print(f"[数据分析智能体] 字段 {field} 的图表生成失败: {e}")

                results["charts"] = chart_results
                results["tools_executed"].append("chart_generator")

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
