from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseTool(ABC):
    name: str
    description: str
    parameters: Dict[str, dict]
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    def validate_parameters(self, **kwargs) -> bool:
        for param_name, param_info in self.parameters.items():
            if param_info.get("required", False) and param_name not in kwargs:
                return False
        return True