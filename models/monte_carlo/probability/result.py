"""
ProbabilityResult Module

This module provides the ProbabilityResult class for structured results
from probability analyses.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union

@dataclass
class ProbabilityResult:
    """
    Structured result class for probability analysis results.
    
    This class organizes probability analysis results in a structured format
    that's easy to consume by front-end displays and decision-making processes.
    It provides a consistent interface for accessing probability data across
    different goal types, with strong error handling and backwards compatibility.
    
    The class follows a nested dictionary structure to organize metrics by category:
    - success_metrics: Core probability and success/failure metrics
    - time_based_metrics/time_metrics: Time-related probability evolution
    - distribution_data: Statistical distribution information for visualizations
    - risk_metrics: Risk assessment and volatility metrics
    - goal_specific_metrics: Category-specific metrics for specialized analysis
    
    The class provides both dictionary-style access and property accessors for
    commonly used metrics, with safe error handling for missing data.
    
    Integration notes:
    - Services should use the get_safe_success_probability() method for robust integration
    - The class provides backwards compatibility for legacy field names
    - All property accessors safely handle missing data with appropriate defaults
    - The to_dict() method produces a JSON-serializable dictionary for API responses
    """
    # Basic success metrics
    success_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Time-based probability metrics
    time_based_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Distribution data for visualizations
    distribution_data: Dict[str, Any] = field(default_factory=dict)
    
    # Risk assessment metrics
    risk_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Goal-specific metrics
    goal_specific_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # API compatibility properties
    probability: float = 0.0
    factors: List[Dict[str, Any]] = field(default_factory=list)
    simulation_results: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_probability(self) -> float:
        """Return the success probability value from success_metrics"""
        return self.success_metrics.get("success_probability", 0.0)
    
    # Add property for backward compatibility with time_metrics naming
    @property
    def time_metrics(self) -> Dict[str, Any]:
        """Backwards compatibility for time_metrics (alias for time_based_metrics)."""
        return self.time_based_metrics
    
    @time_metrics.setter
    def time_metrics(self, value: Dict[str, Any]) -> None:
        """Setter for backwards compatibility with time_metrics."""
        self.time_based_metrics = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary for API responses."""
        return {
            "success_metrics": self.success_metrics,
            "time_based_metrics": self.time_based_metrics,
            "time_metrics": self.time_based_metrics,  # Include both names in output
            "distribution_data": self.distribution_data,
            "risk_metrics": self.risk_metrics,
            "goal_specific_metrics": self.goal_specific_metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProbabilityResult':
        """Create a ProbabilityResult from a dictionary."""
        # Handle both time_metrics and time_based_metrics for backward compatibility
        time_based = data.get('time_based_metrics', {})
        time_metrics = data.get('time_metrics', {})
        # If time_metrics exists but time_based_metrics doesn't, use time_metrics
        if not time_based and time_metrics:
            time_based = time_metrics
            
        return cls(
            success_metrics=data.get('success_metrics', {}),
            time_based_metrics=time_based,
            distribution_data=data.get('distribution_data', {}),
            risk_metrics=data.get('risk_metrics', {}),
            goal_specific_metrics=data.get('goal_specific_metrics', {})
        )
        
    def safe_get(self, dict_name: str, key: str, default: Any = None) -> Any:
        """
        Safely get a value from a nested dictionary.
        
        Args:
            dict_name: Name of the dictionary attribute ("success_metrics", etc.)
            key: Key to look up in the dictionary
            default: Default value to return if key is not found
            
        Returns:
            The value if found, otherwise the default
        """
        try:
            dict_obj = getattr(self, dict_name, {})
            if not isinstance(dict_obj, dict):
                return default
            return dict_obj.get(key, default)
        except (AttributeError, KeyError):
            return default
    
    def get_safe_success_probability(self) -> float:
        """
        Get the success probability safely, handling edge cases.
        
        Returns:
            A float value between 0.0 and 1.0
        """
        try:
            prob = self.success_probability
            if not isinstance(prob, (int, float)):
                return 0.0
            return max(0.0, min(1.0, float(prob)))
        except (TypeError, ValueError):
            return 0.0