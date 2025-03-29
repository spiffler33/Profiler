"""
Integration Tests for Goal Probability, Adjustment, and Scenario Analysis

This module contains end-to-end tests for the integration between goal probability analysis,
adjustment recommendations, and scenario generation/analysis.
"""

import pytest
import json
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch, Mock
import copy
import numpy as np

from models.goal_probability import (
    GoalProbabilityAnalyzer,
    GoalProbabilityResult
)

from models.goal_adjustment import (
    GoalAdjustmentRecommender,
    AdjustmentRecommendation
)

from models.scenario_generator import (
    AlternativeScenarioGenerator,
    ScenarioProfile
)

from models.scenario_analyzer import (
    ScenarioAnalyzer,
    ScenarioComparisonResult
)

from models.gap_analysis import (
    GapResult,
    GapSeverity
)

# Test fixtures
@pytest.fixture
def test_goals():
    """Fixture providing a set of test goals of different types"""
    today = date.today()
    
    # Create goals with consistent IDs and properties for integration testing
    retirement_goal = Mock(
        id="goal-retirement",
        name="Retirement",
        type="retirement",
        category="retirement",
        target_amount=2000000,
        current_amount=500000,
        target_date=today.replace(year=today.year + 25),
        monthly_contribution=2000,
        priority="high",
        asset_allocation={
            "equity": 0.7,
            "debt": 0.2,
            "gold": 0.05,
            "cash": 0.05
        }
    )
    
    emergency_goal = Mock(
        id="goal-emergency",
        name="Emergency Fund",
        type="emergency_fund",
        category="emergency_fund",
        target_amount=50000,
        current_amount=20000,
        target_date=today.replace(year=today.year + 2),
        monthly_contribution=1000,
        priority="high",
        asset_allocation={
            "equity": 0.1,
            "debt": 0.3,
            "cash": 0.6
        }
    )
    
    education_goal = Mock(
        id="goal-education",
        name="Education Fund",
        type="education",
        category="education",
        target_amount=500000,
        current_amount=100000,
        target_date=today.replace(year=today.year + 10),
        monthly_contribution=3000,
        priority="medium",
        asset_allocation={
            "equity": 0.6,
            "debt": 0.3,
            "gold": 0.05,
            "cash": 0.05
        }
    )
    
    home_goal = Mock(
        id="goal-home",
        name="Home Purchase",
        type="home",
        category="home",
        target_amount=3000000,
        current_amount=500000,
        target_date=today.replace(year=today.year + 7),
        monthly_contribution=20000,
        priority="high",
        asset_allocation={
            "equity": 0.5,
            "debt": 0.4,
            "gold": 0.05,
            "cash": 0.05
        }
    )
    
    vacation_goal = Mock(
        id="goal-vacation",
        name="Vacation",
        type="discretionary",
        category="discretionary",
        target_amount=100000,
        current_amount=20000,
        target_date=today.replace(year=today.year + 1),
        monthly_contribution=5000,
        priority="low",
        asset_allocation={
            "equity": 0.3,
            "debt": 0.4,
            "gold": 0.0,
            "cash": 0.3
        }
    )
    
    return {
        "retirement": retirement_goal,
        "emergency": emergency_goal,
        "education": education_goal,
        "home": home_goal,
        "vacation": vacation_goal,
        "all": [retirement_goal, emergency_goal, education_goal, home_goal, vacation_goal]
    }

@pytest.fixture
def test_profiles():
    """Fixture providing test profiles with different risk tolerances"""
    profiles = {}
    
    # Conservative profile
    profiles["conservative"] = Mock(
        id="profile-conservative",
        name="Conservative User",
        age=45,
        retirement_age=65,
        annual_income=100000,
        monthly_expenses=5000,
        risk_tolerance="conservative",
        country="India"
    )
    
    # Moderate profile
    profiles["moderate"] = Mock(
        id="profile-moderate",
        name="Moderate User",
        age=35,
        retirement_age=65,
        annual_income=120000,
        monthly_expenses=4000,
        risk_tolerance="moderate",
        country="India"
    )
    
    # Aggressive profile
    profiles["aggressive"] = Mock(
        id="profile-aggressive",
        name="Aggressive User",
        age=28,
        retirement_age=60,
        annual_income=150000,
        monthly_expenses=4500,
        risk_tolerance="aggressive",
        country="India"
    )
    
    return profiles

