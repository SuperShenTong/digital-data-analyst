"""测试完整协调器流程"""
import sys
sys.path.insert(0, r'E:\ShenTong\AI Course\digital-data-analyst_v1')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_path = r'E:\ShenTong\AI Course\digital-data-analyst_v1\data\example_db.sqlite'
engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db = Session()

from app.agents.agent_coordinator import AgentCoordinator

coordinator = AgentCoordinator(db)

print("=== 执行完整分析 ===")
print("查询: 分析销售数据是否存在异常")
print("数据源: sales_transactions (ID=3)")

try:
    result = coordinator.execute_analysis(
        user_query="分析销售数据是否存在异常",
        data_source_id=3
    )
    
    print(f"\n=== 分析完成 ===")
    print(f"分析ID: {result.get('analysis_id')}")
    print(f"摘要: {result.get('summary', '')}")
    print(f"意图: {result.get('intent', '')}")
    print(f"意图类别: {result.get('intent_category', '')}")
    
    print(f"\n统计信息: {len(result.get('statistics', {}))}个指标")
    print(f"异常数量: {len(result.get('anomalies', []))}个")
    print(f"图表数量: {len(result.get('charts', []))}个")
    print(f"报告长度: {len(result.get('report_content', ''))}字")
    
    if result.get('anomalies'):
        print("\n=== 异常详情 ===")
        for a in result['anomalies']:
            print(f"  - {a.get('column')}: {a.get('type')} ({a.get('count', 1)}处)")
            print(f"    {a.get('description', '')[:80]}")
    
    if result.get('charts'):
        print("\n=== 图表列表 ===")
        for i, chart in enumerate(result['charts']):
            print(f"  [{i+1}] {chart.get('type')} - {chart.get('title', '未命名')}")
    
    if "error" in result:
        print(f"\n❌ 错误: {result['error']}")
    else:
        print("\n✅ 分析成功完成！")
        
except Exception as e:
    print(f"\n❌ 执行失败: {e}")
    import traceback
    traceback.print_exc()
