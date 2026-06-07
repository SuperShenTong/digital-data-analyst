from app.tools.base_tool import BaseTool
from app.services.data_service import DataService
from sqlalchemy.orm import Session
import pandas as pd
import json

class DataReaderTool(BaseTool):
    name = "data_reader"
    description = "读取数据源中的数据，支持过滤、排序等操作"
    parameters = {
        "data_source_id": {"type": "integer", "description": "数据源ID", "required": True},
        "filter_conditions": {"type": "string", "description": "过滤条件（JSON格式）", "required": False},
        "sort_by": {"type": "string", "description": "排序字段", "required": False},
        "limit": {"type": "integer", "description": "返回行数限制", "required": False}
    }
    
    def __init__(self, db: Session):
        self.data_service = DataService(db)
    
    def execute(self, **kwargs):
        data_source_id = kwargs.get("data_source_id")
        filter_conditions = kwargs.get("filter_conditions")
        sort_by = kwargs.get("sort_by")
        limit = kwargs.get("limit")
        
        df = self.data_service.load_dataframe(data_source_id)
        
        if filter_conditions:
            try:
                conditions = json.loads(filter_conditions)
                for col, value in conditions.items():
                    if col in df.columns:
                        df = df[df[col] == value]
            except Exception as e:
                pass
        
        if sort_by and sort_by in df.columns:
            df = df.sort_values(by=sort_by)
        
        if limit:
            df = df.head(limit)
        
        return df.to_dict("records")

class StructureCheckTool(BaseTool):
    name = "structure_check"
    description = "检测数据源的结构信息，包括字段类型、空值统计、数据摘要等"
    parameters = {
        "data_source_id": {"type": "integer", "description": "数据源ID", "required": True}
    }
    
    def __init__(self, db: Session):
        self.data_service = DataService(db)
    
    def execute(self, **kwargs):
        data_source_id = kwargs.get("data_source_id")
        df = self.data_service.load_dataframe(data_source_id)
        
        column_info = []
        for col in df.columns:
            col_type = str(df[col].dtype)
            null_count = df[col].isnull().sum()
            null_percent = (null_count / len(df)) * 100 if len(df) > 0 else 0
            unique_count = df[col].nunique()
            
            column_info.append({
                "name": col,
                "type": col_type,
                "null_count": int(null_count),
                "null_percent": round(null_percent, 2),
                "unique_count": int(unique_count)
            })
        
        summary = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "column_info": column_info
        }
        
        return summary

class StatAnalysisTool(BaseTool):
    name = "stat_analysis"
    description = "对数值型字段进行统计分析，包括均值、中位数、标准差、最值等"
    parameters = {
        "data_source_id": {"type": "integer", "description": "数据源ID", "required": True},
        "target_columns": {"type": "string", "description": "目标字段列表（逗号分隔）", "required": False},
        "group_by": {"type": "string", "description": "分组字段", "required": False}
    }
    
    def __init__(self, db: Session):
        self.data_service = DataService(db)
    
    def execute(self, **kwargs):
        data_source_id = kwargs.get("data_source_id")
        target_columns = kwargs.get("target_columns")
        group_by = kwargs.get("group_by")
        
        df = self.data_service.load_dataframe(data_source_id)
        
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        if target_columns:
            cols = [c.strip() for c in target_columns.split(",")]
            target_cols = [c for c in cols if c in numeric_cols]
        else:
            target_cols = numeric_cols
        
        result = {}
        
        if group_by and group_by in df.columns:
            grouped = df.groupby(group_by)
            for col in target_cols:
                stats = grouped[col].agg(['mean', 'median', 'std', 'min', 'max', 'sum', 'count'])
                result[col] = stats.to_dict()
        else:
            for col in target_cols:
                result[col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "sum": float(df[col].sum()),
                    "count": int(df[col].count()),
                    "unique": int(df[col].nunique())
                }
        
        return result