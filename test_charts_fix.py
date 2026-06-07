"""完整验证：图表生成和API响应"""
import sys
sys.path.insert(0, r'E:\ShenTong\AI Course\digital-data-analyst_v1')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

db_path = r'E:\ShenTong\AI Course\digital-data-analyst_v1\data\example_db.sqlite'
engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db = Session()

from app.agents.agent_coordinator import AgentCoordinator, sanitize_for_json

print("=" * 60)
print("验证1：完整分析流程")
print("=" * 60)

coordinator = AgentCoordinator(db)

# 执行分析
result = coordinator.execute_analysis(
    user_query="分析销售数据是否存在异常",
    data_source_id=3
)

anomalies = result.get('anomalies', [])
charts = result.get('charts', [])
report = result.get('report_content', '')

print(f"异常数量: {len(anomalies)}")
print(f"图表数量: {len(charts)}")
print(f"报告长度: {len(report)}")

# 检查异常字段
print(f"\n异常字段: {[a.get('column', '?') for a in anomalies]}")

# 详细检查每个图表
print(f"\n图表详情:")
for i, chart in enumerate(charts):
    title = chart.get('title', 'N/A')
    chart_type = chart.get('type', 'N/A')
    x_label = chart.get('x_label', '')
    y_label = chart.get('y_label', '')
    data_count = len(chart.get('data', []))
    has_marks = len(chart.get('mark_points', [])) if 'mark_points' in chart else 0
    
    print(f"  [{i+1}] {chart_type} - {title}")
    print(f"       X: {x_label}, Y: {y_label}")
    print(f"       数据点: {data_count}个, 标记点: {has_marks}个")

# 检查是否有我们需要的特定图表
print(f"\n" + "=" * 60)
print("验证2：关键字段检查")
print("=" * 60)

has_discount_rate_line = False
has_anomaly_type_bar = False
has_discount_rate_scatter = False

for chart in charts:
    title = chart.get('title', '')
    chart_type = chart.get('type', '')
    
    if 'discount_rate' in title and chart_type == 'line':
        has_discount_rate_line = True
    if '异常类型分布' in title and chart_type == 'bar':
        has_anomaly_type_bar = True
    if 'discount_rate' in title and chart_type == 'scatter':
        has_discount_rate_scatter = True

print(f"✅ discount_rate 时间序列图: {'存在' if has_discount_rate_line else '❌ 缺失'}")
print(f"✅ 异常类型分布图: {'存在' if has_anomaly_type_bar else '❌ 缺失'}")
print(f"✅ discount_rate 散点图: {'存在' if has_discount_rate_scatter else '（可选）'}")

# 检查数据完整性
print(f"\n" + "=" * 60)
print("验证3：图表数据完整性")
print("=" * 60)

all_valid = True
for i, chart in enumerate(charts):
    data = chart.get('data', [])
    if not data or len(data) == 0:
        print(f"  ❌ 图表 {i+1}（{chart.get('title')}）: 数据为空")
        all_valid = False
        continue
    
    # 检查数据格式
    first_item = data[0]
    if not isinstance(first_item, dict) or 'name' not in first_item or 'value' not in first_item:
        print(f"  ❌ 图表 {i+1}: 数据格式不正确")
        all_valid = False
    else:
        print(f"  ✅ 图表 {i+1}（{chart.get('title')}）: 数据正确")

# JSON序列化检查
print(f"\n" + "=" * 60)
print("验证4：JSON序列化")
print("=" * 60)

try:
    cleaned = sanitize_for_json(result)
    json_str = json.dumps(cleaned, ensure_ascii=False)
    parsed = json.loads(json_str)
    
    # 检查反序列化后的数据
    parsed_charts = parsed.get('charts', [])
    print(f"✅ JSON序列化成功")
    print(f"   序列化后图表数量: {len(parsed_charts)}")
    
    # 检查每个图表的数据完整性
    for i, chart in enumerate(parsed_charts):
        data = chart.get('data', [])
        if not data:
            print(f"   ❌ 图表 {i+1}: 序列化后数据为空")
            all_valid = False
        else:
            print(f"   ✅ 图表 {i+1}: 序列化成功, {len(data)}个数据点")
except Exception as e:
    print(f"❌ JSON序列化失败: {e}")
    import traceback
    traceback.print_exc()
    all_valid = False

# 最终验证
print(f"\n" + "=" * 60)
print("验证5：关键字段的图表检查")
print("=" * 60)

target_fields = ['unit_price', 'quantity', 'discount_rate']
for field in target_fields:
    has_line = False
    has_scatter = False
    for chart in charts:
        title = chart.get('title', '')
        chart_type = chart.get('type', '')
        if field in title:
            if chart_type == 'line':
                has_line = True
            elif chart_type == 'scatter':
                has_scatter = True
    
    print(f"  {field}:")
    print(f"    时间序列图: {'✅' if has_line else '❌'}")
    print(f"    散点图: {'✅' if has_scatter else '（可选）'}")

if all_valid and has_discount_rate_line and has_anomaly_type_bar:
    print(f"\n🎉 所有验证通过！")
else:
    print(f"\n⚠️ 部分验证未通过，请检查")
