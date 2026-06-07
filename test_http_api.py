"""用Python直接测试HTTP API"""
import requests
import json

url = "http://localhost:8000/api/analysis/execute"
data = {
    "data_source_id": 3,
    "user_query": "分析销售数据是否存在异常"
}

print("=== 测试HTTP API ===")
print(f"URL: {url}")
print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")

try:
    response = requests.post(url, json=data, timeout=120)
    
    print(f"\n状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n=== API响应 ===")
        print(f"analysis_id: {result.get('analysis_id')}")
        print(f"anomalies: {len(result.get('anomalies', []))}个")
        print(f"charts: {len(result.get('charts', []))}个")
        print(f"report_content: {len(result.get('report_content', ''))}字符")
        print(f"summary: {result.get('summary', '')[:100]}")
        
        if result.get('anomalies'):
            print(f"\n=== 异常详情 ===")
            for i, a in enumerate(result['anomalies']):
                print(f"  [{i+1}] {a.get('column')} - {a.get('type')} ({a.get('count')}处, {a.get('severity')})")
                print(f"       描述: {str(a.get('description', ''))[:80]}")
        
        if result.get('charts'):
            print(f"\n=== 图表列表 ===")
            for i, chart in enumerate(result['charts']):
                title = chart.get('title', f'图表{i+1}')
                chart_type = chart.get('type', 'unknown')
                print(f"  [{i+1}] {chart_type} - {str(title)[:50]}")
        
        print(f"\n✅ API调用成功!")
    else:
        print(f"❌ 错误: {response.text}")
        
except Exception as e:
    print(f"❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()
