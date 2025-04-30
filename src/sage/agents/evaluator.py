from typing import Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from .base import BaseAgent
from ..core.models import SubPrompt, ExecutionResult, EvaluationResult

class Evaluator(BaseAgent):
    """Agent responsible for evaluating execution results against expected goals."""
    
    def process(self, result: ExecutionResult) -> EvaluationResult:
        """Evaluate an execution result against its expected goal.
        
        Args:
            result: The execution result to evaluate
            
        Returns:
            EvaluationResult containing the evaluation outcome
        """
        self._log_info("Evaluating execution result",
                      subprompt_id=result.subprompt_id)
        
        if not result.success:
            return EvaluationResult(
                subprompt_id=result.subprompt_id,
                success=False,
                similarity_score=0.0,
                feedback="Execution failed",
                retry_count=0
            )
        
        # Calculate similarity between result and expected goal
        similarity_score = self._calculate_similarity(
            result.content,
            result.subprompt.expected_goal
        )
        
        success = similarity_score >= self.config.similarity_threshold
        
        evaluation = EvaluationResult(
            subprompt_id=result.subprompt_id,
            success=success,
            similarity_score=similarity_score,
            feedback=self._generate_feedback(success, similarity_score),
            retry_count=0
        )
        
        self._log_info("Completed evaluation",
                      subprompt_id=result.subprompt_id,
                      success=success,
                      similarity_score=similarity_score)
        
        return evaluation
    
    def evaluate(self, result: ExecutionResult) -> EvaluationResult:
        """Alias for process method to maintain consistent interface."""
        return self.process(result)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using TF-IDF and cosine similarity."""
        vectorizer = TfidfVectorizer()
        try:
            # Create TF-IDF vectors
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
        except Exception as e:
            self._log_error("Failed to calculate similarity",
                          error=e,
                          text1=text1[:100],  # Log first 100 chars
                          text2=text2[:100])
            return 0.0
    
    def _generate_feedback(self, success: bool, similarity_score: float) -> str:
        """Generate feedback based on evaluation results."""
        if success:
            return f"Response meets quality threshold (similarity: {similarity_score:.2f})"
        else:
            return f"Response does not meet quality threshold (similarity: {similarity_score:.2f})" 