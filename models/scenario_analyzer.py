import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
import math
import statistics
from collections import defaultdict

class ScenarioComparisonResult:
    """
    Structured container for scenario analysis results, supporting rich comparison
    and insight generation.
    """
    
    def __init__(self, 
                 scenarios: Dict[str, Dict[str, Any]],
                 goals: List[Any],
                 profile: Any):
        """
        Initialize a scenario comparison result.
        
        Args:
            scenarios: Dictionary mapping scenario names to their analysis results
            goals: List of financial goals being evaluated
            profile: User's financial profile
        """
        self.scenarios = scenarios
        self.baseline_name = next((name for name in scenarios if "baseline" in name.lower()), 
                                  next(iter(scenarios.keys())))
        self.goal_outcomes = {}
        self.success_metrics = {}
        self.difference_metrics = {}
        self.sensitivity_analysis = {}
        self.processed_at = datetime.datetime.now()
        
        # Process goals
        self.goal_ids = [goal.id if hasattr(goal, 'id') else i 
                         for i, goal in enumerate(goals)]
        
        # Initialize structures
        self._initialize_outcome_structures(goals)
        
    def _initialize_outcome_structures(self, goals: List[Any]) -> None:
        """Initialize data structures for storing analysis results."""
        # Initialize goal outcomes for each scenario
        for goal_id in self.goal_ids:
            self.goal_outcomes[goal_id] = {}
            for scenario_name in self.scenarios:
                self.goal_outcomes[goal_id][scenario_name] = {
                    "probability": None,
                    "timeline": None,
                    "funding_gap": None,
                    "achievable": None
                }
        
        # Initialize success metrics for each scenario
        for scenario_name in self.scenarios:
            self.success_metrics[scenario_name] = {
                "overall_success_rate": None,
                "retirement_age": None,
                "net_worth_progression": {},
                "goal_achievement_rate": None,
                "financial_resilience_score": None
            }
            
            # Initialize difference metrics (comparison to baseline)
            if scenario_name != self.baseline_name:
                self.difference_metrics[scenario_name] = {
                    "success_rate_change": None,
                    "retirement_age_change": None,
                    "net_worth_impact": {},
                    "goal_achievement_change": None,
                    "financial_resilience_change": None
                }
    
    def set_goal_outcome(self, goal_id: Any, scenario_name: str, 
                        outcome_type: str, value: Any) -> None:
        """Set a specific goal outcome value."""
        if goal_id in self.goal_outcomes and scenario_name in self.goal_outcomes[goal_id]:
            self.goal_outcomes[goal_id][scenario_name][outcome_type] = value
    
    def set_success_metric(self, scenario_name: str, metric_name: str, value: Any) -> None:
        """Set a specific success metric value."""
        if scenario_name in self.success_metrics:
            self.success_metrics[scenario_name][metric_name] = value
    
    def set_difference_metric(self, scenario_name: str, metric_name: str, value: Any) -> None:
        """Set a specific difference metric value."""
        if scenario_name in self.difference_metrics:
            self.difference_metrics[scenario_name][metric_name] = value
    
    def add_sensitivity_result(self, variable: str, impact_score: float, 
                              affected_goals: List[Any]) -> None:
        """Add a sensitivity analysis result."""
        self.sensitivity_analysis[variable] = {
            "impact_score": impact_score,
            "affected_goals": affected_goals
        }
    
    def get_most_sensitive_variables(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Return the most impactful variables from sensitivity analysis."""
        sorted_variables = sorted(
            self.sensitivity_analysis.items(), 
            key=lambda x: x[1]["impact_score"], 
            reverse=True
        )
        return sorted_variables[:limit]
    
    def get_best_alternative_scenario(self) -> Optional[str]:
        """Identify the best alternative scenario based on overall improvement."""
        if not self.difference_metrics:
            return None
            
        # Calculate an overall score for each alternative scenario
        scenario_scores = {}
        for scenario_name, metrics in self.difference_metrics.items():
            # Simple scoring: success rate change (normalized) + retirement age change (negative is good)
            success_change = metrics.get("success_rate_change", 0) or 0
            retirement_change = metrics.get("retirement_age_change", 0) or 0
            # Retirement age: negative is better (earlier retirement)
            retirement_score = -retirement_change if retirement_change else 0
            
            # Net worth impact at longest timeframe
            net_worth_keys = sorted(metrics.get("net_worth_impact", {}).keys())
            net_worth_change = 0
            if net_worth_keys:
                longest_timeframe = net_worth_keys[-1]
                net_worth_change = metrics["net_worth_impact"].get(longest_timeframe, 0) or 0
                # Normalize to a 0-1 scale based on a $1M change being "significant"
                net_worth_score = min(1.0, net_worth_change / 1000000) if net_worth_change > 0 else max(-1.0, net_worth_change / 1000000)
            else:
                net_worth_score = 0
                
            # Goal achievement change
            goal_change = metrics.get("goal_achievement_change", 0) or 0
            
            # Overall score (simple weighted sum)
            scenario_scores[scenario_name] = (
                success_change * 0.3 +
                retirement_score * 0.3 +
                net_worth_score * 0.2 +
                goal_change * 0.2
            )
            
        # Return the scenario with the highest score
        if scenario_scores:
            return max(scenario_scores.items(), key=lambda x: x[1])[0]
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert comparison results to dictionary for storage or serialization."""
        return {
            "scenarios": [name for name in self.scenarios],
            "baseline_name": self.baseline_name,
            "goal_outcomes": self.goal_outcomes,
            "success_metrics": self.success_metrics,
            "difference_metrics": self.difference_metrics,
            "sensitivity_analysis": self.sensitivity_analysis,
            "processed_at": self.processed_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], scenarios: Dict[str, Dict[str, Any]], 
                 goals: List[Any], profile: Any) -> 'ScenarioComparisonResult':
        """Create scenario comparison result from dictionary."""
        result = cls(scenarios, goals, profile)
        result.baseline_name = data.get("baseline_name", result.baseline_name)
        result.goal_outcomes = data.get("goal_outcomes", {})
        result.success_metrics = data.get("success_metrics", {})
        result.difference_metrics = data.get("difference_metrics", {})
        result.sensitivity_analysis = data.get("sensitivity_analysis", {})
        
        if "processed_at" in data:
            result.processed_at = datetime.datetime.fromisoformat(data["processed_at"])
            
        return result


