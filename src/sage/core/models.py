from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TaskType(str, Enum):
    CREATIVE = "creative"
    TECHNICAL = "technical"
    SUMMARIZATION = "summarization"
    ANALYSIS = "analysis"
    CODE = "code"
    OTHER = "other"

class SubPrompt(BaseModel):
    id: str
    content: str
    task_type: TaskType
    expected_goal: str
    context: Optional[Dict[str, Any]] = None
    dependencies: List[str] = Field(default_factory=list)

class ModelAssignment(BaseModel):
    model_name: str
    model_provider: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    model_config = {'protected_namespaces': ()}

class ExecutionResult(BaseModel):
    subprompt_id: str
    content: str
    model_used: ModelAssignment
    success: bool
    similarity_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_config = {'protected_namespaces': ()}

class EvaluationResult(BaseModel):
    subprompt_id: str
    success: bool
    similarity_score: float
    feedback: Optional[str] = None
    retry_count: int = 0

class AggregatedResponse(BaseModel):
    final_response: str
    execution_results: List[ExecutionResult]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SAGEConfig(BaseModel):
    """
    Configuration for SAGE protocol. Only local Ollama models are supported in this version.
    """
    similarity_threshold: float = 0.9
    max_retries: int = 3
    default_model: str = "gemma3:4b"
    available_models: List[str] = Field(default_factory=lambda: ["gemma3:4b", "deepseek-r1:1.5b", "qwen3:1.7b"])
    model_assignments: Dict[TaskType, str] = Field(default_factory=dict)
    model_parameters: Dict[str, dict] = Field(default_factory=dict)
    evaluator_model: Optional[str] = None
    model_config = {'protected_namespaces': ()} 