from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import json

def custom_json_serializer(obj):
    """自定义JSON序列化器，处理特殊类型：bool, numpy数值, pandas对象等"""
    if isinstance(obj, bool):
        return obj
    if hasattr(obj, 'item'):  # numpy数值类型
        return obj.item()
    if hasattr(obj, 'to_dict'):  # pandas对象
        return obj.to_dict()
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (int, float, str, list, dict, type(None))):
        return obj
    try:
        return str(obj)
    except Exception:
        return f"<{type(obj).__name__}>"

def custom_json_dumps(obj, **kwargs):
    """自定义JSON序列化函数"""
    return json.dumps(obj, default=custom_json_serializer, ensure_ascii=False, **kwargs)

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/example_db.sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    json_serializer=custom_json_dumps
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    columns = Column(JSON)
    row_count = Column(Integer)
    size_bytes = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    analyses = relationship("AnalysisRecord", back_populates="data_source")

class AnalysisRecord(Base):
    __tablename__ = "analysis_records"
    
    id = Column(Integer, primary_key=True, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"))
    user_query = Column(Text, nullable=False)
    analysis_plan = Column(JSON)
    tool_calls = Column(JSON)
    final_result = Column(JSON)
    report_content = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.now)
    
    data_source = relationship("DataSource", back_populates="analyses")

class ToolCallLog(Base):
    __tablename__ = "tool_call_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_record_id = Column(Integer, ForeignKey("analysis_records.id"))
    tool_name = Column(String, nullable=False)
    input_params = Column(JSON)
    output_result = Column(JSON)
    execution_time_ms = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False)
    user_message = Column(Text, nullable=False)
    assistant_message = Column(Text)
    context = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()