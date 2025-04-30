from typing import List, Dict, Any
import time

from .base import BaseAgent
from ..core.models import ExecutionResult, AggregatedResponse

class Aggregator(BaseAgent):
    """Agent responsible for aggregating execution results into a final response."""
    
    def process(self, results: List[ExecutionResult]) -> AggregatedResponse:
        """Aggregate execution results into a final response.
        
        Args:
            results: List of execution results to aggregate
            
        Returns:
            AggregatedResponse containing the final response and metadata
        """
        self._log_info("Starting result aggregation",
                      num_results=len(results))
        
        # Sort results by execution time to maintain order
        sorted_results = sorted(results, key=lambda r: r.metadata.get("execution_time", 0))
        
        # Combine all successful results
        successful_results = [r for r in sorted_results if r.success]
        final_response = "\n\n".join(r.content for r in successful_results)
        
        # Calculate metadata
        total_execution_time = sum(
            r.metadata.get("execution_time", 0) 
            for r in successful_results
        )
        
        success_rate = len(successful_results) / len(results) if results else 0
        
        aggregated = AggregatedResponse(
            final_response=final_response,
            execution_results=results,
            metadata={
                "total_execution_time": total_execution_time,
                "success_rate": success_rate,
                "num_results": len(results),
                "num_successful": len(successful_results),
                "aggregation_time": time.time()
            }
        )
        
        self._log_info("Completed result aggregation",
                      success_rate=success_rate,
                      total_time=total_execution_time)
        
        return aggregated
    
    def aggregate(self, results: List[ExecutionResult]) -> AggregatedResponse:
        """Alias for process method to maintain consistent interface."""
        return self.process(results) 