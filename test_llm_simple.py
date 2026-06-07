"""简单测试：验证LLM服务能否正常调用"""
import sys
from app.services.llm_service import LLMService
from langchain_core.messages import SystemMessage, HumanMessage

print("=" * 60)
print("简单测试：验证LLM服务是否正常工作")
print("=" * 60)

try:
    print("\n[1/3] 初始化LLM服务...")
    service = LLMService()
    print(f"    模型: {service.model}")
    print(f"    可用: {service.is_available()}")
    print("    [OK]")

    print("\n[2/3] 发送测试消息...")
    response = service.llm.invoke([
        SystemMessage(content="你是一个测试助手，只需要回答测试成功这四个字。"),
        HumanMessage(content="请回复测试成功")
    ])
    print(f"    LLM响应: {response.content}")
    print("    [OK]")

    print("\n[3/3] 测试意图分析...")
    result = service.analyze_intent_with_prompts(
        system_prompt="你是一个数据分析助手，负责分析用户的数据分析需求。",
        user_prompt="请分析：分析销售额的统计特征。可用字段：日期、产品、地区、销售额、订单数量、客户数"
    )
    print(f"    意图: {result['intent']}")
    print(f"    类别: {result['intent_category']}")
    print(f"    步骤: {result['analysis_steps']}")
    print("    [OK]")

    print("\n" + "=" * 60)
    print("所有测试通过！LLM服务正常工作")
    print("=" * 60)

except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
