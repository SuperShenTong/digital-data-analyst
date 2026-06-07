from app.agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
from app.services.llm_service import LLMService
from app.tools.chart_tools import ChartGeneratorTool
from app.prompts import PromptLoader
from sqlalchemy.orm import Session
import json


class ReportGenerationAgent(BaseAgent):
    """
    报告生成智能体

    核心职责：
    1. 通过LLM将分析结果转化为通俗易懂的业务报告
    2. 生成结构化、有洞察的Markdown报告
    3. 包含数据、发现、建议等完整信息

    设计：完全基于LLM，没有任何fallback机制
    """

    name = "报告生成智能体"
    role = "报告生成"

    def __init__(self, db: Session):
        super().__init__()
        self.db = db
        self.llm_service = LLMService()
        self.chart_tool = ChartGeneratorTool(db)

    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行报告生成任务

        Args:
            task: 用户的原始问题
            context: 包含analysis_results, analysis_plan, data_source_id等上下文

        Returns:
            包含报告内容、图表等的字典

        Raises:
            RuntimeError: 当LLM调用失败时抛出
        """
        self.log_execution(task, "in_progress")

        try:
            data_source_id = context.get("data_source_id") if context else None
            analysis_results = context.get("analysis_results", {}) if context else {}
            user_query = context.get("user_query", task)
            analysis_plan = context.get("analysis_plan", {}) if context else {}

            # 生成图表
            charts = self._generate_charts(data_source_id, analysis_results)

            # 加载提示词配置
            system_prompt = PromptLoader.get_system_prompt("report_generation_agent")
            user_template = PromptLoader.get_user_prompt_template("report_generation_agent")

            if not system_prompt or not user_template:
                raise RuntimeError("无法加载报告生成Agent的提示词配置")

            # 准备分析结果
            report_data = {
                "user_query": user_query,
                "statistics": analysis_results.get("statistics", {}),
                "anomalies": analysis_results.get("anomalies", []),
                "charts_count": len(charts)
            }

            # 填充用户提示词
            user_prompt = user_template.format(
                user_query=user_query,
                analysis_plan=json.dumps(analysis_plan, ensure_ascii=False, indent=2),
                analysis_results=json.dumps(report_data, ensure_ascii=False, indent=2)
            )

            # 通过LLM生成报告
            report_content = self.llm_service.generate_report_with_prompts(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            self.log_execution(task, "completed")

            return {
                "agent_name": self.name,
                "report_content": report_content,
                "charts": charts,
                "summary": self._generate_summary(report_data),
                "llm_source": "llm"
            }

        except Exception as e:
            self.log_execution(task, "failed", str(e))
            raise

    def _generate_charts(
        self,
        data_source_id: int,
        analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        生成数据可视化图表

        Args:
            data_source_id: 数据源ID
            analysis_results: 分析结果字典

        Returns:
            图表列表
        """
        charts = []

        if not data_source_id:
            return charts

        statistics = analysis_results.get("statistics", {})
        if not isinstance(statistics, dict) or not statistics:
            return charts

        # 为前2个有统计结果的字段生成图表
        numeric_fields = list(statistics.keys())[:2]

        for field in numeric_fields:
            try:
                # 柱状图
                bar_chart = self.chart_tool.execute(
                    data_source_id=data_source_id,
                    chart_type="bar",
                    x_column=field,
                    y_column=field,
                    title=f"{field}的数据分布"
                )
                if "url" in bar_chart:
                    charts.append(bar_chart)

                # 折线图
                line_chart = self.chart_tool.execute(
                    data_source_id=data_source_id,
                    chart_type="line",
                    x_column=field,
                    y_column=field,
                    title=f"{field}的趋势变化"
                )
                if "url" in line_chart:
                    charts.append(line_chart)

            except Exception as e:
                print(f"[报告生成智能体] 图表生成失败 ({field}): {e}")

        return charts

    def _generate_summary(self, report_data: Dict[str, Any]) -> str:
        """
        生成简短的分析摘要

        Args:
            report_data: 报告数据字典

        Returns:
            摘要字符串
        """
        parts = []

        statistics = report_data.get("statistics", {})
        if statistics and isinstance(statistics, dict):
            fields_count = len(statistics)
            parts.append(f"完成了 {fields_count} 个指标的统计分析")

        anomalies = report_data.get("anomalies", [])
        if anomalies:
            parts.append(f"检测到 {len(anomalies)} 个数据异常点")

        charts_count = report_data.get("charts_count", 0)
        if charts_count > 0:
            parts.append(f"生成了 {charts_count} 个可视化图表")

        if not parts:
            return "分析完成"

        return "；".join(parts)
