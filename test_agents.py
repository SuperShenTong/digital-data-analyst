"""
测试三个智能体的协作流程
"""
import requests


def test_agent_collaboration():
    print("=" * 60)
    print("【测试：三个智能体协作分析】")
    print("=" * 60)

    # 测试中文提问
    url = 'http://localhost:8000/api/analysis/execute'
    data = {
        'data_source_id': 2,
        'user_query': '分析销售额和订单数量的统计情况，帮我生成一份完整的分析报告'
    }

    response = requests.post(url, json=data)
    print('响应状态:', response.status_code)

    if response.status_code != 200:
        print("请求失败:", response.text)
        return

    result = response.json()

    # 1. 数据理解Agent的输出
    print("\n1. 数据理解Agent (DataUnderstandingAgent):")
    print("   - 意图识别:", result.get('intent', 'N/A'))
    print("   - 意图类别:", result.get('intent_category', 'N/A'))
    print("   - LLM来源:", result.get('llm_source', 'N/A'))
    print("   - 分析计划步骤:", result.get('analysis_steps', 'N/A'))

    # 2. 数据分析Agent的输出
    print("\n2. 数据分析Agent (DataAnalysisAgent):")
    stats = result.get('statistics', {})
    if stats:
        print(f"   - 分析字段数: {len(stats)}")
        for field, stat_data in stats.items():
            if isinstance(stat_data, dict) and 'mean' in stat_data:
                mean_val = stat_data.get('mean', 'N/A')
                count_val = stat_data.get('count', 'N/A')
                print(f"   - {field}: 均值={mean_val}, 数量={count_val}")
    else:
        print("   - 统计结果: 无")

    anomalies = result.get('anomalies', [])
    print(f"   - 异常检测: 发现 {len(anomalies)} 个异常")

    # 3. 报告生成Agent的输出
    print("\n3. 报告生成Agent (ReportGenerationAgent):")
    report = result.get('report_content', '')
    if report:
        lines = report.strip().split('\n')
        first_lines = '\n'.join(lines[:8])
        print(f"   - 报告长度: {len(report)} 字符")
        print(f"   - 报告内容预览:\n{first_lines}")
    else:
        print("   - 报告: (空)")

    print("\n" + "=" * 60)
    print("【Agent协作测试完成】")
    print("=" * 60)


def test_llm_intent_analysis():
    """测试LLM的意图分析能力"""
    print("\n" + "=" * 60)
    print("【测试：不同问题的意图识别】")
    print("=" * 60)

    test_cases = [
        "分析销售额的基本统计特征",
        "检测数据中的异常值",
        "分析销售额的趋势变化",
        "对比不同地区的销售额差异",
        "生成数据的可视化图表"
    ]

    url = 'http://localhost:8000/api/analysis/execute'

    for i, query in enumerate(test_cases, 1):
        print(f"\n[{i}] 用户问题: '{query}'")
        data = {
            'data_source_id': 2,
            'user_query': query
        }

        try:
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                intent = result.get('intent', '')
                category = result.get('intent_category', '')
                llm_source = result.get('llm_source', '')
                print(f"    → 意图: {intent}")
                print(f"    → 类别: {category}")
                print(f"    → LLM: {llm_source}")
            else:
                print(f"    → 错误: {response.status_code}")
        except Exception as e:
            print(f"    → 异常: {e}")


if __name__ == "__main__":
    test_agent_collaboration()
    test_llm_intent_analysis()
    print("\n[OK] 所有测试完成")
