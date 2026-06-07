"""
详细调试：检查数据分析Agent的工具调用
"""
import requests


def test_data_analysis():
    """测试数据上传和分析"""
    print("=" * 60)
    print("【调试测试】")
    print("=" * 60)

    # 首先获取数据源列表
    url = "http://localhost:8000/api/data/sources"
    response = requests.get(url)
    print(f"\n[1] 获取数据源列表: {response.status_code}")
    if response.status_code == 200:
        sources = response.json()
        print(f"    数据源数量: {len(sources)}")
        for s in sources[:3]:
            print(f"    - {s.get('id')}: {s.get('name')}")
            print(f"      字段: {s.get('columns')}")

    # 测试执行分析
    url = "http://localhost:8000/api/analysis/execute"
    data = {
        "data_source_id": 2,
        "user_query": "分析销售额"
    }
    print(f"\n[2] 执行数据分析...")
    response = requests.post(url, json=data)
    print(f"    响应: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n[3] 完整结果:")
        print(f"    意图: {result.get('intent')}")
        print(f"    类别: {result.get('intent_category')}")
        print(f"    统计结果: {result.get('statistics')}")
        print(f"    异常: {result.get('anomalies')}")
        print(f"    报告内容:\n{result.get('report_content')}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_data_analysis()
