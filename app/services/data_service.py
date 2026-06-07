import os
import pandas as pd
from sqlalchemy.orm import Session
from app.models.database import DataSource
from app.models.schemas import DataSourceInfo, DataPreview
from app.utils.logger import setup_logger

logger = setup_logger()

DATA_DIR = os.environ.get("DATA_DIR", "data")

class DataService:
    def __init__(self, db: Session):
        self.db = db
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def save_uploaded_file(self, file) -> str:
        filename = os.path.basename(file.filename)
        file_path = os.path.join(DATA_DIR, filename)
        content = file.file.read()
        try:
            content.decode('utf-8')
        except UnicodeDecodeError:
            content = content.decode('gbk', errors='replace').encode('utf-8')
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path
    
    def parse_file(self, file_path: str):
        try:
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path, encoding='utf-8')
            elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file type")
            
            columns = df.columns.tolist()
            row_count = len(df)
            column_types = {col: str(df[col].dtype) for col in columns}
            
            return {
                "dataframe": df,
                "columns": columns,
                "column_types": column_types,
                "row_count": row_count
            }
        except Exception as e:
            logger.error(f"Error parsing file: {e}")
            raise
    
    def save_data_source(self, name: str, filename: str, filepath: str, file_type: str, columns: list, row_count: int, size_bytes: int):
        data_source = DataSource(
            name=name,
            filename=filename,
            filepath=filepath,
            file_type=file_type,
            columns=columns,
            row_count=row_count,
            size_bytes=size_bytes
        )
        self.db.add(data_source)
        self.db.commit()
        self.db.refresh(data_source)
        return data_source
    
    def get_data_source(self, data_source_id: int) -> DataSourceInfo:
        data_source = self.db.query(DataSource).filter(DataSource.id == data_source_id).first()
        if not data_source:
            raise ValueError(f"DataSource with id {data_source_id} not found")
        return DataSourceInfo(
            id=data_source.id,
            name=data_source.name,
            filename=data_source.filename,
            file_type=data_source.file_type,
            columns=data_source.columns,
            row_count=data_source.row_count,
            size_bytes=data_source.size_bytes,
            created_at=data_source.created_at
        )
    
    def get_all_data_sources(self) -> list[DataSourceInfo]:
        sources = self.db.query(DataSource).all()
        return [
            DataSourceInfo(
                id=s.id,
                name=s.name,
                filename=s.filename,
                file_type=s.file_type,
                columns=s.columns,
                row_count=s.row_count,
                size_bytes=s.size_bytes,
                created_at=s.created_at
            ) for s in sources
        ]
    
    def get_data_preview(self, data_source_id: int, sample_size: int = 10) -> DataPreview:
        data_source = self.db.query(DataSource).filter(DataSource.id == data_source_id).first()
        if not data_source:
            raise ValueError(f"DataSource with id {data_source_id} not found")
        
        parsed = self.parse_file(data_source.filepath)
        df = parsed["dataframe"]
        preview_rows = df.head(sample_size).to_dict("records")
        
        return DataPreview(
            columns=parsed["columns"],
            rows=preview_rows,
            row_count=parsed["row_count"],
            sample_size=sample_size
        )
    
    def load_dataframe(self, data_source_id: int) -> pd.DataFrame:
        data_source = self.db.query(DataSource).filter(DataSource.id == data_source_id).first()
        if not data_source:
            raise ValueError(f"DataSource with id {data_source_id} not found")
        return self.parse_file(data_source.filepath)["dataframe"]
    
    def delete_data_source(self, data_source_id: int):
        data_source = self.db.query(DataSource).filter(DataSource.id == data_source_id).first()
        if not data_source:
            raise ValueError(f"DataSource with id {data_source_id} not found")
        
        if os.path.exists(data_source.filepath):
            os.remove(data_source.filepath)
        
        self.db.delete(data_source)
        self.db.commit()