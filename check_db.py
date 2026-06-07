"""检查数据库中的数据源列表"""
import sys
sys.path.insert(0, r'E:\ShenTong\AI Course\digital-data-analyst_v1')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 查找数据库文件
import os
for root, dirs, files in os.walk(r'E:\ShenTong\AI Course\digital-data-analyst_v1'):
    for f in files:
        if f.endswith('.db') or f.endswith('.sqlite'):
            print(f"找到数据库: {os.path.join(root, f)}")

# 使用默认路径
db_path = r'E:\ShenTong\AI Course\digital-data-analyst_v1\data_sources.db'
print(f"\n尝试连接: {db_path}")

try:
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    db = Session()
    
    from app.models.database import DataSource, Base
    Base.metadata.create_all(engine)
    
    sources = db.query(DataSource).all()
    print(f"\n数据源列表 (共 {len(sources)} 个):")
    for s in sources:
        print(f"  [{s.id}] {s.name} - {s.filename} ({s.row_count}行, {s.file_type})")
        print(f"      列: {s.columns}")
    
    if not sources:
        print("  (数据库为空，需要上传数据)")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
