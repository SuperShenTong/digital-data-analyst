"""
上下文管理服务 - 支持多轮对话和历史上下文追问
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime


class ContextService:
    """
    上下文管理服务

    核心能力：
    1. 会话管理：创建和维护用户会话
    2. 对话历史存储：记录用户问题和助手回答
    3. 分析结果缓存：保存历史分析结果
    4. 上下文注入：将历史上下文注入到新的分析中
    5. 构建带上下文的查询：增强LLM理解用户意图
    6. 历史查询：查询会话中的所有历史记录
    """

    # 内存存储（生产环境应使用数据库/Redis）
    _sessions: Dict[str, Dict[str, Any]] = {}

    # SQLAlchemy Session 引用
    _db = None

    def __init__(self, db=None):
        """
        初始化上下文服务

        Args:
            db: SQLAlchemy Session（可选，用于持久化存储）
        """
        self._db = db

    @classmethod
    def create_session(cls, user_id: str = "anonymous", initial_data: Optional[Dict[str, Any]] = None) -> str:
        """
        创建新的会话

        Args:
            user_id: 用户标识
            initial_data: 初始上下文数据

        Returns:
            session_id: 会话ID
        """
        session_id = str(uuid.uuid4())

        cls._sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "conversation_history": [],
            "analysis_results": [],
            "data_sources": [],
            "preferences": {},
            "metadata": initial_data or {}
        }

        return session_id

    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息字典，如果会话不存在则返回None
        """
        session = cls._sessions.get(session_id)

        if session is None:
            # 尝试从数据库加载
            if cls._db is not None:
                try:
                    from app.models.database import Conversation
                    convo = cls._db.query(Conversation).filter(
                        Conversation.session_id == session_id
                    ).order_by(Conversation.created_at).all()

                    if convo:
                        session = {
                            "session_id": session_id,
                            "user_id": "unknown",
                            "created_at": convo[0].created_at.isoformat() if hasattr(convo[0], 'created_at') else datetime.now().isoformat(),
                            "last_updated": datetime.now().isoformat(),
                            "conversation_history": [
                                {
                                    "role": "user",
                                    "content": c.user_message,
                                    "assistant_message": c.assistant_message,
                                    "timestamp": c.created_at.isoformat() if hasattr(c, 'created_at') else datetime.now().isoformat()
                                }
                                for c in convo
                            ],
                            "analysis_results": [],
                            "data_sources": [],
                            "preferences": {},
                            "metadata": {}
                        }
                        cls._sessions[session_id] = session
                except Exception:
                    pass

        return session

    @classmethod
    def save_context(cls, session_id: str, data: Dict[str, Any]) -> bool:
        """
        保存上下文数据

        Args:
            session_id: 会话ID
            data: 要保存的数据

        Returns:
            是否保存成功
        """
        try:
            # 确保会话存在
            if session_id not in cls._sessions:
                cls.create_session(session_id=session_id)

            session = cls._sessions[session_id]

            # 更新最后更新时间
            session["last_updated"] = datetime.now().isoformat()

            # 保存对话历史
            if "conversation" in data:
                conversation_entry = {
                    "role": "user",
                    "content": data["conversation"].get("user_query", ""),
                    "assistant_response": data["conversation"].get("assistant_response", ""),
                    "timestamp": datetime.now().isoformat()
                }
                session["conversation_history"].append(conversation_entry)

            # 保存分析结果
            if "analysis_result" in data:
                analysis_entry = {
                    "analysis_id": data["analysis_result"].get("analysis_id"),
                    "user_query": data["analysis_result"].get("user_query", ""),
                    "intent": data["analysis_result"].get("intent", ""),
                    "statistics": data["analysis_result"].get("statistics", {}),
                    "anomalies": data["analysis_result"].get("anomalies", []),
                    "report_content": data["analysis_result"].get("report_content", ""),
                    "data_source_id": data["analysis_result"].get("data_source_id"),
                    "timestamp": datetime.now().isoformat()
                }
                session["analysis_results"].append(analysis_entry)

            # 保存数据源信息
            if "data_source" in data:
                session["data_sources"].append(data["data_source"])

            # 保存偏好设置
            if "preferences" in data:
                session["preferences"].update(data["preferences"])

            # 保存元数据
            if "metadata" in data:
                session["metadata"].update(data["metadata"])

            return True
        except Exception:
            return False

    @classmethod
    def get_conversation_history(cls, session_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取对话历史

        Args:
            session_id: 会话ID
            limit: 返回条数（默认最近10条）
            offset: 偏移量

        Returns:
            对话历史列表
        """
        session = cls.get_session(session_id)

        if not session:
            return []

        history = session["conversation_history"]

        # 返回最近的N条，保持时间顺序
        if limit > 0:
            return history[-limit - offset: len(history) - offset] if offset > 0 else history[-limit:]
        return history

    @classmethod
    def get_analysis_history(cls, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取历史分析结果

        Args:
            session_id: 会话ID
            limit: 返回条数

        Returns:
            分析结果列表
        """
        session = cls.get_session(session_id)

        if not session:
            return []

        return session["analysis_results"][-limit:]

    @classmethod
    def inject_context_to_prompt(cls, prompt: str, session_id: str, max_history: int = 3) -> str:
        """
        将历史上下文注入到提示词中

        Args:
            prompt: 原始提示词
            session_id: 会话ID
            max_history: 注入的最大历史条数

        Returns:
            增强后的提示词
        """
        session = cls.get_session(session_id)

        if not session:
            return prompt

        context_parts = []

        # 添加对话历史
        history = session["conversation_history"][-max_history:]
        if history:
            context_parts.append("【对话历史】")
            for h in history:
                context_parts.append(f"- 用户问题: {h.get('content', '')}")
                if h.get("assistant_response"):
                    context_parts.append(f"  回复: {h.get('assistant_response', '')[:100]}")

        # 添加分析历史
        analysis_history = session["analysis_results"][-max_history:]
        if analysis_history:
            context_parts.append("\n【历史分析结果】")
            for a in analysis_history:
                context_parts.append(f"- 分析目标: {a.get('user_query', '')[:50]}")
                context_parts.append(f"  分析意图: {a.get('intent', '')[:50]}")
                stats = a.get("statistics", {})
                if stats:
                    fields = list(stats.keys())[:3]
                    context_parts.append(f"  分析字段: {', '.join(fields)}")

        # 添加数据源信息
        if session["data_sources"]:
            context_parts.append(f"\n【已使用数据源】 {session['data_sources']}")

        if context_parts:
            enhanced_prompt = "\n".join(context_parts)
            enhanced_prompt += f"\n\n【当前问题】 {prompt}\n\n请基于上述对话历史和分析结果回答当前问题。"
            return enhanced_prompt

        return prompt

    @classmethod
    def build_contextual_query(cls, user_query: str, session_id: str) -> str:
        """
        构建带上下文的查询

        Args:
            user_query: 用户的原始问题
            session_id: 会话ID

        Returns:
            增强后的查询问题
        """
        session = cls.get_session(session_id)

        if not session or not session["conversation_history"]:
            return user_query

        # 检查是否为追问问题
        followup_keywords = [
            "更多", "详细", "继续", "补充", "然后", "之后",
            "more", "detail", "continue", "further",
            "为什么", "原因", "how", "why",
            "还有", "其他", "another", "other"
        ]

        is_followup = any(keyword in user_query.lower() for keyword in followup_keywords)

        if is_followup:
            # 提取最近的分析上下文
            last_analysis = session["analysis_results"][-1] if session["analysis_results"] else None
            last_conversation = session["conversation_history"][-1]

            context_summary = []

            if last_analysis:
                context_summary.append(
                    f"基于之前的分析【{last_analysis.get('user_query', '')[:30]}】，"
                )

                # 添加字段信息
                fields = list(last_analysis.get("statistics", {}).keys())[:3]
                if fields:
                    context_summary.append(
                        f"针对 {', '.join(fields)} 字段，"
                    )

            if last_conversation:
                context_summary.append(
                    f"用户补充: {user_query}"
                )

            return "".join(context_summary) if context_summary else user_query

        return user_query

    @classmethod
    def get_session_summary(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话摘要

        Args:
            session_id: 会话ID

        Returns:
            会话摘要字典
        """
        session = cls.get_session(session_id)

        if not session:
            return None

        return {
            "session_id": session["session_id"],
            "user_id": session["user_id"],
            "created_at": session["created_at"],
            "last_updated": session["last_updated"],
            "conversation_count": len(session["conversation_history"]),
            "analysis_count": len(session["analysis_results"]),
            "data_source_count": len(session["data_sources"]),
            "recent_queries": [
                h.get("content", "")[:50]
                for h in session["conversation_history"][-5:]
            ]
        }

    @classmethod
    def clear_session(cls, session_id: str) -> bool:
        """
        清除会话数据

        Args:
            session_id: 会话ID

        Returns:
            是否清除成功
        """
        if session_id in cls._sessions:
            del cls._sessions[session_id]
            return True
        return False

    @classmethod
    def list_sessions(cls) -> List[Dict[str, Any]]:
        """
        列出所有活跃会话

        Returns:
            会话摘要列表
        """
        return [
            {
                "session_id": sid,
                "conversation_count": len(sess["conversation_history"]),
                "last_updated": sess["last_updated"]
            }
            for sid, sess in cls._sessions.items()
        ]
