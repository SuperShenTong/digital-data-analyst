"""测试完整分析流程 - 使用 sales_transactions 数据源"""
import sys
sys.path.insert(0, r'E:\ShenTong\AI Course\digital-data-analyst_v1')

import time
start = time.time()

# 1. 测试加载数据
print("=" * 50)
print("1. 测试数据加载")
print("=" * 50)

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine('sqlite:///E:/ShenTong/AI Course/digital-data-analyst_v1/data/example_db.sqlite',
                          connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    db = Session()
    
    from app.models.database import DataSource
    source = db.query(DataSource).filter(DataSource.id == 3).first()
    print(f"数据源名称: {source.name}")
    print(f"文件路径: {source.filepath}")
    print(f"行数: {source.row_count}")
    print(f"列: {source.columns}")
    print(f"✅ 数据加载成功")
except Exception as e:
    print(f"❌ 数据加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. 测试数据分析代理
print("\n" + "=" * 50)
print("2. 测试数据分析代理")
print("=" * 50)

try:
    from app.agents.data_analysis_agent import DataAnalysisAgent
    
    agent = DataAnalysisAgent(db)
    
    result = agent.execute(
        task="分析销售数据是否有异常",
        context={
            "data_source_id": 3,
            "user_query": "分析销售数据是否有异常",
            "language": "zh"
        }
    )
    
    print(f"✅ 分析代理执行成功")
    print(f"   摘要: {result.get('summary', 'N/A')}")
    print(f"   统计信息: {len(result.get('statistics', {}))} 个指标")
    print(f"   异常信息: {len(result.get('anomalies', []))} 个异常")
    print(f"   图表: {len(result.get('charts', []))} 个")
    
except Exception as e:
    print(f"❌ 分析代理失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 测试报告生成代理
print("\n" + "=" * 50)
print("3. 测试报告生成代理")
print("=" * 50)

try:
    from app.agents.report_generation_agent import ReportGenerationAgent
    
    report_agent = ReportGenerationAgent(db)
    
    report_result = report_agent.execute(
        task="生成分析报告",
        context={
            "data_source_id": 3,
            "analysis_results": result,
            "user_query": "分析销售数据是否有异常",
            "language": "zh"
        }
    )
    
    print(f"✅ 报告生成成功")
    print(f"   报告长度: {len(report_result.get('report_content', ''))} 字")
    print(f"   图表数量: {len(report_result.get('charts', []))} 个")
    print(f"   摘要: {report_result.get('summary', 'N/A')}")
    
except Exception as e:
    print(f"❌ 报告生成失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. 测试协调器
print("\n" + "=" * 50)
print("4. 测试协调器完整流程")
print("=" * 50)

try:
    from app.agents.agent_coordinator import AgentCoordinator
    
    coordinator = AgentCoordinator(db)
    
    final_result = coordinator.coordinate_analysis(
        data_source_id=3,
        user_query="分析销售数据是否有异常"
    )
    
    print(f"✅ 协调器执行成功")
    print(f"   状态: {final_result.get('status', 'N/A')}")
    print(f"   分析ID: {final_result.get('analysis_id', 'N/A')}")
    print(f"   图表数量: {len(final_result.get('charts', []))} 个")
    print(f"   报告长度: {len(final_result.get('report_content', ''))} 字")
    
except Exception as e:
    print(f"❌ 协调器失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

elapsed = time.time() - start
print(f"\n{'=' * 50}")
print(f"✅ 所有测试通过！总用时: {elapsed:.1f}秒")
print(f"{'=' * 50}")
