"""
测试分析流程的完整脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from app.agents.agent_coordinator import AgentCoordinator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 创建测试数据库会话
engine = create_engine('sqlite:///:memory:')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# 创建测试数据
test_data = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=30, freq='D'),
    'product': ['A', 'B', 'C'] * 10,
    'region': ['East', 'South', 'West'] * 10,
    'quantity': [10, 20, 15, 12, 25, 18, 8, 30, 14, 16] * 3,
    'unit_price': [100.0, 200.0, 150.0] * 10,
    'amount': [1000, 4000, 2250, 1200, 5000, 2700, 800, 6000, 2100, 1600] * 3
})

# 保存测试数据
test_data.to_csv('test_analysis.csv', index=False)

print("测试数据已创建")
print(f"数据行数: {len(test_data)}")
print(f"字段: {list(test_data.columns)}")
print("\n前5行数据:")
print(test_data.head())

# 测试分析流程
print("\n" + "="*50)
print("测试分析流程")
print("="*50)

try:
    # 创建一个模拟的协调器
    coordinator = AgentCoordinator(db)
    
    print("✅ 协调器初始化成功")
    
except Exception as e:
    print(f"❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试图表生成器
print("\n测试图表生成器...")
try:
    from app.services.enhanced_chart_generator import EnhancedChartGenerator
    
    generator = EnhancedChartGenerator()
    charts = generator.generate_charts(
        df=test_data,
        user_query="分析销售数据",
        data_source_name="测试数据"
    )
    
    print(f"✅ 图表生成成功")
    print(f"   生成图表数量: {len(charts)}")
    for i, chart in enumerate(charts):
        print(f"   [{i+1}] {chart.get('type')} - {chart.get('title')}")
        
except Exception as e:
    print(f"❌ 图表生成失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("测试完成")
print("="*50)
