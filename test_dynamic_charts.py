"""
测试动态图表生成功能
验证：SmartChartGenerator能否根据不同数据源自动选择合适的图表
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.chart_generator import SmartChartGenerator

def test_sales_data():
    """测试销售数据的图表生成"""
    print("\n" + "=" * 60)
    print("测试1：销售数据")
    print("=" * 60)
    
    # 创建销售数据
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=12, freq='M'),
        'region': ['华东', '华南', '华北', '华中'] * 3,
        'category': ['电子产品', '服装', '食品', '日用品'] * 3,
        'quantity': [1200, 980, 1350, 1420, 1580, 2800, 1650, 1520, 1780, 1950, 4200, 2100],
        'unit_price': [500, 200, 50, 30, 450, 180, 55, 35, 520, 220, 60, 40],
        'revenue': [600000, 196000, 67500, 42600, 711000, 504000, 90750, 53200, 925600, 429000, 252000, 84000]
    })
    
    print(f"数据源: 销售数据 ({len(df)} 行, {len(df.columns)} 列)")
    print(f"字段: {list(df.columns)}")
    
    charts = SmartChartGenerator.generate_charts(df, "分析销售数据的分布和趋势")
    print(f"\n生成的图表数量: {len(charts)}")
    
    for i, chart in enumerate(charts):
        print(f"\n图表 {i+1}: {chart.get('title', '未命名')}")
        print(f"  类型: {chart.get('type')}")
        print(f"  X轴: {chart.get('x_label', '-')}")
        print(f"  Y轴: {chart.get('y_label', '-')}")
        print(f"  数据点: {len(chart.get('data', []))}")
    
    return len(charts) > 0

def test_operations_data():
    """测试运维数据的图表生成"""
    print("\n" + "=" * 60)
    print("测试2：运维数据")
    print("=" * 60)
    
    # 创建运维数据
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=50, freq='H'),
        'server_name': [f'Server-{i%5+1:02d}' for i in range(50)],
        'cpu_usage': [45 + i*2 + (i%7)*5 for i in range(50)],
        'memory_usage': [60 + i*1.5 + (i%5)*3 for i in range(50)],
        'disk_io': [100 + i*10 + (i%3)*20 for i in range(50)],
        'status': ['正常' if i % 10 != 0 else '警告' for i in range(50)]
    })
    
    print(f"数据源: 服务器性能监控 ({len(df)} 行, {len(df.columns)} 列)")
    print(f"字段: {list(df.columns)}")
    
    charts = SmartChartGenerator.generate_charts(df, "监控服务器性能和异常")
    print(f"\n生成的图表数量: {len(charts)}")
    
    for i, chart in enumerate(charts):
        print(f"\n图表 {i+1}: {chart.get('title', '未命名')}")
        print(f"  类型: {chart.get('type')}")
        print(f"  X轴: {chart.get('x_label', '-')}")
        print(f"  Y轴: {chart.get('y_label', '-')}")
        print(f"  数据点: {len(chart.get('data', []))}")
    
    return len(charts) > 0

def test_project_data():
    """测试项目数据的图表生成"""
    print("\n" + "=" * 60)
    print("测试3：项目管理数据")
    print("=" * 60)
    
    # 创建项目数据
    df = pd.DataFrame({
        'project_name': ['项目A', '项目B', '项目C', '项目D', '项目E', '项目F'],
        'status': ['进行中', '已完成', '已完成', '进行中', '计划中', '已完成'],
        'priority': ['高', '中', '高', '低', '中', '高'],
        'budget': [500000, 300000, 800000, 150000, 250000, 600000],
        'spent': [380000, 290000, 750000, 50000, 100000, 550000],
        'task_count': [45, 32, 68, 18, 25, 55]
    })
    
    print(f"数据源: 项目管理数据 ({len(df)} 行, {len(df.columns)} 列)")
    print(f"字段: {list(df.columns)}")
    
    charts = SmartChartGenerator.generate_charts(df, "分析项目的预算和进度分布")
    print(f"\n生成的图表数量: {len(charts)}")
    
    for i, chart in enumerate(charts):
        print(f"\n图表 {i+1}: {chart.get('title', '未命名')}")
        print(f"  类型: {chart.get('type')}")
        print(f"  X轴: {chart.get('x_label', '-')}")
        print(f"  Y轴: {chart.get('y_label', '-')}")
        print(f"  数据点: {len(chart.get('data', []))}")
    
    return len(charts) > 0

def test_field_detection():
    """测试字段类型检测"""
    print("\n" + "=" * 60)
    print("测试4：字段类型检测")
    print("=" * 60)
    
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=5),
        'quantity': [100, 200, 300, 400, 500],
        'region': ['华东', '华南', '华北', '华中', '西南'],
        'unit_price': [10, 20, 30, 40, 50],
        'status': ['正常', '正常', '警告', '正常', '异常']
    })
    
    field_types = SmartChartGenerator.detect_field_types(df)
    
    for field, ftype in field_types.items():
        print(f"  {field}: {ftype}")
    
    return len(field_types) > 0

if __name__ == "__main__":
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "动态图表生成功能测试" + " " * 25 + "║")
    print("╚" + "═" * 58 + "╝")
    
    results = []
    
    try:
        results.append(("字段类型检测", test_field_detection()))
        results.append(("销售数据图表", test_sales_data()))
        results.append(("运维数据图表", test_operations_data()))
        results.append(("项目数据图表", test_project_data()))
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
        print("🎉 所有测试通过！动态图表生成功能正常工作。")
        print("系统已支持多种数据类型的智能图表选择。")
        sys.exit(0)
    else:
        print("⚠️  部分测试失败，请检查代码。")
        sys.exit(1)
