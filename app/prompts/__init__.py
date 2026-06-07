import os
import yaml
from typing import Dict, Any, Optional


class PromptLoader:
    """提示词加载工具，负责从YAML文件加载Agent的提示词配置"""

    _cache = {}

    @classmethod
    def load_prompt(cls, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        从YAML文件加载指定Agent的提示词配置

        Args:
            agent_name: Agent名称，例如 'data_understanding_agent'

        Returns:
            包含system_prompt和user_prompt_template的字典
        """
        if agent_name in cls._cache:
            return cls._cache[agent_name]

        prompt_file = os.path.join(
            os.path.dirname(__file__),
            f"{agent_name}_prompt.yaml"
        )

        if not os.path.exists(prompt_file):
            print(f"Warning: Prompt file not found: {prompt_file}")
            return None

        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            cls._cache[agent_name] = config
            return config

        except Exception as e:
            print(f"Error loading prompt file {prompt_file}: {e}")
            return None

    @classmethod
    def get_system_prompt(cls, agent_name: str) -> str:
        """获取Agent的系统提示词"""
        config = cls.load_prompt(agent_name)
        if config and 'system_prompt' in config:
            return config['system_prompt']
        return ""

    @classmethod
    def get_user_prompt_template(cls, agent_name: str) -> str:
        """获取Agent的用户提示词模板"""
        config = cls.load_prompt(agent_name)
        if config and 'user_prompt_template' in config:
            return config['user_prompt_template']
        return ""

    @classmethod
    def clear_cache(cls):
        """清除缓存，用于重新加载配置文件"""
        cls._cache = {}