@pytest.fixture
def parameter_service():
    """Fixture providing a consistent parameter service for integration tests"""
    service = Mock()
    
    # Set up return values
    service.get_inflation_assumption.return_value = 0.06  # 6% for India
    service.get_return_assumptions.return_value = {
        "equity": 0.12,  # 12% for equity in India
        "debt": 0.08,    # 8% for debt in India
        "gold": 0.07,    # 7% for gold
        "cash": 0.04     # 4% for cash
    }
    service.get_tax_rate.return_value = 0.30  # 30% tax rate
    service.get_section_80c_limit.return_value = 150000  # Rs. 1.5 lakh for 80C
    
    # Create different return assumptions for different risk profiles
    def get_returns_by_profile(profile_id):
        if "conservative" in profile_id:
            return {
                "equity": 0.10,  # Lower returns for conservative
                "debt": 0.07,
                "gold": 0.06,
                "cash": 0.04
            }
        elif "aggressive" in profile_id:
            return {
                "equity": 0.14,  # Higher returns for aggressive
                "debt": 0.08,
                "gold": 0.07,
                "cash": 0.04
            }
        else:  # moderate
            return {
                "equity": 0.12,
                "debt": 0.08,
                "gold": 0.07,
                "cash": 0.04
            }
    
    # Override the return value with the profile-specific implementation
    service.get_return_assumptions.side_effect = get_returns_by_profile
    
    return service

@pytest.fixture
def probability_analyzer(parameter_service):
    """Fixture providing a probability analyzer with controlled outputs"""
    analyzer = GoalProbabilityAnalyzer(parameter_service=parameter_service)
    
    # Mock the analyze_goal_probability method
    def mock_analyze_probability(goal, profile):
        # Base probability based on goal type
        if goal.type == "retirement":
            base_prob = 0.65
        elif goal.type == "emergency_fund":
            base_prob = 0.85
        elif goal.type == "education":
            base_prob = 0.75
        elif goal.type == "home":
            base_prob = 0.60
        else:  # discretionary
            base_prob = 0.90
            
        # Adjust based on profile risk tolerance
        risk_adjustment = {
            "conservative": -0.05,
            "moderate": 0.0,
            "aggressive": 0.05
        }.get(profile.risk_tolerance, 0.0)
        
        # Final probability
        probability = min(0.99, max(0.01, base_prob + risk_adjustment))
        
        # Create result with appropriate structure
        return Mock(
            goal_id=goal.id,
            success_probability=probability,
            outcome_distribution=Mock(),
            timeline_assessment={
                "expected_years": (goal.target_date.year - date.today().year),
                "expected_months": 0,
                "probability_by_year": {
                    str(goal.target_date.year - date.today().year - 5): max(0.01, probability - 0.2),
                    str(goal.target_date.year - date.today().year): probability,
                    str(goal.target_date.year - date.today().year + 5): min(0.99, probability + 0.2)
                }
            },
            to_dict=lambda: {
                "goal_id": goal.id,
                "success_probability": probability,
                "outcome_distribution": {},
                "timeline_assessment": {
                    "expected_years": (goal.target_date.year - date.today().year),
                    "expected_months": 0,
                    "probability_by_year": {
                        str(goal.target_date.year - date.today().year - 5): max(0.01, probability - 0.2),
                        str(goal.target_date.year - date.today().year): probability,
                        str(goal.target_date.year - date.today().year + 5): min(0.99, probability + 0.2)
                    }
                }
            }
        )
    
    analyzer.analyze_goal_probability = mock_analyze_probability
    
    return analyzer

