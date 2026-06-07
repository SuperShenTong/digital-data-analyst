from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.data_service import DataService
from app.agents.agent_coordinator import AgentCoordinator
from app.models.schemas import DataSourceInfo, DataPreview, AnalysisRequest, AnalysisResult, MessageRequest, MessageResponse
from typing import List

router = APIRouter()

@router.post("/data/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    allowed_types = ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                    "application/vnd.ms-excel", 
                    "text/csv"]
    
    if file.content_type not in allowed_types and not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    
    try:
        data_service = DataService(db)
        file_path = data_service.save_uploaded_file(file)
        parsed = data_service.parse_file(file_path)
        
        data_source = data_service.save_data_source(
            name=file.filename.split(".")[0],
            filename=file.filename,
            filepath=file_path,
            file_type="excel" if file.filename.endswith(".xlsx") else "csv",
            columns=parsed["columns"],
            row_count=parsed["row_count"],
            size_bytes=len(file.file.read()) if hasattr(file.file, 'read') else 0
        )
        
        return {
            "id": data_source.id,
            "name": data_source.name,
            "filename": data_source.filename,
            "columns": parsed["columns"],
            "row_count": parsed["row_count"],
            "message": "文件上传成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/sources", response_model=List[DataSourceInfo])
async def get_data_sources(db: Session = Depends(get_db)):
    data_service = DataService(db)
    return data_service.get_all_data_sources()

