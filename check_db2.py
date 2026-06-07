"""检查数据库中的数据源列表 - 使用正确的路径"""
import sys
sys.path.insert(0, r'E:\ShenTong\AI Course\digital-data-analyst_v1')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# 使用正确的数据库路径
db_path = r'E:\ShenTong\AI Course\digital-data-analyst_v1\data\example_db.sqlite'
print(f"连接数据库: {db_path}")
print(f"文件存在: {os.path.exists(db_path)}")

try:
    engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    db = Session()
    
    from app.models.database import DataSource, Base
    Base.metadata.create_all(engine)
    
    sources = db.query(DataSource).all()
    print(f"\n数据源列表 (共 {len(sources)} 个):")
    for s in sources:
        print(f"  [{s.id}] {s.name}")
        print(f"      文件: {s.filename}")
        print(f"      行数: {s.row_count}")
        print(f"      类型: {s.file_type}")
        print(f"      列: {s.columns}")
        print()
    
    if not sources:
        print("  (数据库为空！请先通过前端上传数据)")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
