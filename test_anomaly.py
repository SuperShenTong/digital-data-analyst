"""测试异常检测功能"""
import sys
sys.path.insert(0, r'E:\ShenTong\AI Course\digital-data-analyst_v1')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

db_path = r'E:\ShenTong\AI Course\digital-data-analyst_v1\data\example_db.sqlite'
engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db = Session()

# 加载数据
from app.services.data_service import DataService
data_service = DataService(db)

# 获取数据源3 - sales_transactions
source = data_service.get_data_source(3)
print(f"数据源: {source.name}")
print(f"字段: {source.columns}")

# 加载数据
df = data_service.load_dataframe(3)
print(f"数据行数: {len(df)}")
print(f"\n数据前5行:")
print(df.head())

# 检查数值型字段
numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
print(f"\n数值型字段: {numeric_cols}")

# 对每个数值字段进行异常检测
from app.tools.anomaly_tools import AnomalyDetectionTool
anomaly_tool = AnomalyDetectionTool(db)

print("\n=== 异常检测结果 ===")
total_anomalies = 0
for col in numeric_cols:
    try:
        result = anomaly_tool.execute(
            data_source_id=3,
            column_name=col,
            method="iqr"
        )
        anomalies = result.get("anomalies", [])
        status = result.get("status", "error")
        print(f"\n字段 {col}:")
        print(f"  状态: {status}")
        print(f"  异常数量: {len(anomalies)}")
        total_anomalies += len(anomalies)
        if anomalies:
            # 显示前3个异常
            for i, a in enumerate(anomalies[:3]):
                print(f"    [{i+1}] 类型={a.get('type')}, 值={a.get('value')}, 行={a.get('index')}")
    except Exception as e:
        print(f"  错误: {e}")

print(f"\n总计异常: {total_anomalies}")

# 查看数据的统计信息
print("\n=== 数据统计信息 ===")
for col in numeric_cols:
    series = df[col].dropna()
    if len(series) > 0:
        print(f"{col}: mean={series.mean():.2f}, std={series.std():.2f}, min={series.min():.2f}, max={series.max():.2f}")
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = series[(series < lower) | (series > upper)]
        print(f"  IQR范围: [{lower:.2f}, {upper:.2f}], 超出范围的数量: {len(outliers)}")
