import datetime
from typing import Dict, List, Optional, Any, Tuple

class ScenarioProfile:
    """
    Class to capture scenario-specific parameters for financial planning simulations.
    """
    def __init__(self, 
                 name: str,
                 description: str,
                 market_returns: Dict[str, float],
                 inflation_assumption: float,
                 income_growth_rates: Dict[str, float],
                 expense_patterns: Dict[str, Any],
                 life_events: List[Dict[str, Any]],
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a scenario profile with specific assumptions.
        
        Args:
            name: Unique name for this scenario
            description: Detailed description of what this scenario represents
            market_returns: Dictionary mapping asset classes to expected returns
            inflation_assumption: Annual inflation rate for this scenario
            income_growth_rates: Dictionary of income sources and their growth rates
            expense_patterns: Spending behavior patterns and adjustments
            life_events: List of significant financial events in this scenario
            metadata: Additional information about the scenario
        """
        self.name = name
        self.description = description
        self.market_returns = market_returns
        self.inflation_assumption = inflation_assumption
        self.income_growth_rates = income_growth_rates
        self.expense_patterns = expense_patterns
        self.life_events = life_events
        self.metadata = metadata or {}
        self.created_at = datetime.datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario profile to dictionary for storage."""
        return {
            "name": self.name,
            "description": self.description,
            "market_returns": self.market_returns,
            "inflation_assumption": self.inflation_assumption,
            "income_growth_rates": self.income_growth_rates,
            "expense_patterns": self.expense_patterns,
            "life_events": self.life_events,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScenarioProfile':
        """Create scenario profile from dictionary."""
        created_at = data.pop("created_at", None)
        scenario = cls(**data)
        if created_at:
            scenario.created_at = datetime.datetime.fromisoformat(created_at)
        return scenario


class AlternativeScenarioGenerator:
    """
    Generates meaningful "what-if" scenarios for financial planning and analysis.
    Integrates with existing gap analysis and goal probability modules.
    """
    
    def __init__(self, parameter_service=None):
        """
        Initialize the scenario generator with optional parameter service.
        
        Args:
            parameter_service: Service for accessing financial parameters
        """
        self.parameter_service = parameter_service
        self._stored_scenarios = {}
        self._scenario_defaults = self._initialize_default_parameters()
        
    def _initialize_default_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Initialize default parameters for standard scenario types."""
        return {
            "baseline": {
                "market_returns": {
                    "stocks": 0.07,
                    "bonds": 0.03,
                    "cash": 0.01,
                    "real_estate": 0.04
                },
                "inflation_assumption": 0.025,
                "income_growth_rates": {
                    "primary": 0.03,
                    "secondary": 0.03,
                    "passive": 0.02
                },
                "expense_patterns": {
                    "essential": 1.0,
                    "discretionary": 1.0,
                    "healthcare_inflation_premium": 0.02
                },
                "life_events": []
            },
            "optimistic": {
                "market_returns": {
                    "stocks": 0.09,
                    "bonds": 0.04,
                    "cash": 0.02,
                    "real_estate": 0.06
                },
                "inflation_assumption": 0.02,
                "income_growth_rates": {
                    "primary": 0.045,
                    "secondary": 0.045,
                    "passive": 0.03
                },
                "expense_patterns": {
                    "essential": 0.95,
                    "discretionary": 1.0,
                    "healthcare_inflation_premium": 0.01
                },
                "life_events": []
            },
            "pessimistic": {
                "market_returns": {
                    "stocks": 0.04,
                    "bonds": 0.02,
                    "cash": 0.005,
                    "real_estate": 0.02
                },
                "inflation_assumption": 0.035,
                "income_growth_rates": {
                    "primary": 0.02,
                    "secondary": 0.02,
                    "passive": 0.01
                },
                "expense_patterns": {
                    "essential": 1.1,
                    "discretionary": 1.05,
                    "healthcare_inflation_premium": 0.03
                },
                "life_events": [
                    {
                        "type": "job_loss",
                        "timing": "random",
                        "duration": 6,
                        "impact": "income_reduction",
                        "probability": 0.3
                    }
                ]
            },
            "high_inflation": {
                "market_returns": {
                    "stocks": 0.06,
                    "bonds": 0.02,
                    "cash": 0.01,
                    "real_estate": 0.05
                },
                "inflation_assumption": 0.06,
                "income_growth_rates": {
                    "primary": 0.04,
                    "secondary": 0.04,
                    "passive": 0.02
                },
                "expense_patterns": {
                    "essential": 1.2,
                    "discretionary": 1.1,
                    "healthcare_inflation_premium": 0.03
                },
                "life_events": []
            },
            "early_retirement": {
                "market_returns": {
                    "stocks": 0.07,
                    "bonds": 0.03,
                    "cash": 0.01,
                    "real_estate": 0.04
                },
                "inflation_assumption": 0.025,
                "income_growth_rates": {
                    "primary": 0.03,
                    "secondary": 0.03,
                    "passive": 0.02
                },
                "expense_patterns": {
                    "essential": 1.0,
                    "discretionary": 0.9,
                    "healthcare_inflation_premium": 0.02
                },
                "life_events": [
                    {
                        "type": "retirement",
                        "timing": "early",
                        "years_early": 5,
                        "impact": "income_end",
                        "probability": 1.0
                    }
                ]
            }
        }
    
    def generate_standard_scenarios(self, goals, profile) -> Dict[str, Dict[str, Any]]:
        """
        Generate a set of standard financial planning scenarios.
        
        Args:
            goals: User's financial goals
            profile: User's financial profile
            
        Returns:
            Dictionary of scenarios with their analysis results
        """
        scenarios = {
            "baseline": self.generate_baseline_scenario(goals, profile),
            "optimistic": self.generate_optimistic_scenario(goals, profile),
            "pessimistic": self.generate_pessimistic_scenario(goals, profile),
            "high_inflation": self.generate_high_inflation_scenario(goals, profile),
            "early_retirement": self.generate_early_retirement_scenario(goals, profile)
        }
        
        return scenarios
    
    def generate_targeted_scenario(self, goals, profile, scenario_type: str) -> Dict[str, Any]:
        """
        Generate a specific type of scenario based on predefined parameters.
        
        Args:
            goals: User's financial goals
            profile: User's financial profile
            scenario_type: Type of scenario to generate
            
        Returns:
            Analysis results for the targeted scenario
        """
        if scenario_type not in self._scenario_defaults:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
            
        parameters = self.get_default_parameters(scenario_type)
        name = f"{scenario_type.replace('_', ' ').title()} Scenario"
        description = f"Standard {scenario_type.replace('_', ' ')} scenario"
        
        scenario_profile = ScenarioProfile(
            name=name,
            description=description,
            market_returns=parameters["market_returns"],
            inflation_assumption=parameters["inflation_assumption"],
            income_growth_rates=parameters["income_growth_rates"],
            expense_patterns=parameters["expense_patterns"],
            life_events=parameters["life_events"],
            metadata={"type": scenario_type, "standard": True}
        )
        
        return self._run_scenario_analysis(goals, profile, scenario_profile)
    
    def compare_scenarios(self, baseline_scenario, alternative_scenarios) -> Dict[str, Any]:
        """
        Compare baseline scenario with alternative scenarios to highlight differences.
        
        Args:
            baseline_scenario: The reference scenario to compare against
            alternative_scenarios: Dictionary of scenarios to compare
            
        Returns:
            Detailed comparison of scenarios
        """
        comparison = {
            "baseline": baseline_scenario,
            "alternatives": alternative_scenarios,
            "differences": {},
            "summary": {}
        }
        
        for name, scenario in alternative_scenarios.items():
            comparison["differences"][name] = self._calculate_scenario_differences(
                baseline_scenario, scenario
            )
            comparison["summary"][name] = self._summarize_scenario_comparison(
                name, comparison["differences"][name]
            )
            
        return comparison
    
    def _calculate_scenario_differences(self, baseline, alternative) -> Dict[str, Any]:
        """Calculate detailed differences between two scenarios."""
        differences = {
            "goal_probability_changes": {},
            "retirement_age_impact": None,
            "net_worth_trajectory": {},
            "goal_achievement_timeline": {}
        }
        
        # Calculate differences in goal probabilities
        for goal_id, baseline_prob in baseline.get("goal_probabilities", {}).items():
            alt_prob = alternative.get("goal_probabilities", {}).get(goal_id, 0)
            differences["goal_probability_changes"][goal_id] = alt_prob - baseline_prob
            
        # Compare retirement timing
        if "retirement_age" in baseline and "retirement_age" in alternative:
            differences["retirement_age_impact"] = alternative["retirement_age"] - baseline["retirement_age"]
            
        # Compare net worth at key points
        for year in [5, 10, 20, 30]:
            key = f"year_{year}"
            if key in baseline.get("net_worth_projection", {}) and key in alternative.get("net_worth_projection", {}):
                differences["net_worth_trajectory"][key] = (
                    alternative["net_worth_projection"][key] - 
                    baseline["net_worth_projection"][key]
                )
                
        # Compare goal achievement timelines
        for goal_id, baseline_time in baseline.get("goal_achievement_timeline", {}).items():
            alt_time = alternative.get("goal_achievement_timeline", {}).get(goal_id)
            if alt_time:
                differences["goal_achievement_timeline"][goal_id] = alt_time - baseline_time
                
        return differences
    
    def _summarize_scenario_comparison(self, scenario_name, differences) -> Dict[str, str]:
        """Create human-readable summary of scenario comparison."""
        summary = {
            "title": f"Impact of {scenario_name.replace('_', ' ').title()} Scenario",
            "overall_assessment": "",
            "key_findings": []
        }
        
        # Analyze goal probability changes
        prob_changes = differences.get("goal_probability_changes", {})
        if prob_changes:
            improved_goals = sum(1 for change in prob_changes.values() if change > 0.05)
            worsened_goals = sum(1 for change in prob_changes.values() if change < -0.05)
            
            if improved_goals > worsened_goals:
                summary["key_findings"].append(
                    f"{improved_goals} goals have significantly improved probability"
                )
            elif worsened_goals > improved_goals:
                summary["key_findings"].append(
                    f"{worsened_goals} goals have significantly reduced probability"
                )
                
        # Analyze retirement impact
        ret_impact = differences.get("retirement_age_impact")
        if ret_impact:
            if ret_impact < 0:
                summary["key_findings"].append(
                    f"Retirement possible {abs(ret_impact):.1f} years earlier"
                )
            elif ret_impact > 0:
                summary["key_findings"].append(
                    f"Retirement delayed by {ret_impact:.1f} years"
                )
                
        # Analyze net worth impact
        long_term_impact = differences.get("net_worth_trajectory", {}).get("year_30")
        if long_term_impact:
            if long_term_impact > 0:
                summary["key_findings"].append(
                    f"Long-term net worth increases by ${long_term_impact:,.0f}"
                )
            else:
                summary["key_findings"].append(
                    f"Long-term net worth decreases by ${abs(long_term_impact):,.0f}"
                )
                
        # Overall assessment
        if summary["key_findings"]:
            if any("decreases" in finding or "delayed" in finding for finding in summary["key_findings"]):
                summary["overall_assessment"] = "This scenario presents significant challenges to your financial plan."
            else:
                summary["overall_assessment"] = "This scenario could positively impact your financial outcomes."
        else:
            summary["overall_assessment"] = "This scenario has minimal impact on your financial plan."
            
        return summary
    
    def _run_scenario_analysis(self, goals, profile, scenario_profile) -> Dict[str, Any]:
        """
        Run a full analysis of a scenario with the given parameters.
        
        This is where integration with gap analysis and goal probability would occur.
        """
        # This would typically invoke the gap analysis and goal probability modules
        # For now, we'll return a placeholder result structure
        return {
            "scenario_profile": scenario_profile.to_dict(),
            "goal_probabilities": {},  # Would be populated by goal probability module
            "gap_analysis_results": {},  # Would be populated by gap analysis module
            "net_worth_projection": {},
            "goal_achievement_timeline": {},
            "retirement_age": None,
            "analysis_date": datetime.datetime.now().isoformat()
        }
    
    def generate_baseline_scenario(self, goals, profile) -> Dict[str, Any]:
        """
        Generate baseline scenario using current assumptions.
        
        Args:
            goals: User's financial goals
            profile: User's financial profile
            
        Returns:
            Analysis results for baseline scenario
        """
        parameters = self.get_default_parameters("baseline")
        
        # Customize baseline parameters based on user's actual information if available
        if self.parameter_service:
            try:
                # Update with user's actual parameters if available
                user_inflation = self.parameter_service.get_inflation_assumption(profile.id)
                if user_inflation:
                    parameters["inflation_assumption"] = user_inflation
                
                user_returns = self.parameter_service.get_return_assumptions(profile.id)
                if user_returns:
                    parameters["market_returns"].update(user_returns)
            except Exception as e:
                # Fallback to defaults if parameter service fails
                pass
        
        scenario_profile = ScenarioProfile(
            name="Baseline Scenario",
            description="Current financial trajectory based on existing assumptions",
            market_returns=parameters["market_returns"],
            inflation_assumption=parameters["inflation_assumption"],
            income_growth_rates=parameters["income_growth_rates"],
            expense_patterns=parameters["expense_patterns"],
            life_events=parameters["life_events"],
            metadata={"type": "baseline", "standard": True}
        )
        
        return self._run_scenario_analysis(goals, profile, scenario_profile)
    
    def generate_optimistic_scenario(self, goals, profile) -> Dict[str, Any]:
        """
        Generate optimistic scenario with favorable market returns and career outcomes.
        
        Args:
            goals: User's financial goals
            profile: User's financial profile
            
        Returns:
            Analysis results for optimistic scenario
        """
        parameters = self.get_default_parameters("optimistic")
        
        scenario_profile = ScenarioProfile(
            name="Optimistic Scenario",
            description="Favorable economic conditions with strong market returns and career growth",
            market_returns=parameters["market_returns"],
            inflation_assumption=parameters["inflation_assumption"],
            income_growth_rates=parameters["income_growth_rates"],
            expense_patterns=parameters["expense_patterns"],
            life_events=parameters["life_events"],
            metadata={"type": "optimistic", "standard": True}
        )
        
        return self._run_scenario_analysis(goals, profile, scenario_profile)
    
    def generate_pessimistic_scenario(self, goals, profile) -> Dict[str, Any]:
        """
        Generate pessimistic scenario with poor market returns and financial challenges.
        
        Args:
            goals: User's financial goals
            profile: User's financial profile
            
        Returns:
            Analysis results for pessimistic scenario
        """
        parameters = self.get_default_parameters("pessimistic")
        
        scenario_profile = ScenarioProfile(
            name="Pessimistic Scenario",
            description="Challenging economic conditions with lower returns and potential job insecurity",
            market_returns=parameters["market_returns"],
            inflation_assumption=parameters["inflation_assumption"],
            income_growth_rates=parameters["income_growth_rates"],
            expense_patterns=parameters["expense_patterns"],
            life_events=parameters["life_events"],
            metadata={"type": "pessimistic", "standard": True}
        )
        
        return self._run_scenario_analysis(goals, profile, scenario_profile)
    
    def generate_high_inflation_scenario(self, goals, profile) -> Dict[str, Any]:
        """
        Generate high inflation scenario for testing inflation resilience.
        
        Args:
            goals: User's financial goals
            profile: User's financial profile
            
        Returns:
            Analysis results for high inflation scenario
        """
        parameters = self.get_default_parameters("high_inflation")
        
        scenario_profile = ScenarioProfile(
            name="High Inflation Scenario",
            description="Elevated inflation environment with increased living costs",
            market_returns=parameters["market_returns"],
            inflation_assumption=parameters["inflation_assumption"],
            income_growth_rates=parameters["income_growth_rates"],
            expense_patterns=parameters["expense_patterns"],
            life_events=parameters["life_events"],
            metadata={"type": "high_inflation", "standard": True}
        )
        
        return self._run_scenario_analysis(goals, profile, scenario_profile)
    
    def generate_early_retirement_scenario(self, goals, profile) -> Dict[str, Any]:
        """
        Generate early retirement scenario for earlier retirement planning.
        
        Args:
            goals: User's financial goals
            profile: User's financial profile
            
        Returns:
            Analysis results for early retirement scenario
        """
        parameters = self.get_default_parameters("early_retirement")
        
        scenario_profile = ScenarioProfile(
            name="Early Retirement Scenario",
            description="Analysis of retiring 5 years earlier than planned",
            market_returns=parameters["market_returns"],
            inflation_assumption=parameters["inflation_assumption"],
            income_growth_rates=parameters["income_growth_rates"],
            expense_patterns=parameters["expense_patterns"],
            life_events=parameters["life_events"],
            metadata={"type": "early_retirement", "standard": True}
        )
        
        return self._run_scenario_analysis(goals, profile, scenario_profile)
    
    def set_scenario_parameters(self, scenario_type: str, parameters: Dict[str, Any]) -> None:
        """
        Update default parameters for a scenario type.
        
        Args:
            scenario_type: Type of scenario to update
            parameters: New parameters to set
        """
        if scenario_type not in self._scenario_defaults:
            self._scenario_defaults[scenario_type] = {}
            
        # Update only the specified parameters
        for key, value in parameters.items():
            if key in self._scenario_defaults[scenario_type]:
                if isinstance(value, dict) and isinstance(self._scenario_defaults[scenario_type][key], dict):
                    self._scenario_defaults[scenario_type][key].update(value)
                else:
                    self._scenario_defaults[scenario_type][key] = value
            else:
                self._scenario_defaults[scenario_type][key] = value
    
    def get_default_parameters(self, scenario_type: str) -> Dict[str, Any]:
        """
        Retrieve default parameters for a scenario type.
        
        Args:
            scenario_type: Type of scenario
            
        Returns:
            Dictionary of default parameters for the scenario
        """
        if scenario_type not in self._scenario_defaults:
            raise ValueError(f"Unknown scenario type: {scenario_type}")
            
        # Return a deep copy to prevent unintended modifications
        import copy
        return copy.deepcopy(self._scenario_defaults[scenario_type])
    
    def create_custom_scenario(self, goals, profile, custom_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create user-defined scenario with custom parameters.
        
        Args:
            goals: User's financial goals
            profile: User's financial profile
            custom_parameters: User-defined scenario parameters
            
        Returns:
            Analysis results for custom scenario
        """
        required_fields = ["name", "description", "market_returns", "inflation_assumption",
                          "income_growth_rates", "expense_patterns"]
        
        # Validate required fields
        for field in required_fields:
            if field not in custom_parameters:
                raise ValueError(f"Missing required field in custom parameters: {field}")
                
        # Create scenario profile
        scenario_profile = ScenarioProfile(
            name=custom_parameters["name"],
            description=custom_parameters["description"],
            market_returns=custom_parameters["market_returns"],
            inflation_assumption=custom_parameters["inflation_assumption"],
            income_growth_rates=custom_parameters["income_growth_rates"],
            expense_patterns=custom_parameters["expense_patterns"],
            life_events=custom_parameters.get("life_events", []),
            metadata=custom_parameters.get("metadata", {"type": "custom", "standard": False})
        )
        
        return self._run_scenario_analysis(goals, profile, scenario_profile)
    
    def save_scenario(self, scenario: Dict[str, Any], name: str) -> None:
        """
        Save scenario for later reuse.
        
        Args:
            scenario: Scenario to save
            name: Name to save the scenario under
        """
        self._stored_scenarios[name] = scenario
        
        # In a real implementation, this would persist to database
        # For example:
        # if self.parameter_service and hasattr(self.parameter_service, 'save_scenario'):
        #     self.parameter_service.save_scenario(name, scenario)
    
    def load_scenario(self, name: str) -> Dict[str, Any]:
        """
        Load previously saved scenario.
        
        Args:
            name: Name of scenario to load
            
        Returns:
            Saved scenario
        """
        # Check in-memory cache first
        if name in self._stored_scenarios:
            return self._stored_scenarios[name]
            
        # In a real implementation, this would also check the database
        # For example:
        # if self.parameter_service and hasattr(self.parameter_service, 'get_scenario'):
        #     scenario = self.parameter_service.get_scenario(name)
        #     if scenario:
        #         self._stored_scenarios[name] = scenario
        #         return scenario
                
        raise ValueError(f"Scenario not found: {name}")