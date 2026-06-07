"""
基于LLM的智能图表选择器
通过自然语言分析用户问题和数据结构，智能推荐图表类型
"""

import json
from typing import Dict, List, Any
from app.services.llm_service import LLMService

class LLMChartSelector:
    """
    LLM驱动的图表选择器
    
    核心能力：
    1. 分析用户问题意图
    2. 理解数据结构特征
    3. 智能推荐合适的图表类型
    4. 生成完整的图表配置
    """
    
    def __init__(self):
        self.llm_service = LLMService()
    
    def analyze_and_select_charts(
        self,
        user_query: str,
        data_summary: Dict[str, Any],
        max_charts: int = 4
    ) -> List[Dict[str, Any]]:
        """
        通过LLM分析用户问题和数据结构，返回推荐的图表配置
        
        Args:
            user_query: 用户的分析问题
            data_summary: 数据摘要，包含字段列表、字段类型、样本数据等
            max_charts: 最大生成图表数量
            
        Returns:
            图表配置列表
        """
        prompt = self._build_prompt(user_query, data_summary, max_charts)
        response = self.llm_service.generate_report_with_prompts(
            system_prompt=self._get_system_prompt(),
            user_prompt=prompt
        )
        
        return self._parse_response(response)
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词 - 支持中英文双语"""
        return """
You are a professional data visualization expert specializing in recommending the most appropriate chart types based on user analysis needs and data characteristics.

## Core Capabilities
1. Parse user queries in both Chinese and English
2. Analyze data structure (numeric fields, categorical fields, time fields, etc.)
3. Recommend the most suitable chart types based on analysis
4. Output chart configurations in JSON format

## Available Chart Types:
- bar: Bar Chart - Suitable for categorical comparison, ranking, distribution display
- line: Line Chart - Suitable for time series, trend changes display
- pie: Pie Chart - Suitable for proportion analysis, composition display
- scatter: Scatter Plot - Suitable for correlation analysis, anomaly detection
- area: Area Chart - Suitable for cumulative trends, total changes
- histogram: Histogram - Suitable for numerical distribution, frequency statistics

## Output Format:
{
    "charts": [
        {
            "type": "chart_type",
            "title": "Chart Title",
            "x_field": "X-axis field name",
            "y_field": "Y-axis field name",
            "purpose": "Reason for selecting this chart type",
            "analysis_goal": "Analysis goal this chart aims to demonstrate"
        }
    ]
}

## Important Notes:
- Output ONLY JSON format, do not include other explanatory text
- Select appropriate fields based on data characteristics
- Each chart must have a clear analysis goal
- Avoid recommending duplicate or redundant charts
- Respond in the same language as the user query (Chinese or English)
        """.strip()
    
    def _build_prompt(self, user_query: str, data_summary: Dict[str, Any], max_charts: int) -> str:
        """构建用户提示词 - 支持中英文双语"""
        fields_info = "\n".join([
            f"- {field['name']}: {field['type']} (Sample: {field['sample']})"
            for field in data_summary.get('fields', [])
        ])
        
        # 检测用户查询语言
        is_chinese = any('\u4e00' <= char <= '\u9fff' for char in user_query)
        
        if is_chinese:
            return f"""
用户问题：{user_query}

数据摘要：
- 数据集名称: {data_summary.get('name', '未知')}
- 数据行数: {data_summary.get('row_count', 0)}
- 字段列表 ({len(data_summary.get('fields', []))} 个字段):
{fields_info}

请分析以上信息，推荐最多{max_charts}个最合适的图表，并输出JSON格式的图表配置。
            """.strip()
        else:
            return f"""
User Query: {user_query}

Data Summary:
- Dataset Name: {data_summary.get('name', 'Unknown')}
- Row Count: {data_summary.get('row_count', 0)}
- Field List ({len(data_summary.get('fields', []))} fields):
{fields_info}

Please analyze the above information, recommend up to {max_charts} most suitable charts, and output the chart configuration in JSON format.
            """.strip()
    
    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """解析LLM响应"""
        try:
            # 尝试提取JSON部分
            if '{' in response:
                start = response.index('{')
                end = response.rindex('}') + 1
                json_str = response[start:end]
                result = json.loads(json_str)
                return result.get('charts', [])
        except Exception as e:
            print(f"[LLM图表选择器] 解析响应失败: {e}")
        
        return []
