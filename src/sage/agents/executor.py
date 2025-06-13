from typing import Dict, Any, Optional
import time

from .base import BaseAgent
from ..core.models import SubPrompt, ModelAssignment, ExecutionResult
from ..core.utils import call_ollama, call_gemini

class ExecutionManager(BaseAgent):
    """Agent responsible for executing sub-tasks using assigned local Ollama models or cloud LLMs."""
    
    def __init__(self, config):
        """Initialize the execution manager with configuration."""
        super().__init__(config)
    
    def process(self, subprompt: SubPrompt, assignment: ModelAssignment) -> ExecutionResult:
        """Execute a subprompt using the assigned model (Ollama local or Gemini cloud)."""
        provider = assignment.model_provider.lower()
        self._log_info(f"Executing subprompt ({provider})", subprompt_id=subprompt.id, model=assignment.model_name)
        try:
            if provider == "gemini":
                response = call_gemini(subprompt.content, model=assignment.model_name, parameters=assignment.parameters)
            else:
                response = call_ollama(subprompt.content, model=assignment.model_name)
            result = ExecutionResult(
                subprompt_id=subprompt.id,
                content=response,
                model_used=assignment,
                success=True,
                similarity_score=1.0,  # Will be updated by evaluator
                metadata={
                    "execution_time": time.time(),
                    "provider": provider
                }
            )
            self._log_info(f"Successfully executed subprompt ({provider})", subprompt_id=subprompt.id, model=assignment.model_name)
            return result
        except Exception as e:
            self._log_error(f"Failed to execute subprompt ({provider})", error=e, subprompt_id=subprompt.id, model=assignment.model_name)
            return ExecutionResult(
                subprompt_id=subprompt.id,
                content="",
                model_used=assignment,
                success=False,
                similarity_score=0.0,
                metadata={
                    "error": str(e),
                    "execution_time": time.time(),
                    "provider": provider
                }
            )
    
    def execute(self, subprompt: SubPrompt, assignment: ModelAssignment) -> ExecutionResult:
        """Alias for process method to maintain consistent interface."""
        return self.process(subprompt, assignment) 