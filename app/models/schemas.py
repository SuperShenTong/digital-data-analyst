from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Any, Dict


# ============================================================
# 数据源相关
# ============================================================
class DataSourceInfo(BaseModel):
    id: int
    name: str
    filename: str
    file_type: str
    columns: List[str]
    row_count: int
    size_bytes: int
    created_at: datetime


class DataPreview(BaseModel):
    columns: List[str]
    rows: List[dict]
    row_count: int
    sample_size: int = 10


# ============================================================
# 分析请求与计划
# ============================================================
class AnalysisRequest(BaseModel):
    data_source_id: int
    user_query: str
    session_id: Optional[str] = None


class AnalysisStep(BaseModel):
    """多步骤任务规划中单个步骤的结构化定义"""
    step_id: str
    description: str
    tool: str
    dependencies: Optional[List[str]] = []
    priority: Optional[str] = "medium"
    fields: Optional[List[str]] = []
    is_validation: Optional[bool] = False


class AnalysisPlan(BaseModel):
    """支持多步骤任务规划的分析计划"""
    steps: List[Dict[str, Any]]
    required_fields: List[str]
    description: str
    complexity_level: Optional[str] = "medium"
    preprocessing_needed: Optional[bool] = False
    preprocessing_description: Optional[str] = ""


# ============================================================
# 工具调用与结果
# ============================================================
class ToolCall(BaseModel):
    tool_name: str
    input_params: dict
    output_result: Optional[Any] = None
    execution_time_ms: Optional[int] = None


class AnalysisResult(BaseModel):
    user_query: str
    data_source_id: int
    analysis_plan: AnalysisPlan
    tool_calls: List[ToolCall]
    final_result: dict
    report_content: str
    created_at: datetime


class ChartData(BaseModel):
    chart_type: str
    title: str
    x_data: List[Any]
    y_data: List[Any]
    labels: Optional[List[str]] = None
    series: Optional[List[dict]] = None
    chart_explanation: Optional[str] = ""


class AnomalyDetectionResult(BaseModel):
    anomaly_type: str
    detected_at: str
    value: float
    expected_range: Optional[List[float]] = None
    severity: str
    description: str
    recommendation: str
    impact_scope: Optional[str] = ""
    basis: Optional[str] = ""


# ============================================================
# 上下文/会话相关
# ============================================================
class ContextEntry(BaseModel):
    """单个历史分析记录，用于多轮追问"""
    user_query: str
    data_source_id: Optional[int] = None
    analysis_plan: Optional[Dict[str, Any]] = None
    analysis_results: Optional[Dict[str, Any]] = None
    intent: Optional[str] = ""
    intent_category: Optional[str] = ""
    timestamp: Optional[float] = None


class SessionContext(BaseModel):
    """会话完整上下文信息"""
    session_id: str
    history: List[ContextEntry]
    message_count: int
    created_at: float
    updated_at: float


# ============================================================
# 可观测性相关
# ============================================================
class ExecutionStepLog(BaseModel):
    """单个执行步骤记录"""
    step_id: str
    analysis_id: str
    step_name: str
    status: str
    data: Optional[Dict[str, Any]] = {}
    timestamp: float
    datetime: str


class ExecutionTrace(BaseModel):
    """完整执行追踪"""
    analysis_id: str
    total_steps: int
    duration_ms: int
    logged_steps: List[ExecutionStepLog]
    tool_calls_from_db: List[Dict[str, Any]] = []
    database_record: Optional[Dict[str, Any]] = None


class ToolCallsSummary(BaseModel):
    """工具调用摘要"""
    analysis_id: str
    total_tool_calls: int
    failed_calls: int
    success_rate: float
    total_execution_ms: int
    by_tool: Dict[str, Dict[str, Any]]


# ============================================================
# 聊天相关
# ============================================================
class MessageRequest(BaseModel):
    session_id: str
    message: str


class MessageResponse(BaseModel):
    session_id: str
    response: str
    context: dict
    created_at: datetime