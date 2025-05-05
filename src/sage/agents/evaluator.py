from typing import Dict, Any, Optional
from .base import BaseAgent
from ..core.models import SubPrompt, ExecutionResult, EvaluationResult
from ..core.utils import call_ollama

LLM_EVAL_PROMPT = """
You are an expert evaluator. Given a sub-task and a model's answer, determine if the answer correctly and sufficiently fulfills the sub-task. 

Sub-task:
{subtask}

Model's answer:
{answer}

Respond with 'YES' if the answer is correct and sufficient, 'NO' otherwise. Optionally, provide a confidence score (0-1) and a brief explanation, e.g.:
YES (0.95): The answer is correct and complete.
NO (0.2): The answer is missing key details.
"""

class Evaluator(BaseAgent):
    """Agent responsible for evaluating execution results against expected goals using LLM-based evaluation."""
    
    def process(self, result: ExecutionResult, subprompt: SubPrompt) -> EvaluationResult:
        self._log_info("Evaluating execution result (LLM)", subprompt_id=result.subprompt_id)
        if not result.success:
            return EvaluationResult(
                subprompt_id=result.subprompt_id,
                success=False,
                similarity_score=0.0,
                feedback="Execution failed",
                retry_count=0
            )
        # Select evaluation model dynamically
        eval_model = getattr(self.config, 'evaluator_model', None) or self.config.model_assignments.get('evaluation', 'deepseek-r1:1.5b')
        prompt = LLM_EVAL_PROMPT.format(subtask=subprompt.content, answer=result.content)
        try:
            llm_response = call_ollama(prompt, model=eval_model)
            # Parse LLM response
            llm_response_lower = llm_response.lower()
            if 'yes' in llm_response_lower:
                success = True
            elif 'no' in llm_response_lower:
                success = False
            else:
                success = False
            # Extract confidence if present
            import re
            conf_match = re.search(r'([01](?:\.\d+)?)', llm_response)
            similarity_score = float(conf_match.group(1)) if conf_match else (1.0 if success else 0.0)
            feedback = llm_response.strip()
        except Exception as e:
            self._log_error("LLM evaluation failed, falling back to similarity", error=e)
            # Fallback: always fail
            return EvaluationResult(
                subprompt_id=result.subprompt_id,
                success=False,
                similarity_score=0.0,
                feedback=f"LLM evaluation failed: {e}",
                retry_count=0
            )
        self._log_info("Completed evaluation (LLM)", subprompt_id=result.subprompt_id, success=success, similarity_score=similarity_score)
        return EvaluationResult(
            subprompt_id=result.subprompt_id,
            success=success,
            similarity_score=similarity_score,
            feedback=feedback,
            retry_count=0
        )
    
    def evaluate(self, result: ExecutionResult, subprompt: SubPrompt) -> EvaluationResult:
        return self.process(result, subprompt) 