@pytest.fixture
def gap_analyzer():
    """Fixture providing a gap analyzer with controlled outputs"""
    analyzer = Mock()
    
    # Create a mock analyze_goal_gap method
    def mock_analyze_goal(goal, profile):
        # Return different gaps based on goal type
        if goal.type == "retirement":
            return GapResult(
                goal_id=goal.id,
                goal_title=goal.name,
                goal_category=goal.category,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                gap_amount=500000,
                gap_percentage=25.0,
                severity=GapSeverity.SIGNIFICANT,
                timeframe_gap=5,
                capacity_gap=1000
            )
        elif goal.type == "emergency_fund":
            return GapResult(
                goal_id=goal.id,
                goal_title=goal.name,
                goal_category=goal.category,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                gap_amount=10000,
                gap_percentage=20.0,
                severity=GapSeverity.MODERATE,
                timeframe_gap=1,
                capacity_gap=500
            )
        elif goal.type == "education":
            return GapResult(
                goal_id=goal.id,
                goal_title=goal.name,
                goal_category=goal.category,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                gap_amount=150000,
                gap_percentage=30.0,
                severity=GapSeverity.SIGNIFICANT,
                timeframe_gap=3,
                capacity_gap=1500
            )
        elif goal.type == "home":
            return GapResult(
                goal_id=goal.id,
                goal_title=goal.name,
                goal_category=goal.category,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                gap_amount=1000000,
                gap_percentage=33.3,
                severity=GapSeverity.SEVERE,
                timeframe_gap=2,
                capacity_gap=10000
            )
        else:  # discretionary
            return GapResult(
                goal_id=goal.id,
                goal_title=goal.name,
                goal_category=goal.category,
                target_amount=goal.target_amount,
                current_amount=goal.current_amount,
                gap_amount=20000,
                gap_percentage=20.0,
                severity=GapSeverity.MANAGEABLE,
                timeframe_gap=0,
                capacity_gap=1000
            )
    
    analyzer.analyze_goal_gap.side_effect = mock_analyze_goal
    
    return analyzer

@pytest.fixture
def adjustment_recommender(parameter_service, gap_analyzer, probability_analyzer):
    """Fixture providing an adjustment recommender with controlled component behavior"""
    recommender = GoalAdjustmentRecommender(
        parameter_service=parameter_service,
        gap_analyzer=gap_analyzer,
        probability_analyzer=probability_analyzer
    )
    
    # Override the _simulate_probability_change method to provide controlled values
    def simulate_probability_change(goal, profile, adjustment_type, adjustment_value):
        # Define standard changes for different adjustment types
        if adjustment_type == "target_amount":
            # Probability change based on how much the target is reduced
            reduction_factor = 1.0 - (adjustment_value / goal.target_amount)
            return min(0.3, max(0.0, reduction_factor * 0.5))  # Up to 0.3 increase for 60% reduction
            
        elif adjustment_type == "timeframe":
            # Probability change based on how many years the timeframe is extended
            original_years = goal.target_date.year - date.today().year
            new_years = adjustment_value.year - date.today().year
            extension_years = new_years - original_years
            return min(0.3, max(0.0, extension_years * 0.05))  # 0.05 per year, up to 0.3
            
        elif adjustment_type == "contribution":
            # Probability change based on how much the contribution is increased
            increase_factor = adjustment_value / goal.monthly_contribution - 1.0
            return min(0.3, max(0.0, increase_factor * 0.25))  # 0.25 for 100% increase, up to 0.3
            
        elif adjustment_type == "allocation":
            # Probability change based on how much equity allocation is adjusted
            original_equity = goal.asset_allocation.get("equity", 0)
            new_equity = adjustment_value.get("equity", 0)
            equity_change = new_equity - original_equity
            
            # Effect depends on the goal type and timeframe
            years_to_goal = goal.target_date.year - date.today().year
            
            if years_to_goal > 10:  # Long-term goals benefit from higher equity
                return min(0.2, max(-0.2, equity_change * 0.4))  # Up to 0.2 for 50% increase
            elif years_to_goal > 5:  # Medium-term goals have moderate benefit
                return min(0.1, max(-0.2, equity_change * 0.2))  # Up to 0.1 for 50% increase
            else:  # Short-term goals may be harmed by higher equity
                return min(0.05, max(-0.3, equity_change * -0.3))  # Down to -0.3 for 100% increase
        
        # For combined adjustments
        elif isinstance(adjustment_type, list):
            # Sum the individual effects with a small synergy bonus
            total_effect = 0
            for i, adj_type in enumerate(adjustment_type):
                total_effect += simulate_probability_change(goal, profile, adj_type, adjustment_value[i])
            
            # Add synergy bonus (10% of the total effect)
            return total_effect * 1.1
            
        return 0.0
    
    # Apply the mock method
    recommender._simulate_probability_change = simulate_probability_change
    
    return recommender

