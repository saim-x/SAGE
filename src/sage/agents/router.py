from typing import Dict, Any, Optional
import random

from .base import BaseAgent
from ..core.models import SubPrompt, ModelAssignment, TaskType, EvaluationResult

class RouterAgent(BaseAgent):
    """Agent responsible for routing tasks to appropriate models."""
    
    def process(self, subprompt: SubPrompt) -> ModelAssignment:
        """Process a subprompt and determine the best model to handle it.
        
        Args:
            subprompt: The subprompt to route
            
        Returns:
            ModelAssignment containing the selected model and parameters
        """
        self._log_info("Routing subprompt", subprompt_id=subprompt.id, task_type=subprompt.task_type)
        
        # Get the assigned model from config based on task type
        model_name = self.config.model_assignments.get(subprompt.task_type, self.config.default_model)
        
        # Get model parameters from config
        model_params = self.config.model_parameters.get(model_name, {})
        
        assignment = ModelAssignment(
            model_name=model_name,
            model_provider=self._get_provider(model_name),
            parameters=model_params
        )
        
        self._log_info("Completed routing", 
                      subprompt_id=subprompt.id,
                      model_name=model_name,
                      parameters=model_params)
        
        return assignment
    
    def route(self, subprompt: SubPrompt) -> ModelAssignment:
        """Alias for process method to maintain consistent interface."""
        return self.process(subprompt)
    
    def reassign(self, subprompt: SubPrompt, evaluation: EvaluationResult) -> ModelAssignment:
        """Reassign a subprompt to a different model after a failed attempt.
        
        Args:
            subprompt: The subprompt to reassign
            evaluation: The evaluation result from the previous attempt
            
        Returns:
            New ModelAssignment with potentially different model or parameters
        """
        self._log_info("Reassigning subprompt after failed attempt",
                      subprompt_id=subprompt.id,
                      retry_count=evaluation.retry_count)
        
        # Get available models for this task type
        available_models = [m for m in self.config.available_models 
                          if m != evaluation.model_used.model_name]
        
        if not available_models:
            # If no other models available, try the same model with different parameters
            model_name = evaluation.model_used.model_name
            model_params = self._adjust_parameters(evaluation.model_used.parameters)
        else:
            # Select a different model
            model_name = random.choice(available_models)
            model_params = self.config.model_parameters.get(model_name, {})
        
        assignment = ModelAssignment(
            model_name=model_name,
            model_provider=self._get_provider(model_name),
            parameters=model_params
        )
        
        self._log_info("Completed reassignment",
                      subprompt_id=subprompt.id,
                      new_model=model_name,
                      parameters=model_params)
        
        return assignment
    
    def _get_provider(self, model_name: str) -> str:
        """Determine the provider for a given model name."""
        if "gpt" in model_name:
            return "openai"
        elif "claude" in model_name:
            return "anthropic"
        else:
            return "unknown"
    
    def _adjust_parameters(self, current_params: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust model parameters for retry attempts."""
        adjusted_params = current_params.copy()
        
        # Increase temperature slightly for more diverse responses
        if "temperature" in adjusted_params:
            adjusted_params["temperature"] = min(1.0, adjusted_params["temperature"] + 0.1)
        
        # Increase max_tokens if possible
        if "max_tokens" in adjusted_params:
            adjusted_params["max_tokens"] = int(adjusted_params["max_tokens"] * 1.2)
        
        return adjusted_params 