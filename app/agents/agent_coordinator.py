from typing import Dict, Any, List, Optional
from app.agents.data_understanding_agent import DataUnderstandingAgent
from app.agents.data_analysis_agent import DataAnalysisAgent
from app.agents.report_generation_agent import ReportGenerationAgent
from app.services.context_service import ContextService
from sqlalchemy.orm import Session
from app.models.database import AnalysisRecord, ToolCallLog
from datetime import datetime
import json
import numpy as np
import pandas as pd


def sanitize_for_json(obj):
    """
    清理数据，确保可以被JSON序列化
    处理：numpy类型, pandas对象, 布尔值, 日期时间等
    """
    if obj is None:
        return None
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, (int, float, str)):
        return obj
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    if isinstance(obj, tuple):
        return [sanitize_for_json(item) for item in obj]
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    if isinstance(obj, pd.Series):
        return obj.tolist()
    if hasattr(obj, 'item') and callable(getattr(obj, 'item')):
        try:
            return obj.item()
        except Exception:
            pass
    # 对于其他类型，尝试转换为字符串
    try:
        return str(obj)
    except Exception:
        return None


class AgentCoordinator:
    def __init__(self, db: Session):
        self.db = db
        self.data_understanding_agent = DataUnderstandingAgent(db)
        self.data_analysis_agent = DataAnalysisAgent(db)
        self.report_generation_agent = ReportGenerationAgent(db)
        # 初始化上下文服务（多轮对话历史管理）
        self.context_service = ContextService()

    def execute_analysis(self, user_query: str, data_source_id: int, session_id: Optional[str] = None) -> Dict[str, Any]:
        # ============================================================
        # 多轮上下文：若提供了 session_id，则注入历史对话到 user_query
        # ============================================================
        effective_query = user_query
        if session_id:
            effective_query = self.context_service.build_contextual_query(user_query, session_id)

        analysis_record = AnalysisRecord(
            data_source_id=data_source_id,
            user_query=user_query,
            status="in_progress",
            created_at=datetime.now()
        )
        self.db.add(analysis_record)
        self.db.commit()
        self.db.refresh(analysis_record)

        try:
            context = {
                "data_source_id": data_source_id,
                "user_query": user_query,
                "session_id": session_id,
                "analysis_record_id": analysis_record.id,
                "effective_query": effective_query
            }

            print(f"Step 1: Calling DataUnderstandingAgent with query: {effective_query}")
            # 使用带上下文的 effective_query 调用"意图理解"Agent
            understanding_result = self.data_understanding_agent.execute(effective_query, context)
            print(f"Step 1 result keys: {list(understanding_result.keys())}")
            print(f"Step 1 intent: {understanding_result.get('intent')}")
            print(f"Step 1 intent_category: {understanding_result.get('intent_category')}")
            print(f"Step 1 required_fields: {understanding_result.get('required_fields')}")
            print(f"Step 1 analysis_steps: {understanding_result.get('analysis_steps')}")
            
            if "error" in understanding_result:
                analysis_record.status = "failed"
                analysis_record.final_result = {"error": understanding_result["error"]}
                self.db.commit()
                return understanding_result
            
            # 将理解结果作为分析计划
            analysis_plan = {
                "intent": understanding_result.get("intent", ""),
                "intent_category": understanding_result.get("intent_category", ""),
                "required_fields": understanding_result.get("required_fields", []),
                "analysis_steps": understanding_result.get("analysis_steps", []),
                "complexity_level": understanding_result.get("complexity_level", "simple"),
                "preprocessing_needed": understanding_result.get("preprocessing_needed", False),
                "requires_followup": understanding_result.get("requires_followup", False),
                "description": understanding_result.get("description", "")
            }
            print(f"Step 2: Analysis plan: {analysis_plan}")
            analysis_record.analysis_plan = sanitize_for_json(analysis_plan)
            self.db.commit()
            
            context["analysis_plan"] = analysis_plan
            
            print(f"Step 3: Calling DataAnalysisAgent with context keys: {list(context.keys())}")
            analysis_result = self.data_analysis_agent.execute(user_query, context)
            print(f"Step 3 result keys: {list(analysis_result.keys())}")
            
            if "error" in analysis_result:
                analysis_record.status = "failed"
                analysis_record.final_result = sanitize_for_json({"error": analysis_result["error"]})
                self.db.commit()
                return analysis_result
            
            context["analysis_results"] = analysis_result
            
            print(f"Step 4: Calling ReportGenerationAgent")
            report_result = self.report_generation_agent.execute(user_query, context)
            print(f"Step 4 result keys: {list(report_result.keys())}")
            
            if "error" in report_result:
                analysis_record.status = "failed"
                analysis_record.final_result = sanitize_for_json({"error": report_result["error"]})
                self.db.commit()
                return report_result
            
            tool_calls = []
            for tool_result in analysis_result.get("tool_results", []):
                tool_log = ToolCallLog(
                    analysis_record_id=analysis_record.id,
                    tool_name=tool_result["tool_name"],
                    input_params=sanitize_for_json(tool_result["parameters"]),
                    output_result=sanitize_for_json(tool_result["result"]),
                    execution_time_ms=tool_result["execution_time_ms"],
                    timestamp=datetime.now()
                )
                self.db.add(tool_log)
                tool_calls.append({
                    "tool_name": tool_result["tool_name"],
                    "input_params": sanitize_for_json(tool_result["parameters"]),
                    "output_result": sanitize_for_json(tool_result["result"]),
                    "execution_time_ms": tool_result["execution_time_ms"]
                })
            
            analysis_record.tool_calls = sanitize_for_json(tool_calls)
            analysis_record.final_result = sanitize_for_json({
                "statistics": analysis_result.get("statistics"),
                "anomalies": analysis_result.get("anomalies"),
                "charts": analysis_result.get("charts", []),
                "summary": analysis_result.get("summary")
            })
            analysis_record.report_content = report_result.get("report_content", "")
            analysis_record.status = "completed"
            self.db.commit()

            # ============================================================
            # 多轮上下文：把本次分析结果保存到 ContextService，供后续追问使用
            # ============================================================
            if session_id:
                self.context_service.save_context(session_id, {
                    "user_query": user_query,
                    "data_source_id": data_source_id,
                    "analysis_plan": analysis_plan,
                    "analysis_results": analysis_result.get("final_result") or analysis_result,
                    "analysis_id": analysis_record.id,
                    "intent": understanding_result.get("intent", ""),
                    "intent_category": understanding_result.get("intent_category", "")
                })

            # 关键改进：现在图表由报告生成代理使用 EnhancedChartGenerator 智能生成
            # EnhancedChartGenerator 的流程：
            # 1. 读取原始数据和分析结果（异常数据、统计数据）
            # 2. 调用 LLM 分析：是否需要图表？需要什么类型的图表？
            # 3. LLM 返回图表配置（如果需要）
            # 4. 为 LLM 推荐的图表填充实际数据
            # 5. 额外生成异常可视化图表（如果有异常数据）
            # 所以优先使用报告生成代理返回的图表（更智能）
            final_charts = report_result.get("charts", [])
            
            # 如果报告生成代理没有返回图表，回退到分析代理的图表
            if not final_charts:
                final_charts = analysis_result.get("charts", [])

            return {
                "analysis_id": analysis_record.id,
                "user_query": user_query,
                "data_source_id": data_source_id,
                "session_id": session_id,
                "analysis_plan": analysis_plan,
                "tool_calls": tool_calls,
                "statistics": analysis_result.get("statistics"),
                "anomalies": analysis_result.get("anomalies"),
                "report_content": report_result.get("report_content", ""),
                "summary": report_result.get("summary", analysis_result.get("summary", "")),
                "charts": final_charts,
                "created_at": analysis_record.created_at.isoformat(),
                "intent": understanding_result.get("intent", ""),
                "intent_category": understanding_result.get("intent_category", ""),
                "llm_source": understanding_result.get("llm_source", "fallback")
            }
        
        except Exception as e:
            analysis_record.status = "failed"
            analysis_record.final_result = {"error": str(e)}
            self.db.commit()
            return {"error": str(e)}
    
    def get_analysis_history(self, data_source_id: Optional[int] = None) -> List[Dict[str, Any]]:
        query = self.db.query(AnalysisRecord)
        if data_source_id:
            query = query.filter(AnalysisRecord.data_source_id == data_source_id)
        
        records = query.order_by(AnalysisRecord.created_at.desc()).all()
        
        return [{
            "id": r.id,
            "data_source_id": r.data_source_id,
            "user_query": r.user_query,
            "status": r.status,
            "created_at": r.created_at.isoformat()
        } for r in records]
    
    def get_analysis_detail(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        record = self.db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()
        if not record:
            return None
        
        tool_logs = self.db.query(ToolCallLog).filter(ToolCallLog.analysis_record_id == analysis_id).all()
        
        return {
            "id": record.id,
            "data_source_id": record.data_source_id,
            "user_query": record.user_query,
            "analysis_plan": record.analysis_plan,
            "tool_calls": [
                {
                    "tool_name": t.tool_name,
                    "input_params": t.input_params,
                    "output_result": t.output_result,
                    "execution_time_ms": t.execution_time_ms,
                    "timestamp": t.timestamp.isoformat()
                } for t in tool_logs
            ],
            "final_result": record.final_result,
            "report_content": record.report_content,
            "status": record.status,
            "created_at": record.created_at.isoformat()
        }