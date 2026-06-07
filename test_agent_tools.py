"""测试数据分析代理的工具决策"""
import sys
sys.path.insert(0, r'E:\ShenTong\AI Course\digital-data-analyst_v1')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_path = r'E:\ShenTong\AI Course\digital-data-analyst_v1\data\example_db.sqlite'
engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db = Session()

from app.agents.data_analysis_agent import DataAnalysisAgent
from app.services.data_service import DataService

agent = DataAnalysisAgent(db)
data_service = DataService(db)

# 获取数据源
source = data_service.get_data_source(3)
available_columns = source.columns
print(f"可用字段: {available_columns}")

# 检查数据分析代理如何识别数值型字段
numeric_cols = agent._identify_numeric_columns(available_columns)
print(f"识别的数值型字段: {numeric_cols}")

# 直接调用LLM决策工具
from app.services.llm_service import LLMService
from app.prompts import PromptLoader
import json

llm_service = LLMService()

system_prompt = PromptLoader.get_system_prompt("data_analysis_agent")
user_template = PromptLoader.get_user_prompt_template("data_analysis_agent")

user_query = "分析销售数据是否存在异常"
analysis_plan = {
    "intent": "检测异常数据",
    "intent_category": "anomaly_detection",
    "required_fields": ["quantity", "unit_price", "discount_rate"],
    "analysis_steps": ["检测各字段的异常值", "分析异常类型", "统计异常数量"]
}

user_prompt = user_template.format(
    user_query=user_query,
    analysis_plan=json.dumps(analysis_plan, ensure_ascii=False, indent=2),
    available_columns=available_columns
)

print("\n=== 发送给LLM的提示词 ===")
print(f"System prompt 长度: {len(system_prompt)}")
print(f"User prompt 长度: {len(user_prompt)}")

# 获取LLM决策
try:
    tool_decision = llm_service.decide_tools_with_prompts(
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )
    print("\n=== LLM工具决策结果 ===")
    print(json.dumps(tool_decision, ensure_ascii=False, indent=2))
    
    tools_to_call = tool_decision.get("tools_to_call", [])
    print(f"\n需要调用的工具: {len(tools_to_call)}个")
    for tool in tools_to_call:
        print(f"  - {tool.get('name')}: 字段={tool.get('fields', [])}")
except Exception as e:
    print(f"LLM调用失败: {e}")
    import traceback
    traceback.print_exc()

# 直接执行数据分析代理
print("\n=== 直接执行数据分析代理 ===")
try:
    result = agent.execute(
        task="分析销售数据是否存在异常",
        context={
            "data_source_id": 3,
            "user_query": "分析销售数据是否存在异常",
            "analysis_plan": analysis_plan
        }
    )
    print(f"统计信息: {len(result.get('statistics', {}))}个指标")
    print(f"异常数量: {len(result.get('anomalies', []))}个")
    print(f"图表数量: {len(result.get('charts', []))}个")
    print(f"执行的工具: {result.get('tools_executed', [])}")
    
    if result.get('anomalies'):
        print("\n前3个异常:")
        for a in result['anomalies'][:3]:
            print(f"  - {a.get('column')}: {a.get('description')[:80]}")
except Exception as e:
    print(f"执行失败: {e}")
    import traceback
    traceback.print_exc()
