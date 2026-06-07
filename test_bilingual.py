"""测试：验证提示词支持中英文"""
import time
from app.services.llm_service import LLMService
from app.prompts import PromptLoader


def test_english_queries():
    """测试英文提问"""
    print("\n" + "=" * 70)
    print(" Testing Bilingual Support - English Queries")
    print("=" * 70)

    try:
        service = LLMService()
        system_prompt = PromptLoader.get_system_prompt("data_understanding_agent")
        user_template = PromptLoader.get_user_prompt_template("data_understanding_agent")

        test_cases = [
            ("Analyze the sales statistics", "Expected: Statistical Analysis"),
            ("Detect anomalies in the data", "Expected: Anomaly Detection"),
            ("Show me the recent sales trends", "Expected: Trend Analysis"),
            ("Compare sales across different regions", "Expected: Comparative Analysis"),
        ]

        all_passed = True
        available_columns = "Date, Product Name, Region, Sales Amount, Order Quantity, Customer Count"

        for i, (query, expected) in enumerate(test_cases, 1):
            print("\n[{0}] Query: {1}".format(i, query))
            print("    Expected: {0}".format(expected))

            try:
                user_prompt = user_template.format(
                    user_query=query,
                    available_columns=available_columns
                )

                start = time.time()
                result = service.analyze_intent_with_prompts(system_prompt, user_prompt)
                elapsed = time.time() - start

                print("    [OK] Detected Intent: {0}".format(result['intent']))
                print("    [OK] Category: {0}".format(result['intent_category']))
                print("    [OK] Steps: {0}".format(result['analysis_steps']))
                print("    [OK] Time: {0:.1f}s".format(elapsed))

            except Exception as e:
                print("    [FAIL] Error: {0}".format(e))
                all_passed = False

        return all_passed

    except Exception as e:
        print("[-] LLM Service Error: {0}".format(e))
        return False


def test_chinese_queries():
    """测试中文提问"""
    print("\n" + "=" * 70)
    print(" Testing Bilingual Support - Chinese Queries")
    print("=" * 70)

    try:
        service = LLMService()
        system_prompt = PromptLoader.get_system_prompt("data_understanding_agent")
        user_template = PromptLoader.get_user_prompt_template("data_understanding_agent")

        test_cases = [
            ("分析销售额的统计特征", "Expected: 统计分析"),
            ("检测数据中的异常值", "Expected: 异常检测"),
            ("看看最近的销售趋势变化", "Expected: 趋势分析"),
            ("对比不同地区的销售差异", "Expected: 对比分析"),
        ]

        all_passed = True
        available_columns = "日期、产品名称、地区、销售额、订单数量、客户数"

        for i, (query, expected) in enumerate(test_cases, 1):
            print("\n[{0}] Query: {1}".format(i, query))
            print("    Expected: {0}".format(expected))

            try:
                user_prompt = user_template.format(
                    user_query=query,
                    available_columns=available_columns
                )

                start = time.time()
                result = service.analyze_intent_with_prompts(system_prompt, user_prompt)
                elapsed = time.time() - start

                print("    [OK] Detected Intent: {0}".format(result['intent']))
                print("    [OK] Category: {0}".format(result['intent_category']))
                print("    [OK] Steps: {0}".format(result['analysis_steps']))
                print("    [OK] Time: {0:.1f}s".format(elapsed))

            except Exception as e:
                print("    [FAIL] Error: {0}".format(e))
                all_passed = False

        return all_passed

    except Exception as e:
        print("[-] LLM Service Error: {0}".format(e))
        return False


def main():
    print("\n" + "=" * 70)
    print(" AI Data Analysis System - Bilingual Support Test")
    print(" Testing: Chinese and English query support")
    print("=" * 70)

    results = []

    # Test English
    passed = test_english_queries()
    results.append(("English Queries", passed))

    # Test Chinese
    passed = test_chinese_queries()
    results.append(("Chinese Queries", passed))

    # Summary
    print("\n" + "=" * 70)
    print(" Test Summary")
    print("=" * 70)

    all_passed = True
    for name, passed in results:
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(" {0}: {1}".format(name, status))
        all_passed = all_passed and passed

    print("\n" + "=" * 70)
    if all_passed:
        print(" All tests passed! System supports both Chinese and English queries.")
    else:
        print(" Some tests failed. Please check the output above.")
    print("=" * 70)


if __name__ == "__main__":
    main()
