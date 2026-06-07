"""
测试LLM图表选择器的中英文双语支持
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_chart_selector import LLMChartSelector

def test_chinese_query():
    """测试中文查询"""
    print("\n" + "=" * 60)
    print("测试1：中文查询")
    print("=" * 60)
    
    selector = LLMChartSelector()
    
    data_summary = {
        "name": "销售数据",
        "row_count": 1000,
        "fields": [
            {"name": "date", "type": "datetime", "sample": "2024-01-01, 2024-01-02"},
            {"name": "region", "type": "category", "sample": "华东, 华南, 华北"},
            {"name": "quantity", "type": "numeric", "sample": "1200, 980, 1350"},
            {"name": "revenue", "type": "numeric", "sample": "600000, 196000, 67500"}
        ]
    }
    
    user_query = "分析各区域的销售分布和趋势变化"
    
    print(f"用户问题: {user_query}")
    
    try:
        charts = selector.analyze_and_select_charts(user_query, data_summary, max_charts=3)
        print(f"\n推荐图表数量: {len(charts)}")
        
        for i, chart in enumerate(charts):
            print(f"\n图表 {i+1}:")
            print(f"  类型: {chart.get('type')}")
            print(f"  标题: {chart.get('title')}")
            print(f"  目的: {chart.get('purpose')}")
        
        return len(charts) > 0
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def test_english_query():
    """测试英文查询"""
    print("\n" + "=" * 60)
    print("测试2：英文查询")
    print("=" * 60)
    
    selector = LLMChartSelector()
    
    data_summary = {
        "name": "Sales Data",
        "row_count": 1000,
        "fields": [
            {"name": "date", "type": "datetime", "sample": "2024-01-01, 2024-01-02"},
            {"name": "region", "type": "category", "sample": "East, West, North"},
            {"name": "quantity", "type": "numeric", "sample": "1200, 980, 1350"},
            {"name": "revenue", "type": "numeric", "sample": "600000, 196000, 67500"}
        ]
    }
    
    user_query = "Analyze the sales distribution and trends by region"
    
    print(f"User Query: {user_query}")
    
    try:
        charts = selector.analyze_and_select_charts(user_query, data_summary, max_charts=3)
        print(f"\nRecommended charts: {len(charts)}")
        
        for i, chart in enumerate(charts):
            print(f"\nChart {i+1}:")
            print(f"  Type: {chart.get('type')}")
            print(f"  Title: {chart.get('title')}")
            print(f"  Purpose: {chart.get('purpose')}")
        
        return len(charts) > 0
    except Exception as e:
        print(f"Test failed: {e}")
        return False

def test_mixed_query():
    """测试中英混合查询"""
    print("\n" + "=" * 60)
    print("测试3：中英混合查询")
    print("=" * 60)
    
    selector = LLMChartSelector()
    
    data_summary = {
        "name": "Server Monitoring",
        "row_count": 500,
        "fields": [
            {"name": "timestamp", "type": "datetime", "sample": "2024-01-01 00:00, 2024-01-01 01:00"},
            {"name": "server_name", "type": "category", "sample": "Server-01, Server-02"},
            {"name": "cpu_usage", "type": "numeric", "sample": "45.2, 62.8, 38.5"},
            {"name": "memory_usage", "type": "numeric", "sample": "60.5, 72.3, 55.1"}
        ]
    }
    
    user_query = "监控服务器CPU和内存使用率，检测异常"
    
    print(f"用户问题: {user_query}")
    
    try:
        charts = selector.analyze_and_select_charts(user_query, data_summary, max_charts=3)
        print(f"\n推荐图表数量: {len(charts)}")
        
        for i, chart in enumerate(charts):
            print(f"\n图表 {i+1}:")
            print(f"  类型: {chart.get('type')}")
            print(f"  标题: {chart.get('title')}")
        
        return len(charts) > 0
    except Exception as e:
        print(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "LLM图表选择器双语测试" + " " * 21 + "║")
    print("╚" + "═" * 58 + "╝")
    
    results = []
    
    try:
        results.append(("中文查询测试", test_chinese_query()))
        results.append(("英文查询测试", test_english_query()))
        results.append(("中英混合测试", test_mixed_query()))
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！LLM图表选择器已支持中英文双语。")
        sys.exit(0)
    else:
        print("⚠️  部分测试失败，请检查代码。")
        sys.exit(1)
