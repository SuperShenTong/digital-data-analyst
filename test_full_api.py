"""完整测试API路由中的数据"""
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

# 步骤1：执行分析并检查原始结果
print("=== 步骤1：执行分析 ===")
result = coordinator.execute_analysis(
    user_query="分析销售数据是否存在异常",
    data_source_id=3
)

print(f"analysis_id: {result.get('analysis_id')}")
print(f"anomalies原始: {len(result.get('anomalies', []))}个")
if result.get('anomalies'):
    print(f"第一个异常: {result['anomalies'][0].get('column')} - {result['anomalies'][0].get('type')}")

# 步骤2：检查sanitize_for_json后的数据
print(f"\n=== 步骤2：清理数据 ===")
cleaned_result = sanitize_for_json(result)
print(f"anomalies清理后: {len(cleaned_result.get('anomalies', []))}个")
if cleaned_result.get('anomalies'):
    print(f"第一个异常: {cleaned_result['anomalies'][0].get('column')} - {cleaned_result['anomalies'][0].get('type')}")

# 步骤3：测试JSON序列化
print(f"\n=== 步骤3：测试JSON序列化 ===")
try:
    json_str = json.dumps(cleaned_result, ensure_ascii=False)
    print(f"✅ JSON序列化成功! 长度: {len(json_str)}")
    
    # 反序列化后再检查
    result2 = json.loads(json_str)
    print(f"反序列化后 anomalies: {len(result2.get('anomalies', []))}个")
    if result2.get('anomalies'):
        print(f"反序列化后第一个异常: {result2['anomalies'][0]}")
except Exception as e:
    print(f"❌ JSON序列化失败: {e}")
    import traceback
    traceback.print_exc()

# 步骤4：模拟FastAPI的响应模型序列化
print(f"\n=== 步骤4：检查是否有不可序列化的字段 ===")
def check_serializable(obj, path=""):
    """递归检查对象中的不可序列化字段"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            check_serializable(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            check_serializable(item, f"{path}[{i}]")
    else:
        # 检查基本类型
        if not isinstance(obj, (str, int, float, bool, type(None))):
            print(f"⚠️ 非标准类型: {path} = {type(obj).__name__}({repr(obj)[:50]})")

check_serializable(cleaned_result)

# 步骤5：手动构建一个简化的响应，确保包含关键数据
print(f"\n=== 步骤5：构建最小化响应 ===")
minimal_response = {
    "analysis_id": cleaned_result.get("analysis_id"),
    "user_query": cleaned_result.get("user_query"),
    "summary": cleaned_result.get("summary"),
    "intent": cleaned_result.get("intent"),
    "intent_category": cleaned_result.get("intent_category"),
    "anomalies": cleaned_result.get("anomalies", []),
    "charts": cleaned_result.get("charts", []),
    "statistics": cleaned_result.get("statistics", {}),
    "report_content": cleaned_result.get("report_content", ""),
    "created_at": cleaned_result.get("created_at"),
    "llm_source": cleaned_result.get("llm_source"),
}

print(f"最小化响应 anomalies: {len(minimal_response['anomalies'])}个")
print(f"最小化响应 charts: {len(minimal_response['charts'])}个")

try:
    json_str2 = json.dumps(minimal_response, ensure_ascii=False)
    result3 = json.loads(json_str2)
    print(f"✅ 最小化响应JSON成功!")
    print(f"反序列化后 anomalies: {len(result3.get('anomalies', []))}个")
except Exception as e:
    print(f"❌ 最小化响应JSON失败: {e}")

print(f"\n=== 测试完成 ===")