@pytest.fixture
def scenario_generator(parameter_service):
    """Fixture providing a scenario generator with controlled behavior"""
    generator = AlternativeScenarioGenerator(parameter_service=parameter_service)
    
    # Mock the _run_scenario_analysis method to return controlled results
    def mock_run_analysis(goals, profile, scenario_profile):
        # Create a basic scenario result
        result = {
            "scenario_profile": scenario_profile.to_dict(),
            "goal_probabilities": {},
            "goal_achievement_timeline": {},
            "retirement_age": None,
            "net_worth_projection": {
                "year_5": 500000,
                "year_10": 1000000,
                "year_20": 2000000,
                "year_30": 3000000
            },
            "analysis_date": datetime.now().isoformat()
        }
        
        # Add goal probabilities based on goal type and scenario characteristics
        # Use inflation as a proxy for scenario type (higher inflation = more pessimistic)
        if scenario_profile.inflation_assumption > 0.05:  # High inflation/pessimistic
            scenario_factor = 0.8  # Reduce probabilities
        elif scenario_profile.inflation_assumption < 0.03:  # Low inflation/optimistic
            scenario_factor = 1.2  # Increase probabilities
        else:  # Moderate/baseline
            scenario_factor = 1.0  # No change
            
        # Process each goal
        for goal in goals if isinstance(goals, list) else [goals]:
            # Base probability based on goal type
            if goal.type == "retirement":
                base_prob = 0.65
            elif goal.type == "emergency_fund":
                base_prob = 0.85
            elif goal.type == "education":
                base_prob = 0.75
            elif goal.type == "home":
                base_prob = 0.60
            else:  # discretionary
                base_prob = 0.90
                
            # Adjust based on scenario
            prob = min(0.99, max(0.01, base_prob * scenario_factor))
            result["goal_probabilities"][goal.id] = prob
            
            # Set goal achievement timeline
            years_to_goal = goal.target_date.year - date.today().year
            # Adjust timeline based on scenario factor (optimistic achieves sooner)
            adjusted_years = int(years_to_goal / scenario_factor)
            result["goal_achievement_timeline"][goal.id] = adjusted_years
            
            # For retirement goals, set retirement age
            if goal.type == "retirement" and not result["retirement_age"]:
                result["retirement_age"] = profile.age + adjusted_years
        
        return result
    
    # Apply the mock method
    generator._run_scenario_analysis = mock_run_analysis
    
    return generator

@pytest.fixture
def scenario_analyzer():
    """Fixture providing a scenario analyzer for testing"""
    return ScenarioAnalyzer()


