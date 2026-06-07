"""
用户使用指南 - 演示脚本：上传数据 + 发起提问 + 查看结果
运行方式: python demo_usage.py
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api"
DATA_FILE = "data/sales_data.csv"  # 已有示例数据


def print_separator(title):
    print("\n" + "=" * 70)
    print(" " + title)
    print("=" * 70)


def step_1_start_service():
    """步骤1: 确认服务启动"""
    print_separator("步骤1: 启动服务")
    print("请先在另一个终端运行以下命令启动服务:")
    print("  python main.py")
    print("\n启动成功后，浏览器访问:")
    print("  http://localhost:8000")
    print("\n按回车键继续...")
    input()


def step_2_upload_data():
    """步骤2: 上传数据文件"""
    print_separator("步骤2: 上传数据文件")

    # 方式A: 通过浏览器上传
    print("【方式1: 浏览器操作】")
    print("  1. 打开 http://localhost:8000")
    print("  2. 在 [数据管理] 标签页，点击上传区域或拖拽文件")
    print("  3. 支持的格式: .csv, .xlsx")
    print("  4. 上传成功后会显示在数据源列表中")

    # 方式B: 通过API上传
    print("\n【方式2: API调用】")
    print("  POST /api/data/upload")
    print("  multipart/form-data: file=<你的文件>")

    # 检查现有数据源
    try:
        print("\n当前系统中的数据源:")
        response = requests.get(f"{BASE_URL}/data/sources")
        data_sources = response.json()
        for ds in data_sources:
            print(f"  - ID={ds['id']}, 名称={ds['name']}, 字段数={len(ds['columns'])}, 行数={ds['row_count']}")
        return data_sources
    except Exception as e:
        print(f"  (服务未启动或出错: {e})")
        return []


def step_3_ask_question(data_sources):
    """步骤3: 发起分析提问"""
    print_separator("步骤3: 用自然语言发起分析提问")

    if not data_sources:
        print("(没有可用数据源，以下仅为演示)")
        return

    ds_id = data_sources[0]["id"]
    ds_name = data_sources[0]["name"]
    columns = data_sources[0]["columns"]

    print(f"使用数据源: {ds_name} (ID={ds_id})")
    print(f"字段列表: {', '.join(columns)}")

    # 示例问题
    example_queries = [
        "分析销售额的统计特征，并检测异常值",
        "不同地区的销售额有什么差异？",
        "最近销售趋势如何？",
        "Analyze the statistics of sales amount",
    ]

    print("\n【方式1: 浏览器操作】")
    print("  1. 打开 [问答分析] 标签页")
    print("  2. 选择数据源")
    print("  3. 在文本框中输入问题，例如:")
    for i, q in enumerate(example_queries, 1):
        print(f"     {i}. {q}")
    print("  4. 点击 [开始分析]")
    print("  5. 等待约30-60秒，查看统计分析、异常检测、分析报告")

    print("\n【方式2: API调用】")
    print("  POST /api/analysis/execute")
    print("  {")
    print(f"    \"data_source_id\": {ds_id},")
    print(f"    \"user_query\": \"{example_queries[0]}\"")
    print("  }")

    # 实际发起一次分析
    print("\n现在演示发起一次分析 (需要服务已启动)")
    query = example_queries[0]
    print(f"\n问题: {query}")
    print("正在分析中... (约需30-60秒)")

    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/analysis/execute",
            json={"data_source_id": ds_id, "user_query": query},
            timeout=120
        )
        elapsed = time.time() - start

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 分析完成! 耗时: {elapsed:.1f}秒")
            print(f"  意图: {result.get('intent')}")
            print(f"  分析类别: {result.get('intent_category')}")
            print(f"  分析ID: {result.get('analysis_id')}")

            # 打印统计摘要
            stats = result.get("statistics", {})
            if stats:
                print("\n📊 统计分析:")
                for field, data in stats.items():
                    if isinstance(data, dict):
                        print(f"  - {field}: 均值={data.get('mean', 'N/A')}, 中位数={data.get('median', 'N/A')}, 最大值={data.get('max', 'N/A')}")

            # 打印异常检测摘要
            anomalies = result.get("anomalies", [])
            if anomalies:
                print(f"\n⚠️  异常检测: 共发现 {len(anomalies)} 个异常")
                for a in anomalies[:5]:
                    print(f"  - {a.get('type', '未知')}: {a.get('description', '')[:60]}")

            # 打印报告摘要
            report = result.get("report_content", "")
            if report:
                print(f"\n📝 分析报告: (前300字)")
                print(f"  {report[:300]}...")

            return result.get("analysis_id")
        else:
            print(f"❌ 分析失败: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务，请确保已启动 python main.py")
    except Exception as e:
        print(f"❌ 出错: {e}")

    return None


def step_4_followup_question(data_sources, analysis_id):
    """步骤4: 多轮上下文追问"""
    print_separator("步骤4: 多轮上下文追问 (基于历史的连续提问)")

    print("系统支持基于上下文的连续提问，不需要每次重复背景说明")

    if not data_sources:
        print("(没有可用数据源，以下仅为演示)")
        return

    session_id = f"demo_session_{int(time.time())}"

    print(f"\n会话ID: {session_id}")
    print("\n【使用方法】")
    print("  POST /api/analysis/followup")
    print("  {")
    print(f"    \"data_source_id\": {data_sources[0]['id']},")
    print(f"    \"session_id\": \"{session_id}\",")
    print("    \"user_query\": \"更详细地分析一下订单数量字段的分布\"")
    print("  }")

    print("\n追问示例:")
    print("  1. 第一轮: \"分析销售额的统计特征\"")
    print("  2. 第二轮: \"再帮我检测一下异常值\" (无需再次说明上下文)")
    print("  3. 第三轮: \"生成一个趋势图表\" (系统知道是之前分析的数据)")

    print("\n【查看会话上下文】")
    print(f"  GET /api/analysis/sessions/{session_id}")


def step_5_view_trace(analysis_id):
    """步骤5: 查看执行过程（可观测性）"""
    print_separator("步骤5: 查看执行过程 - 可观测性")

    if not analysis_id:
        print("(没有分析ID，以下仅为演示)")
        analysis_id = 1

    print("【执行追踪】查看分析过程中的每一步:")
    print(f"  GET /api/analysis/{analysis_id}/trace")

    print("\n【工具调用摘要】查看每个工具的执行时间和输入输出:")
    print(f"  GET /api/analysis/{analysis_id}/tools")

    print("\n【导出完整执行报告】审计和追溯使用:")
    print(f"  GET /api/analysis/{analysis_id}/export")

    print("\n【报告中心】查看所有历史分析:")
    print("  GET /api/analysis/history")

    # 实际查询一次
    try:
        response = requests.get(f"{BASE_URL}/analysis/history")
        records = response.json()
        print(f"\n当前共有 {len(records)} 条历史分析记录")
        for r in records[:5]:
            print(f"  - #{r['id']}: {r['user_query'][:50]}... [{r['status']}]")
    except Exception:
        pass


def step_6_api_reference():
    """步骤6: 完整API参考"""
    print_separator("步骤6: 完整API参考")

    apis = [
        ("POST /api/data/upload", "上传CSV/Excel数据文件"),
        ("GET /api/data/sources", "获取所有数据源列表"),
        ("GET /api/data/sources/{id}", "获取单个数据源信息"),
        ("GET /api/data/sources/{id}/preview", "预览数据前N行"),
        ("DELETE /api/data/sources/{id}", "删除数据源"),
        ("POST /api/analysis/execute", "发起分析提问（核心API）"),
        ("POST /api/analysis/followup", "基于会话的追问（多轮对话）"),
        ("GET /api/analysis/history", "获取分析历史"),
        ("GET /api/analysis/{id}", "获取分析详情"),
        ("GET /api/analysis/{id}/trace", "获取执行追踪"),
        ("GET /api/analysis/{id}/tools", "获取工具调用记录"),
        ("GET /api/analysis/{id}/export", "导出完整执行报告"),
        ("GET /api/analysis/sessions/{session_id}", "获取会话上下文"),
        ("GET /api/tools/list", "获取所有可用工具列表"),
    ]

    for endpoint, desc in apis:
        print(f"  {endpoint:<50} {desc}")


def main():
    print("\n" + "=" * 70)
    print("  AI智能数据分析系统 - 用户使用指南")
    print("=" * 70)

    # 步骤1: 确认服务
    step_1_start_service()

    # 步骤2: 上传数据
    data_sources = step_2_upload_data()

    # 步骤3: 发起提问
    analysis_id = step_3_ask_question(data_sources)

    # 步骤4: 多轮追问
    step_4_followup_question(data_sources, analysis_id)

    # 步骤5: 可观测性
    step_5_view_trace(analysis_id)

    # 步骤6: API参考
    step_6_api_reference()

    print_separator("完成！")
    print("\n📖 快速总结:")
    print("  1. 启动: python main.py")
    print("  2. 浏览器: http://localhost:8000")
    print("  3. 上传数据 -> 提问分析 -> 查看结果")
    print("  4. 支持多轮追问，系统自动记住上下文")
    print("  5. 所有执行过程可追溯，可导出完整报告\n")


if __name__ == "__main__":
    main()
