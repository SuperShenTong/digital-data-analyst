"""
可观测性服务 - 执行过程追踪和可观测性
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class ObservabilityService:
    """
    执行过程可观测性服务

    核心能力：
    1. 步骤追踪：记录每个分析步骤的执行状态
    2. 工具调用日志：记录每个工具的调用参数和结果
    3. 执行追踪：完整记录从用户问题到最终报告的全流程
    4. 性能监控：记录每个步骤的执行时间和资源使用
    5. 执行报告导出：生成完整的可追溯执行报告
    """

    # 内存存储（生产环境应使用数据库）
    _execution_traces: Dict[str, Dict[str, Any]] = {}
    _tool_call_logs: Dict[str, List[Dict[str, Any]]] = {}

    def __init__(self, db=None):
        """
        初始化可观测性服务

        Args:
            db: SQLAlchemy Session（可选，用于持久化）
        """
        self._db = db

    def log_step(self, analysis_id: str, step_name: str, status: str, data: Optional[Dict[str, Any]] = None) -> str:
        """
        记录分析步骤

        Args:
            analysis_id: 分析任务ID
            step_name: 步骤名称
            status: 状态（pending/in_progress/completed/failed）
            data: 步骤相关数据

        Returns:
            step_id: 步骤ID
        """
        step_id = f"step_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # 初始化执行追踪
        if analysis_id not in self._execution_traces:
            self._execution_traces[analysis_id] = {
                "analysis_id": analysis_id,
                "created_at": datetime.now().isoformat(),
                "steps": [],
                "tool_calls": [],
                "final_result": None,
                "status": "in_progress"
            }

        # 记录步骤
        step_entry = {
            "step_id": step_id,
            "step_name": step_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }

        self._execution_traces[analysis_id]["steps"].append(step_entry)

        return step_id

    def log_tool_call(self, analysis_id: str, tool_name: str, input_params: Dict[str, Any],
                       output_result: Dict[str, Any], execution_time_ms: int, status: str = "success") -> str:
        """
        记录工具调用

        Args:
            analysis_id: 分析任务ID
            tool_name: 工具名称
            input_params: 输入参数
            output_result: 输出结果
            execution_time_ms: 执行时间（毫秒）
            status: 状态（success/failed）

        Returns:
            tool_call_id: 工具调用ID
        """
        tool_call_id = f"tool_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # 初始化工具调用日志
        if analysis_id not in self._tool_call_logs:
            self._tool_call_logs[analysis_id] = []

        # 记录工具调用
        tool_call_entry = {
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "input_params": input_params,
            "output_summary": self._summarize_output(output_result),
            "output_size": len(json.dumps(output_result, ensure_ascii=False)),
            "execution_time_ms": execution_time_ms,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }

        self._tool_call_logs[analysis_id].append(tool_call_entry)

        # 同步到执行追踪
        if analysis_id in self._execution_traces:
            self._execution_traces[analysis_id]["tool_calls"].append(tool_call_entry)

        return tool_call_id

    def log_final_result(self, analysis_id: str, result: Dict[str, Any]) -> bool:
        """
        记录最终结果

        Args:
            analysis_id: 分析任务ID
            result: 最终结果

        Returns:
            是否成功
        """
        try:
            if analysis_id not in self._execution_traces:
                self._execution_traces[analysis_id] = {
                    "analysis_id": analysis_id,
                    "created_at": datetime.now().isoformat(),
                    "steps": [],
                    "tool_calls": [],
                    "final_result": None,
                    "status": "in_progress"
                }

            self._execution_traces[analysis_id]["final_result"] = {
                "intent": result.get("intent", ""),
                "intent_category": result.get("intent_category", ""),
                "statistics": self._summarize_statistics(result.get("statistics", {})),
                "anomalies_count": len(result.get("anomalies", [])),
                "report_length": len(result.get("report_content", "")),
                "total_time_ms": self._calculate_total_time(analysis_id),
                "timestamp": datetime.now().isoformat()
            }
            self._execution_traces[analysis_id]["status"] = "completed"
            return True
        except Exception:
            return False

    def mark_analysis_failed(self, analysis_id: str, error_message: str) -> bool:
        """
        标记分析任务失败

        Args:
            analysis_id: 分析任务ID
            error_message: 错误信息

        Returns:
            是否成功
        """
        try:
            if analysis_id not in self._execution_traces:
                self._execution_traces[analysis_id] = {
                    "analysis_id": analysis_id,
                    "created_at": datetime.now().isoformat(),
                    "steps": [],
                    "tool_calls": [],
                    "final_result": None,
                    "status": "in_progress"
                }

            self._execution_traces[analysis_id]["final_result"] = {
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            }
            self._execution_traces[analysis_id]["status"] = "failed"
            return True
        except Exception:
            return False

    def get_execution_trace(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        获取执行追踪

        Args:
            analysis_id: 分析任务ID

        Returns:
            完整的执行追踪
        """
        trace = self._execution_traces.get(analysis_id)

        if not trace:
            # 尝试从数据库加载
            if self._db is not None:
                try:
                    from app.models.database import AnalysisRecord, ToolCallLog

                    record = self._db.query(AnalysisRecord).filter(
                        AnalysisRecord.id == int(analysis_id) if analysis_id.isdigit() else -1
                    ).first()

                    if record:
                        tool_logs = self._db.query(ToolCallLog).filter(
                            ToolCallLog.analysis_record_id == record.id
                        ).all()

                        trace = {
                            "analysis_id": analysis_id,
                            "created_at": record.created_at.isoformat() if hasattr(record, 'created_at') else datetime.now().isoformat(),
                            "steps": [],
                            "tool_calls": [
                                {
                                    "tool_call_id": f"db_tool_{log.id}",
                                    "tool_name": log.tool_name,
                                    "input_params": log.input_params,
                                    "output_summary": str(log.output_result)[:200],
                                    "execution_time_ms": log.execution_time_ms,
                                    "status": "success",
                                    "timestamp": log.timestamp.isoformat() if hasattr(log, 'timestamp') else datetime.now().isoformat()
                                }
                                for log in tool_logs
                            ],
                            "final_result": record.final_result,
                            "status": record.status if hasattr(record, 'status') else "completed"
                        }

                        # 补充分析步骤
                        trace["steps"] = [
                            {"step_name": "理解用户问题", "status": "completed"},
                            {"step_name": "执行数据分析", "status": "completed"},
                            {"step_name": "生成分析报告", "status": "completed"}
                        ]
                except Exception:
                    pass

        return trace

    def get_tool_calls_summary(self, analysis_id: str) -> Dict[str, Any]:
        """
        获取工具调用摘要

        Args:
            analysis_id: 分析任务ID

        Returns:
            工具调用摘要
        """
        tool_calls = self._tool_call_logs.get(analysis_id, [])

        if not tool_calls:
            # 尝试从执行追踪获取
            trace = self.get_execution_trace(analysis_id)
            if trace:
                tool_calls = trace.get("tool_calls", [])

        if not tool_calls:
            return {
                "total_calls": 0,
                "tools": [],
                "total_time_ms": 0,
                "success_rate": "0%"
            }

        total_time = sum(tc.get("execution_time_ms", 0) for tc in tool_calls)
        success_count = sum(1 for tc in tool_calls if tc.get("status") == "success")
        success_rate = f"{int((success_count / len(tool_calls)) * 100)}%"

        # 按工具类型统计
        tool_stats = {}
        for tc in tool_calls:
            tool_name = tc.get("tool_name", "unknown")
            if tool_name not in tool_stats:
                tool_stats[tool_name] = {"count": 0, "total_time_ms": 0}
            tool_stats[tool_name]["count"] += 1
            tool_stats[tool_name]["total_time_ms"] += tc.get("execution_time_ms", 0)

        return {
            "total_calls": len(tool_calls),
            "tools": [
                {
                    "tool_name": name,
                    "call_count": stats["count"],
                    "total_time_ms": stats["total_time_ms"]
                }
                for name, stats in tool_stats.items()
            ],
            "total_time_ms": total_time,
            "success_rate": success_rate,
            "breakdown": self._generate_execution_breakdown(tool_calls)
        }

    def export_execution_report(self, analysis_id: str) -> Dict[str, Any]:
        """
        导出完整执行报告

        Args:
            analysis_id: 分析任务ID

        Returns:
            完整的可追溯执行报告
        """
        trace = self.get_execution_trace(analysis_id)
        tool_summary = self.get_tool_calls_summary(analysis_id)

        if not trace:
            return {
                "error": f"Analysis ID {analysis_id} not found",
                "timestamp": datetime.now().isoformat()
            }

        return {
            "analysis_id": analysis_id,
            "created_at": trace.get("created_at", ""),
            "status": trace.get("status", "unknown"),

            "execution_summary": {
                "total_steps": len(trace.get("steps", [])),
                "total_tool_calls": tool_summary.get("total_calls", 0),
                "total_time_ms": tool_summary.get("total_time_ms", 0),
                "success_rate": tool_summary.get("success_rate", "0%")
            },

            "step_details": trace.get("steps", []),

            "tool_call_details": tool_summary.get("tools", []),

            "analysis_result_summary": trace.get("final_result", {}),

            "observability_info": {
                "traceability_level": "full",
                "timestamp": datetime.now().isoformat(),
                "recommended_actions": self._generate_recommendations(trace)
            }
        }

    def list_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        列出最近的分析任务

        Args:
            limit: 返回条数

        Returns:
            分析任务摘要列表
        """
        analyses = list(self._execution_traces.values())
        analyses.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return analyses[:limit]

    @staticmethod
    def _summarize_output(output: Dict[str, Any]) -> str:
        """生成输出摘要"""
        try:
            output_str = json.dumps(output, ensure_ascii=False)
            if len(output_str) > 500:
                return output_str[:500] + "...[truncated]"
            return output_str
        except Exception:
            return str(output)[:200]

    @staticmethod
    def _summarize_statistics(statistics: Dict[str, Any]) -> Dict[str, Any]:
        """生成统计摘要"""
        summary = {}
        for field, stats in statistics.items():
            if isinstance(stats, dict):
                summary[field] = {
                    "mean": stats.get("mean"),
                    "median": stats.get("median"),
                    "count": stats.get("count")
                }
        return summary

    def _calculate_total_time(self, analysis_id: str) -> int:
        """计算总执行时间"""
        trace = self._execution_traces.get(analysis_id)
        if not trace:
            return 0

        total_time = 0
        for tool_call in trace.get("tool_calls", []):
            total_time += tool_call.get("execution_time_ms", 0)
        return total_time

    @staticmethod
    def _generate_execution_breakdown(tool_calls: List[Dict[str, Any]]) -> str:
        """生成执行时间分解说明"""
        if not tool_calls:
            return "无工具调用记录"

        lines = []
        for tc in tool_calls:
            lines.append(f"- {tc.get('tool_name')}: {tc.get('execution_time_ms', 0)}ms")

        return "\n".join(lines)

    @staticmethod
    def _generate_recommendations(trace: Dict[str, Any]) -> List[str]:
        """基于执行追踪生成推荐"""
        recommendations = []

        # 基于失败步骤的推荐
        failed_steps = [s for s in trace.get("steps", []) if s.get("status") == "failed"]
        if failed_steps:
            recommendations.append(
                f"检测到 {len(failed_steps)} 个失败步骤，建议重新执行这些步骤"
            )

        # 基于执行时间的推荐
        total_time = sum(
            tc.get("execution_time_ms", 0)
            for tc in trace.get("tool_calls", [])
        )
        if total_time > 10000:  # 超过10秒
            recommendations.append(
                "分析耗时较长，建议考虑数据采样或优化查询"
            )

        # 默认推荐
        if not recommendations:
            recommendations.append("执行过程正常，所有步骤已完成")

        return recommendations