@router.get("/data/sources/{data_source_id}", response_model=DataSourceInfo)
async def get_data_source(data_source_id: int, db: Session = Depends(get_db)):
    data_service = DataService(db)
    try:
        return data_service.get_data_source(data_source_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/data/sources/{data_source_id}/preview", response_model=DataPreview)
async def get_data_preview(data_source_id: int, sample_size: int = 10, db: Session = Depends(get_db)):
    data_service = DataService(db)
    try:
        return data_service.get_data_preview(data_source_id, sample_size)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/data/sources/{data_source_id}")
async def delete_data_source(data_source_id: int, db: Session = Depends(get_db)):
    data_service = DataService(db)
    try:
        data_service.delete_data_source(data_source_id)
        return {"message": "数据源删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/analysis/execute")
async def execute_analysis(request: AnalysisRequest, db: Session = Depends(get_db)):
    coordinator = AgentCoordinator(db)
    result = coordinator.execute_analysis(request.user_query, request.data_source_id, request.session_id)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.get("/analysis/history")
async def get_analysis_history(data_source_id: int = None, db: Session = Depends(get_db)):
    coordinator = AgentCoordinator(db)
    return coordinator.get_analysis_history(data_source_id)

@router.get("/analysis/{analysis_id}")
async def get_analysis_detail(analysis_id: int, db: Session = Depends(get_db)):
    coordinator = AgentCoordinator(db)
    result = coordinator.get_analysis_detail(analysis_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="分析记录未找到")
    
    return result

# ============================================================
# 多轮上下文追问：基于 session_id 的上下文分析
# ============================================================
@router.post("/analysis/followup")
async def followup_analysis(request: AnalysisRequest, db: Session = Depends(get_db)):
    """
    基于会话历史的追问分析。
    会把 session_id 对应的历史对话注入到本次查询中。
    """
    if not request.session_id:
        raise HTTPException(status_code=400, detail="session_id is required for followup")

    coordinator = AgentCoordinator(db)
    result = coordinator.execute_analysis(
        user_query=request.user_query,
        data_source_id=request.data_source_id,
        session_id=request.session_id
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.get("/analysis/sessions/{session_id}")
async def get_session_context(session_id: str, db: Session = Depends(get_db)):
    """
    获取指定 session_id 的完整上下文（包含历史对话）。
    """
    from app.services.context_service import ContextService

    ctx_service = ContextService()
    # 使用 get_session 方法获取会话信息
    session = ctx_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return session


# ============================================================
# 执行过程可观测性：执行追踪、工具调用摘要、执行报告导出
# ============================================================
@router.get("/analysis/{analysis_id}/trace")
async def get_analysis_trace(analysis_id: int, db: Session = Depends(get_db)):
    """获取指定分析任务的执行追踪。"""
    from app.services.observability_service import ObservabilityService

    obs = ObservabilityService(db)
    return obs.get_execution_trace(str(analysis_id))


@router.get("/analysis/{analysis_id}/tools")
async def get_analysis_tools(analysis_id: int, db: Session = Depends(get_db)):
    """获取指定分析任务的工具调用摘要。"""
    from app.services.observability_service import ObservabilityService

    obs = ObservabilityService(db)
    return obs.get_tool_calls_summary(str(analysis_id))


@router.get("/analysis/{analysis_id}/export")
async def export_analysis_report(analysis_id: int, db: Session = Depends(get_db)):
    """导出指定分析任务的完整执行报告（Markdown 格式）。"""
    from app.services.observability_service import ObservabilityService

    obs = ObservabilityService(db)
    report = obs.export_execution_report(str(analysis_id))

    return {
        "analysis_id": analysis_id,
        "format": "markdown",
        "report": report
    }


# ============================================================
# 聊天消息（增强版）：与 ContextService 联动
# ============================================================
@router.post("/chat/message")
async def chat_message(request: MessageRequest, db: Session = Depends(get_db)):
    from app.models.database import Conversation
    from app.services.context_service import ContextService
    from datetime import datetime

    conversation = Conversation(
        session_id=request.session_id,
        user_message=request.message,
        created_at=datetime.now()
    )
    db.add(conversation)

    # 查询数据库中的历史对话
    data_sources = db.query(Conversation).filter(
        Conversation.session_id == request.session_id
    ).all()

    # 也从 ContextService 读取上下文
    ctx_service = ContextService()
    service_ctx = ctx_service.get_session(request.session_id)

    history = []
    # 从数据库构建历史
    history.extend([
        {"user": c.user_message, "assistant": c.assistant_message}
        for c in data_sources[:-1]
    ])

    # 从 ContextService 添加分析结果
    if service_ctx and service_ctx.get("analysis_results"):
        for a in service_ctx["analysis_results"]:
            history.append({
                "user": a.get("user_query", ""),
                "assistant": f"分析结果: {a.get('intent', '')[:50]}"
            })

    context = {
        "history": history,
        "analysis_results": service_ctx.get("analysis_results", []) if service_ctx else [],
        "session_id": request.session_id
    }

    # 如果历史中包含了分析结果，给出更智能的回复
    reply_base = "我来帮您分析这个问题。请告诉我您想要分析哪个数据源？"
    if service_ctx and service_ctx.get("analysis_results"):
        latest = service_ctx["analysis_results"][-1]
        prev_intent = latest.get("intent_category", "")
        if prev_intent:
            reply_base = f"您之前进行了「{prev_intent}」分析，这次希望了解什么？请告诉我。"

    conversation.assistant_message = reply_base
    db.commit()

    return MessageResponse(
        session_id=request.session_id,
        response=reply_base,
        context=context,
        created_at=datetime.now()
    )

@router.get("/tools/list")
async def get_tools_list():
    from app.tools.data_tools import DataReaderTool, StructureCheckTool, StatAnalysisTool
    from app.tools.anomaly_tools import AnomalyDetectionTool
    from app.tools.chart_tools import ChartGeneratorTool
    from app.tools.report_tools import ReportGeneratorTool
    
    return {
        "tools": [
            DataReaderTool.get_schema.__func__(None),
            StructureCheckTool.get_schema.__func__(None),
            StatAnalysisTool.get_schema.__func__(None),
            AnomalyDetectionTool.get_schema.__func__(None),
            ChartGeneratorTool.get_schema.__func__(None),
            ReportGeneratorTool.get_schema.__func__(None)
        ]
    }