"""
完整测试：验证三个Agent都能成功调用LLM完成数据分析任务
"""
import os
import sys
import json
import time
import requests


def print_header(title):
    print("\n" + "=" * 70)
    print(" " + title)
    print("=" * 70)


def test_step_1_llm_service():
    """测试1: LLM服务初始化和基本功能"""
    print_header("测试1: LLM服务初始化测试")

    try:
        from app.services.llm_service import LLMService
        print("[+] 成功导入LLMService")

        service = LLMService()
        info = service.get_model_info()
        print("    - 模型: {0}".format(info['model']))
        print("    - 提供商: {0}".format(info['provider']))
        print("    - API: {0}".format(info['api_base']))
        print("    - 可用状态: {0}".format(info['available']))
        print("[OK] LLM服务正常")

        return True, service
    except Exception as e:
        print("[-] LLM服务初始化失败: {0}".format(e))
        return False, None


def test_step_2_understanding_agent(service):
    """测试2: 数据理解Agent - LLM意图识别"""
    print_header("测试2: 数据理解Agent - LLM意图分析")

    try:
        from app.prompts import PromptLoader

        test_cases = [
            ("分析销售额的统计特征", "统计分析"),
            ("检测数据中有哪些异常值", "异常检测"),
            ("看看最近的销售趋势变化", "趋势分析"),
            ("对比不同地区的销售差异", "对比分析"),
        ]

        system_prompt = PromptLoader.get_system_prompt("data_understanding_agent")
        user_template = PromptLoader.get_user_prompt_template("data_understanding_agent")

        if not system_prompt:
            print("[-] 无法加载提示词")
            return False

        print("[+] 提示词加载成功")

        all_passed = True
        for i, (query, expected_category) in enumerate(test_cases, 1):
            print("\n  [{0}] 问题: {1}".format(i, query))

            try:
                available_columns = "日期、产品名称、地区、销售额、订单数量、客户数"
                user_prompt = user_template.format(
                    user_query=query,
                    available_columns=available_columns
                )

                start = time.time()
                result = service.analyze_intent_with_prompts(system_prompt, user_prompt)
                elapsed = time.time() - start

                print("    [OK] 意图: {0}".format(result['intent']))
                print("    [OK] 类别: {0}".format(result['intent_category']))
                print("    [OK] 步骤: {0}".format(result['analysis_steps']))
                print("    [OK] 耗时: {0:.1f}秒".format(elapsed))

                if expected_category not in result['intent_category']:
                    print("    [提示] 预期类别包含: {0}".format(expected_category))

            except Exception as e:
                print("    [FAIL] 失败: {0}".format(e))
                all_passed = False

        print("\n  [OK] 数据理解Agent测试完成")
        return all_passed

    except Exception as e:
        print("[-] 测试失败: {0}".format(e))
        import traceback
        traceback.print_exc()
        return False


def test_step_3_analysis_agent(service):
    """测试3: 数据分析Agent - LLM工具决策"""
    print_header("测试3: 数据分析Agent - LLM工具决策")

    try:
        from app.prompts import PromptLoader

        system_prompt = PromptLoader.get_system_prompt("data_analysis_agent")
        user_template = PromptLoader.get_user_prompt_template("data_analysis_agent")

        if not system_prompt:
            print("[-] 无法加载提示词")
            return False

        print("[+] 提示词加载成功")

        test_cases = [
            {
                "query": "分析销售额的统计特征",
                "plan": "用户想要了解数据的基本统计特征",
                "columns": "日期、产品名称、地区、销售额、订单数量、客户数"
            }
        ]

        all_passed = True
        for i, case in enumerate(test_cases, 1):
            print("\n  [{0}] 场景: {1}".format(i, case['query']))

            try:
                user_prompt = user_template.format(
                    user_query=case["query"],
                    analysis_plan=case["plan"],
                    available_columns=case["columns"]
                )

                start = time.time()
                result = service.decide_tools_with_prompts(system_prompt, user_prompt)
                elapsed = time.time() - start

                summary = result['summary']
                if len(summary) > 60:
                    summary = summary[:60] + "..."
                print("    [OK] 摘要: {0}".format(summary))
                tools = result['tools_to_call']
                print("    [OK] 工具数: {0}".format(len(tools)))
                for j, tool in enumerate(tools, 1):
                    print("      * 工具{0}: {1} - 字段: {2}".format(j, tool.get('name'), tool.get('fields')))
                print("    [OK] 耗时: {0:.1f}秒".format(elapsed))

            except Exception as e:
                print("    [FAIL] 失败: {0}".format(e))
                import traceback
                traceback.print_exc()
                all_passed = False

        print("\n  [OK] 数据分析Agent测试完成")
        return all_passed

    except Exception as e:
        print("[-] 测试失败: {0}".format(e))
        import traceback
        traceback.print_exc()
        return False