# Integration tests
class TestGoalProbabilityAdjustmentWorkflow:
    """Tests for the integration between probability analysis and adjustment recommendations"""
    
    def test_probability_to_adjustment_workflow(self, test_goals, test_profiles, 
                                              probability_analyzer, adjustment_recommender):
        """Test the complete workflow from probability analysis to adjustment recommendations"""
        # Use a specific goal and profile for this test
        goal = test_goals["retirement"]
        profile = test_profiles["moderate"]
        
        # Step 1: Analyze goal probability
        probability_result = probability_analyzer.analyze_goal_probability(goal, profile)
        
        # Verify probability result
        assert probability_result.goal_id == goal.id
        assert isinstance(probability_result.success_probability, float)
        
        # Step 2: Get adjustment recommendations based on the probability
        recommendations = adjustment_recommender.recommend_adjustments(
            goal, profile, probability_result.success_probability
        )
        
        # Verify recommendations
        assert recommendations.goal_id == goal.id
        assert recommendations.current_probability == probability_result.success_probability
        assert len(recommendations.adjustment_options) > 0
        
        # Verify all adjustment types are present
        adjustment_types = {option.adjustment_type for option in recommendations.adjustment_options}
        assert "target_amount" in adjustment_types
        assert "timeframe" in adjustment_types
        assert "contribution" in adjustment_types
        assert "allocation" in adjustment_types
        
        # Verify each option has impact assessment
        for option in recommendations.adjustment_options:
            assert hasattr(option, 'impact')
            assert hasattr(option.impact, 'probability_change')
            assert option.impact.probability_change > 0  # All should improve probability
    
    def test_adjustment_to_scenario_workflow(self, test_goals, test_profiles,
                                           adjustment_recommender, scenario_generator):
        """Test the workflow from adjustment recommendations to scenario generation"""
        # Use a specific goal and profile for this test
        goal = test_goals["education"]
        profile = test_profiles["moderate"]
        
        # Step 1: Get adjustment recommendations
        recommendations = adjustment_recommender.recommend_adjustments(goal, profile)
        
        # Verify we have recommendations
        assert len(recommendations.adjustment_options) > 0
        
        # Step 2: Apply an adjustment to create a custom scenario
        selected_option = next(option for option in recommendations.adjustment_options 
                              if option.adjustment_type == "contribution")
        
        # Create a custom scenario based on this adjustment
        custom_parameters = {
            "name": "Increased Contribution Scenario",
            "description": "Scenario with increased monthly contribution for education goal",
            "market_returns": scenario_generator._scenario_defaults["baseline"]["market_returns"],
            "inflation_assumption": scenario_generator._scenario_defaults["baseline"]["inflation_assumption"],
            "income_growth_rates": scenario_generator._scenario_defaults["baseline"]["income_growth_rates"],
            "expense_patterns": scenario_generator._scenario_defaults["baseline"]["expense_patterns"],
            "life_events": []
        }
        
        # Generate the scenario
        custom_scenario = scenario_generator.create_custom_scenario(
            [goal], profile, custom_parameters
        )
        
        # Verify scenario creation
        assert "scenario_profile" in custom_scenario
        assert custom_scenario["scenario_profile"]["name"] == "Increased Contribution Scenario"
        
        # Verify goal probabilities are included
        assert "goal_probabilities" in custom_scenario
        assert goal.id in custom_scenario["goal_probabilities"]
        
        # Verify goal timeline is included
        assert "goal_achievement_timeline" in custom_scenario
        assert goal.id in custom_scenario["goal_achievement_timeline"]
    
    def test_complete_analysis_workflow(self, test_goals, test_profiles, probability_analyzer,
                                      adjustment_recommender, scenario_generator, scenario_analyzer):
        """Test the complete pipeline from analysis to adjustment to scenario generation and comparison"""
        # Use multiple goals for this test
        goals = [test_goals["retirement"], test_goals["education"]]
        profile = test_profiles["moderate"]
        
        # Step 1: Analyze goal probabilities
        probability_results = {
            goal.id: probability_analyzer.analyze_goal_probability(goal, profile)
            for goal in goals
        }
        
        # Step 2: Get adjustment recommendations for each goal
        adjustment_recommendations = {
            goal.id: adjustment_recommender.recommend_adjustments(
                goal, profile, probability_results[goal.id].success_probability
            )
            for goal in goals
        }
        
        # Step 3: Generate baseline scenario
        baseline_scenario = scenario_generator.generate_baseline_scenario(goals, profile)
        
        # Step 4: Create alternative scenarios based on adjustments
        alternative_scenarios = {}
        
        # For each goal, select one adjustment option
        for goal in goals:
            # Get the contribution option for this goal
            options = adjustment_recommendations[goal.id].adjustment_options
            contribution_option = next(option for option in options if option.adjustment_type == "contribution")
            
            # Create a scenario name
            scenario_name = f"Increased_Contribution_{goal.name}"
            
            # Create custom parameters
            custom_parameters = {
                "name": scenario_name,
                "description": f"Scenario with increased contribution for {goal.name}",
                "market_returns": scenario_generator._scenario_defaults["baseline"]["market_returns"],
                "inflation_assumption": scenario_generator._scenario_defaults["baseline"]["inflation_assumption"],
                "income_growth_rates": scenario_generator._scenario_defaults["baseline"]["income_growth_rates"],
                "expense_patterns": scenario_generator._scenario_defaults["baseline"]["expense_patterns"],
                "life_events": []
            }
            
            # Generate custom scenario
            alternative_scenarios[scenario_name] = scenario_generator.create_custom_scenario(
                goals, profile, custom_parameters
            )
        
        # Step 5: Compare scenarios
        comparison = scenario_generator.compare_scenarios(baseline_scenario, alternative_scenarios)
        
        # Verify comparison structure
        assert "baseline" in comparison
        assert "alternatives" in comparison
        assert "differences" in comparison
        assert "summary" in comparison
        
        # Step 6: Analyze scenarios using ScenarioAnalyzer
        scenario_analysis = scenario_analyzer.analyze_scenario_impact(baseline_scenario, goals, profile)
        
        # Verify analysis structure
        assert "scenario_name" in scenario_analysis
        assert "goal_impacts" in scenario_analysis
        assert "overall_metrics" in scenario_analysis
        
        # Verify goals are included
        for goal in goals:
            assert goal.id in scenario_analysis["goal_impacts"]
            
        # Step 7: Generate insights from scenario analysis
        insights = scenario_analyzer.generate_scenario_insights(scenario_analysis)
        
        # Verify insights
        assert isinstance(insights, list)
        assert len(insights) > 0
        
        # Verify each insight has the required fields
        for insight in insights:
            assert "type" in insight
            assert "title" in insight
            assert "description" in insight
            assert "recommendation" in insight
            assert "severity" in insight
    
    def test_goal_specific_end_to_end(self, test_goals, test_profiles, probability_analyzer,
                                    adjustment_recommender, scenario_generator, scenario_analyzer):
        """Test end-to-end workflow for each major goal type"""
        profile = test_profiles["moderate"]
        
        # Test each goal type separately
        for goal_key in ["retirement", "emergency", "education", "home", "vacation"]:
            goal = test_goals[goal_key]
            
            # Step 1: Analyze goal probability
            probability_result = probability_analyzer.analyze_goal_probability(goal, profile)
            
            # Step 2: Get adjustment recommendations
            recommendations = adjustment_recommender.recommend_adjustments(
                goal, profile, probability_result.success_probability
            )
            
            # Verify we have recommendations
            assert len(recommendations.adjustment_options) > 0
            
            # Step 3: Generate baseline and alternative scenarios
            baseline_scenario = scenario_generator.generate_baseline_scenario(goal, profile)
            
            # Create an alternative scenario
            selected_option = next(option for option in recommendations.adjustment_options)
            scenario_name = f"Alternative_{goal.name}"
            
            # Create custom parameters
            custom_parameters = {
                "name": scenario_name,
                "description": f"Alternative scenario for {goal.name}",
                "market_returns": scenario_generator._scenario_defaults["baseline"]["market_returns"],
                "inflation_assumption": scenario_generator._scenario_defaults["baseline"]["inflation_assumption"],
                "income_growth_rates": scenario_generator._scenario_defaults["baseline"]["income_growth_rates"],
                "expense_patterns": scenario_generator._scenario_defaults["baseline"]["expense_patterns"],
                "life_events": []
            }
            
            # Generate alternative scenario
            alternative_scenario = scenario_generator.create_custom_scenario(
                goal, profile, custom_parameters
            )
            
            # Step 4: Compare scenarios
            comparison = scenario_generator.compare_scenarios(
                baseline_scenario, {scenario_name: alternative_scenario}
            )
            
            # Step 5: Analyze scenarios
            scenario_analysis = scenario_analyzer.analyze_scenario_impact(baseline_scenario, [goal], profile)
            
            # Verify goal is included in analysis
            assert goal.id in scenario_analysis["goal_impacts"]
            
            # Step 6: Generate insights
            insights = scenario_analyzer.generate_scenario_insights(scenario_analysis)
            
            # Verify we got insights
            assert isinstance(insights, list)
    
    def test_with_realistic_user_profiles(self, test_goals, test_profiles, probability_analyzer,
                                        adjustment_recommender, scenario_generator, scenario_analyzer):
        """Test with different user profiles (conservative, moderate, aggressive)"""
        # Test each profile with the retirement goal
        goal = test_goals["retirement"]
        
        for profile_key, profile in test_profiles.items():
            # Step 1: Analyze goal probability
            probability_result = probability_analyzer.analyze_goal_probability(goal, profile)
            
            # Step 2: Get adjustment recommendations
            recommendations = adjustment_recommender.recommend_adjustments(
                goal, profile, probability_result.success_probability
            )
            
            # Step 3: Generate baseline and optimistic scenarios
            baseline = scenario_generator.generate_baseline_scenario(goal, profile)
            optimistic = scenario_generator.generate_optimistic_scenario(goal, profile)
            
            # Step 4: Compare scenarios
            comparison = scenario_generator.compare_scenarios(
                baseline, {"optimistic": optimistic}
            )
            
            # Step 5: Analyze scenarios
            scenario_analysis = scenario_analyzer.analyze_scenario_impact(baseline, [goal], profile)
            
            # Step 6: Calculate success metrics
            success_metrics = scenario_analyzer.calculate_scenario_success_metrics(
                baseline, [goal], profile
            )
            
            # Verify profile-specific results
            if profile_key == "conservative":
                # Conservative profile should have lower equity allocation recommendations
                allocation_options = [
                    option for option in recommendations.adjustment_options
                    if option.adjustment_type == "allocation"
                ]
                
                if allocation_options:
                    equity_allocations = [
                        option.adjustment_value.get("equity", 0) for option in allocation_options
                    ]
                    assert all(equity <= 0.7 for equity in equity_allocations)
                    
            elif profile_key == "aggressive":
                # Aggressive profile should have higher initial probability
                assert probability_result.success_probability >= 0.65
    
    def test_performance_with_multiple_goals(self, test_goals, test_profiles, probability_analyzer,
                                           adjustment_recommender, scenario_generator, scenario_analyzer):
        """Test system performance with a complex portfolio of multiple goals"""
        # Use all goals and a moderate profile
        goals = test_goals["all"]
        profile = test_profiles["moderate"]
        
        # Measure execution time for each stage
        import time
        
        # Stage 1: Probability analysis
        start_time = time.time()
        probability_results = {
            goal.id: probability_analyzer.analyze_goal_probability(goal, profile)
            for goal in goals
        }
        probability_time = time.time() - start_time
        
        # Stage 2: Adjustment recommendations
        start_time = time.time()
        adjustment_recommendations = {
            goal.id: adjustment_recommender.recommend_adjustments(
                goal, profile, probability_results[goal.id].success_probability
            )
            for goal in goals
        }
        adjustment_time = time.time() - start_time
        
        # Stage 3: Scenario generation
        start_time = time.time()
        scenarios = {
            "baseline": scenario_generator.generate_baseline_scenario(goals, profile),
            "optimistic": scenario_generator.generate_optimistic_scenario(goals, profile),
            "pessimistic": scenario_generator.generate_pessimistic_scenario(goals, profile)
        }
        scenario_time = time.time() - start_time
        
        # Stage 4: Scenario analysis
        start_time = time.time()
        scenario_analyses = {
            name: scenario_analyzer.analyze_scenario_impact(scenario, goals, profile)
            for name, scenario in scenarios.items()
        }
        analysis_time = time.time() - start_time
        
        # Stage 5: Compare scenarios
        start_time = time.time()
        comparison = scenario_generator.compare_scenarios(
            scenarios["baseline"], 
            {k: v for k, v in scenarios.items() if k != "baseline"}
        )
        comparison_time = time.time() - start_time
        
        # Verify all goals are included in the results
        for goal in goals:
            assert goal.id in probability_results
            assert goal.id in adjustment_recommendations
            
            for scenario in scenarios.values():
                assert goal.id in scenario["goal_probabilities"]
                assert goal.id in scenario["goal_achievement_timeline"]
                
            for analysis in scenario_analyses.values():
                assert goal.id in analysis["goal_impacts"]
                
        # Performance is acceptable if each stage takes less than 1 second
        # (this is very lenient since we're using mocks that should be fast)
        assert probability_time < 1.0, f"Probability analysis took too long: {probability_time}s"
        assert adjustment_time < 1.0, f"Adjustment recommendation took too long: {adjustment_time}s"
        assert scenario_time < 1.0, f"Scenario generation took too long: {scenario_time}s"
        assert analysis_time < 1.0, f"Scenario analysis took too long: {analysis_time}s"
        assert comparison_time < 1.0, f"Scenario comparison took too long: {comparison_time}s"
    
    def test_backward_compatibility(self, test_goals, test_profiles, probability_analyzer,
                                   adjustment_recommender, scenario_generator, scenario_analyzer):
        """Test backward compatibility with existing data structures"""
        # Create an "old format" goal without some of the newer fields
        old_format_goal = Mock(
            id="goal-old-format",
            name="Old Format Goal",
            type="education",
            category="education",
            target_amount=500000,
            current_amount=100000,
            target_date=date.today().replace(year=date.today().year + 10),
            monthly_contribution=3000,
            # Missing: priority, asset_allocation
        )
        
        profile = test_profiles["moderate"]
        
        # Try each component with the old format goal
        try:
            # Step 1: Analyze goal probability
            probability_result = probability_analyzer.analyze_goal_probability(old_format_goal, profile)
            
            # Step 2: Get adjustment recommendations
            recommendations = adjustment_recommender.recommend_adjustments(
                old_format_goal, profile, probability_result.success_probability
            )
            
            # Step 3: Generate baseline scenario
            baseline_scenario = scenario_generator.generate_baseline_scenario(old_format_goal, profile)
            
            # Step 4: Analyze scenario
            scenario_analysis = scenario_analyzer.analyze_scenario_impact(
                baseline_scenario, [old_format_goal], profile
            )
            
            # If we get here without exceptions, the backward compatibility is good
            assert True
            
        except Exception as e:
            pytest.fail(f"Backward compatibility test failed: {str(e)}")
    
    def test_integrated_scenario_optimization(self, test_goals, test_profiles, probability_analyzer,
                                             adjustment_recommender, scenario_generator, scenario_analyzer):
        """Test integrated scenario optimization based on adjustment recommendations"""
        # Use retirement goal and moderate profile
        goal = test_goals["retirement"]
        profile = test_profiles["moderate"]
        
        # Step 1: Analyze goal probability
        probability_result = probability_analyzer.analyze_goal_probability(goal, profile)
        
        # Step 2: Get adjustment recommendations
        recommendations = adjustment_recommender.recommend_adjustments(
            goal, profile, probability_result.success_probability
        )
        
        # Step 3: Generate baseline scenario
        baseline_scenario = scenario_generator.generate_baseline_scenario(goal, profile)
        
        # Step 4: Create optimized scenarios from each adjustment type
        optimized_scenarios = {}
        
        # Group options by adjustment type
        options_by_type = {}
        for option in recommendations.adjustment_options:
            if option.adjustment_type not in options_by_type:
                options_by_type[option.adjustment_type] = []
            options_by_type[option.adjustment_type].append(option)
        
        # For each adjustment type, create a scenario with the best option
        for adj_type, options in options_by_type.items():
            if not options:
                continue
                
            # Sort options by probability change (descending)
            options.sort(key=lambda x: x.impact.probability_change, reverse=True)
            best_option = options[0]
            
            # Create scenario name and description
            scenario_name = f"Optimized_{adj_type}"
            description = f"Scenario optimized through {adj_type} adjustment"
            
            # Create custom parameters (starting with baseline)
            custom_parameters = {
                "name": scenario_name,
                "description": description,
                "market_returns": scenario_generator._scenario_defaults["baseline"]["market_returns"],
                "inflation_assumption": scenario_generator._scenario_defaults["baseline"]["inflation_assumption"],
                "income_growth_rates": scenario_generator._scenario_defaults["baseline"]["income_growth_rates"],
                "expense_patterns": scenario_generator._scenario_defaults["baseline"]["expense_patterns"],
                "life_events": []
            }
            
            # Generate optimized scenario
            optimized_scenarios[scenario_name] = scenario_generator.create_custom_scenario(
                goal, profile, custom_parameters
            )
        
        # Step 5: Compare all scenarios
        comparison = scenario_generator.compare_scenarios(baseline_scenario, optimized_scenarios)
        
        # Step 6: Identify the best scenario
        best_scenario = scenario_analyzer.identify_most_effective_adjustments(
            {**{"baseline": baseline_scenario}, **optimized_scenarios}
        )
        
        # Verify we have a result
        assert isinstance(best_scenario, list)
        assert len(best_scenario) > 0
        
        # Verify each adjustment has the expected structure
        for adjustment in best_scenario:
            assert "scenario_name" in adjustment
            assert "parameter" in adjustment
            assert "baseline_value" in adjustment
            assert "alternative_value" in adjustment
            assert "impact_score" in adjustment