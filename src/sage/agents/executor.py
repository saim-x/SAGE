from typing import Dict, Any, Optional
import time
import openai
import anthropic

from .base import BaseAgent
from ..core.models import SubPrompt, ModelAssignment, ExecutionResult

class ExecutionManager(BaseAgent):
    """Agent responsible for executing sub-tasks using assigned models."""
    
    def __init__(self, config):
        """Initialize the execution manager with configuration."""
        super().__init__(config)
        self._setup_clients()
    
    def _setup_clients(self):
        """Set up API clients for different providers."""
        # TODO: Load API keys from environment variables
        self.openai_client = openai.OpenAI()
        self.anthropic_client = anthropic.Anthropic()
    
    def process(self, subprompt: SubPrompt, assignment: ModelAssignment) -> ExecutionResult:
        """Execute a subprompt using the assigned model.
        
        Args:
            subprompt: The subprompt to execute
            assignment: The model assignment for this task
            
        Returns:
            ExecutionResult containing the model's response and metadata
        """
        self._log_info("Executing subprompt",
                      subprompt_id=subprompt.id,
                      model=assignment.model_name)
        
        try:
            # Execute based on provider
            if assignment.model_provider == "openai":
                response = self._execute_openai(subprompt, assignment)
            elif assignment.model_provider == "anthropic":
                response = self._execute_anthropic(subprompt, assignment)
            else:
                raise ValueError(f"Unsupported model provider: {assignment.model_provider}")
            
            result = ExecutionResult(
                subprompt_id=subprompt.id,
                content=response,
                model_used=assignment,
                success=True,
                similarity_score=1.0,  # Will be updated by evaluator
                metadata={
                    "execution_time": time.time(),
                    "provider": assignment.model_provider
                }
            )
            
            self._log_info("Successfully executed subprompt",
                          subprompt_id=subprompt.id,
                          model=assignment.model_name)
            
            return result
            
        except Exception as e:
            self._log_error("Failed to execute subprompt",
                          error=e,
                          subprompt_id=subprompt.id,
                          model=assignment.model_name)
            
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
    
    def _execute_openai(self, subprompt: SubPrompt, assignment: ModelAssignment) -> str:
        """Execute a subprompt using OpenAI models."""
        response = self.openai_client.chat.completions.create(
            model=assignment.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": subprompt.content}
            ],
            **assignment.parameters
        )
        return response.choices[0].message.content
    
    def _execute_anthropic(self, subprompt: SubPrompt, assignment: ModelAssignment) -> str:
        """Execute a subprompt using Anthropic models."""
        response = self.anthropic_client.messages.create(
            model=assignment.model_name,
            max_tokens=assignment.parameters.get("max_tokens", 1000),
            messages=[
                {"role": "user", "content": subprompt.content}
            ]
        )
        return response.content[0].text 