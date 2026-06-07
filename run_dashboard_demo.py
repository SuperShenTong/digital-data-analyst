"""
演示脚本：上传测试数据并展示 Dashboard 图表
"""

import requests

# 上传测试数据
def upload_test_data():
    print("=" * 60)
    print("📤 上传测试数据")
    print("=" * 60)
    
    # 上传销售交易数据
    print("\n1️⃣ 上传销售交易数据...")
    try:
        with open('data/sales/sales_transactions.csv', 'rb') as f:
            response = requests.post('http://localhost:8000/api/data/upload', files={'file': f})
        if response.ok:
            result = response.json()
            print(f"   ✅ 上传成功: {result['filename']}")
            print(f"   ✅ 记录数: {result['row_count']:,}")
            print(f"   ✅ 字段数: {len(result['columns'])}")
            return result['id']
        else:
            print(f"   ❌ 上传失败: {response.json().get('detail', '未知错误')}")
            return None
    except Exception as e:
        print(f"   ❌ 上传失败: {e}")
        return None

# 测试 Dashboard 功能
def test_dashboard(ds_id):
    print("\n" + "=" * 60)
    print("📊 测试 Dashboard 图表功能")
    print("=" * 60)
    
    # 获取统计数据
    print("\n1️⃣ 获取统计数据...")
    try:
        stats_response = requests.get(f'http://localhost:8000/api/data/sources/{ds_id}/stats')
        stats = stats_response.json()
        print(f"   ✅ 总记录数: {stats.get('total_records', 0):,}")
        print(f"   ✅ 总销售额: ¥{(stats.get('total_sales', 0)/10000):,.1f}万")
        print(f"   ✅ 平均订单价值: ¥{stats.get('avg_value', 0):,.0f}")
    except Exception as e:
        print(f"   ⚠️ 获取统计数据失败: {e}")
    
    # 获取图表数据
    print("\n2️⃣ 获取图表数据...")
    try:
        chart_response = requests.get(f'http://localhost:8000/api/data/sources/{ds_id}/chart-data')
        chart_data = chart_response.json()
        
        print("\n   🌍 区域销售分布:")
        for region in chart_data.get('region_data', []):
            print(f"      - {region['name']}: {region['value']:,} 件")
        
        print("\n   📢 渠道销售占比:")
        for channel in chart_data.get('channel_data', []):
            print(f"      - {channel['name']}: {channel['value']}%")
        
        print("\n   📈 月度销售趋势:")
        monthly_data = chart_data.get('monthly_data', [])[:6]
        for month in monthly_data:
            print(f"      - {month['name']}: {month['value']:,} 件")
        
        print("\n   ⚠️ 异常检测统计:")
        for anomaly in chart_data.get('anomaly_data', []):
            print(f"      - {anomaly['name']}: {anomaly['value']} 个")
    except Exception as e:
        print(f"   ⚠️ 获取图表数据失败: {e}")

if __name__ == "__main__":
    ds_id = upload_test_data()
    if ds_id:
        test_dashboard(ds_id)
        print("\n" + "=" * 60)
        print("🎉 Dashboard 演示完成！")
        print("=" * 60)
        print("\n📱 请打开浏览器访问: http://localhost:8000")
        print("\nDashboard 已更新，包含:")
        print("  📈 4个关键指标卡片（销售额、订单数、平均价值、异常数）")
        print("  🥧 区域销售分布图（环形图）")
        print("  🥧 渠道销售占比图（环形图）")
        print("  📊 月度销售趋势图（柱状图）")
        print("  📊 异常检测统计图（柱状图）")
        print("\n💡 提示：在页面上可以进行以下操作：")
        print("  - 查看实时数据统计")
        print("  - 交互式图表（悬停查看详情）")
        print("  - 通过快捷分析入口发起智能分析")
