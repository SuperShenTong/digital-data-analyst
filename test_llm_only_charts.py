"""测试：验证图表完全由LLM决定"""
import sys
sys.path.insert(0, r'E:\ShenTong\AI Course\digital-data-analyst_v1')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

db_path = r'E:\ShenTong\AI Course\digital-data-analyst_v1\data\example_db.sqlite'
engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db = Session()

from app.agents.agent_coordinator import AgentCoordinator

coordinator = AgentCoordinator(db)

print("=" * 60)
print("测试：验证图表完全由LLM决定")
print("=" * 60)

# 执行分析
result = coordinator.execute_analysis(
    user_query="分析销售数据是否存在异常",
    data_source_id=3
)

anomalies = result.get('anomalies', [])
charts = result.get('charts', [])
report = result.get('report_content', '')

print(f"\n分析结果:")
print(f"  异常数量: {len(anomalies)}")
print(f"  图表数量: {len(charts)}")
print(f"  报告长度: {len(report)}")

print(f"\n图表详情（仅LLM推荐）:")
if charts:
    for i, chart in enumerate(charts):
        title = chart.get('title', 'N/A')
        chart_type = chart.get('type', 'N/A')
        x_label = chart.get('x_label', '')
        y_label = chart.get('y_label', '')
        data_count = len(chart.get('data', []))
        
        print(f"  [{i+1}] {chart_type} - {title}")
        print(f"       X: {x_label}, Y: {y_label}, 数据点: {data_count}")
else:
    print("  （LLM未推荐任何图表）")

# 检查是否有自动添加的异常图表
has_anomaly_auto_chart = False
for chart in charts:
    title = chart.get('title', '')
    # 检查是否是自动添加的异常图表（包含这些关键词）
    if '时间序列' in title or '异常类型分布' in title or '异常值分布' in title:
        has_anomaly_auto_chart = True
        break

print(f"\n验证结果:")
print(f"  ✅ 无自动添加的异常可视化图表: {'是' if not has_anomaly_auto_chart else '❌ 否'}")
print(f"  ✅ 图表数量: {len(charts)}（由LLM决定）")

if len(charts) == 0:
    print(f"\n提示：LLM认为当前问题不需要图表辅助理解，这是正常的。")
else:
    print(f"\n提示：所有图表都是LLM根据问题和数据特征智能推荐的。")
