"""
演示脚本：展示 Dashboard 的图表功能
"""

import requests
import json

# 测试 Dashboard 功能
def test_dashboard():
    print("=" * 60)
    print("📊 测试 Dashboard 图表功能")
    print("=" * 60)
    
    # 获取统计数据
    print("\n1️⃣ 获取统计数据...")
    try:
        response = requests.get('http://localhost:8000/api/data/sources')
        sources = response.json()
        
        if sources:
            ds_id = sources[0]['id']
            stats_response = requests.get(f'http://localhost:8000/api/data/sources/{ds_id}/stats')
            stats = stats_response.json()
            print(f"   ✅ 总记录数: {stats.get('total_records', 0):,}")
            print(f"   ✅ 总销售额: ¥{stats.get('total_sales', 0):,.0f}")
            print(f"   ✅ 平均订单价值: ¥{stats.get('avg_value', 0):,.0f}")
        else:
            print("   ⚠️ 暂无数据源，使用模拟数据")
    except Exception as e:
        print(f"   ⚠️ 获取统计数据失败: {e}")
    
    # 获取图表数据
    print("\n2️⃣ 获取图表数据...")
    try:
        chart_response = requests.get(f'http://localhost:8000/api/data/sources/{ds_id}/chart-data')
        chart_data = chart_response.json()
        
        print(f"   ✅ 区域数据: {len(chart_data.get('region_data', []))} 个区域")
        print(f"   ✅ 渠道数据: {len(chart_data.get('channel_data', []))} 个渠道")
        print(f"   ✅ 月度数据: {len(chart_data.get('monthly_data', []))} 个月")
        print(f"   ✅ 异常数据: {len(chart_data.get('anomaly_data', []))} 种类型")
    except Exception as e:
        print(f"   ⚠️ 获取图表数据失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Dashboard 功能测试完成！")
    print("=" * 60)
    print("\n📱 打开浏览器访问: http://localhost:8000")
    print("\nDashboard 包含以下图表：")
    print("  🥧 区域销售分布 - 环形图")
    print("  🥧 渠道销售占比 - 环形图")
    print("  📊 月度销售趋势 - 柱状图")
    print("  📊 异常检测统计 - 柱状图")

if __name__ == "__main__":
    test_dashboard()
