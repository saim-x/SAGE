from typing import Optional, Dict, Any
import yaml
from pathlib import Path

from .core.models import SAGEConfig, SubPrompt, AggregatedResponse
from .agents.decomposer import DecomposerAgent
from .agents.router import RouterAgent
from .agents.executor import ExecutionManager
from .agents.evaluator import Evaluator
from .agents.aggregator import Aggregator

class SAGE:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the SAGE protocol.
        
        Args:
            config_path: Path to the configuration file. If None, uses default settings.
        """
        self.config = self._load_config(config_path)
        self.decomposer = DecomposerAgent()
        self.router = RouterAgent(self.config)
        self.executor = ExecutionManager(self.config)
        self.evaluator = Evaluator(self.config)
        self.aggregator = Aggregator()

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
        # 1. Decompose the prompt
        subprompts = self.decomposer.decompose(prompt, context)
        
        # 2. Route each subprompt to appropriate model
        assignments = [self.router.route(subprompt) for subprompt in subprompts]
        
        # 3. Execute subprompts and evaluate results
        execution_results = []
        for subprompt, assignment in zip(subprompts, assignments):
            result = self.executor.execute(subprompt, assignment)
            evaluation = self.evaluator.evaluate(result)
            
            # Handle retries if needed
            while not evaluation.success and evaluation.retry_count < self.config.max_retries:
                # Try different model or parameters
                new_assignment = self.router.reassign(subprompt, evaluation)
                result = self.executor.execute(subprompt, new_assignment)
                evaluation = self.evaluator.evaluate(result)
            
            execution_results.append(result)
        
        # 4. Aggregate results
        return self.aggregator.aggregate(execution_results) 