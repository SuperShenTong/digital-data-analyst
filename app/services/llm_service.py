import os
import json
import re
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain.chat_models import ChatOpenAI

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from pydantic import BaseModel, Field


class AnalysisStep(BaseModel):
    """分析步骤的结构化定义 - 支持多层级任务拆解"""
    step_id: str = Field(description="步骤唯一标识符，如 step_1, step_2")
    description: str = Field(description="用简短中文描述这个步骤的作用，10-20字")
    tool: str = Field(description="该步骤使用的工具名称：stat_analysis, anomaly_detection, chart_generator, report_generator")
    dependencies: List[str] = Field(description="该步骤依赖的前置步骤的 step_id 列表，无依赖则为空列表")
    priority: str = Field(description="步骤优先级：high, medium, low")
    fields: List[str] = Field(description="该步骤涉及的字段名称列表")
    is_validation: bool = Field(description="是否为中间验证点，用于验证结果合理性")


class AnalysisPlanResult(BaseModel):
    """数据理解Agent的输出格式 - LLM必须严格按照此格式返回（支持多层级任务拆解）"""
    intent: str = Field(description="用简短中文描述用户的分析意图，不超过30字")
    intent_category: str = Field(description="从以下类别中选择一个：统计分析、趋势分析、异常检测、对比分析、可视化分析、其他")
    required_fields: List[str] = Field(description="从用户提供的可用字段列表中选择需要分析的字段名称")
    analysis_steps: List[AnalysisStep] = Field(description="按顺序列出结构化的分析步骤，每个步骤包含step_id/description/tool/dependencies/priority/fields/is_validation。report_generator 必须是最后一项")
    complexity_level: str = Field(description="任务复杂度评估：simple(单步)/medium(2-3步)/complex(4步以上或需预处理)")
    preprocessing_needed: bool = Field(description="是否需要数据预处理（过滤、分组、聚合、类型转换等）")
    preprocessing_description: str = Field(description="预处理步骤的简要描述，不需要则返回空字符串")
    requires_followup: bool = Field(description="如果用户问题不明确或缺少必要信息，返回true；否则返回false")
    followup_question: str = Field(description="如果需要追问，用中文提出具体问题；否则返回空字符串")
    description: str = Field(description="用50-100字的中文描述本次分析的目标和范围")


class ToolDecision(BaseModel):
    """数据分析Agent的工具决策输出格式 - LLM必须严格按照此格式返回"""
    tools_to_call: List[Dict[str, Any]] = Field(description="需要调用的工具列表，每个工具是一个字典，必须包含name, fields, parameters")
    summary: str = Field(description="用50-100字的中文描述本次分析的重点和预期产出")


