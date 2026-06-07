"""详细测试协调器流程"""
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

coordinator = AgentCoordinator(db)

print("=== 测试完整分析流程 ===")
print("查询: 分析销售数据是否存在异常")
print("数据源: sales_transactions (ID=3)")

try:
    result = coordinator.execute_analysis(
        user_query="分析销售数据是否存在异常",
        data_source_id=3
    )
    
    print(f"\n✅ 分析完成!")
    print(f"分析ID: {result.get('analysis_id')}")
    print(f"摘要: {result.get('summary', '')[:100]}")
    
    # 检查异常数据
    anomalies = result.get('anomalies', [])
    print(f"\n异常数量: {len(anomalies)}")
    if anomalies:
        for i, a in enumerate(anomalies):
            print(f"  [{i+1}] {a.get('column', '?')} - {a.get('type', '?')} - {a.get('count', 1)}处")
            print(f"       描述: {str(a.get('description', ''))[:80]}")
    else:
        print("  (无异常数据)")
    
    # 检查图表
    charts = result.get('charts', [])
    print(f"\n图表数量: {len(charts)}")
    for i, chart in enumerate(charts):
        title = chart.get('title', f'图表{i+1}')
        chart_type = chart.get('type', 'unknown')
        print(f"  [{i+1}] {chart_type} - {str(title)[:50]}")
    
    # 测试JSON序列化
    print(f"\n=== 测试JSON序列化 ===")
    try:
        json_str = json.dumps(sanitize_for_json(result), ensure_ascii=False)
        print(f"✅ JSON序列化成功! 长度: {len(json_str)}")
    except Exception as e:
        print(f"❌ JSON序列化失败: {e}")
    
    # 打印报告摘要
    print(f"\n=== 报告摘要 ===")
    report = result.get('report_content', '')
    if report:
        lines = report.split('\n')[:20]
        for line in lines:
            if line.strip():
                print(f"  {line.strip()}")
    
except Exception as e:
    print(f"\n❌ 执行失败: {e}")
    import traceback
    traceback.print_exc()
