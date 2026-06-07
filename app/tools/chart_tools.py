from app.tools.base_tool import BaseTool
from app.services.data_service import DataService
from sqlalchemy.orm import Session
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
import json


class ChartGeneratorTool(BaseTool):
    """
    智能图表生成工具

    核心能力：
    1. 根据分析结果自动选择合适的图表类型
    2. 支持柱状图、折线图、饼图、散点图、直方图
    3. 生成图表的文字解释（洞察摘要）
    4. 支持一键批量生成多图表
    """

    name = "chart_generator"
    description = "根据数据智能生成可视化图表，自动选择图表类型并生成解释"
    parameters = {
        "data_source_id": {"type": "integer", "description": "数据源ID", "required": True},
        "chart_type": {"type": "string", "description": "图表类型：bar, line, pie, scatter, histogram", "required": True},
        "x_column": {"type": "string", "description": "X轴字段", "required": True},
        "y_column": {"type": "string", "description": "Y轴字段", "required": False},
        "group_column": {"type": "string", "description": "分组字段", "required": False},
        "title": {"type": "string", "description": "图表标题", "required": False}
    }

    def __init__(self, db: Session):
        self.data_service = DataService(db)
        self.static_dir = os.environ.get("STATIC_DIR", "app/static")
        os.makedirs(self.static_dir, exist_ok=True)

    def execute(self, **kwargs):
        """
        执行单个图表生成

        Args:
            data_source_id: 数据源ID
            chart_type: 图表类型
            x_column: X轴字段
            y_column: Y轴字段（可选）
            group_column: 分组字段（可选）
            title: 图表标题

        Returns:
            包含图表URL和元信息的字典
        """
        data_source_id = kwargs.get("data_source_id")
        chart_type = kwargs.get("chart_type", "bar")
        x_column = kwargs.get("x_column")
        y_column = kwargs.get("y_column")
        group_column = kwargs.get("group_column")
        title = kwargs.get("title", f"{chart_type} Chart")

        if not data_source_id or not x_column:
            return {"error": "缺少必填参数: data_source_id 和 x_column"}

        try:
            df = self.data_service.load_dataframe(data_source_id)

            if x_column not in df.columns:
                return {"error": f"X轴字段 '{x_column}' 不在数据源中"}

            if y_column and y_column not in df.columns:
                return {"error": f"Y轴字段 '{y_column}' 不在数据源中"}

            if group_column and group_column not in df.columns:
                return {"error": f"分组字段 '{group_column}' 不在数据源中"}

            fig = self._create_chart(df, chart_type, x_column, y_column, group_column, title)

            if fig is None:
                return {"error": f"无法生成图表类型: {chart_type}"}

            filename = f"chart_{data_source_id}_{chart_type}_{hash(title)}.html"
            filepath = os.path.join(self.static_dir, filename)
            pio.write_html(fig, filepath)

            explanation = self._generate_chart_explanation(df, chart_type, x_column, y_column)

            return {
                "chart_type": chart_type,
                "title": title,
                "file_path": filepath,
                "url": f"/static/{filename}",
                "data_points": len(df),
                "x_column": x_column,
                "y_column": y_column,
                "explanation": explanation
            }
        except Exception as e:
            return {"error": f"图表生成失败: {str(e)}"}

    def smart_generate_charts(self, analysis_plan: dict, analysis_results: dict, data_source_id: int) -> dict:
        """
        【智能图表生成】根据分析计划和结果自动批量生成图表

        Args:
            analysis_plan: 数据理解Agent生成的分析计划
            analysis_results: 已有的分析结果（统计数据、异常等）
            data_source_id: 数据源ID

        Returns:
            {
                "charts": [...],  # 生成的图表列表
                "strategy": "...",  # 使用的图表策略
                "recommendations": [...]  # 图表建议
            }
        """
        charts = []
        recommendations = []

        try:
            # 获取意图类别和复杂度
            intent_category = analysis_plan.get("intent_category", "")
            complexity = analysis_plan.get("complexity_level", "simple")
            required_fields = analysis_plan.get("required_fields", [])

            # 根据分析意图自动选择图表策略
            strategy = self._select_chart_strategy(intent_category, analysis_results)
            recommendations.append(f"根据分析意图【{intent_category}】采用图表策略: {strategy}")

            df = self.data_service.load_dataframe(data_source_id)

            # 根据策略生成图表
            if "bar" in strategy:
                for field in required_fields[:2]:
                    if field in df.columns:
                        chart = self.execute(
                            data_source_id=data_source_id,
                            chart_type="bar",
                            x_column=field,
                            y_column=field if self._is_numeric(df, field) else None,
                            title=f"{field} - 数据分布柱状图"
                        )
                        if "url" in chart:
                            charts.append(chart)
                            recommendations.append(f"生成柱状图: {field} 字段数据分布")

            if "line" in strategy:
                for field in required_fields[:2]:
                    if field in df.columns and self._is_numeric(df, field):
                        chart = self.execute(
                            data_source_id=data_source_id,
                            chart_type="line",
                            x_column=df.columns[0],
                            y_column=field,
                            title=f"{field} - 趋势变化折线图"
                        )
                        if "url" in chart:
                            charts.append(chart)
                            recommendations.append(f"生成折线图: {field} 字段趋势变化")

            if "pie" in strategy:
                for field in required_fields[:1]:
                    if field in df.columns:
                        chart = self.execute(
                            data_source_id=data_source_id,
                            chart_type="pie",
                            x_column=field,
                            y_column=field if self._is_numeric(df, field) else None,
                            title=f"{field} - 占比分析饼图"
                        )
                        if "url" in chart:
                            charts.append(chart)
                            recommendations.append(f"生成饼图: {field} 字段占比分布")

            if "histogram" in strategy:
                for field in required_fields[:1]:
                    if field in df.columns and self._is_numeric(df, field):
                        chart = self.execute(
                            data_source_id=data_source_id,
                            chart_type="histogram",
                            x_column=field,
                            title=f"{field} - 数值分布直方图"
                        )
                        if "url" in chart:
                            charts.append(chart)
                            recommendations.append(f"生成直方图: {field} 字段数值分布")

            # 异常检测结果专用图表
            anomalies = analysis_results.get("anomalies", [])
            if anomalies and complexity != "simple":
                anomaly_fields = list(set(a.get("column", "") for a in anomalies if a.get("column")))
                for field in anomaly_fields[:1]:
                    if field in df.columns and self._is_numeric(df, field):
                        chart = self.execute(
                            data_source_id=data_source_id,
                            chart_type="scatter",
                            x_column=df.columns[0],
                            y_column=field,
                            title=f"{field} - 异常检测散点图 (共{len(anomalies)}个异常)"
                        )
                        if "url" in chart:
                            charts.append(chart)
                            recommendations.append(f"生成散点图: 展示 {field} 字段异常点位置")

            return {
                "charts": charts,
                "strategy": strategy,
                "chart_count": len(charts),
                "recommendations": recommendations
            }

        except Exception as e:
            return {
                "charts": [],
                "strategy": "none",
                "chart_count": 0,
                "recommendations": [f"智能图表生成失败: {str(e)}"]
            }

    @staticmethod
    def detect_chart_types(analysis_plan: dict, analysis_results: dict) -> list:
        """
        【静态方法】根据分析计划和结果检测应该使用的图表类型

        Returns:
            [{"chart_type": "bar", "purpose": "...", "fields": [...]}]
        """
        chart_types = []
        intent_category = analysis_plan.get("intent_category", "")

        # 根据分析意图选择基础图表类型
        type_mapping = {
            "统计分析": [
                {"chart_type": "bar", "purpose": "数据分布展示", "when": "有分类字段时"},
                {"chart_type": "histogram", "purpose": "数值分布分析", "when": "有数值字段时"}
            ],
            "趋势分析": [
                {"chart_type": "line", "purpose": "时间趋势展示", "when": "有时间/顺序字段时"},
                {"chart_type": "bar", "purpose": "趋势对比", "when": "对比不同时间段时"}
            ],
            "异常检测": [
                {"chart_type": "scatter", "purpose": "异常点可视化", "when": "检测到异常时"},
                {"chart_type": "line", "purpose": "异常位置标记", "when": "有时间序列时"}
            ],
            "对比分析": [
                {"chart_type": "bar", "purpose": "分组对比展示", "when": "有多组数据时"},
                {"chart_type": "pie", "purpose": "占比对比分析", "when": "占比分析场景"}
            ],
            "可视化分析": [
                {"chart_type": "bar", "purpose": "基础可视化", "when": "默认"},
                {"chart_type": "pie", "purpose": "占比展示", "when": "有分类字段时"},
                {"chart_type": "scatter", "purpose": "关联分析", "when": "有两个数值字段时"}
            ],
            "综合分析": [
                {"chart_type": "bar", "purpose": "主要指标分布"},
                {"chart_type": "line", "purpose": "趋势变化"},
                {"chart_type": "scatter", "purpose": "异常/关联分析"}
            ]
        }

        chart_types = type_mapping.get(intent_category, [
            {"chart_type": "bar", "purpose": "基础数据可视化", "when": "默认"}
        ])

        return chart_types

    def _create_chart(self, df, chart_type, x_column, y_column, group_column, title):
        """创建图表的内部方法"""
        try:
            if chart_type == "bar":
                if y_column and y_column in df.columns and self._is_numeric(df, y_column):
                    if group_column:
                        fig = px.bar(df, x=x_column, y=y_column, color=group_column, title=title)
                    else:
                        fig = px.bar(df, x=x_column, y=y_column, title=title)
                else:
                    # 没有Y轴时，按X轴分组计数
                    count_data = df[x_column].value_counts().reset_index()
                    count_data.columns = [x_column, "count"]
                    fig = px.bar(count_data.head(20), x=x_column, y="count", title=title)
            elif chart_type == "line":
                if y_column and self._is_numeric(df, y_column):
                    if group_column:
                        fig = px.line(df, x=x_column, y=y_column, color=group_column, title=title)
                    else:
                        fig = px.line(df, x=x_column, y=y_column, title=title)
                else:
                    # 没有Y轴数值字段时，统计计数
                    count_data = df[x_column].value_counts().sort_index().reset_index()
                    count_data.columns = [x_column, "count"]
                    fig = px.line(count_data.head(50), x=x_column, y="count", title=title)
            elif chart_type == "pie":
                if y_column and self._is_numeric(df, y_column):
                    fig = px.pie(df, values=y_column, names=x_column, title=title)
                else:
                    count_data = df[x_column].value_counts().reset_index()
                    count_data.columns = [x_column, "count"]
                    fig = px.pie(count_data.head(10), values="count", names=x_column, title=title)
            elif chart_type == "scatter":
                if y_column:
                    if group_column:
                        fig = px.scatter(df, x=x_column, y=y_column, color=group_column, title=title)
                    else:
                        fig = px.scatter(df, x=x_column, y=y_column, title=title)
                else:
                    fig = px.scatter(df, x=x_column, title=title)
            elif chart_type == "histogram":
                fig = px.histogram(df, x=x_column, title=title)
            else:
                return None

            fig.update_layout(
                xaxis_title=x_column,
                yaxis_title=y_column or "数值",
                showlegend=True
            )
            return fig
        except Exception as e:
            return None

    def _generate_chart_explanation(self, df, chart_type, x_column, y_column):
        """生成图表的文字解释"""
        try:
            if x_column not in df.columns:
                return f"该图表展示 {x_column} 的数据分布情况"

            col_data = df[x_column]
            unique_count = col_data.nunique()

            explanations = {
                "bar": f"柱状图展示了 {x_column} 的{unique_count}个分类的数值分布，便于快速比较各分类的大小",
                "line": f"折线图展示了 {x_column} 随{y_column or '顺序'}的变化趋势，可观察增长/下降/波动模式",
                "pie": f"饼图展示了 {x_column} 中各分类的占比情况，直观呈现各部分在整体中的比例",
                "scatter": f"散点图展示了 {x_column} 与 {y_column or '自身'} 的数据点分布，可用于发现异常值和数据聚类",
                "histogram": f"直方图展示了 {x_column} 的数值频率分布，可识别数据分布形态（正态/偏态等）"
            }

            return explanations.get(chart_type, f"该图表展示 {x_column} 的数据可视化")
        except Exception:
            return f"该图表展示 {x_column} 的数据分布"

    def _select_chart_strategy(self, intent_category, analysis_results):
        """根据分析意图选择图表生成策略"""
        strategies = {
            "统计分析": ["bar", "histogram"],
            "趋势分析": ["line", "bar"],
            "异常检测": ["scatter", "line"],
            "对比分析": ["bar", "pie"],
            "可视化分析": ["bar", "pie", "scatter"],
            "综合分析": ["bar", "line", "scatter"],
            "其他": ["bar"]
        }
        return strategies.get(intent_category, ["bar"])

    @staticmethod
    def _is_numeric(df, column):
        """判断列是否为数值型"""
        if column not in df.columns:
            return False
        return pd.api.types.is_numeric_dtype(df[column])
