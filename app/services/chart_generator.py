"""
智能图表选择器：根据数据源字段和问题类型自动选择合适的图表
"""

import pandas as pd
from typing import Dict, List, Any

class SmartChartGenerator:
    """智能图表生成器 - 根据数据字段和问题类型自动选择图表"""
    
    # 字段类型映射
    FIELD_TYPES = {
        'numeric': ['quantity', 'amount', 'sales', 'revenue', 'profit', 'price', 
                    'count', 'total', 'sum', 'value', 'unit_price', 'cost',
                    'number', 'num', 'qty', '数值', '数量', '金额', '价格'],
        'category': ['region', 'area', 'province', 'city', 'channel', 'category',
                    'type', 'status', 'level', 'department', 'department_name',
                    'product', 'product_name', 'product_id', 'category_name',
                    '分类', '地区', '区域', '渠道', '状态', '类型', '产品', '部门'],
        'date': ['date', 'time', 'datetime', 'month', 'year', 'day', 'week',
                 '日期', '时间', '月份', '年份', '日', '周'],
        'anomaly': ['is_anomaly', 'anomaly', 'error', 'issue', '异常', '错误', '问题']
    }
    
    # 问题关键词与图表类型映射
    QUESTION_CHART_MAP = {
        '分布': 'bar',
        '占比': 'pie',
        '比例': 'pie',
        '趋势': 'line',
        '变化': 'line',
        '对比': 'bar',
        '比较': 'bar',
        '异常': 'scatter',
        '统计': 'bar',
        '汇总': 'bar',
        '总量': 'bar',
        'top': 'bar',
        '排名': 'bar',
        '环比': 'mom',
        '同比': 'yoy'
    }
    
    @classmethod
    def detect_field_types(cls, df: pd.DataFrame) -> Dict[str, str]:
        """检测每个字段的类型"""
        field_types = {}
        
        for column in df.columns:
            col_lower = str(column).lower()
            
            # 检测日期类型
            if pd.api.types.is_datetime64_any_dtype(df[column]):
                field_types[column] = 'date'
                continue
            
            # 检测数值类型
            if pd.api.types.is_numeric_dtype(df[column]):
                field_types[column] = 'numeric'
                continue
            
            # 基于关键词检测
            detected = False
            for field_type, keywords in cls.FIELD_TYPES.items():
                if any(keyword in col_lower for keyword in keywords):
                    field_types[column] = field_type
                    detected = True
                    break
            
            if not detected:
                # 默认为分类类型（如果唯一值较少）
                if df[column].nunique() < 20:
                    field_types[column] = 'category'
                else:
                    field_types[column] = 'text'
        
        return field_types
    
    @classmethod
    def generate_charts(cls, df: pd.DataFrame, question: str = '') -> List[Dict[str, Any]]:
        """根据数据和问题生成图表配置"""
        charts = []
        field_types = cls.detect_field_types(df)
        
        # 获取各类型字段
        numeric_fields = [f for f, t in field_types.items() if t == 'numeric']
        category_fields = [f for f, t in field_types.items() if t == 'category']
        date_fields = [f for f, t in field_types.items() if t == 'date']
        
        # 根据问题类型选择图表
        question_lower = question.lower() if question else ''
        chart_types = cls._select_chart_types(question_lower, numeric_fields, category_fields, date_fields)
        
        for chart_type in chart_types[:4]:  # 最多生成4个图表
            chart = cls._create_chart_config(df, chart_type, numeric_fields, category_fields, date_fields)
            if chart:
                charts.append(chart)
        
        return charts
    
    @classmethod
    def _select_chart_types(cls, question: str, numeric_fields: List[str], 
                           category_fields: List[str], date_fields: List[str]) -> List[str]:
        """根据问题和字段选择图表类型"""
        chart_types = []
        
        # 根据问题关键词匹配
        for keyword, chart_type in cls.QUESTION_CHART_MAP.items():
            if keyword in question:
                if chart_type not in chart_types:
                    chart_types.append(chart_type)
        
        # 根据字段类型补充图表
        if date_fields and numeric_fields and 'line' not in chart_types:
            chart_types.append('line')  # 有日期和数值字段 -> 折线图
        
        if category_fields and numeric_fields and 'bar' not in chart_types:
            chart_types.append('bar')  # 有分类和数值字段 -> 柱状图
        
        if category_fields and 'pie' not in chart_types:
            chart_types.append('pie')  # 有分类字段 -> 饼图
        
        if len(numeric_fields) > 1 and 'scatter' not in chart_types:
            chart_types.append('scatter')  # 多个数值字段 -> 散点图
        
        # 如果没有匹配任何图表，使用默认图表
        if not chart_types:
            if category_fields:
                chart_types.append('bar')
            if date_fields:
                chart_types.append('line')
            chart_types.append('pie')
        
        return chart_types
    
    @classmethod
    def _create_chart_config(cls, df: pd.DataFrame, chart_type: str, 
                            numeric_fields: List[str], category_fields: List[str],
                            date_fields: List[str]) -> Dict[str, Any]:
        """创建单个图表的配置"""
        try:
            if chart_type == 'bar':
                return cls._create_bar_chart(df, numeric_fields, category_fields)
            elif chart_type == 'line':
                return cls._create_line_chart(df, numeric_fields, date_fields)
            elif chart_type == 'pie':
                return cls._create_pie_chart(df, numeric_fields, category_fields)
            elif chart_type == 'scatter':
                return cls._create_scatter_chart(df, numeric_fields)
            elif chart_type == 'mom':
                return cls._create_mom_chart(df, numeric_fields, date_fields)
            elif chart_type == 'yoy':
                return cls._create_yoy_chart(df, numeric_fields, date_fields)
        except Exception as e:
            print(f"创建图表 {chart_type} 时出错: {e}")
            return None
    
    @classmethod
    def _create_bar_chart(cls, df: pd.DataFrame, numeric_fields: List[str], 
                         category_fields: List[str]) -> Dict[str, Any]:
        """创建柱状图配置"""
        if not category_fields or not numeric_fields:
            return None
        
        cat_field = category_fields[0]
        num_field = numeric_fields[0]
        
        # 按分类聚合
        grouped = df.groupby(cat_field)[num_field].sum().sort_values(ascending=False).head(10)
        
        categories = grouped.index.tolist()
        values = grouped.values.tolist()
        
        return {
            'type': 'bar',
            'title': f'{cat_field} - {num_field} 分布',
            'x_label': cat_field,
            'y_label': num_field,
            'data': [
                {'name': str(cat), 'value': float(val)}
                for cat, val in zip(categories, values)
            ]
        }
    
    @classmethod
    def _create_line_chart(cls, df: pd.DataFrame, numeric_fields: List[str],
                          date_fields: List[str]) -> Dict[str, Any]:
        """创建折线图配置"""
        if not date_fields or not numeric_fields:
            return None
        
        date_field = date_fields[0]
        num_field = numeric_fields[0]
        
        # 按日期聚合
        temp_df = df.copy()
        temp_df[date_field] = pd.to_datetime(temp_df[date_field])
        temp_df['month'] = temp_df[date_field].dt.strftime('%Y-%m')
        
        grouped = temp_df.groupby('month')[num_field].sum().sort_index()
        
        dates = grouped.index.tolist()
        values = grouped.values.tolist()
        
        return {
            'type': 'line',
            'title': f'{num_field} 趋势变化',
            'x_label': '日期',
            'y_label': num_field,
            'data': [
                {'name': str(date), 'value': float(val)}
                for date, val in zip(dates, values)
            ]
        }
    
    @classmethod
    def _create_pie_chart(cls, df: pd.DataFrame, numeric_fields: List[str],
                         category_fields: List[str]) -> Dict[str, Any]:
        """创建饼图配置"""
        if not category_fields or not numeric_fields:
            return None
        
        cat_field = category_fields[0] if len(category_fields) > 0 else category_fields[0]
        num_field = numeric_fields[0]
        
        # 按分类聚合
        grouped = df.groupby(cat_field)[num_field].sum().sort_values(ascending=False).head(8)
        total = grouped.sum()
        
        if total == 0:
            # 如果没有数值字段，用计数
            grouped = df[cat_field].value_counts().head(8)
            return {
                'type': 'pie',
                'title': f'{cat_field} 占比',
                'data': [
                    {'name': str(cat), 'value': float(count)}
                    for cat, count in grouped.items()
                ]
            }
        
        return {
            'type': 'pie',
            'title': f'{cat_field} 占比分布',
            'data': [
                {'name': str(cat), 'value': float(val)}
                for cat, val in zip(grouped.index, grouped.values)
            ]
        }
    
    @classmethod
    def _create_scatter_chart(cls, df: pd.DataFrame, numeric_fields: List[str]) -> Dict[str, Any]:
        """创建散点图配置（用于异常检测）"""
        if len(numeric_fields) < 2:
            return None
        
        x_field = numeric_fields[0]
        y_field = numeric_fields[1] if len(numeric_fields) > 1 else numeric_fields[0]
        
        # 采样数据（最多100个点）
        sample_df = df[[x_field, y_field]].dropna().head(100)
        
        return {
            'type': 'scatter',
            'title': f'{x_field} vs {y_field} 分布',
            'x_label': x_field,
            'y_label': y_field,
            'data': [
                {'name': f'点{i}', 'value': [float(row[x_field]), float(row[y_field])]}
                for i, (_, row) in enumerate(sample_df.iterrows())
            ]
        }
    
    @classmethod
    def _create_mom_chart(cls, df: pd.DataFrame, numeric_fields: List[str],
                         date_fields: List[str]) -> Dict[str, Any]:
        """创建环比分析图表（柱状图展示环比变化率）"""
        if not date_fields or not numeric_fields:
            return None
        
        date_field = date_fields[0]
        num_field = numeric_fields[0]
        
        # 按日期排序并计算环比
        temp_df = df.copy()
        temp_df[date_field] = pd.to_datetime(temp_df[date_field])
        temp_df = temp_df.sort_values(date_field)
        temp_df['month'] = temp_df[date_field].dt.strftime('%Y-%m')
        
        # 按月聚合
        monthly_data = temp_df.groupby('month')[num_field].sum().reset_index()
        monthly_data['mom_rate'] = monthly_data[num_field].pct_change() * 100
        
        # 移除NaN（第一个月没有环比）
        monthly_data = monthly_data.dropna()
        
        if len(monthly_data) < 2:
            return None
        
        return {
            'type': 'bar',
            'title': f'{num_field} 环比变化率',
            'x_label': '月份',
            'y_label': '环比变化率 (%)',
            'data': [
                {
                    'name': str(row['month']),
                    'value': float(row['mom_rate']),
                    'raw_value': float(row[num_field])
                }
                for _, row in monthly_data.iterrows()
            ]
        }
    
    @classmethod
    def _create_yoy_chart(cls, df: pd.DataFrame, numeric_fields: List[str],
                         date_fields: List[str]) -> Dict[str, Any]:
        """创建同比分析图表（折线图展示同比变化率）"""
        if not date_fields or not numeric_fields:
            return None
        
        date_field = date_fields[0]
        num_field = numeric_fields[0]
        
        temp_df = df.copy()
        temp_df[date_field] = pd.to_datetime(temp_df[date_field])
        temp_df['month'] = temp_df[date_field].dt.strftime('%m')
        temp_df['year'] = temp_df[date_field].dt.year
        
        # 按年月聚合
        yearly_monthly = temp_df.groupby(['year', 'month'])[num_field].sum().reset_index()
        
        # 计算同比
        result = []
        years = sorted(yearly_monthly['year'].unique())
        
        if len(years) < 2:
            # 如果只有一年数据，计算与均值的偏离
            yearly_monthly['mean_val'] = yearly_monthly[num_field].mean()
            yearly_monthly['yoy_rate'] = (yearly_monthly[num_field] - yearly_monthly['mean_val']) / yearly_monthly['mean_val'] * 100
            
            return {
                'type': 'bar',
                'title': f'{num_field} 同比偏离率',
                'x_label': '月份',
                'y_label': '同比偏离率 (%)',
                'data': [
                    {'name': str(row['month']), 'value': float(row['yoy_rate'])}
                    for _, row in yearly_monthly.iterrows()
                ]
            }
        
        # 有多年数据，计算真正的同比
        for month in sorted(yearly_monthly['month'].unique()):
            month_data = yearly_monthly[yearly_monthly['month'] == month]
            if len(month_data) >= 2:
                current_year = month_data.iloc[-1]
                prev_year = month_data.iloc[-2]
                if prev_year[num_field] != 0:
                    yoy_rate = (current_year[num_field] - prev_year[num_field]) / prev_year[num_field] * 100
                    result.append({
                        'name': f"{current_year['year']}-{current_year['month']}",
                        'value': float(yoy_rate)
                    })
        
        if not result:
            return None
        
        return {
            'type': 'line',
            'title': f'{num_field} 同比变化率',
            'x_label': '年月',
            'y_label': '同比变化率 (%)',
            'data': result
        }
    
    @staticmethod
    def generate_chart_title(question: str, data_source_name: str) -> str:
        """生成图表标题"""
        if question:
            return f"分析: {question[:30]}..."
        return f"{data_source_name} 数据分析"
