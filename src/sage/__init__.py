import logging
from typing import Optional, Dict, Any
import yaml
from pathlib import Path
import random

from .core.models import SAGEConfig, SubPrompt, AggregatedResponse
from .agents.decomposer import DecomposerAgent
from .agents.router import RouterAgent
from .agents.executor import ExecutionManager
from .agents.evaluator import Evaluator
from .agents.aggregator import Aggregator

# Setup file logger
logger = logging.getLogger("SAGEProtocol")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("sage_protocol.log")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(file_handler)

class SAGE:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the SAGE protocol.
        
        Args:
            config_path: Path to the configuration file. If None, uses default settings.
        """
        self.config = self._load_config(config_path)
        self.decomposer = DecomposerAgent(self.config)
        self.router = RouterAgent(self.config)
        self.executor = ExecutionManager(self.config)
        self.evaluator = Evaluator(self.config)
        self.aggregator = Aggregator(self.config)

    def _load_config(self, config_path: Optional[str]) -> SAGEConfig:
        """Load configuration from YAML file or use defaults."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        
        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f)
        
        return SAGEConfig(**config_dict)

    def process_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> AggregatedResponse:
        """Process a user prompt through the SAGE workflow.
        
        Args:
            prompt: The user's input prompt
            context: Optional context information
            
        Returns:
            AggregatedResponse containing the final result and execution details
        """
        print(f"\n[INFO] Processing prompt: {prompt}\n")
        logger.info(f"Processing prompt: {prompt}")
        # 1. Decompose the prompt
        subprompts = self.decomposer.decompose(prompt, context)
        print(f"[INFO] Decomposed into {len(subprompts)} sub-prompts:")
        for i, sp in enumerate(subprompts):
            print(f"  SubPrompt {i+1}: {sp.content} (type: {sp.task_type})")
        logger.info(f"Decomposed into {len(subprompts)} subprompts.")
        
        # 2. Route each subprompt to appropriate model (meta-router only once, fallback to gemma3:4b)
        assignments = []
        for i, subprompt in enumerate(subprompts):
            print(f"\n[INFO] Assigning model for SubPrompt {i+1}: {subprompt.content}")
            print(f"[INFO] Expected answer for SubPrompt {i+1}: {subprompt.expected_goal}")
            logger.info(f"Expected answer for SubPrompt {i+1}: {subprompt.expected_goal}")
            try:
                assignment = self.router.route(subprompt)
                if assignment.model_name not in self.config.available_models:
                    print(f"[WARN] Meta-router failed, assigning 'gemma3:4b' to SubPrompt {i+1}")
                    assignment = assignment.copy(update={
                        'model_name': 'gemma3:4b',
                        'model_provider': self.router._get_provider('gemma3:4b'),
                        'parameters': self.config.model_parameters.get('gemma3:4b', {})
                    })
            except Exception as e:
                print(f"[WARN] Meta-router exception: {e}. Assigning 'gemma3:4b' to SubPrompt {i+1}")
                assignment = self.router.route(subprompt)
                assignment = assignment.copy(update={
                    'model_name': 'gemma3:4b',
                    'model_provider': self.router._get_provider('gemma3:4b'),
                    'parameters': self.config.model_parameters.get('gemma3:4b', {})
                })
            print(f"[INFO] Assigned model: {assignment.model_name}")
            assignments.append(assignment)
        logger.info(f"Initial model assignments: {[a.model_name for a in assignments]}")
        
        # 3. Execute subprompts and evaluate results
        execution_results = []
        previous_output = None
        for idx, (subprompt, assignment) in enumerate(zip(subprompts, assignments)):
            if previous_output:
                # Chain previous output as context
                if subprompt.context is None:
                    subprompt.context = {}
                subprompt.context["previous_output"] = previous_output
            tried_models = set()
            retry_count = 0
            attempts = []  # Track all attempts for this sub-prompt
            result = self.executor.execute(subprompt, assignment)
            tried_models.add(assignment.model_name)
            evaluation = self.evaluator.evaluate(result, subprompt)
            attempts.append((result, evaluation))
            print(f"[INFO] SubPrompt {idx+1} | Attempt 1 | Model: {assignment.model_name} | Similarity: {evaluation.similarity_score:.2f} | Success: {evaluation.success}")
            print(f"[INFO] Model Output: {result.content[:200]}{'...' if len(result.content) > 200 else ''}")
            logger.info(f"[SubPrompt {subprompt.id}] Attempt 1 - Model: {assignment.model_name} - Similarity: {evaluation.similarity_score:.2f} - Success: {evaluation.success}")
            # Only allow retries with random fallback if initial model fails
            while not evaluation.success and retry_count < self.config.max_retries:
                available_models = [m for m in self.config.available_models if m not in tried_models]
                if not available_models:
                    logger.warning(f"[SubPrompt {subprompt.id}] All models tried. Skipping further retries.")
                    break
                model_name = random.choice(available_models)
                model_params = self.config.model_parameters.get(model_name, {})
                new_assignment = assignment.copy(update={
                    'model_name': model_name,
                    'model_provider': self.router._get_provider(model_name),
                    'parameters': model_params
                })
                result = self.executor.execute(subprompt, new_assignment)
                tried_models.add(new_assignment.model_name)
                evaluation = self.evaluator.evaluate(result, subprompt)
                attempts.append((result, evaluation))
                retry_count += 1
                print(f"[INFO] SubPrompt {idx+1} | Attempt {retry_count+1} | Model: {model_name} | Similarity: {evaluation.similarity_score:.2f} | Success: {evaluation.success}")
                print(f"[INFO] Model Output: {result.content[:200]}{'...' if len(result.content) > 200 else ''}")
                logger.info(f"[SubPrompt {subprompt.id}] Attempt {retry_count+1} - Model: {model_name} - Similarity: {evaluation.similarity_score:.2f} - Success: {evaluation.success}")
            # Select the best attempt (highest similarity)
            best_result, best_eval = max(attempts, key=lambda x: x[1].similarity_score)
            previous_output = best_result.content  # For next subprompt
            if not best_eval.success:
                print(f"[WARN] SubPrompt {idx+1} did not meet the similarity threshold. Returning best attempt.")
                logger.error(f"[SubPrompt {subprompt.id}] All attempts below threshold. Returning best attempt with similarity {best_eval.similarity_score:.2f}")
            execution_results.append(best_result)
        # 4. Aggregate results
        logger.info("Aggregating results.")
        agg = self.aggregator.aggregate(execution_results)
        logger.info(f"Final aggregated response: {agg.final_response}")
        return agg 