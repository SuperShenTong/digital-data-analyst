from app.tools.base_tool import BaseTool
from typing import Dict, Any
import json
from datetime import datetime

class ReportGeneratorTool(BaseTool):
    name = "report_generator"
    description = "将分析结果生成为结构化的数据分析报告"
    parameters = {
        "analysis_result": {"type": "string", "description": "分析结果（JSON格式）", "required": True},
        "report_type": {"type": "string", "description": "报告类型：summary, detailed, executive", "required": False},
        "include_charts": {"type": "boolean", "description": "是否包含图表", "required": False}
    }
    
    def execute(self, **kwargs):
        analysis_result_str = kwargs.get("analysis_result")
        report_type = kwargs.get("report_type", "summary")
        include_charts = kwargs.get("include_charts", False)
        
        try:
            analysis_result = json.loads(analysis_result_str)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format for analysis_result"}
        
        report = self.generate_report(analysis_result, report_type, include_charts)
        
        return {"report_content": report, "report_type": report_type}
    
    def generate_report(self, analysis_result: Dict[str, Any], report_type: str, include_charts: bool):
        sections = []
        
        sections.append(f"# 数据分析报告\n\n**生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n")
        
        if "user_query" in analysis_result:
            sections.append(f"## 分析需求\n\n{analysis_result['user_query']}\n\n")
        
        if "summary" in analysis_result:
            sections.append(f"## 核心结论\n\n{analysis_result['summary']}\n\n")
        
        if "statistics" in analysis_result:
            sections.append(self._generate_statistics_section(analysis_result["statistics"]))
        
        if "anomalies" in analysis_result and analysis_result["anomalies"]:
            sections.append(self._generate_anomalies_section(analysis_result["anomalies"]))
        
        if "recommendations" in analysis_result:
            sections.append(self._generate_recommendations_section(analysis_result["recommendations"]))
        
        if include_charts and "charts" in analysis_result:
            sections.append(self._generate_charts_section(analysis_result["charts"]))
        
        sections.append(f"\n---\n\n*报告结束*")
        
        return "".join(sections)
    
    def _generate_statistics_section(self, statistics: Dict[str, Any]):
        sections = ["## 统计分析结果\n\n"]
        
        for field, stats in statistics.items():
            sections.append(f"### {field}\n\n")
            sections.append(f"- 均值: {stats.get('mean', 'N/A'):.2f}\n")
            sections.append(f"- 中位数: {stats.get('median', 'N/A'):.2f}\n")
            sections.append(f"- 标准差: {stats.get('std', 'N/A'):.2f}\n")
            sections.append(f"- 最小值: {stats.get('min', 'N/A'):.2f}\n")
            sections.append(f"- 最大值: {stats.get('max', 'N/A'):.2f}\n")
            sections.append(f"- 总和: {stats.get('sum', 'N/A'):.2f}\n")
            sections.append("\n")
        
        return "".join(sections)
    
    def _generate_anomalies_section(self, anomalies: list):
        sections = ["## 异常检测结果\n\n"]
        
        if not anomalies:
            sections.append("未检测到数据异常。\n\n")
            return "".join(sections)
        
        for i, anomaly in enumerate(anomalies, 1):
            sections.append(f"### 异常 #{i}\n\n")
            sections.append(f"- **类型**: {anomaly.get('type', '未知')}\n")
            sections.append(f"- **严重程度**: {anomaly.get('severity', '未知')}\n")
            sections.append(f"- **描述**: {anomaly.get('description', '无')}\n")
            sections.append(f"- **建议**: {anomaly.get('recommendation', '无')}\n")
            if "expected_range" in anomaly:
                sections.append(f"- **预期范围**: [{anomaly['expected_range'][0]:.2f}, {anomaly['expected_range'][1]:.2f}]\n")
            sections.append("\n")
        
        return "".join(sections)
    
    def _generate_recommendations_section(self, recommendations: list):
        sections = ["## 业务优化建议\n\n"]
        
        for i, rec in enumerate(recommendations, 1):
            sections.append(f"{i}. {rec}\n")
        
        sections.append("\n")
        return "".join(sections)
    
    def _generate_charts_section(self, charts: list):
        sections = ["## 可视化图表\n\n"]
        
        for chart in charts:
            title = chart.get("title", "图表")
            url = chart.get("url", "")
            if url:
                sections.append(f"### {title}\n\n")
                sections.append(f"![{title}]({url})\n\n")
        
        return "".join(sections)