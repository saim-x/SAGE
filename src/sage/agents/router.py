from typing import Dict, Any, Optional
import random

from .base import BaseAgent
from ..core.models import SubPrompt, ModelAssignment, TaskType, EvaluationResult, ExecutionResult
from ..core.utils import call_ollama, extract_model_name_from_response

META_ROUTER_PROMPT_TEMPLATE = """
You are an expert model selector for a multi-LLM AI system.

Given a sub-task description and a list of available language models, select the best model for the sub-task. Only respond with the model name.

Sub-task description:
{subtask}

Available models:
{model_list}

Respond with only the model name that is best suited for this sub-task.
"""

class RouterAgent(BaseAgent):
    """Agent responsible for routing tasks to appropriate models using a meta-router LLM."""
    
    def process(self, subprompt: SubPrompt) -> ModelAssignment:
        """Process a subprompt and determine the best model to handle it using the meta-router LLM."""
        self._log_info("Routing subprompt (meta-router)", subprompt_id=subprompt.id, task_type=subprompt.task_type)
        
        available_models = self.config.available_models
        prompt = META_ROUTER_PROMPT_TEMPLATE.format(
            subtask=subprompt.content,
            model_list="\n- ".join([""].__add__(available_models))
        )
        try:
            response = call_ollama(prompt)
            model_name = response.strip()
            if model_name not in available_models:
                # Fallback: try to extract model name from response
                model_name = extract_model_name_from_response(response, available_models)
        except Exception as e:
            self._log_error("Meta-router LLM failed, falling back to config assignment", error=e)
            # Fallback: use config assignment
            model_name = self.config.model_assignments.get(subprompt.task_type, self.config.default_model)
        
        model_params = self.config.model_parameters.get(model_name, {})
        assignment = ModelAssignment(
            model_name=model_name,
            model_provider=self._get_provider(model_name),
            parameters=model_params
        )
        self._log_info("Completed routing (meta-router)", subprompt_id=subprompt.id, model_name=model_name, parameters=model_params)
        return assignment
    
    def route(self, subprompt: SubPrompt) -> ModelAssignment:
        """Alias for process method to maintain consistent interface."""
        return self.process(subprompt)
    
    def reassign(self, subprompt: SubPrompt, evaluation: EvaluationResult, last_result: 'ExecutionResult') -> ModelAssignment:
        """Reassign a subprompt to a different model after a failed attempt.
        Args:
            subprompt: The subprompt to reassign
            evaluation: The evaluation result from the previous attempt
            last_result: The last ExecutionResult (to get model_used)
        Returns:
            New ModelAssignment with potentially different model or parameters
        """
        self._log_info("Reassigning subprompt after failed attempt", subprompt_id=subprompt.id, retry_count=evaluation.retry_count)
        available_models = [m for m in self.config.available_models if m != last_result.model_used.model_name]
        if not available_models:
            model_name = last_result.model_used.model_name
            model_params = self._adjust_parameters(last_result.model_used.parameters)
        else:
            # Use meta-router again for reassignment
            prompt = META_ROUTER_PROMPT_TEMPLATE.format(
                subtask=subprompt.content,
                model_list="\n- ".join([""].__add__(available_models))
            )
            try:
                response = call_ollama(prompt)
                model_name = response.strip()
                if model_name not in available_models:
                    model_name = extract_model_name_from_response(response, available_models)
            except Exception as e:
                self._log_error("Meta-router LLM failed during reassignment, falling back to random", error=e)
                model_name = random.choice(available_models)
            model_params = self.config.model_parameters.get(model_name, {})
        assignment = ModelAssignment(
            model_name=model_name,
            model_provider=self._get_provider(model_name),
            parameters=model_params
        )
        self._log_info("Completed reassignment (meta-router)", subprompt_id=subprompt.id, new_model=model_name, parameters=model_params)
        return assignment
    
    def _get_provider(self, model_name: str) -> str:
        if "gpt" in model_name:
            return "openai"
        elif "claude" in model_name:
            return "anthropic"
        else:
            return "unknown"
    
    def _adjust_parameters(self, current_params: Dict[str, Any]) -> Dict[str, Any]:
        adjusted_params = current_params.copy()
        if "temperature" in adjusted_params:
            adjusted_params["temperature"] = min(1.0, adjusted_params["temperature"] + 0.1)
        if "max_tokens" in adjusted_params:
            adjusted_params["max_tokens"] = int(adjusted_params["max_tokens"] * 1.2)
        return adjusted_params 