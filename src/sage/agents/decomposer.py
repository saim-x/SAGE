from typing import List, Dict, Any, Optional
import uuid
import re

from .base import BaseAgent
from ..core.models import SubPrompt, TaskType

class DecomposerAgent(BaseAgent):
    """Agent responsible for breaking down user prompts into sub-tasks."""
    
    def process(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[SubPrompt]:
        """Process the input prompt and break it down into sub-tasks.
        
        Args:
            prompt: The user's input prompt
            context: Optional context information
            
        Returns:
            List of SubPrompt objects representing the decomposed tasks
        """
        self._log_info("Starting prompt decomposition", prompt=prompt)
        # Rule-based split for numbered steps
        steps = re.split(r'\d+\. ', prompt)
        steps = [s.strip() for s in steps if s.strip()]
        subprompts = []
        for i, step in enumerate(steps):
            # Heuristic: assign task type and expected goal
            step_lower = step.lower()
            if "analyz" in step_lower:
                task_type = TaskType.ANALYSIS
                expected_goal = "Identify and explain main challenges"
            elif "propos" in step_lower or "solution" in step_lower:
                task_type = TaskType.TECHNICAL
                expected_goal = "Propose a technical solution with sensors, data infrastructure, and AI models"
            elif "summary" in step_lower or "persuasive" in step_lower:
                task_type = TaskType.CREATIVE
                expected_goal = "Write a persuasive summary for city officials"
            else:
                task_type = TaskType.OTHER
                expected_goal = "Complete the sub-task"
            subprompts.append(
                SubPrompt(
                    id=str(uuid.uuid4()),
                    content=step,
                    task_type=task_type,
                    expected_goal=expected_goal,
                    context=context if i == 0 else None,
                    dependencies=[subprompts[i-1].id] if i > 0 else []
                )
            )
        self._log_info("Completed prompt decomposition", num_subprompts=len(subprompts))
        return subprompts
    
    def decompose(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> List[SubPrompt]:
        """Alias for process method to maintain consistent interface."""
        return self.process(prompt, context) 