def test_step_4_report_agent(service):
    """测试4: 报告生成Agent - LLM生成报告"""
    print_header("测试4: 报告生成Agent - LLM报告生成")

    try:
        from app.prompts import PromptLoader

        system_prompt = PromptLoader.get_system_prompt("report_generation_agent")
        user_template = PromptLoader.get_user_prompt_template("report_generation_agent")

        if not system_prompt:
            print("[-] 无法加载提示词")
            return False

        print("[+] 提示词加载成功")

        # 准备模拟的分析结果
        user_query = "分析销售额的统计特征"
        analysis_plan = "对销售数据进行统计分析"
        analysis_results = json.dumps({
            "user_query": user_query,
            "statistics": {
                "销售额": {
                    "count": 120,
                    "sum": 1560000,
                    "mean": 13000,
                    "median": 12500,
                    "std": 3500,
                    "min": 6000,
                    "max": 28500
                },
                "订单数量": {
                    "count": 120,
                    "sum": 4800,
                    "mean": 40,
                    "median": 38,
                    "std": 12,
                    "min": 15,
                    "max": 85
                }
            },
            "anomalies": [
                {"row": 15, "column": "销售额", "value": 28500, "reason": "极值异常"}
            ],
            "charts_count": 2
        }, ensure_ascii=False)

        # 填充用户提示词
        user_prompt = user_template.format(
            user_query=user_query,
            analysis_plan=analysis_plan,
            analysis_results=analysis_results
        )

        print("[+] 正在调用LLM生成报告...")
        start = time.time()

        report = service.generate_report_with_prompts(system_prompt, user_prompt)
        elapsed = time.time() - start

        print("[+] 报告生成成功")
        print("    - 长度: {0} 字符".format(len(report)))
        print("    - 耗时: {0:.1f}秒".format(elapsed))

        # 检查关键部分
        for keyword in ["执行摘要", "数据指标", "洞察", "建议"]:
            if keyword in report:
                print("    [OK] 包含: {0}".format(keyword))
            else:
                print("    [提示] 未包含: {0}".format(keyword))

        # 预览报告
        print("\n    报告预览 (前500字符):")
        preview = report[:500]
        for line in preview.split('\n'):
            print("    | {0}".format(line))
        print("    ...")

        print("\n  [OK] 报告生成Agent测试完成")
        return True

    except Exception as e:
        print("[-] 测试失败: {0}".format(e))
        import traceback
        traceback.print_exc()
        return False


def test_step_5_api_flow():
    """测试5: 完整的API调用流程"""
    print_header("测试5: 完整API调用流程 - 三个Agent协作")

    try:
        url = "http://localhost:8000/api/data/sources"
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            print("[-] API服务不可用，请确认服务已启动")
            return False

        sources = response.json()
        print("[+] API服务正常，共 {0} 个数据源".format(len(sources)))

        if not sources:
            print("[-] 没有可用的数据源")
            return False

        data_source_id = sources[0].get("id")
        print("[+] 使用数据源 ID: {0}".format(data_source_id))

        # 执行分析
        analysis_url = "http://localhost:8000/api/analysis/execute"
        test_query = "分析销售额的统计特征并生成报告"

        print("\n  [1] 用户问题: {0}".format(test_query))
        print("  [2] 正在执行三个Agent的完整流程...")
        print("      数据理解Agent -> 数据分析Agent -> 报告生成Agent")

        payload = {
            "data_source_id": data_source_id,
            "user_query": test_query
        }

        start = time.time()
        response = requests.post(analysis_url, json=payload, timeout=120)
        elapsed = time.time() - start

        if response.status_code != 200:
            print("\n  [FAIL] 请求失败 ({0})".format(response.status_code))
            print("      错误: {0}".format(response.text))
            return False

        result = response.json()

        print("\n  [3] 分析完成！总耗时: {0:.1f}秒".format(elapsed))
        print("\n  ===== 分析结果摘要 =====")
        print("    [OK] 识别意图: {0}".format(result.get('intent')))
        print("    [OK] 分析类别: {0}".format(result.get('intent_category')))

        stats = result.get('statistics', {})
        if stats:
            print("    [OK] 统计分析: 分析了 {0} 个字段".format(len(stats)))
            for field, data in stats.items():
                if isinstance(data, dict) and 'mean' in data:
                    print("        - {0}: 均值 {1}".format(field, data['mean']))

        anomalies = result.get('anomalies', [])
        print("    [OK] 异常检测: 发现 {0} 个异常".format(len(anomalies)))

        report = result.get('report_content', '')
        print("    [OK] 报告生成: 成功，长度 {0} 字符".format(len(report)))

        print("\n  ===== 报告预览 =====")
        lines = report.strip().split('\n')[:15]
        for line in lines:
            print("    | {0}".format(line))
        print("    ...")

        print("\n  [OK] 完整API流程测试成功！三个Agent已成功协作完成分析")
        return True

    except requests.exceptions.ConnectionError:
        print("[-] 无法连接到API服务，请确认服务已启动")
        return False
    except Exception as e:
        print("[-] 测试失败: {0}".format(e))
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 70)
    print("  AI智能数据分析系统 - LLM完整调用流程测试")
    print("  目标: 验证三个Agent都能成功调用LLM完成分析任务")
    print("=" * 70)

    results = []

    # 测试1: LLM服务初始化
    passed, service = test_step_1_llm_service()
    results.append(("LLM服务初始化", passed))

    if not passed or service is None:
        print("\n测试中止: LLM服务不可用")
        return

    # 测试2: 数据理解Agent
    passed = test_step_2_understanding_agent(service)
    results.append(("数据理解Agent", passed))

    # 测试3: 数据分析Agent
    passed = test_step_3_analysis_agent(service)
    results.append(("数据分析Agent", passed))

    # 测试4: 报告生成Agent
    passed = test_step_4_report_agent(service)
    results.append(("报告生成Agent", passed))

    # 测试5: 完整API流程
    passed = test_step_5_api_flow()
    results.append(("完整API协作", passed))

    # 总结
    print_header("测试总结")
    all_passed = True
    for name, passed in results:
        status = "[OK] 通过" if passed else "[FAIL] 失败"
        print("  {0}: {1}".format(name, status))
        all_passed = all_passed and passed

    print("\n" + "=" * 70)
    if all_passed:
        print("  恭喜！所有测试通过！")
        print("  三个Agent都能成功调用LLM完成数据分析任务")
    else:
        print("  部分测试失败，请检查以上输出")
    print("=" * 70)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
