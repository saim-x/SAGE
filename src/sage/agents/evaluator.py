from typing import Dict, Any, Optional
from .base import BaseAgent
from ..core.models import SubPrompt, ExecutionResult, EvaluationResult
from ..core.utils import call_ollama
import difflib
from sentence_transformers import SentenceTransformer, util

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
            import re
            conf_match = re.search(r'([01](?:\.\d+)?)', llm_response)
            similarity_score = float(conf_match.group(1)) if conf_match else 0.0
            feedback = llm_response.strip()
            threshold = getattr(self.config, 'similarity_threshold', 0.9)
            if 'yes' in llm_response_lower:
                success = True
            elif 'no' in llm_response_lower:
                success = False
            elif conf_match:
                # If confidence is high, treat as success
                if similarity_score >= threshold:
                    self._log_warning("LLM response ambiguous but confidence high, treating as success", subprompt_id=result.subprompt_id, confidence=similarity_score)
                    success = True
                else:
                    self._log_warning("LLM response ambiguous and confidence low, treating as failure", subprompt_id=result.subprompt_id, confidence=similarity_score)
                    success = False
            else:
                self._log_warning("LLM response ambiguous and no confidence found, treating as failure", subprompt_id=result.subprompt_id)
                success = False
        except Exception as e:
            self._log_error("LLM evaluation using Ollama failed, falling back to semantic similarity", error=e)
            # Fallback: use semantic similarity between result.content and subprompt.content
            answer = result.content or ""
            question = subprompt.content or ""
            similarity_score = 0.0
            threshold = getattr(self.config, 'similarity_threshold', 0.9)
            feedback = ""
            try:
                model = SentenceTransformer('all-MiniLM-L6-v2')
                emb_answer = model.encode(answer, convert_to_tensor=True)
                emb_question = model.encode(question, convert_to_tensor=True)
                similarity_score = float(util.pytorch_cos_sim(emb_answer, emb_question).item())
                feedback = f"Semantic similarity score: {similarity_score:.2f} (threshold: {threshold})"
            except Exception as embed_e:
                similarity_score = difflib.SequenceMatcher(None, answer, question).ratio() if answer and question else 0.0
                feedback = f"Fallback string similarity score: {similarity_score:.2f} (threshold: {threshold}) (embedding error: {embed_e})"
            success = similarity_score >= threshold
            return EvaluationResult(
                subprompt_id=result.subprompt_id,
                success=success,
                similarity_score=similarity_score,
                feedback=feedback,
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