class ScenarioAnalyzer:
    """
    Analyzes financial scenarios to provide actionable insights and comparisons.
    Builds on the AlternativeScenarioGenerator to evaluate scenario impacts.
    """
    
    def __init__(self, parameter_service=None, goal_probability_service=None):
        """
        Initialize the scenario analyzer with optional services.
        
        Args:
            parameter_service: Service for accessing financial parameters
            goal_probability_service: Service for calculating goal probabilities
        """
        self.parameter_service = parameter_service
        self.goal_probability_service = goal_probability_service
        
    def analyze_scenario_impact(self, scenario: Dict[str, Any], 
                               goals: List[Any], profile: Any) -> Dict[str, Any]:
        """
        Evaluate the effects of a scenario across all goals.
        
        Args:
            scenario: The scenario to analyze
            goals: List of financial goals
            profile: User's financial profile
            
        Returns:
            Detailed analysis of scenario impacts
        """
        analysis = {
            "scenario_name": scenario.get("scenario_profile", {}).get("name", "Unnamed Scenario"),
            "goal_impacts": {},
            "overall_metrics": {},
            "timeline_impacts": {},
            "risk_assessment": {}
        }
        
        # Analyze impact on each goal
        for goal in goals:
            goal_id = goal.id if hasattr(goal, 'id') else str(goal)
            goal_probability = scenario.get("goal_probabilities", {}).get(goal_id, 0)
            goal_timeline = scenario.get("goal_achievement_timeline", {}).get(goal_id)
            
            analysis["goal_impacts"][goal_id] = {
                "probability": goal_probability,
                "timeline": goal_timeline,
                "funding_status": self._determine_funding_status(goal_probability),
                "timeline_change": None  # Would be calculated in comparison
            }
        
        # Calculate overall metrics
        probabilities = [impact.get("probability", 0) for impact in analysis["goal_impacts"].values()]
        if probabilities:
            analysis["overall_metrics"]["average_goal_probability"] = sum(probabilities) / len(probabilities)
            analysis["overall_metrics"]["min_goal_probability"] = min(probabilities)
            analysis["overall_metrics"]["goals_above_threshold"] = sum(1 for p in probabilities if p >= 0.8)
            analysis["overall_metrics"]["goals_at_risk"] = sum(1 for p in probabilities if p < 0.5)
        
        # Assess timeline impacts
        retirement_goal_ids = self._identify_retirement_goals(goals)
        retirement_timelines = [
            analysis["goal_impacts"].get(goal_id, {}).get("timeline")
            for goal_id in retirement_goal_ids
            if analysis["goal_impacts"].get(goal_id, {}).get("timeline") is not None
        ]
        
        if retirement_timelines:
            analysis["timeline_impacts"]["retirement_age"] = min(retirement_timelines)
        
        # Risk assessment
        analysis["risk_assessment"]["goals_at_high_risk"] = sum(
            1 for impact in analysis["goal_impacts"].values() 
            if impact.get("probability", 0) < 0.3
        )
        analysis["risk_assessment"]["risk_concentration"] = self._calculate_risk_concentration(
            analysis["goal_impacts"]
        )
        
        return analysis
    
    def _determine_funding_status(self, probability: float) -> str:
        """Determine the funding status of a goal based on its probability."""
        if probability is None:
            return "unknown"
        if probability >= 0.9:
            return "fully_funded"
        if probability >= 0.7:
            return "mostly_funded"
        if probability >= 0.4:
            return "partially_funded"
        return "underfunded"
    
    def _identify_retirement_goals(self, goals: List[Any]) -> List[Any]:
        """Identify retirement goals from a list of goals."""
        retirement_ids = []
        for goal in goals:
            # Different ways to identify retirement goals based on available attributes
            if hasattr(goal, 'type') and 'retirement' in str(goal.type).lower():
                retirement_ids.append(goal.id if hasattr(goal, 'id') else str(goal))
            elif hasattr(goal, 'category') and 'retirement' in str(goal.category).lower():
                retirement_ids.append(goal.id if hasattr(goal, 'id') else str(goal))
            elif hasattr(goal, 'name') and 'retirement' in str(goal.name).lower():
                retirement_ids.append(goal.id if hasattr(goal, 'id') else str(goal))
        return retirement_ids
    
    def _calculate_risk_concentration(self, goal_impacts: Dict[Any, Dict[str, Any]]) -> float:
        """
        Calculate risk concentration across goals.
        Higher values indicate risk is concentrated in few critical goals.
        """
        probabilities = [1.0 - impact.get("probability", 0) for impact in goal_impacts.values()]
        if not probabilities:
            return 0.0
            
        # Use Herfindahl-Hirschman Index to measure concentration
        total = sum(probabilities)
        if total == 0:
            return 0.0
            
        normalized_probs = [p / total for p in probabilities]
        hhi = sum(p * p for p in normalized_probs)
        
        # Normalize to 0-1 scale
        n = len(probabilities)
        if n <= 1:
            return 0.0
            
        normalized_hhi = (hhi - (1/n)) / (1 - (1/n))
        return normalized_hhi
    
    def compare_scenario_outcomes(self, baseline: Dict[str, Any], 
                                 alternative: Dict[str, Any], 
                                 goals: List[Any]) -> Dict[str, Any]:
        """
        Compare baseline and alternative scenarios to identify improvements and deteriorations.
        
        Args:
            baseline: Baseline scenario analysis
            alternative: Alternative scenario analysis
            goals: List of financial goals
            
        Returns:
            Detailed comparison highlighting differences
        """
        comparison = {
            "baseline_name": baseline.get("scenario_profile", {}).get("name", "Baseline"),
            "alternative_name": alternative.get("scenario_profile", {}).get("name", "Alternative"),
            "goal_comparisons": {},
            "overall_changes": {},
            "risk_profile_change": {}
        }
        
        # Compare impact on each goal
        for goal in goals:
            goal_id = goal.id if hasattr(goal, 'id') else str(goal)
            
            baseline_probability = baseline.get("goal_probabilities", {}).get(goal_id, 0)
            alternative_probability = alternative.get("goal_probabilities", {}).get(goal_id, 0)
            
            baseline_timeline = baseline.get("goal_achievement_timeline", {}).get(goal_id)
            alternative_timeline = alternative.get("goal_achievement_timeline", {}).get(goal_id)
            
            probability_change = alternative_probability - baseline_probability if (
                alternative_probability is not None and baseline_probability is not None
            ) else None
            
            timeline_change = alternative_timeline - baseline_timeline if (
                alternative_timeline is not None and baseline_timeline is not None
            ) else None
            
            comparison["goal_comparisons"][goal_id] = {
                "probability_change": probability_change,
                "timeline_change": timeline_change,
                "impact_assessment": self._assess_goal_impact(probability_change, timeline_change),
                "baseline_status": self._determine_funding_status(baseline_probability),
                "alternative_status": self._determine_funding_status(alternative_probability)
            }
        
        # Calculate overall changes
        probability_changes = [
            comp.get("probability_change", 0) 
            for comp in comparison["goal_comparisons"].values()
            if comp.get("probability_change") is not None
        ]
        
        if probability_changes:
            comparison["overall_changes"]["average_probability_change"] = sum(probability_changes) / len(probability_changes)
            comparison["overall_changes"]["improved_goals"] = sum(1 for change in probability_changes if change > 0.05)
            comparison["overall_changes"]["worsened_goals"] = sum(1 for change in probability_changes if change < -0.05)
        
        # Retirement impact
        retirement_goal_ids = self._identify_retirement_goals(goals)
        baseline_retirement = min(
            (baseline.get("goal_achievement_timeline", {}).get(goal_id) 
             for goal_id in retirement_goal_ids
             if baseline.get("goal_achievement_timeline", {}).get(goal_id) is not None),
            default=None
        )
        
        alternative_retirement = min(
            (alternative.get("goal_achievement_timeline", {}).get(goal_id) 
             for goal_id in retirement_goal_ids
             if alternative.get("goal_achievement_timeline", {}).get(goal_id) is not None),
            default=None
        )
        
        if baseline_retirement is not None and alternative_retirement is not None:
            comparison["overall_changes"]["retirement_age_change"] = alternative_retirement - baseline_retirement
        
        # Risk profile change
        baseline_analysis = self.analyze_scenario_impact(baseline, goals, None)
        alternative_analysis = self.analyze_scenario_impact(alternative, goals, None)
        
        comparison["risk_profile_change"]["goals_at_high_risk_change"] = (
            alternative_analysis["risk_assessment"]["goals_at_high_risk"] - 
            baseline_analysis["risk_assessment"]["goals_at_high_risk"]
        )
        
        comparison["risk_profile_change"]["risk_concentration_change"] = (
            alternative_analysis["risk_assessment"]["risk_concentration"] - 
            baseline_analysis["risk_assessment"]["risk_concentration"]
        )
        
        # Overall assessment
        comparison["overall_assessment"] = self._generate_comparison_assessment(comparison)
        
        return comparison
    
    def _assess_goal_impact(self, probability_change: Optional[float], 
                          timeline_change: Optional[float]) -> str:
        """Assess the impact of scenario changes on a specific goal."""
        if probability_change is None:
            return "unknown"
            
        if probability_change > 0.1:
            impact = "significantly_improved"
        elif probability_change > 0.03:
            impact = "improved"
        elif probability_change < -0.1:
            impact = "significantly_worsened"
        elif probability_change < -0.03:
            impact = "worsened"
        else:
            impact = "minimal_change"
            
        # Timeline improvements can modify the assessment
        if timeline_change is not None:
            if timeline_change < -1 and impact in ("improved", "significantly_improved"):
                # Achieved earlier and higher probability
                impact = "significantly_improved"
            elif timeline_change > 1 and impact in ("improved", "minimal_change"):
                # Delayed despite probability increase
                impact = "mixed_impact"
                
        return impact
    
    def _generate_comparison_assessment(self, comparison: Dict[str, Any]) -> str:
        """Generate an overall assessment of the comparison results."""
        improved_goals = comparison["overall_changes"].get("improved_goals", 0)
        worsened_goals = comparison["overall_changes"].get("worsened_goals", 0)
        retirement_change = comparison["overall_changes"].get("retirement_age_change")
        
        if improved_goals > worsened_goals * 2:
            base_assessment = "significantly_better"
        elif improved_goals > worsened_goals:
            base_assessment = "better"
        elif worsened_goals > improved_goals * 2:
            base_assessment = "significantly_worse"
        elif worsened_goals > improved_goals:
            base_assessment = "worse"
        else:
            base_assessment = "mixed"
            
        # Retirement age can modify the assessment
        if retirement_change is not None:
            if retirement_change < -2 and base_assessment in ("better", "significantly_better"):
                return "significantly_better"
            elif retirement_change > 2 and base_assessment in ("better", "mixed"):
                return "mixed"
                
        return base_assessment
    
    def calculate_scenario_success_metrics(self, scenario: Dict[str, Any], 
                                         goals: List[Any],
                                         profile: Any) -> Dict[str, Any]:
        """
        Calculate overall assessment metrics for a scenario.
        
        Args:
            scenario: The scenario to evaluate
            goals: List of financial goals
            profile: User's financial profile
            
        Returns:
            Dictionary of success metrics for the scenario
        """
        metrics = {
            "goal_success_rate": 0,
            "retirement_readiness": 0,
            "financial_resilience": 0,
            "net_worth_trajectory": {},
            "goal_achievement_timeline": {},
            "goal_funding_levels": {}
        }
        
        # Goal success rate
        goal_probabilities = [
            probability for probability in scenario.get("goal_probabilities", {}).values()
            if probability is not None
        ]
        
        if goal_probabilities:
            # Weighted success rate giving higher weight to lower probabilities
            weighted_probs = [p**2 for p in goal_probabilities]  # Square emphasizes lower values
            metrics["goal_success_rate"] = sum(weighted_probs) / len(weighted_probs)
            
            # Count fully funded goals (>90% probability)
            metrics["fully_funded_goals"] = sum(1 for p in goal_probabilities if p >= 0.9)
            metrics["underfunded_goals"] = sum(1 for p in goal_probabilities if p < 0.5)
        
        # Retirement readiness
        retirement_goal_ids = self._identify_retirement_goals(goals)
        retirement_probabilities = [
            scenario.get("goal_probabilities", {}).get(goal_id, 0)
            for goal_id in retirement_goal_ids
        ]
        
        if retirement_probabilities:
            metrics["retirement_readiness"] = min(retirement_probabilities)
            
            # Earliest retirement date
            retirement_timelines = [
                scenario.get("goal_achievement_timeline", {}).get(goal_id)
                for goal_id in retirement_goal_ids
                if scenario.get("goal_achievement_timeline", {}).get(goal_id) is not None
            ]
            
            if retirement_timelines:
                metrics["retirement_age"] = min(retirement_timelines)
        
        # Financial resilience score
        # Based on emergency fund status, debt levels, and income stability
        metrics["financial_resilience"] = self._calculate_financial_resilience(scenario, goals, profile)
        
        # Net worth trajectory
        metrics["net_worth_trajectory"] = scenario.get("net_worth_projection", {})
        
        # Goal funding levels
        for goal in goals:
            goal_id = goal.id if hasattr(goal, 'id') else str(goal)
            probability = scenario.get("goal_probabilities", {}).get(goal_id, 0)
            
            metrics["goal_funding_levels"][goal_id] = {
                "probability": probability,
                "status": self._determine_funding_status(probability)
            }
        
        return metrics
    
    def _calculate_financial_resilience(self, scenario: Dict[str, Any], 
                                      goals: List[Any], 
                                      profile: Any) -> float:
        """
        Calculate a financial resilience score based on emergency fund, debt, and income.
        
        Returns:
            Score from 0-1 indicating financial resilience
        """
        # This would normally use scenario-specific calculations
        # For demonstration, we'll use a simplified approach
        
        # Find emergency fund goals
        emergency_fund_status = 0.5  # Default middle value
        for goal in goals:
            if (hasattr(goal, 'type') and 'emergency' in str(goal.type).lower()) or \
               (hasattr(goal, 'name') and 'emergency' in str(goal.name).lower()):
                goal_id = goal.id if hasattr(goal, 'id') else str(goal)
                probability = scenario.get("goal_probabilities", {}).get(goal_id, 0)
                if probability is not None:
                    emergency_fund_status = probability
                    break
        
        # Debt ratio would normally come from scenario calculations
        debt_ratio = 0.5  # Placeholder
        
        # Income stability would normally come from scenario calculations
        income_stability = 0.5  # Placeholder
        
        # Weighted combination for overall resilience
        resilience = (emergency_fund_status * 0.4 + 
                     (1 - debt_ratio) * 0.3 + 
                     income_stability * 0.3)
        
        return min(1.0, max(0.0, resilience))
    
    def identify_critical_variables(self, scenarios: Dict[str, Dict[str, Any]], 
                                  goals: List[Any], 
                                  profile: Any) -> Dict[str, Any]:
        """
        Identify key variables that most influence financial outcomes.
        
        Args:
            scenarios: Dictionary of scenario analysis results
            goals: List of financial goals
            profile: User's financial profile
            
        Returns:
            Dictionary of critical variables and their impacts
        """
        # Extract scenario profiles
        scenario_profiles = {
            name: scenario.get("scenario_profile", {})
            for name, scenario in scenarios.items()
        }
        
        # Variables to analyze
        variables = {
            "market_returns.stocks": [],
            "market_returns.bonds": [],
            "market_returns.cash": [],
            "market_returns.real_estate": [],
            "inflation_assumption": [],
            "income_growth_rates.primary": [],
            "income_growth_rates.secondary": [],
            "expense_patterns.essential": [],
            "expense_patterns.discretionary": []
        }
        
        # Collect variable values and corresponding outcomes
        variable_outcomes = defaultdict(list)
        
        for name, profile in scenario_profiles.items():
            # Extract variable values
            for var_path in variables.keys():
                parts = var_path.split('.')
                if len(parts) == 1:
                    value = profile.get(parts[0])
                else:
                    container = profile.get(parts[0], {})
                    value = container.get(parts[1]) if container else None
                
                if value is not None:
                    # Store the value along with goal probabilities
                    scenario_probs = scenarios[name].get("goal_probabilities", {})
                    avg_probability = (
                        sum(scenario_probs.values()) / len(scenario_probs)
                        if scenario_probs else 0
                    )
                    variable_outcomes[var_path].append((value, avg_probability))
        
        # Calculate sensitivity for each variable
        sensitivities = {}
        for var_path, outcomes in variable_outcomes.items():
            if len(outcomes) < 2:
                continue
                
            # Sort by variable value
            outcomes.sort(key=lambda x: x[0])
            
            # Calculate correlation
            if len(outcomes) >= 3:
                values = [v for v, _ in outcomes]
                probs = [p for _, p in outcomes]
                
                try:
                    # Calculate correlation coefficient if possible
                    correlation = self._calculate_correlation(values, probs)
                    sensitivities[var_path] = abs(correlation)
                except:
                    # Fallback to range-based sensitivity
                    min_val, min_prob = min(outcomes, key=lambda x: x[0])
                    max_val, max_prob = max(outcomes, key=lambda x: x[0])
                    
                    val_range = max_val - min_val
                    prob_range = max_prob - min_prob
                    
                    if val_range != 0:
                        sensitivities[var_path] = abs(prob_range / val_range)
                    else:
                        sensitivities[var_path] = 0
            else:
                # With only 2 points, use simple difference
                (val1, prob1), (val2, prob2) = outcomes
                val_diff = val2 - val1
                prob_diff = prob2 - prob1
                
                if val_diff != 0:
                    sensitivities[var_path] = abs(prob_diff / val_diff)
                else:
                    sensitivities[var_path] = 0
        
        # Normalize sensitivities
        max_sensitivity = max(sensitivities.values()) if sensitivities else 1
        normalized_sensitivities = {
            var: sens / max_sensitivity
            for var, sens in sensitivities.items()
        }
        
        # Identify most critical variables
        critical_variables = {
            var: {
                "sensitivity": sens,
                "impact_level": "high" if sens > 0.7 else "medium" if sens > 0.3 else "low",
                "direction": self._determine_impact_direction(var, variable_outcomes[var])
            }
            for var, sens in normalized_sensitivities.items()
        }
        
        return critical_variables
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient between two lists."""
        if len(x) != len(y) or len(x) < 2:
            return 0
            
        mean_x = sum(x) / len(x)
        mean_y = sum(y) / len(y)
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator_x = sum((xi - mean_x) ** 2 for xi in x)
        denominator_y = sum((yi - mean_y) ** 2 for yi in y)
        
        if denominator_x == 0 or denominator_y == 0:
            return 0
            
        return numerator / (math.sqrt(denominator_x) * math.sqrt(denominator_y))
    
    def _determine_impact_direction(self, variable: str, 
                                  outcomes: List[Tuple[float, float]]) -> str:
        """Determine if increasing a variable has positive or negative impact."""
        if len(outcomes) < 2:
            return "unknown"
            
        # Sort by variable value
        outcomes.sort(key=lambda x: x[0])
        
        # Check if probability increases or decreases
        (_, first_prob) = outcomes[0]
        (_, last_prob) = outcomes[-1]
        
        if last_prob > first_prob:
            return "positive"
        elif last_prob < first_prob:
            return "negative"
        else:
            return "neutral"
    
    def generate_scenario_insights(self, scenario_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate human-readable insights from scenario analysis.
        
        Args:
            scenario_analysis: Results from analyzing a scenario
            
        Returns:
            List of insight objects with descriptions and recommendations
        """
        insights = []
        
        # Goal probability insights
        goal_impacts = scenario_analysis.get("goal_impacts", {})
        underfunded_goals = [
            goal_id for goal_id, impact in goal_impacts.items()
            if impact.get("funding_status") in ("underfunded", "partially_funded")
        ]
        
        if underfunded_goals:
            insights.append({
                "type": "risk_alert",
                "title": "Underfunded Goals Detected",
                "description": f"This scenario has {len(underfunded_goals)} goals that are underfunded.",
                "recommendation": "Consider adjusting priorities, timeframes, or increasing savings.",
                "severity": "high" if len(underfunded_goals) > 2 else "medium"
            })
        
        # Retirement insights
        retirement_age = scenario_analysis.get("timeline_impacts", {}).get("retirement_age")
        if retirement_age:
            if retirement_age > 70:
                insights.append({
                    "type": "retirement_alert",
                    "title": "Late Retirement Detected",
                    "description": f"This scenario projects retirement at age {retirement_age}.",
                    "recommendation": "Consider increasing retirement savings rate or adjusting retirement expectations.",
                    "severity": "high"
                })
            elif retirement_age < 60:
                insights.append({
                    "type": "retirement_opportunity",
                    "title": "Early Retirement Possible",
                    "description": f"This scenario supports retirement as early as age {retirement_age}.",
                    "recommendation": "Verify that your retirement savings are aligned with this early timeframe.",
                    "severity": "low"
                })
        
        # Risk concentration insight
        risk_concentration = scenario_analysis.get("risk_assessment", {}).get("risk_concentration", 0)
        if risk_concentration > 0.7:
            insights.append({
                "type": "risk_concentration",
                "title": "High Risk Concentration",
                "description": "Financial risk is concentrated in a few critical goals.",
                "recommendation": "Diversify your financial strategies to reduce concentration of risk.",
                "severity": "medium"
            })
        
        # Overall probability insight
        avg_probability = scenario_analysis.get("overall_metrics", {}).get("average_goal_probability", 0)
        if avg_probability < 0.6:
            insights.append({
                "type": "overall_success",
                "title": "Low Overall Success Probability",
                "description": f"The average goal success probability is {avg_probability:.1%}.",
                "recommendation": "This scenario may need significant adjustments to improve outcomes.",
                "severity": "high"
            })
        elif avg_probability > 0.8:
            insights.append({
                "type": "overall_success",
                "title": "Strong Overall Success Probability",
                "description": f"The average goal success probability is {avg_probability:.1%}.",
                "recommendation": "This scenario shows strong overall performance across goals.",
                "severity": "low"
            })
        
        return insights
    
    def identify_most_effective_adjustments(self, scenarios: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify the most effective adjustments based on scenario comparisons.
        
        Args:
            scenarios: Dictionary of scenario analysis results
            
        Returns:
            List of effective adjustments with their impact
        """
        # Identify baseline scenario
        baseline_name = next((name for name in scenarios if "baseline" in name.lower()), None)
        if baseline_name is None and scenarios:
            baseline_name = next(iter(scenarios.keys()))
            
        if baseline_name is None or baseline_name not in scenarios:
            return []
            
        baseline = scenarios[baseline_name]
        
        # Compare each alternative to baseline
        adjustments = []
        
        for name, scenario in scenarios.items():
            if name == baseline_name:
                continue
                
            # Extract scenario profiles
            baseline_profile = baseline.get("scenario_profile", {})
            scenario_profile = scenario.get("scenario_profile", {})
            
            # Skip if profiles aren't available
            if not baseline_profile or not scenario_profile:
                continue
                
            # Identify key differences between scenarios
            differences = self._identify_scenario_differences(baseline_profile, scenario_profile)
            
            # Calculate impact on goal probabilities
            baseline_probs = baseline.get("goal_probabilities", {})
            scenario_probs = scenario.get("goal_probabilities", {})
            
            avg_baseline_prob = (
                sum(baseline_probs.values()) / len(baseline_probs)
                if baseline_probs else 0
            )
            
            avg_scenario_prob = (
                sum(scenario_probs.values()) / len(scenario_probs)
                if scenario_probs else 0
            )
            
            probability_impact = avg_scenario_prob - avg_baseline_prob
            
            # Calculate impact score - normalized to -1 to 1 scale
            impact_score = min(1.0, max(-1.0, probability_impact * 2))
            
            # Add each difference as a potential adjustment
            for diff in differences:
                adjustments.append({
                    "scenario_name": name,
                    "parameter": diff["parameter"],
                    "baseline_value": diff["baseline_value"],
                    "alternative_value": diff["alternative_value"],
                    "impact_score": impact_score,
                    "impact_description": self._describe_adjustment_impact(impact_score),
                    "adjustment_description": diff["description"]
                })
        
        # Sort by absolute impact score (highest impact first)
        adjustments.sort(key=lambda x: abs(x["impact_score"]), reverse=True)
        
        return adjustments
    
    def _identify_scenario_differences(self, profile1: Dict[str, Any], 
                                     profile2: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify key differences between two scenario profiles."""
        differences = []
        
        # Check market returns
        market_returns1 = profile1.get("market_returns", {})
        market_returns2 = profile2.get("market_returns", {})
        
        for asset_class in set(market_returns1.keys()) | set(market_returns2.keys()):
            val1 = market_returns1.get(asset_class)
            val2 = market_returns2.get(asset_class)
            
            if val1 != val2 and val1 is not None and val2 is not None:
                differences.append({
                    "parameter": f"market_returns.{asset_class}",
                    "baseline_value": val1,
                    "alternative_value": val2,
                    "description": f"Change {asset_class} returns from {val1:.1%} to {val2:.1%}"
                })
        
        # Check inflation
        inflation1 = profile1.get("inflation_assumption")
        inflation2 = profile2.get("inflation_assumption")
        
        if inflation1 != inflation2 and inflation1 is not None and inflation2 is not None:
            differences.append({
                "parameter": "inflation_assumption",
                "baseline_value": inflation1,
                "alternative_value": inflation2,
                "description": f"Change inflation assumption from {inflation1:.1%} to {inflation2:.1%}"
            })
        
        # Check income growth rates
        income_rates1 = profile1.get("income_growth_rates", {})
        income_rates2 = profile2.get("income_growth_rates", {})
        
        for source in set(income_rates1.keys()) | set(income_rates2.keys()):
            val1 = income_rates1.get(source)
            val2 = income_rates2.get(source)
            
            if val1 != val2 and val1 is not None and val2 is not None:
                differences.append({
                    "parameter": f"income_growth_rates.{source}",
                    "baseline_value": val1,
                    "alternative_value": val2,
                    "description": f"Change {source} income growth from {val1:.1%} to {val2:.1%}"
                })
        
        # Check expense patterns
        expenses1 = profile1.get("expense_patterns", {})
        expenses2 = profile2.get("expense_patterns", {})
        
        for category in set(expenses1.keys()) | set(expenses2.keys()):
            val1 = expenses1.get(category)
            val2 = expenses2.get(category)
            
            if val1 != val2 and val1 is not None and val2 is not None:
                differences.append({
                    "parameter": f"expense_patterns.{category}",
                    "baseline_value": val1,
                    "alternative_value": val2,
                    "description": f"Change {category} expenses from {val1:.2f} to {val2:.2f}"
                })
        
        # Life events would also be analyzed here
        
        return differences
    
    def _describe_adjustment_impact(self, impact_score: float) -> str:
        """Generate a description of the impact based on the score."""
        if impact_score > 0.5:
            return "Significantly improves financial outcomes"
        elif impact_score > 0.2:
            return "Moderately improves financial outcomes"
        elif impact_score > 0.05:
            return "Slightly improves financial outcomes"
        elif impact_score > -0.05:
            return "Has minimal impact on financial outcomes"
        elif impact_score > -0.2:
            return "Slightly worsens financial outcomes"
        elif impact_score > -0.5:
            return "Moderately worsens financial outcomes"
        else:
            return "Significantly worsens financial outcomes"
    
    def calculate_scenario_robustness(self, scenario: Dict[str, Any], 
                                    variations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assess stability of scenario outcomes under different conditions.
        
        Args:
            scenario: Base scenario to evaluate
            variations: List of variation scenarios
            
        Returns:
            Robustness assessment
        """
        robustness = {
            "overall_score": 0,
            "probability_stability": 0,
            "timeline_stability": 0,
            "sensitive_factors": [],
            "resilient_factors": []
        }
        
        # Extract goal probabilities
        base_probabilities = scenario.get("goal_probabilities", {})
        if not base_probabilities:
            return robustness
            
        # Track probability variations across scenarios
        probability_variations = defaultdict(list)
        
        for variation in variations:
            var_probabilities = variation.get("goal_probabilities", {})
            for goal_id, base_prob in base_probabilities.items():
                if goal_id in var_probabilities:
                    probability_variations[goal_id].append(
                        var_probabilities[goal_id] - base_prob
                    )
        
        # Calculate standard deviation of variations for each goal
        probability_stability = {}
        for goal_id, variations_list in probability_variations.items():
            if variations_list:
                # Standard deviation as a measure of stability
                stability = 1.0 - min(1.0, statistics.stdev(variations_list) * 5)
                probability_stability[goal_id] = stability
        
        # Overall probability stability
        if probability_stability:
            robustness["probability_stability"] = (
                sum(probability_stability.values()) / len(probability_stability)
            )
        
        # Timeline stability would be calculated similarly
        
        # Overall robustness score
        robustness["overall_score"] = robustness["probability_stability"]
        
        # Identify sensitive and resilient factors
        for goal_id, stability in probability_stability.items():
            if stability < 0.5:
                robustness["sensitive_factors"].append(goal_id)
            elif stability > 0.8:
                robustness["resilient_factors"].append(goal_id)
        
        return robustness
    
    def suggest_optimization_opportunities(self, scenario_comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify areas for optimization based on scenario comparison.
        
        Args:
            scenario_comparison: Comparison between scenarios
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        # Analyze goal comparisons for opportunities
        goal_comparisons = scenario_comparison.get("goal_comparisons", {})
        
        # Find goals with significant improvement
        improved_goals = {
            goal_id: comp for goal_id, comp in goal_comparisons.items()
            if comp.get("impact_assessment") in ("significantly_improved", "improved")
        }
        
        if improved_goals:
            # This would extract the specific parameters that led to improvements
            # For demonstration, we'll use a placeholder
            opportunities.append({
                "type": "goal_improvement",
                "title": "Goal Improvement Opportunity",
                "description": f"Found {len(improved_goals)} goals with improvement potential",
                "potential_impact": "medium",
                "implementation_difficulty": "medium",
                "related_goals": list(improved_goals.keys())
            })
        
        # Check retirement impact
        retirement_change = scenario_comparison.get("overall_changes", {}).get("retirement_age_change")
        if retirement_change and retirement_change < -1:
            opportunities.append({
                "type": "retirement_timeline",
                "title": "Earlier Retirement Opportunity",
                "description": f"Potential to retire {abs(retirement_change):.1f} years earlier",
                "potential_impact": "high",
                "implementation_difficulty": "high",
                "related_goals": []  # Would list retirement goals
            })
        
        # Check risk profile improvements
        risk_changes = scenario_comparison.get("risk_profile_change", {})
        high_risk_change = risk_changes.get("goals_at_high_risk_change", 0)
        
        if high_risk_change < 0:
            opportunities.append({
                "type": "risk_reduction",
                "title": "Risk Reduction Opportunity",
                "description": f"Potential to reduce high-risk goals by {abs(high_risk_change)}",
                "potential_impact": "medium",
                "implementation_difficulty": "medium",
                "related_goals": []  # Would list high-risk goals
            })
        
        return opportunities
    
    def prepare_comparison_table_data(self, scenario_comparison: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data for tabular display of scenario comparison.
        
        Args:
            scenario_comparison: Comparison between scenarios
            
        Returns:
            Structured data for table display
        """
        table_data = {
            "headers": ["Metric", "Baseline", "Alternative", "Change", "Impact"],
            "rows": []
        }
        
        # Add overall metrics
        overall_changes = scenario_comparison.get("overall_changes", {})
        
        # Success rate change
        avg_prob_change = overall_changes.get("average_probability_change")
        if avg_prob_change is not None:
            table_data["rows"].append({
                "metric": "Average Goal Success Rate",
                "baseline": f"{avg_prob_change:.1%}",  # Would need actual baseline value
                "alternative": f"{avg_prob_change:.1%}",  # Would need actual alternative value
                "change": f"{avg_prob_change:.1%}" if avg_prob_change >= 0 else f"{avg_prob_change:.1%}",
                "impact": "Positive" if avg_prob_change > 0.05 else "Negative" if avg_prob_change < -0.05 else "Neutral"
            })
        
        # Retirement age
        retirement_change = overall_changes.get("retirement_age_change")
        if retirement_change is not None:
            table_data["rows"].append({
                "metric": "Retirement Age",
                "baseline": "Unknown",  # Would need actual baseline value
                "alternative": "Unknown",  # Would need actual alternative value
                "change": f"{retirement_change:+.1f} years",
                "impact": "Positive" if retirement_change < 0 else "Negative" if retirement_change > 0 else "Neutral"
            })
        
        # Risk profile
        risk_changes = scenario_comparison.get("risk_profile_change", {})
        high_risk_change = risk_changes.get("goals_at_high_risk_change")
        if high_risk_change is not None:
            table_data["rows"].append({
                "metric": "Goals at High Risk",
                "baseline": "Unknown",  # Would need actual baseline value
                "alternative": "Unknown",  # Would need actual alternative value
                "change": f"{high_risk_change:+d}",
                "impact": "Positive" if high_risk_change < 0 else "Negative" if high_risk_change > 0 else "Neutral"
            })
        
        # Could add more rows for other metrics
        
        return table_data
    
    def prepare_scenario_chart_data(self, scenarios: Dict[str, Dict[str, Any]], 
                                  metric: str) -> Dict[str, Any]:
        """
        Prepare data for graphical comparison of scenarios.
        
        Args:
            scenarios: Dictionary of scenario analysis results
            metric: The metric to compare (e.g., "net_worth", "goal_probabilities")
            
        Returns:
            Data formatted for chart display
        """
        chart_data = {
            "type": metric,
            "labels": [],
            "datasets": []
        }
        
        if metric == "net_worth":
            # Net worth projection over time
            for name, scenario in scenarios.items():
                data_points = []
                net_worth = scenario.get("net_worth_projection", {})
                
                # Convert to sorted list of (year, value) tuples
                years_values = [(int(year.replace("year_", "")), value) 
                               for year, value in net_worth.items()
                               if year.startswith("year_")]
                years_values.sort()
                
                # Populate chart data
                if not chart_data["labels"] and years_values:
                    chart_data["labels"] = [year for year, _ in years_values]
                
                data_points = [value for _, value in years_values]
                
                chart_data["datasets"].append({
                    "label": name,
                    "data": data_points
                })
                
        elif metric == "goal_probabilities":
            # Goal success probabilities
            goal_ids = set()
            for scenario in scenarios.values():
                goal_ids.update(scenario.get("goal_probabilities", {}).keys())
            
            chart_data["labels"] = list(goal_ids)
            
            for name, scenario in scenarios.items():
                probabilities = scenario.get("goal_probabilities", {})
                data_points = [probabilities.get(goal_id, 0) for goal_id in goal_ids]
                
                chart_data["datasets"].append({
                    "label": name,
                    "data": data_points
                })
        
        return chart_data
    
    def format_timeline_comparison_data(self, scenarios: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepare data for time-based visualizations.
        
        Args:
            scenarios: Dictionary of scenario analysis results
            
        Returns:
            Data formatted for timeline visualization
        """
        timeline_data = {
            "scenarios": [],
            "timeline_points": []
        }
        
        # Extract timeline data for each scenario
        for name, scenario in scenarios.items():
            scenario_data = {
                "name": name,
                "events": []
            }
            
            # Goal achievement events
            goal_timeline = scenario.get("goal_achievement_timeline", {})
            for goal_id, achievement_time in goal_timeline.items():
                scenario_data["events"].append({
                    "type": "goal_achievement",
                    "goal_id": goal_id,
                    "time": achievement_time
                })
            
            # Life events would be added here as well
            
            timeline_data["scenarios"].append(scenario_data)
        
        # Create merged timeline of significant points
        all_times = set()
        for scenario_data in timeline_data["scenarios"]:
            for event in scenario_data["events"]:
                all_times.add(event["time"])
        
        # Sort and format timeline points
        timeline_data["timeline_points"] = sorted(all_times)
        
        return timeline_data
    
    def prepare_scenario_summary(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare concise summary of a scenario.
        
        Args:
            scenario: Scenario analysis results
            
        Returns:
            Formatted summary
        """
        summary = {
            "name": scenario.get("scenario_profile", {}).get("name", "Unnamed Scenario"),
            "description": scenario.get("scenario_profile", {}).get("description", ""),
            "key_metrics": {},
            "notable_outcomes": [],
            "risk_assessment": ""
        }
        
        # Extract key metrics
        goal_probabilities = scenario.get("goal_probabilities", {})
        if goal_probabilities:
            avg_probability = sum(goal_probabilities.values()) / len(goal_probabilities)
            summary["key_metrics"]["average_goal_probability"] = avg_probability
            summary["key_metrics"]["goals_above_80_percent"] = sum(
                1 for p in goal_probabilities.values() if p >= 0.8
            )
            summary["key_metrics"]["goals_below_50_percent"] = sum(
                1 for p in goal_probabilities.values() if p < 0.5
            )
        
        # Extract retirement information
        retirement_age = None
        for goal_id, timeline in scenario.get("goal_achievement_timeline", {}).items():
            if goal_id.lower().find("retirement") >= 0:
                retirement_age = timeline
                break
                
        if retirement_age:
            summary["key_metrics"]["retirement_age"] = retirement_age
        
        # Notable outcomes
        if retirement_age:
            if retirement_age < 60:
                summary["notable_outcomes"].append("Early retirement possible")
            elif retirement_age > 70:
                summary["notable_outcomes"].append("Late retirement projected")
        
        if goal_probabilities:
            high_prob_goals = sum(1 for p in goal_probabilities.values() if p >= 0.9)
            low_prob_goals = sum(1 for p in goal_probabilities.values() if p < 0.5)
            
            if high_prob_goals > len(goal_probabilities) * 0.7:
                summary["notable_outcomes"].append("Most goals highly achievable")
            elif low_prob_goals > len(goal_probabilities) * 0.3:
                summary["notable_outcomes"].append("Many goals at risk")
        
        # Risk assessment
        if "average_goal_probability" in summary["key_metrics"]:
            avg_prob = summary["key_metrics"]["average_goal_probability"]
            if avg_prob >= 0.8:
                summary["risk_assessment"] = "Low Risk"
            elif avg_prob >= 0.6:
                summary["risk_assessment"] = "Moderate Risk"
            else:
                summary["risk_assessment"] = "High Risk"
        
        return summary