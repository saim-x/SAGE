from typing import Dict, Any, Optional
import time

from .base import BaseAgent
from ..core.models import SubPrompt, ModelAssignment, ExecutionResult
from ..core.utils import call_ollama

class ExecutionManager(BaseAgent):
    """Agent responsible for executing sub-tasks using assigned local Ollama models."""
    
    def __init__(self, config):
        """Initialize the execution manager with configuration."""
        super().__init__(config)
    
    def process(self, subprompt: SubPrompt, assignment: ModelAssignment) -> ExecutionResult:
        """Execute a subprompt using the assigned local Ollama model."""
        self._log_info("Executing subprompt (Ollama)", subprompt_id=subprompt.id, model=assignment.model_name)
        try:
            response = call_ollama(subprompt.content, model=assignment.model_name)
            result = ExecutionResult(
                subprompt_id=subprompt.id,
                content=response,
                model_used=assignment,
                success=True,
                similarity_score=1.0,  # Will be updated by evaluator
                metadata={
                    "execution_time": time.time(),
                    "provider": "ollama"
                }
            )
            self._log_info("Successfully executed subprompt (Ollama)", subprompt_id=subprompt.id, model=assignment.model_name)
            return result
        except Exception as e:
            self._log_error("Failed to execute subprompt (Ollama)", error=e, subprompt_id=subprompt.id, model=assignment.model_name)
            return ExecutionResult(
                subprompt_id=subprompt.id,
                content="",
                model_used=assignment,
                success=False,
                similarity_score=0.0,
                metadata={
                    "error": str(e),
                    "execution_time": time.time()
                }
            )
    
    def execute(self, subprompt: SubPrompt, assignment: ModelAssignment) -> ExecutionResult:
        """Alias for process method to maintain consistent interface."""
        return self.process(subprompt, assignment) 