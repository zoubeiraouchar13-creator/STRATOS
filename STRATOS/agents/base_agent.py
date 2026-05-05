from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

class BaseAgent(ABC):
    """Classe abstraite pour tous les agents"""
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.logger = logging.getLogger(f"Agent.{name}")
        self.execution_history = []
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute la tâche de l'agent"""
        pass
    
    def log_execution(self, input_data: Any, output_data: Any, duration: float):
        """Enregistre l'exécution pour traçabilité"""
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "input": str(input_data)[:200],
            "output": str(output_data)[:200],
            "duration_ms": duration * 1000
        })
    
    def get_status(self) -> Dict:
        """Retourne le statut de l'agent"""
        return {
            "name": self.name,
            "role": self.role,
            "executions": len(self.execution_history),
            "last_execution": self.execution_history[-1] if self.execution_history else None
        }