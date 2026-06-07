from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseAgent(ABC):
    name: str
    role: str
    
    def __init__(self):
        self.execution_history: List[Dict[str, Any]] = []
    
    @abstractmethod
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass
    
    def log_execution(self, task: str, status: str, details: Optional[str] = None):
        self.execution_history.append({
            "agent_name": self.name,
            "task": task,
            "status": status,
            "details": details,
            "timestamp": self._get_timestamp()
        })
    
    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        return self.execution_history
    
    def clear_history(self):
        self.execution_history = []