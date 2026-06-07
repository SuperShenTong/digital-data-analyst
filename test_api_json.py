"""直接测试API路由的返回格式"""
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

# 模拟API路由
print("=== 模拟API路由 ===")

# 1. 执行分析
result = coordinator.execute_analysis(
    user_query="分析销售数据是否存在异常",
    data_source_id=3
)

print(f"步骤1 - 原始结果:")
print(f"  analysis_id: {result.get('analysis_id')}")
print(f"  anomalies: {len(result.get('anomalies', []))}个")
print(f"  charts: {len(result.get('charts', []))}个")

# 2. 检查是否有error
if "error" in result:
    print(f"❌ 有错误: {result['error']}")
    sys.exit(1)

# 3. 清理数据
cleaned_result = sanitize_for_json(result)

print(f"\n步骤2 - 清理后数据:")
print(f"  anomalies: {len(cleaned_result.get('anomalies', []))}个")
print(f"  charts: {len(cleaned_result.get('charts', []))}个")

# 4. 模拟FastAPI的JSON响应
print(f"\n步骤3 - 模拟FastAPI响应:")

# 使用json.dumps模拟FastAPI的序列化
try:
    response_json = json.dumps(cleaned_result, ensure_ascii=False)
    print(f"✅ JSON序列化成功! 长度: {len(response_json)}")
    
    # 反序列化回来检查
    parsed_result = json.loads(response_json)
    print(f"  anomalies: {len(parsed_result.get('anomalies', []))}个")
    print(f"  charts: {len(parsed_result.get('charts', []))}个")
    
    # 检查anomalies的内容
    if parsed_result.get('anomalies'):
        for a in parsed_result['anomalies']:
            print(f"  - {a.get('column')}: {a.get('type')} ({a.get('count')}处, {a.get('severity')})")
            
except Exception as e:
    print(f"❌ JSON序列化失败: {e}")
    import traceback
    traceback.print_exc()

# 5. 检查返回的完整JSON结构
print(f"\n步骤4 - JSON结构检查:")
for key in ['analysis_id', 'anomalies', 'charts', 'report_content', 'summary', 'intent']:
    val = parsed_result.get(key)
    if isinstance(val, list):
        print(f"  {key}: list(len={len(val)})")
    elif isinstance(val, dict):
        print(f"  {key}: dict(keys={list(val.keys())[:5]})")
    elif val is not None:
        print(f"  {key}: {type(val).__name__} = {str(val)[:50]}")
    else:
        print(f"  {key}: None")

print(f"\n=== 测试通过! ===")
