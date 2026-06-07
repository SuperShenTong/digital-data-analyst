"""
调试脚本：验证异常检测和图表生成的实际数据流程
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tools.anomaly_tools import AnomalyDetectionTool
from app.services.data_service import DataService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

# 创建模拟数据库会话
engine = create_engine('sqlite:///:memory:')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# 1. 先创建模拟数据
sample_data = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=30, freq='D'),
    'product': ['A', 'B', 'C', 'D'] * 7 + ['A', 'B'],
    'region': ['华东', '华南', '华北'] * 10,
    'quantity': [1, 32, 1, 32, 1, 32, 1, 32, 1, 32] * 3,  # 明显的异常模式
    'unit_price': [10.0, 4500.0, 12.0, 4800.0, 11.0, 5200.0] * 5,
    'discount_rate': [0.05, 0.3, 0.05, 0.3, 0.05, 0.3] * 5,
    'amount': [10, 144000, 12, 153600, 11, 156000] * 5
})

print("=" * 60)
print("步骤1：模拟数据结构")
print("=" * 60)
print(f"数据行数: {len(sample_data)}")
print(f"字段: {list(sample_data.columns)}")
print("\n前5行数据:")
print(sample_data.head())

# 2. 测试异常检测工具
print("\n" + "=" * 60)
print("步骤2：测试异常检测工具 - quantity 字段")
print("=" * 60)

anomaly_tool = AnomalyDetectionTool(db)

# 模拟 data_service.load_dataframe 返回的结果
# 实际实现中，我们直接用 sample_data 测试
class MockDataService:
    def __init__(self, df):
        self.df = df
    def load_dataframe(self, data_source_id):
        return self.df

# 替换内部 data_service
anomaly_tool.data_service = MockDataService(sample_data)

# 测试 quantity 字段的综合异常检测
result_qty = anomaly_tool.execute(
    data_source_id=1,
    column_name="quantity",
    method="comprehensive"
)

print(f"检测状态: {result_qty.get('status')}")
print(f"异常总数: {result_qty.get('total_count')}")
print(f"返回的前10条异常:")

anomalies = result_qty.get("anomalies", [])
for i, a in enumerate(anomalies[:10]):
    print(f"  [{i+1}] {a.get('type')} - {a.get('type_en')} - "
          f"行{a.get('index')}: {a.get('description')[:50]}...")

# 按类型统计
type_counts = {}
for a in anomalies:
    t = f"{a.get('column')} - {a.get('type_en')}"
    type_counts[t] = type_counts.get(t, 0) + 1

print(f"\n按(字段, 类型)组合统计:")
for key, count in type_counts.items():
    print(f"  {key}: {count} 条")

# 3. 测试多个字段的异常检测
print("\n" + "=" * 60)
print("步骤3：测试多个字段的异常检测")
print("=" * 60)

all_field_anomalies = []
for field in ["quantity", "unit_price", "discount_rate", "amount"]:
    if field not in sample_data.columns:
        continue
    if not pd.api.types.is_numeric_dtype(sample_data[field]):
        continue
        
    result = anomaly_tool.execute(
        data_source_id=1,
        column_name=field,
        method="comprehensive"
    )
    
    field_anomalies = result.get("anomalies", [])
    print(f"\n{field}: 检测到 {result.get('total_count')} 个异常")
    for a in field_anomalies[:3]:
        print(f"  {a.get('type')}: {a.get('description')[:60]}")
    
    all_field_anomalies.extend(field_anomalies)

# 4. 测试当前的去重逻辑
print("\n" + "=" * 60)
print("步骤4：测试当前去重逻辑效果")
print("=" * 60)

# 当前逻辑：(column, type_en) 去重
seen_current = set()
deduped_current = []
for a in all_field_anomalies:
    key = (a.get("column"), a.get("type_en"))
    if key not in seen_current:
        seen_current.add(key)
        deduped_current.append(a)

print(f"原始异常总数: {len(all_field_anomalies)}")
print(f"按(字段, 类型)去重后: {len(deduped_current)}")

print("\n去重后的异常列表:")
for i, a in enumerate(deduped_current[:20]):
    print(f"  [{i+1}] {a.get('column')} - {a.get('type')} (严重度: {a.get('severity_score'):.2f})")
    print(f"       {a.get('description')[:70]}")

# 5. 检查图表生成逻辑
print("\n" + "=" * 60)
print("步骤5：测试图表生成逻辑")
print("=" * 60)

from app.services.chart_generator import SmartChartGenerator

charts = SmartChartGenerator.generate_charts(sample_data, "分析销售数据的异常")

print(f"生成的图表数量: {len(charts)}")
for i, chart in enumerate(charts):
    print(f"\n图表 {i+1}:")
    print(f"  类型: {chart.get('type')}")
    print(f"  标题: {chart.get('title')}")
    print(f"  数据点数: {len(chart.get('data', []))}")
    print(f"  前3个数据点: {chart.get('data', [])[:3]}")

print("\n" + "=" * 60)
print("调试完成！")
print("=" * 60)
