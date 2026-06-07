"""直接测试API路由中的数据"""
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

# 执行分析
print("=== 执行分析 ===")
result = coordinator.execute_analysis(
    user_query="分析销售数据是否存在异常",
    data_source_id=3
)

print(f"analysis_id: {result.get('analysis_id')}")
print(f"anomalies 类型: {type(result.get('anomalies'))}")
print(f"anomalies 数量: {len(result.get('anomalies', []))}")

# 检查anomalies的具体内容
anomalies = result.get('anomalies')
print(f"anomalies: {anomalies}")

# 如果anomalies不是列表，检查一下analysis_results
if not anomalies:
    print(f"\n=== 检查是否在其他字段中 ===")
    print(f"result keys: {list(result.keys())}")
    
    # 检查final_result（如果有）
    if 'final_result' in result:
        print(f"final_result: {type(result['final_result'])}")
        if isinstance(result['final_result'], dict):
            print(f"final_result keys: {list(result['final_result'].keys())}")
            print(f"final_result.anomalies: {result['final_result'].get('anomalies')}")

# 测试JSON序列化
print(f"\n=== 测试JSON序列化 ===")
try:
    json_str = json.dumps(result, ensure_ascii=False)
    print(f"✅ JSON序列化成功! 长度: {len(json_str)}")
    
    # 反序列化后再检查
    result2 = json.loads(json_str)
    print(f"反序列化后 anomalies: {result2.get('anomalies')}")
    print(f"反序列化后 anomalies数量: {len(result2.get('anomalies', []))}")
except Exception as e:
    print(f"❌ JSON序列化失败: {e}")
    import traceback
    traceback.print_exc()

# 直接用sanitize_for_json处理
print(f"\n=== 使用sanitize_for_json处理 ===")
from app.agents.agent_coordinator import sanitize_for_json
clean_result = sanitize_for_json(result)
print(f"clean_result['anomalies']: {clean_result.get('anomalies')}")
try:
    json_str2 = json.dumps(clean_result, ensure_ascii=False)
    print(f"✅ 清理后的JSON序列化成功! 长度: {len(json_str2)}")
except Exception as e:
    print(f"❌ 清理后的JSON序列化失败: {e}")
