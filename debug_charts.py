"""诊断：检查异常图表的数据生成问题"""
import sys
sys.path.insert(0, r'E:\ShenTong\AI Course\digital-data-analyst_v1')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

db_path = r'E:\ShenTong\AI Course\digital-data-analyst_v1\data\example_db.sqlite'
engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db = Session()

from app.services.enhanced_chart_generator import EnhancedChartGenerator
from app.agents.data_analysis_agent import DataAnalysisAgent

generator = EnhancedChartGenerator()
agent = DataAnalysisAgent(db)

print("=" * 60)
print("诊断1：执行数据分析代理")
print("=" * 60)

# 执行分析，获取异常数据
result = agent.execute(
    task="分析销售数据是否存在异常",
    context={"data_source_id": 3, "user_query": "分析销售数据是否存在异常"}
)

anomalies = result.get("anomalies", [])
print(f"\n异常数据: {len(anomalies)}个")
for i, a in enumerate(anomalies):
    print(f"  [{i+1}] column={a.get('column')}, type={a.get('type')}, count={a.get('count')}, severity={a.get('severity')}")
    print(f"       description={str(a.get('description', ''))[:80]}")

print("\n" + "=" * 60)
print("诊断2：加载原始数据")
print("=" * 60)

from app.services.data_service import DataService
data_service = DataService(db)
df = data_service.load_dataframe(3)
print(f"数据行数: {len(df)}")
print(f"数据列: {list(df.columns)}")
print(f"\n前5行数据:")
print(df.head())

# 检查字段类型
print(f"\n字段类型:")
for col in df.columns:
    is_numeric = pd.api.types.is_numeric_dtype(df[col])
    is_datetime = pd.api.types.is_datetime64_any_dtype(df[col])
    print(f"  {col}: numeric={is_numeric}, datetime={is_datetime}, dtype={df[col].dtype}")

print("\n" + "=" * 60)
print("诊断3：测试时间字段识别")
print("=" * 60)

date_col = None
for col in df.columns:
    if "date" in col.lower() or "time" in col.lower() or "日期" in col:
        try:
            test_dates = pd.to_datetime(df[col].head(5))
            print(f"发现时间字段: {col}")
            print(f"  示例值: {df[col].head(3).tolist()}")
            date_col = col
            break
        except Exception as e:
            print(f"  {col} 尝试转换失败: {e}")
            continue

if not date_col:
    print("❌ 未找到时间字段")
else:
    print(f"✅ 时间字段: {date_col}")

# 检查 anomaly_fields 中的字段
print(f"\n检查异常字段是否数值类型:")
for a in anomalies:
    field = a.get("column", "")
    if field:
        is_num = pd.api.types.is_numeric_dtype(df[field]) if field in df.columns else False
        print(f"  {field}: 数值类型={is_num}, 存在={field in df.columns}")

print("\n" + "=" * 60)
print("诊断4：直接测试_generate_anomaly_visualization_charts")
print("=" * 60)

analysis_results = {"anomalies": anomalies}
charts = generator._generate_anomaly_visualization_charts(df, analysis_results)
print(f"\n生成的图表数量: {len(charts)}")

for i, chart in enumerate(charts):
    print(f"\n图表 [{i+1}]:")
    print(f"  type: {chart.get('type')}")
    print(f"  title: {chart.get('title')}")
    print(f"  x_label: {chart.get('x_label')}")
    print(f"  y_label: {chart.get('y_label')}")
    print(f"  data点数: {len(chart.get('data', []))}")
    if chart.get('data'):
        print(f"  data前3个: {chart['data'][:3]}")
    if chart.get('mark_points'):
        print(f"  mark_points数量: {len(chart['mark_points'])}")
        print(f"  mark_points前3个: {chart['mark_points'][:3]}")

print("\n" + "=" * 60)
print("诊断5：测试异常类型分布的数据准备")
print("=" * 60)

anomaly_types = {}
for a in anomalies:
    t = a.get("type", "未知类型")
    if t:
        anomaly_types[t] = anomaly_types.get(t, 0) + a.get("count", 1)

print(f"异常类型统计: {anomaly_types}")
if anomaly_types:
    anomaly_chart_data = [{"name": k, "value": v} for k, v in 
                          sorted(anomaly_types.items(), key=lambda x: x[1], reverse=True)[:8]]
    print(f"异常类型图表数据: {anomaly_chart_data}")

# 测试时序图数据
print(f"\n" + "=" * 60)
print("诊断6：测试时序图数据准备")
print("=" * 60)

if date_col and anomalies:
    field = anomalies[0].get("column", "")
    if field and field in df.columns and pd.api.types.is_numeric_dtype(df[field]):
        print(f"\n字段: {field}")
        series = df[field].dropna()
        print(f"有效值: {len(series)}")
        
        temp_df = df[[date_col, field]].dropna().head(100)
        print(f"temp_df行数: {len(temp_df)}")
        
        if len(temp_df) > 5:
            x_data = [str(x)[:10] for x in temp_df[date_col].tolist()]
            y_data = temp_df[field].tolist()
            print(f"x_data前5个: {x_data[:5]}")
            print(f"y_data前5个: {y_data[:5]}")
            
            mean_val = series.mean()
            std_val = series.std() if series.std() > 0 else 1
            print(f"mean={mean_val}, std={std_val}")
            
            mark_points = []
            for i, (idx, row) in enumerate(temp_df.iterrows()):
                value = row[field]
                z_score = abs((value - mean_val) / std_val) if std_val > 0 else 0
                if z_score > 2.5:
                    mark_points.append({
                        "xAxis": i,
                        "yAxis": float(value),
                        "value": float(value)
                    })
            print(f"标记异常点数: {len(mark_points)}")
        else:
            print(f"❌ temp_df数据不足5行")
