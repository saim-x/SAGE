from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

from ..core.models import SAGEConfig

class BaseAgent(ABC):
    """Base class for all SAGE agents."""
    
    def __init__(self, config: SAGEConfig):
        """Initialize the agent with configuration.
        
        Args:
            config: SAGE configuration
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """Process the input and return the result.
        
        This method must be implemented by all subclasses.
        """
        pass
    
    def _log_info(self, message: str, **kwargs):
        """Log an info message with additional context."""
        self.logger.info(f"{message} | Context: {kwargs}")
    
    def _log_error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log an error message with additional context and exception."""
        if error:
            self.logger.error(f"{message} | Error: {str(error)} | Context: {kwargs}")
        else:
            self.logger.error(f"{message} | Context: {kwargs}")
    
    def _log_warning(self, message: str, **kwargs):
        """Log a warning message with additional context."""
        self.logger.warning(f"{message} | Context: {kwargs}")
    
    def _log_debug(self, message: str, **kwargs):
        """Log a debug message with additional context."""
        self.logger.debug(f"{message} | Context: {kwargs}") 