from app.agents.base_agent import BaseAgent
from typing import Dict, Any, List, Optional
from app.services.data_service import DataService
from app.services.llm_service import LLMService
from app.prompts import PromptLoader
from sqlalchemy.orm import Session


class DataUnderstandingAgent(BaseAgent):
    """
    数据理解智能体

    核心职责：
    1. 通过LLM分析用户的自然语言问题，识别分析意图
    2. 匹配可用的数据源字段，确定分析目标
    3. 生成标准化的分析计划，指导后续分析步骤

    设计：完全基于LLM，没有任何关键词匹配等fallback机制
    """

    name = "数据理解智能体"
    role = "数据理解"

    def __init__(self, db: Session):
        super().__init__()
        self.data_service = DataService(db)
        self.llm_service = LLMService()

    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行数据理解任务

        Args:
            task: 用户的原始问题
            context: 包含data_source_id等上下文信息

        Returns:
            包含分析意图、分析计划、所需字段的字典

        Raises:
            RuntimeError: 当LLM调用失败时抛出
        """
        self.log_execution(task, "in_progress")

        data_source_id = context.get("data_source_id") if context else None

        if not data_source_id:
            raise RuntimeError("缺少数据源ID，无法进行分析")

        # 获取数据源的字段信息
        data_source_info = self.data_service.get_data_source(data_source_id)
        available_columns = data_source_info.columns

        # 加载提示词配置
        system_prompt = PromptLoader.get_system_prompt("data_understanding_agent")
        user_template = PromptLoader.get_user_prompt_template("data_understanding_agent")

        if not system_prompt or not user_template:
            raise RuntimeError("无法加载数据理解Agent的提示词配置")

        # 填充用户提示词
        user_prompt = user_template.format(
            user_query=task,
            available_columns=available_columns
        )

        # 通过LLM分析意图
        result = self.llm_service.analyze_intent_with_prompts(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        self.log_execution(task, "completed")

        return {
            "agent_name": self.name,
            "intent": result["intent"],
            "intent_category": result["intent_category"],
            "required_fields": result["required_fields"],
            "analysis_steps": result["analysis_steps"],
            "complexity_level": result.get("complexity_level", "medium"),
            "preprocessing_needed": result.get("preprocessing_needed", False),
            "preprocessing_description": result.get("preprocessing_description", ""),
            "requires_followup": result["requires_followup"],
            "followup_question": result["followup_question"],
            "description": result["description"],
            "llm_source": "llm"
        }