class LLMService:
    """
    LLM服务 - 统一管理与大模型的所有交互

    设计原则：
    1. 所有Agent的决策都通过LLM实现 - 不使用关键词匹配等fallback
    2. 提示词从外部YAML文件加载，便于优化和调整
    3. LLM调用失败时直接抛出异常，由调用方处理
    4. 使用Pydantic结构化输出，保证结果可解析
    """

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.api_base = os.getenv("LLM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = os.getenv("LLM_MODEL", "qwen-plus")
        self.provider = os.getenv("LLM_PROVIDER", "aliyun")

        # 验证API Key配置
        if not self.api_key or self.api_key in ["your_api_key_here", ""]:
            raise RuntimeError(
                "LLM API Key 未配置！\n"
                "请在项目根目录的 .env 文件中设置 LLM_API_KEY。\n"
                "当前配置：LLM_MODEL=" + self.model
            )

        # 初始化LLM客户端
        try:
            self.llm = ChatOpenAI(
                model=self.model,
                temperature=0.1,
                api_key=self.api_key,
                base_url=self.api_base
            )
            print(f"[LLMService] 初始化成功 - 模型: {self.model}, 提供商: {self.provider}")
        except Exception as e:
            raise RuntimeError(f"LLM 初始化失败: {e}")

        # 结构化输出解析器
        self.analysis_plan_parser = PydanticOutputParser(pydantic_object=AnalysisPlanResult)
        self.tool_decision_parser = PydanticOutputParser(pydantic_object=ToolDecision)

    # ============================================
    # 核心方法1：数据理解Agent - 意图分析
    # ============================================
    def analyze_intent_with_prompts(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        分析用户意图，生成分析计划

        Args:
            system_prompt: 系统提示词（角色定义、任务说明）
            user_prompt: 用户提示词（问题内容 + 可用字段）

        Returns:
            包含分析计划的字典

        Raises:
            RuntimeError: LLM调用失败时抛出
        """
        # 获取格式要求说明
        format_instructions = self.analysis_plan_parser.get_format_instructions()

        # 构造完整的用户消息：问题 + 字段 + JSON格式要求
        # 注意：这里不使用LangChain的模板变量，避免与JSON中的 {} 冲突
        full_user_prompt = user_prompt + "\n\n【输出格式要求】\n请严格按照以下JSON格式输出结果，不要添加任何额外的文字说明：\n" + format_instructions

        # 直接构造消息列表，避免模板解析问题
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=full_user_prompt)
        ]

        try:
            # 调用LLM + 结构化解析
            result = self.llm.invoke(messages)
            parsed_result = self.analysis_plan_parser.parse(result.content)
        except Exception as e:
            # 尝试简单的JSON提取（如果LLM返回了额外文字）
            try:
                parsed_result = self._extract_json(result.content, AnalysisPlanResult)
            except:
                raise RuntimeError(f"LLM 意图分析调用失败: {e}")

        # 将 AnalysisStep 对象转换为字典，便于下游处理
        steps_as_dicts = []
        for step in parsed_result.analysis_steps:
            steps_as_dicts.append({
                "step_id": step.step_id,
                "description": step.description,
                "tool": step.tool,
                "dependencies": step.dependencies,
                "priority": step.priority,
                "fields": step.fields,
                "is_validation": step.is_validation
            })

        return {
            "intent": parsed_result.intent,
            "intent_category": parsed_result.intent_category,
            "required_fields": parsed_result.required_fields,
            "analysis_steps": steps_as_dicts,
            "complexity_level": parsed_result.complexity_level,
            "preprocessing_needed": parsed_result.preprocessing_needed,
            "preprocessing_description": parsed_result.preprocessing_description,
            "requires_followup": parsed_result.requires_followup,
            "followup_question": parsed_result.followup_question,
            "description": parsed_result.description,
            "source": "llm"
        }

    # ============================================
    # 核心方法2：数据分析Agent - 工具决策
    # ============================================
    def decide_tools_with_prompts(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        根据分析计划，决策调用哪些分析工具

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词（分析计划 + 可用字段）

        Returns:
            包含工具决策的字典

        Raises:
            RuntimeError: LLM调用失败时抛出
        """
        format_instructions = self.tool_decision_parser.get_format_instructions()

        # 构造完整用户消息
        full_user_prompt = user_prompt + "\n\n【输出格式要求】\n请严格按照以下JSON格式输出结果，不要添加任何额外的文字说明：\n" + format_instructions

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=full_user_prompt)
        ]

        try:
            result = self.llm.invoke(messages)
            parsed_result = self.tool_decision_parser.parse(result.content)
        except Exception as e:
            try:
                parsed_result = self._extract_json(result.content, ToolDecision)
            except:
                raise RuntimeError(f"LLM 工具决策调用失败: {e}")

        return {
            "tools_to_call": parsed_result.tools_to_call,
            "summary": parsed_result.summary,
            "source": "llm"
        }

    # ============================================
    # 核心方法3：报告生成Agent - 报告生成
    # ============================================
    def generate_report_with_prompts(self, system_prompt: str, user_prompt: str) -> str:
        """
        根据分析结果生成完整的数据分析报告

        Args:
            system_prompt: 系统提示词（报告结构要求）
            user_prompt: 用户提示词（用户问题 + 分析结果数据）

        Returns:
            Markdown格式的报告字符串

        Raises:
            RuntimeError: LLM调用失败时抛出
        """
        # 报告生成不需要结构化JSON输出，直接生成Markdown
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            result = self.llm.invoke(messages)
            report = result.content
        except Exception as e:
            raise RuntimeError(f"LLM 报告生成调用失败: {e}")

        return report

    # ============================================
    # 辅助方法：JSON提取（当LLM返回额外文本时）
    # ============================================
    def _extract_json(self, text: str, parser_class: BaseModel) -> Any:
        """
        尝试从文本中提取JSON并解析

        处理LLM返回 "好的，这是JSON... {json}" 这样的情况
        """
        # 尝试提取第一个 { 到最后一个 } 之间的内容
        start_idx = text.find('{')
        end_idx = text.rfind('}')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_text = text[start_idx:end_idx + 1]

            # 清理可能的Markdown代码块标记
            json_text = json_text.replace('```json', '').replace('```', '')

            # 尝试解析
            parser = PydanticOutputParser(pydantic_object=parser_class)
            return parser.parse(json_text)

        # 如果无法提取，直接抛出异常
        raise ValueError(f"无法从文本中提取JSON: {text[:200]}")

    # ============================================
    # 工具方法
    # ============================================
    def is_available(self) -> bool:
        """检查LLM服务是否可用"""
        return self.llm is not None

    def get_model_info(self) -> Dict[str, str]:
        """获取当前模型配置信息"""
        return {
            "provider": self.provider,
            "model": self.model,
            "api_base": self.api_base,
            "available": self.is_available()
        }
