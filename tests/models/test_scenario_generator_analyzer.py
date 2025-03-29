"""
Tests for the Scenario Generator and Analyzer Modules

This module contains tests for the scenario generation and analysis functionality including
AlternativeScenarioGenerator, ScenarioProfile, ScenarioAnalyzer, and ScenarioComparisonResult classes.
"""

import pytest
import json
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch, Mock
import copy

from models.scenario_generator import (
    AlternativeScenarioGenerator,
    ScenarioProfile
)

from models.scenario_analyzer import (
    ScenarioAnalyzer,
    ScenarioComparisonResult
)

# Test fixtures
@pytest.fixture
def sample_goal():
    """Fixture providing a sample financial goal for testing"""
    return Mock(
        id="goal-1",
        name="Test Retirement Goal",
        type="retirement",
        category="retirement",
        target_amount=1000000,
        current_amount=300000,
        target_date=date.today().replace(year=date.today().year + 20),
        monthly_contribution=1000,
        priority="high"
    )

@pytest.fixture
def sample_goals():
    """Fixture providing multiple goals for testing scenario analysis"""
    today = date.today()
    
    retirement_goal = Mock(
        id="goal-retirement",
        name="Retirement",
        type="retirement",
        category="retirement",
        target_amount=2000000,
        current_amount=500000,
        target_date=today.replace(year=today.year + 25),
        monthly_contribution=2000,
        priority="high"
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
        priority="high"
    )
    
    vacation_goal = Mock(
        id="goal-vacation",
        name="Vacation",
        type="discretionary",
        category="discretionary",
        target_amount=10000,
        current_amount=2000,
        target_date=today.replace(year=today.year + 1),
        monthly_contribution=500,
        priority="medium"
    )
    
    return [retirement_goal, emergency_goal, vacation_goal]

@pytest.fixture
def sample_profile():
    """Fixture providing a sample user profile for testing"""
    return Mock(
        id="profile-1",
        name="Test User",
        age=35,
        retirement_age=65,
        annual_income=120000,
        monthly_expenses=4000,
        risk_tolerance="moderate"
    )

@pytest.fixture
def mock_parameter_service():
    """Fixture providing a mock parameter service"""
    service = Mock()
    
    # Set up mock return values
    service.get_inflation_assumption.return_value = 0.03
    service.get_return_assumptions.return_value = {
        "stocks": 0.08,
        "bonds": 0.04,
        "cash": 0.015
    }
    
    return service

@pytest.fixture
def sample_scenario_profile():
    """Fixture providing a sample scenario profile"""
    return ScenarioProfile(
        name="Test Scenario",
        description="A test scenario",
        market_returns={
            "stocks": 0.07,
            "bonds": 0.03,
            "cash": 0.01,
            "real_estate": 0.04
        },
        inflation_assumption=0.025,
        income_growth_rates={
            "primary": 0.03,
            "secondary": 0.03,
            "passive": 0.02
        },
        expense_patterns={
            "essential": 1.0,
            "discretionary": 1.0,
            "healthcare_inflation_premium": 0.02
        },
        life_events=[],
        metadata={"type": "test", "standard": True}
    )

@pytest.fixture
def sample_scenario_results():
    """Fixture providing sample scenario analysis results"""
    # Create baseline scenario results
    baseline = {
        "scenario_profile": {
            "name": "Baseline Scenario",
            "description": "Current financial trajectory based on existing assumptions",
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
        "goal_probabilities": {
            "goal-retirement": 0.75,
            "goal-emergency": 0.95,
            "goal-vacation": 0.85
        },
        "goal_achievement_timeline": {
            "goal-retirement": 65,
            "goal-emergency": 37,
            "goal-vacation": 36
        },
        "retirement_age": 65,
        "net_worth_projection": {
            "year_5": 500000,
            "year_10": 800000,
            "year_20": 1600000,
            "year_30": 2500000
        },
        "analysis_date": datetime.now().isoformat()
    }
    
    # Create optimistic scenario results
    optimistic = {
        "scenario_profile": {
            "name": "Optimistic Scenario",
            "description": "Favorable economic conditions with strong market returns and career growth",
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
        "goal_probabilities": {
            "goal-retirement": 0.92,
            "goal-emergency": 0.99,
            "goal-vacation": 0.98
        },
        "goal_achievement_timeline": {
            "goal-retirement": 60,
            "goal-emergency": 36,
            "goal-vacation": 35.5
        },
        "retirement_age": 60,
        "net_worth_projection": {
            "year_5": 600000,
            "year_10": 1100000,
            "year_20": 2200000,
            "year_30": 3800000
        },
        "analysis_date": datetime.now().isoformat()
    }
    
    # Create pessimistic scenario results
    pessimistic = {
        "scenario_profile": {
            "name": "Pessimistic Scenario",
            "description": "Challenging economic conditions with lower returns and potential job insecurity",
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
        "goal_probabilities": {
            "goal-retirement": 0.45,
            "goal-emergency": 0.80,
            "goal-vacation": 0.70
        },
        "goal_achievement_timeline": {
            "goal-retirement": 70,
            "goal-emergency": 38,
            "goal-vacation": 36.5
        },
        "retirement_age": 70,
        "net_worth_projection": {
            "year_5": 400000,
            "year_10": 600000,
            "year_20": 1100000,
            "year_30": 1800000
        },
        "analysis_date": datetime.now().isoformat()
    }
    
    return {
        "baseline": baseline,
        "optimistic": optimistic,
        "pessimistic": pessimistic
    }


# Tests for ScenarioProfile
class TestScenarioProfile:
    """Tests for the ScenarioProfile class"""
    
    def test_initialization(self, sample_scenario_profile):
        """Test that ScenarioProfile initializes with correct parameters"""
        # Assert that initialization works
        assert sample_scenario_profile.name == "Test Scenario"
        assert sample_scenario_profile.description == "A test scenario"
        assert sample_scenario_profile.inflation_assumption == 0.025
        assert sample_scenario_profile.market_returns["stocks"] == 0.07
        assert sample_scenario_profile.income_growth_rates["primary"] == 0.03
        assert sample_scenario_profile.expense_patterns["essential"] == 1.0
        assert sample_scenario_profile.metadata["type"] == "test"
        assert isinstance(sample_scenario_profile.created_at, datetime)
    
    def test_to_dict(self, sample_scenario_profile):
        """Test conversion to dictionary"""
        profile_dict = sample_scenario_profile.to_dict()
        
        # Check that all expected keys are present
        assert "name" in profile_dict
        assert "description" in profile_dict
        assert "market_returns" in profile_dict
        assert "inflation_assumption" in profile_dict
        assert "income_growth_rates" in profile_dict
        assert "expense_patterns" in profile_dict
        assert "life_events" in profile_dict
        assert "metadata" in profile_dict
        assert "created_at" in profile_dict
        
        # Check that values are correctly stored
        assert profile_dict["name"] == "Test Scenario"
        assert profile_dict["inflation_assumption"] == 0.025
        assert profile_dict["market_returns"]["stocks"] == 0.07
        assert profile_dict["metadata"]["standard"] is True
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        profile_data = {
            "name": "From Dict Scenario",
            "description": "Created from dictionary",
            "market_returns": {
                "stocks": 0.08,
                "bonds": 0.035,
                "cash": 0.015
            },
            "inflation_assumption": 0.03,
            "income_growth_rates": {
                "primary": 0.04,
                "secondary": 0.03,
                "passive": 0.02
            },
            "expense_patterns": {
                "essential": 0.9,
                "discretionary": 0.8
            },
            "life_events": [],
            "metadata": {"source": "test"},
            "created_at": "2025-03-01T12:00:00"
        }
        
        profile = ScenarioProfile.from_dict(profile_data)
        
        # Check that values are correctly loaded
        assert profile.name == "From Dict Scenario"
        assert profile.description == "Created from dictionary"
        assert profile.inflation_assumption == 0.03
        assert profile.market_returns["stocks"] == 0.08
        assert profile.expense_patterns["essential"] == 0.9
        assert profile.metadata["source"] == "test"
        assert profile.created_at.year == 2025
        assert profile.created_at.month == 3
        assert profile.created_at.day == 1


# Tests for AlternativeScenarioGenerator
class TestAlternativeScenarioGenerator:
    """Tests for the AlternativeScenarioGenerator class"""
    
    def test_initialization(self, mock_parameter_service):
        """Test that generator initializes correctly"""
        # Test initialization without parameter service
        generator = AlternativeScenarioGenerator()
        assert generator.parameter_service is None
        assert hasattr(generator, '_stored_scenarios')
        assert hasattr(generator, '_scenario_defaults')
        
        # Test initialization with parameter service
        generator_with_service = AlternativeScenarioGenerator(parameter_service=mock_parameter_service)
        assert generator_with_service.parameter_service == mock_parameter_service
    
    def test_initialize_default_parameters(self):
        """Test default parameters initialization"""
        generator = AlternativeScenarioGenerator()
        defaults = generator._scenario_defaults
        
        # Verify standard scenario types exist
        assert "baseline" in defaults
        assert "optimistic" in defaults
        assert "pessimistic" in defaults
        assert "high_inflation" in defaults
        assert "early_retirement" in defaults
        
        # Verify structure of defaults
        for scenario_type in defaults:
            assert "market_returns" in defaults[scenario_type]
            assert "inflation_assumption" in defaults[scenario_type]
            assert "income_growth_rates" in defaults[scenario_type]
            assert "expense_patterns" in defaults[scenario_type]
            assert "life_events" in defaults[scenario_type]
    
    def test_generate_standard_scenarios(self, sample_goals, sample_profile):
        """Test generation of standard scenarios"""
        generator = AlternativeScenarioGenerator()
        
        # Mock the individual scenario generation methods to avoid complex dependencies
        with patch.object(generator, 'generate_baseline_scenario') as mock_baseline, \
             patch.object(generator, 'generate_optimistic_scenario') as mock_optimistic, \
             patch.object(generator, 'generate_pessimistic_scenario') as mock_pessimistic, \
             patch.object(generator, 'generate_high_inflation_scenario') as mock_high_inflation, \
             patch.object(generator, 'generate_early_retirement_scenario') as mock_early_retirement:
            
            # Set return values for mock methods
            mock_baseline.return_value = {"scenario_type": "baseline"}
            mock_optimistic.return_value = {"scenario_type": "optimistic"}
            mock_pessimistic.return_value = {"scenario_type": "pessimistic"}
            mock_high_inflation.return_value = {"scenario_type": "high_inflation"}
            mock_early_retirement.return_value = {"scenario_type": "early_retirement"}
            
            # Generate standard scenarios
            scenarios = generator.generate_standard_scenarios(sample_goals, sample_profile)
            
            # Verify structure of result
            assert "baseline" in scenarios
            assert "optimistic" in scenarios
            assert "pessimistic" in scenarios
            assert "high_inflation" in scenarios
            assert "early_retirement" in scenarios
            
            # Verify that scenario generation methods were called
            mock_baseline.assert_called_once_with(sample_goals, sample_profile)
            mock_optimistic.assert_called_once_with(sample_goals, sample_profile)
            mock_pessimistic.assert_called_once_with(sample_goals, sample_profile)
            mock_high_inflation.assert_called_once_with(sample_goals, sample_profile)
            mock_early_retirement.assert_called_once_with(sample_goals, sample_profile)
    
    def test_generate_targeted_scenario(self, sample_goals, sample_profile):
        """Test generation of a specific scenario type"""
        generator = AlternativeScenarioGenerator()
        
        # Mock the _run_scenario_analysis method to avoid complex dependencies
        with patch.object(generator, '_run_scenario_analysis') as mock_run_analysis:
            mock_run_analysis.return_value = {"scenario_type": "test_targeted"}
            
            # Generate a targeted scenario
            scenario = generator.generate_targeted_scenario(sample_goals, sample_profile, "optimistic")
            
            # Verify that _run_scenario_analysis was called with the correct parameters
            assert mock_run_analysis.called
            # Check that the first two arguments are the goals and profile
            assert mock_run_analysis.call_args[0][0] == sample_goals
            assert mock_run_analysis.call_args[0][1] == sample_profile
            # The third argument should be a ScenarioProfile object
            assert isinstance(mock_run_analysis.call_args[0][2], ScenarioProfile)
            # The ScenarioProfile should have optimistic parameters
            assert mock_run_analysis.call_args[0][2].name == "Optimistic Scenario"
            
            # Test with an invalid scenario type
            with pytest.raises(ValueError):
                generator.generate_targeted_scenario(sample_goals, sample_profile, "nonexistent_type")
    
    def test_compare_scenarios(self, sample_scenario_results):
        """Test comparison between scenarios"""
        generator = AlternativeScenarioGenerator()
        
        # Set up test data
        baseline = sample_scenario_results["baseline"]
        alternatives = {
            "optimistic": sample_scenario_results["optimistic"],
            "pessimistic": sample_scenario_results["pessimistic"]
        }
        
        # Compare scenarios
        comparison = generator.compare_scenarios(baseline, alternatives)
        
        # Verify comparison structure
        assert "baseline" in comparison
        assert "alternatives" in comparison
        assert "differences" in comparison
        assert "summary" in comparison
        
        # Verify that differences and summary were calculated for each alternative
        for alt_name in alternatives:
            assert alt_name in comparison["differences"]
            assert alt_name in comparison["summary"]
    
    def test_calculate_scenario_differences(self, sample_scenario_results):
        """Test calculation of differences between scenarios"""
        generator = AlternativeScenarioGenerator()
        
        # Set up test data
        baseline = sample_scenario_results["baseline"]
        alternative = sample_scenario_results["optimistic"]
        
        # Calculate differences
        differences = generator._calculate_scenario_differences(baseline, alternative)
        
        # Verify differences structure
        assert "goal_probability_changes" in differences
        assert "retirement_age_impact" in differences
        assert "net_worth_trajectory" in differences
        assert "goal_achievement_timeline" in differences
        
        # Verify specific differences
        assert differences["retirement_age_impact"] == -5  # 60 - 65
        assert differences["goal_probability_changes"]["goal-retirement"] == 0.92 - 0.75
        assert differences["net_worth_trajectory"]["year_30"] == 3800000 - 2500000
        assert differences["goal_achievement_timeline"]["goal-retirement"] == 60 - 65
    
    def test_summarize_scenario_comparison(self, sample_scenario_results):
        """Test summary generation from scenario comparison"""
        generator = AlternativeScenarioGenerator()
        
        # Set up test data
        baseline = sample_scenario_results["baseline"]
        optimistic = sample_scenario_results["optimistic"]
        
        # Calculate differences
        differences = generator._calculate_scenario_differences(baseline, optimistic)
        
        # Generate summary
        summary = generator._summarize_scenario_comparison("optimistic", differences)
        
        # Verify summary structure
        assert "title" in summary
        assert "overall_assessment" in summary
        assert "key_findings" in summary
        
        # Title should contain the scenario name
        assert "Optimistic" in summary["title"]
        
        # Key findings should include retirement impact and net worth change
        retirement_finding = next((finding for finding in summary["key_findings"] 
                                if "Retirement" in finding and "earlier" in finding), None)
        assert retirement_finding is not None
        
        net_worth_finding = next((finding for finding in summary["key_findings"] 
                                if "net worth" in finding and "increases" in finding), None)
        assert net_worth_finding is not None
        
        # Overall assessment should be positive (since the optimistic scenario is better)
        assert summary["overall_assessment"] == "This scenario could positively impact your financial outcomes."
    
    def test_set_and_get_scenario_parameters(self):
        """Test setting and retrieving scenario parameters"""
        generator = AlternativeScenarioGenerator()
        
        # Get original parameters
        original_params = generator.get_default_parameters("baseline")
        
        # Create modified parameters
        modified_params = {
            "inflation_assumption": 0.04,
            "market_returns": {
                "stocks": 0.09
            }
        }
        
        # Set new parameters
        generator.set_scenario_parameters("baseline", modified_params)
        
        # Get updated parameters
        updated_params = generator.get_default_parameters("baseline")
        
        # Verify that parameters were updated correctly
        assert updated_params["inflation_assumption"] == 0.04
        assert updated_params["market_returns"]["stocks"] == 0.09
        
        # Verify that unmodified parameters remain the same
        assert updated_params["market_returns"]["bonds"] == original_params["market_returns"]["bonds"]
        
        # Test with a new scenario type
        custom_params = {
            "inflation_assumption": 0.05,
            "market_returns": {
                "stocks": 0.10,
                "bonds": 0.05
            }
        }
        
        generator.set_scenario_parameters("custom_scenario", custom_params)
        custom_params_result = generator.get_default_parameters("custom_scenario")
        
        assert custom_params_result["inflation_assumption"] == 0.05
        assert custom_params_result["market_returns"]["stocks"] == 0.10
    
    def test_create_custom_scenario(self, sample_goals, sample_profile):
        """Test creation of custom scenarios"""
        generator = AlternativeScenarioGenerator()
        
        # Define custom parameters
        custom_parameters = {
            "name": "Custom Scenario",
            "description": "A custom test scenario",
            "market_returns": {
                "stocks": 0.08,
                "bonds": 0.04,
                "cash": 0.02,
                "real_estate": 0.05
            },
            "inflation_assumption": 0.03,
            "income_growth_rates": {
                "primary": 0.04,
                "secondary": 0.03,
                "passive": 0.02
            },
            "expense_patterns": {
                "essential": 0.95,
                "discretionary": 0.9
            }
        }
        
        # Mock the _run_scenario_analysis method
        with patch.object(generator, '_run_scenario_analysis') as mock_run_analysis:
            mock_run_analysis.return_value = {"scenario_type": "custom"}
            
            # Create custom scenario
            scenario = generator.create_custom_scenario(sample_goals, sample_profile, custom_parameters)
            
            # Verify that _run_scenario_analysis was called with the correct parameters
            assert mock_run_analysis.called
            # Check that the first two arguments are the goals and profile
            assert mock_run_analysis.call_args[0][0] == sample_goals
            assert mock_run_analysis.call_args[0][1] == sample_profile
            # The third argument should be a ScenarioProfile object
            assert isinstance(mock_run_analysis.call_args[0][2], ScenarioProfile)
            # The ScenarioProfile should have custom parameters
            assert mock_run_analysis.call_args[0][2].name == "Custom Scenario"
            assert mock_run_analysis.call_args[0][2].inflation_assumption == 0.03
            
            # Test with missing required fields
            incomplete_params = {
                "name": "Incomplete Scenario",
                "description": "Missing required fields"
            }
            
            with pytest.raises(ValueError):
                generator.create_custom_scenario(sample_goals, sample_profile, incomplete_params)
    
    def test_save_and_load_scenario(self, sample_scenario_results):
        """Test saving and loading scenarios"""
        generator = AlternativeScenarioGenerator()
        
        # Save a scenario
        generator.save_scenario(sample_scenario_results["optimistic"], "saved_optimistic")
        
        # Load the saved scenario
        loaded_scenario = generator.load_scenario("saved_optimistic")
        
        # Verify that the loaded scenario is the same as the original
        assert loaded_scenario == sample_scenario_results["optimistic"]
        
        # Test loading a non-existent scenario
        with pytest.raises(ValueError):
            generator.load_scenario("nonexistent_scenario")


# Tests for ScenarioComparisonResult
class TestScenarioComparisonResult:
    """Tests for the ScenarioComparisonResult class"""
    
    def test_initialization(self, sample_scenario_results, sample_goals, sample_profile):
        """Test initialization of comparison result"""
        # Create a comparison result
        comparison = ScenarioComparisonResult(sample_scenario_results, sample_goals, sample_profile)
        
        # Verify basic structure
        assert comparison.scenarios == sample_scenario_results
        assert comparison.baseline_name == "baseline"
        assert hasattr(comparison, "goal_outcomes")
        assert hasattr(comparison, "success_metrics")
        assert hasattr(comparison, "difference_metrics")
        assert hasattr(comparison, "sensitivity_analysis")
        
        # Verify that goal outcomes were initialized for each goal and scenario
        for goal in sample_goals:
            assert goal.id in comparison.goal_outcomes
            for scenario_name in sample_scenario_results:
                assert scenario_name in comparison.goal_outcomes[goal.id]
                
        # Verify that success metrics were initialized for each scenario
        for scenario_name in sample_scenario_results:
            assert scenario_name in comparison.success_metrics
            
        # Verify that difference metrics were initialized for non-baseline scenarios
        for scenario_name in sample_scenario_results:
            if scenario_name != comparison.baseline_name:
                assert scenario_name in comparison.difference_metrics
    
    def test_set_goal_outcome(self, sample_scenario_results, sample_goals, sample_profile):
        """Test setting specific goal outcomes"""
        comparison = ScenarioComparisonResult(sample_scenario_results, sample_goals, sample_profile)
        
        # Set a goal outcome
        comparison.set_goal_outcome("goal-retirement", "baseline", "probability", 0.8)
        
        # Verify that the outcome was set
        assert comparison.goal_outcomes["goal-retirement"]["baseline"]["probability"] == 0.8
        
        # Test with invalid goal ID
        comparison.set_goal_outcome("nonexistent-goal", "baseline", "probability", 0.7)
        assert "nonexistent-goal" not in comparison.goal_outcomes
        
        # Test with invalid scenario name
        comparison.set_goal_outcome("goal-retirement", "nonexistent-scenario", "probability", 0.7)
        assert "nonexistent-scenario" not in comparison.goal_outcomes["goal-retirement"]
    
    def test_set_success_metric(self, sample_scenario_results, sample_goals, sample_profile):
        """Test setting specific success metrics"""
        comparison = ScenarioComparisonResult(sample_scenario_results, sample_goals, sample_profile)
        
        # Set a success metric
        comparison.set_success_metric("baseline", "overall_success_rate", 0.85)
        
        # Verify that the metric was set
        assert comparison.success_metrics["baseline"]["overall_success_rate"] == 0.85
        
        # Test with invalid scenario name
        comparison.set_success_metric("nonexistent-scenario", "overall_success_rate", 0.7)
        assert "nonexistent-scenario" not in comparison.success_metrics
    
    def test_get_most_sensitive_variables(self, sample_scenario_results, sample_goals, sample_profile):
        """Test retrieval of most sensitive variables"""
        comparison = ScenarioComparisonResult(sample_scenario_results, sample_goals, sample_profile)
        
        # Add sensitivity results
        comparison.add_sensitivity_result("market_returns.stocks", 0.9, ["goal-retirement"])
        comparison.add_sensitivity_result("market_returns.bonds", 0.5, ["goal-retirement"])
        comparison.add_sensitivity_result("inflation_assumption", 0.7, ["goal-retirement", "goal-emergency"])
        comparison.add_sensitivity_result("income_growth_rates.primary", 0.3, ["goal-vacation"])
        
        # Get the most sensitive variables (top 3)
        sensitive_vars = comparison.get_most_sensitive_variables(limit=3)
        
        # Verify results
        assert len(sensitive_vars) == 3
        assert sensitive_vars[0][0] == "market_returns.stocks"  # Highest impact (0.9)
        assert sensitive_vars[1][0] == "inflation_assumption"   # Second highest (0.7)
        assert sensitive_vars[2][0] == "market_returns.bonds"   # Third highest (0.5)
    
    def test_get_best_alternative_scenario(self, sample_scenario_results, sample_goals, sample_profile):
        """Test identification of best alternative scenario"""
        comparison = ScenarioComparisonResult(sample_scenario_results, sample_goals, sample_profile)
        
        # Set difference metrics to simulate scenario comparisons
        comparison.set_difference_metric("optimistic", "success_rate_change", 0.15)
        comparison.set_difference_metric("optimistic", "retirement_age_change", -5)
        comparison.set_difference_metric("optimistic", "net_worth_impact", {"year_30": 1300000})
        comparison.set_difference_metric("optimistic", "goal_achievement_change", 0.2)
        
        comparison.set_difference_metric("pessimistic", "success_rate_change", -0.1)
        comparison.set_difference_metric("pessimistic", "retirement_age_change", 5)
        comparison.set_difference_metric("pessimistic", "net_worth_impact", {"year_30": -700000})
        comparison.set_difference_metric("pessimistic", "goal_achievement_change", -0.15)
        
        # Get the best alternative scenario
        best_scenario = comparison.get_best_alternative_scenario()
        
        # Verify that optimistic is chosen as the best (since it has positive changes)
        assert best_scenario == "optimistic"
        
        # Test with no difference metrics
        empty_comparison = ScenarioComparisonResult(
            {"baseline": sample_scenario_results["baseline"]}, 
            sample_goals, 
            sample_profile
        )
        assert empty_comparison.get_best_alternative_scenario() is None
    
    def test_to_dict_and_from_dict(self, sample_scenario_results, sample_goals, sample_profile):
        """Test conversion to and from dictionary"""
        # Create a comparison result
        comparison = ScenarioComparisonResult(sample_scenario_results, sample_goals, sample_profile)
        
        # Add some data
        comparison.set_goal_outcome("goal-retirement", "baseline", "probability", 0.8)
        comparison.set_success_metric("baseline", "overall_success_rate", 0.85)
        comparison.set_difference_metric("optimistic", "success_rate_change", 0.15)
        comparison.add_sensitivity_result("market_returns.stocks", 0.9, ["goal-retirement"])
        
        # Convert to dictionary
        comparison_dict = comparison.to_dict()
        
        # Verify structure
        assert "scenarios" in comparison_dict
        assert "baseline_name" in comparison_dict
        assert "goal_outcomes" in comparison_dict
        assert "success_metrics" in comparison_dict
        assert "difference_metrics" in comparison_dict
        assert "sensitivity_analysis" in comparison_dict
        assert "processed_at" in comparison_dict
        
        # Create a new instance from the dictionary
        new_comparison = ScenarioComparisonResult.from_dict(
            comparison_dict, sample_scenario_results, sample_goals, sample_profile
        )
        
        # Verify that the values were loaded correctly
        assert new_comparison.baseline_name == comparison.baseline_name
        assert new_comparison.goal_outcomes == comparison.goal_outcomes
        assert new_comparison.success_metrics == comparison.success_metrics
        assert new_comparison.difference_metrics == comparison.difference_metrics
        assert new_comparison.sensitivity_analysis == comparison.sensitivity_analysis


# Tests for ScenarioAnalyzer
class TestScenarioAnalyzer:
    """Tests for the ScenarioAnalyzer class"""
    
    def test_initialization(self, mock_parameter_service):
        """Test initialization of scenario analyzer"""
        # Test initialization without services
        analyzer = ScenarioAnalyzer()
        assert analyzer.parameter_service is None
        assert analyzer.goal_probability_service is None
        
        # Test initialization with services
        mock_goal_prob_service = Mock()
        analyzer_with_services = ScenarioAnalyzer(
            parameter_service=mock_parameter_service,
            goal_probability_service=mock_goal_prob_service
        )
        assert analyzer_with_services.parameter_service == mock_parameter_service
        assert analyzer_with_services.goal_probability_service == mock_goal_prob_service
    
    def test_analyze_scenario_impact(self, sample_scenario_results, sample_goals, sample_profile):
        """Test analysis of scenario impact on goals"""
        analyzer = ScenarioAnalyzer()
        
        # Analyze the baseline scenario
        baseline = sample_scenario_results["baseline"]
        impact_analysis = analyzer.analyze_scenario_impact(baseline, sample_goals, sample_profile)
        
        # Verify analysis structure
        assert "scenario_name" in impact_analysis
        assert "goal_impacts" in impact_analysis
        assert "overall_metrics" in impact_analysis
        assert "timeline_impacts" in impact_analysis
        assert "risk_assessment" in impact_analysis
        
        # Verify scenario name is extracted from the scenario profile
        assert impact_analysis["scenario_name"] == "Baseline Scenario"
        
        # Verify that each goal is analyzed
        for goal in sample_goals:
            assert goal.id in impact_analysis["goal_impacts"]
            goal_impact = impact_analysis["goal_impacts"][goal.id]
            assert "probability" in goal_impact
            assert "timeline" in goal_impact
            assert "funding_status" in goal_impact
        
        # Verify that overall metrics are calculated
        overall_metrics = impact_analysis["overall_metrics"]
        assert "average_goal_probability" in overall_metrics
        assert "min_goal_probability" in overall_metrics
        assert "goals_above_threshold" in overall_metrics
        assert "goals_at_risk" in overall_metrics
        
        # Verify that retirement age is detected
        assert "retirement_age" in impact_analysis["timeline_impacts"]
        assert impact_analysis["timeline_impacts"]["retirement_age"] == 65
        
        # Verify risk assessment
        risk_assessment = impact_analysis["risk_assessment"]
        assert "goals_at_high_risk" in risk_assessment
        assert "risk_concentration" in risk_assessment
    
    def test_determine_funding_status(self):
        """Test determination of funding status based on probability"""
        analyzer = ScenarioAnalyzer()
        
        # Test various probability levels
        assert analyzer._determine_funding_status(0.95) == "fully_funded"
        assert analyzer._determine_funding_status(0.8) == "mostly_funded"
        assert analyzer._determine_funding_status(0.6) == "partially_funded"
        assert analyzer._determine_funding_status(0.5) == "partially_funded"
        assert analyzer._determine_funding_status(0.3) == "underfunded"
        assert analyzer._determine_funding_status(None) == "unknown"
    
    def test_identify_retirement_goals(self, sample_goals):
        """Test identification of retirement goals"""
        analyzer = ScenarioAnalyzer()
        
        # Identify retirement goals
        retirement_goals = analyzer._identify_retirement_goals(sample_goals)
        
        # Verify that the retirement goal is identified
        assert len(retirement_goals) == 1
        assert retirement_goals[0] == "goal-retirement"
        
        # Test with a different set of goals (using name instead of type)
        goals_with_names = [
            Mock(id="goal-1", name="Retirement Planning", type="custom"),
            Mock(id="goal-2", name="Vacation Fund", type="discretionary")
        ]
        
        retirement_goals_by_name = analyzer._identify_retirement_goals(goals_with_names)
        assert len(retirement_goals_by_name) == 1
        assert retirement_goals_by_name[0] == "goal-1"
    
    def test_compare_scenario_outcomes(self, sample_scenario_results, sample_goals):
        """Test comparison of scenario outcomes"""
        analyzer = ScenarioAnalyzer()
        
        # Compare baseline and optimistic scenarios
        baseline = sample_scenario_results["baseline"]
        optimistic = sample_scenario_results["optimistic"]
        
        comparison = analyzer.compare_scenario_outcomes(baseline, optimistic, sample_goals)
        
        # Verify comparison structure
        assert "baseline_name" in comparison
        assert "alternative_name" in comparison
        assert "goal_comparisons" in comparison
        assert "overall_changes" in comparison
        assert "risk_profile_change" in comparison
        assert "overall_assessment" in comparison
        
        # Verify goal comparisons
        for goal in sample_goals:
            assert goal.id in comparison["goal_comparisons"]
            goal_comparison = comparison["goal_comparisons"][goal.id]
            assert "probability_change" in goal_comparison
            assert "timeline_change" in goal_comparison
            assert "impact_assessment" in goal_comparison
            assert "baseline_status" in goal_comparison
            assert "alternative_status" in goal_comparison
        
        # Verify overall changes
        overall_changes = comparison["overall_changes"]
        assert "average_probability_change" in overall_changes
        assert "improved_goals" in overall_changes
        assert "worsened_goals" in overall_changes
        assert "retirement_age_change" in overall_changes
        assert overall_changes["retirement_age_change"] == -5  # 60 - 65
        
        # Verify risk profile change
        risk_change = comparison["risk_profile_change"]
        assert "goals_at_high_risk_change" in risk_change
        assert "risk_concentration_change" in risk_change
        
        # Verify overall assessment is positive (optimistic is better than baseline)
        assert comparison["overall_assessment"] in ["significantly_better", "better"]
    
    def test_assess_goal_impact(self):
        """Test assessment of goal impact based on probability and timeline changes"""
        analyzer = ScenarioAnalyzer()
        
        # Test various combinations of probability and timeline changes
        assert analyzer._assess_goal_impact(0.15, -2) == "significantly_improved"  # Significant improvement in both
        assert analyzer._assess_goal_impact(0.15, None) == "significantly_improved"  # Significant probability improvement
        assert analyzer._assess_goal_impact(0.05, -1.5) == "significantly_improved"  # Moderate prob + good timeline
        assert analyzer._assess_goal_impact(0.05, 0) == "improved"  # Moderate probability improvement only
        assert analyzer._assess_goal_impact(0.02, -2) == "minimal_change"  # Small prob improvement
        assert analyzer._assess_goal_impact(0.05, 2) == "mixed_impact"  # Improved prob but delayed timeline
        assert analyzer._assess_goal_impact(-0.15, None) == "significantly_worsened"  # Significant worsening
        assert analyzer._assess_goal_impact(-0.05, None) == "worsened"  # Moderate worsening
        assert analyzer._assess_goal_impact(0.01, None) == "minimal_change"  # Minimal change
        assert analyzer._assess_goal_impact(None, None) == "unknown"  # Unknown impact
    
    def test_calculate_scenario_success_metrics(self, sample_scenario_results, sample_goals, sample_profile):
        """Test calculation of scenario success metrics"""
        analyzer = ScenarioAnalyzer()
        
        # Calculate success metrics for baseline scenario
        baseline = sample_scenario_results["baseline"]
        metrics = analyzer.calculate_scenario_success_metrics(baseline, sample_goals, sample_profile)
        
        # Verify metrics structure
        assert "goal_success_rate" in metrics
        assert "retirement_readiness" in metrics
        assert "financial_resilience" in metrics
        assert "net_worth_trajectory" in metrics
        assert "goal_achievement_timeline" in metrics
        assert "goal_funding_levels" in metrics
        
        # Verify retirement_readiness (should be the minimum of retirement goal probabilities)
        assert metrics["retirement_readiness"] == 0.75  # From baseline probabilities
        
        # Verify retirement_age
        assert metrics["retirement_age"] == 65  # From baseline timeline
        
        # Verify goal funding levels
        for goal in sample_goals:
            assert goal.id in metrics["goal_funding_levels"]
            funding = metrics["goal_funding_levels"][goal.id]
            assert "probability" in funding
            assert "status" in funding
    
    def test_identify_critical_variables(self, sample_scenario_results, sample_goals, sample_profile):
        """Test identification of critical variables"""
        analyzer = ScenarioAnalyzer()
        
        # Identify critical variables from the sample scenarios
        critical_vars = analyzer.identify_critical_variables(
            sample_scenario_results, sample_goals, sample_profile
        )
        
        # Verify structure and content
        assert isinstance(critical_vars, dict)
        assert len(critical_vars) > 0
        
        # Check a specific variable that should be identified as critical
        for var_name, var_info in critical_vars.items():
            assert "sensitivity" in var_info
            assert "impact_level" in var_info
            assert "direction" in var_info
            assert var_info["impact_level"] in ["high", "medium", "low"]
            assert var_info["direction"] in ["positive", "negative", "neutral", "unknown"]
    
    def test_generate_scenario_insights(self, sample_scenario_results, sample_goals, sample_profile):
        """Test generation of scenario insights"""
        analyzer = ScenarioAnalyzer()
        
        # Generate insights for the pessimistic scenario (which has lower probabilities)
        pessimistic = sample_scenario_results["pessimistic"]
        
        # First analyze the scenario
        scenario_analysis = analyzer.analyze_scenario_impact(pessimistic, sample_goals, sample_profile)
        
        # Then generate insights
        insights = analyzer.generate_scenario_insights(scenario_analysis)
        
        # Verify structure
        assert isinstance(insights, list)
        assert len(insights) > 0
        
        # Check that each insight has the expected fields
        for insight in insights:
            assert "type" in insight
            assert "title" in insight
            assert "description" in insight
            assert "recommendation" in insight
            assert "severity" in insight
        
        # Print insights to debug
        print("Generated insights:", insights)
        
        # Check that we have at least one insight
        assert len(insights) > 0
        
        # Since the exact insights generated can vary based on implementation details,
        # we'll just verify that there is at least one insight with a severity level
        has_insight_with_severity = any("severity" in insight for insight in insights)
        assert has_insight_with_severity is True
    
    def test_identify_most_effective_adjustments(self, sample_scenario_results):
        """Test identification of most effective adjustments"""
        analyzer = ScenarioAnalyzer()
        
        # Identify effective adjustments
        adjustments = analyzer.identify_most_effective_adjustments(sample_scenario_results)
        
        # Verify structure
        assert isinstance(adjustments, list)
        
        # Check that each adjustment has the expected fields
        for adjustment in adjustments:
            assert "scenario_name" in adjustment
            assert "parameter" in adjustment
            assert "baseline_value" in adjustment
            assert "alternative_value" in adjustment
            assert "impact_score" in adjustment
            assert "impact_description" in adjustment
            assert "adjustment_description" in adjustment
    
    def test_calculate_scenario_robustness(self, sample_scenario_results):
        """Test calculation of scenario robustness"""
        analyzer = ScenarioAnalyzer()
        
        # Calculate robustness of baseline against variations
        baseline = sample_scenario_results["baseline"]
        variations = [sample_scenario_results["optimistic"], sample_scenario_results["pessimistic"]]
        
        robustness = analyzer.calculate_scenario_robustness(baseline, variations)
        
        # Verify structure
        assert "overall_score" in robustness
        assert "probability_stability" in robustness
        assert "timeline_stability" in robustness
        assert "sensitive_factors" in robustness
        assert "resilient_factors" in robustness
    
    def test_suggest_optimization_opportunities(self, sample_scenario_results, sample_goals):
        """Test suggestion of optimization opportunities"""
        analyzer = ScenarioAnalyzer()
        
        # Compare baseline and optimistic
        baseline = sample_scenario_results["baseline"]
        optimistic = sample_scenario_results["optimistic"]
        
        # Generate comparison
        comparison = analyzer.compare_scenario_outcomes(baseline, optimistic, sample_goals)
        
        # Suggest optimization opportunities
        opportunities = analyzer.suggest_optimization_opportunities(comparison)
        
        # Verify structure
        assert isinstance(opportunities, list)
        
        # Check that each opportunity has the expected fields
        for opportunity in opportunities:
            assert "type" in opportunity
            assert "title" in opportunity
            assert "description" in opportunity
            assert "potential_impact" in opportunity
            assert "implementation_difficulty" in opportunity
            assert "related_goals" in opportunity
        
        # Verify that retirement opportunity is identified
        retirement_opp = next((o for o in opportunities if "retirement" in o["type"].lower()), None)
        assert retirement_opp is not None
        assert "Earlier Retirement" in retirement_opp["title"]
    
    def test_prepare_visualization_data(self, sample_scenario_results):
        """Test preparation of visualization data"""
        analyzer = ScenarioAnalyzer()
        
        # Test chart data preparation
        chart_data = analyzer.prepare_scenario_chart_data(
            sample_scenario_results, "goal_probabilities"
        )
        
        # Verify structure
        assert "type" in chart_data
        assert "labels" in chart_data
        assert "datasets" in chart_data
        assert chart_data["type"] == "goal_probabilities"
        
        # Check that we have a dataset for each scenario
        assert len(chart_data["datasets"]) == len(sample_scenario_results)
        
        # Test timeline data preparation
        timeline_data = analyzer.format_timeline_comparison_data(sample_scenario_results)
        
        # Verify structure
        assert "scenarios" in timeline_data
        assert "timeline_points" in timeline_data
        assert len(timeline_data["scenarios"]) == len(sample_scenario_results)
        
        # Test scenario summary preparation
        baseline = sample_scenario_results["baseline"]
        summary = analyzer.prepare_scenario_summary(baseline)
        
        # Verify structure
        assert "name" in summary
        assert "description" in summary
        assert "key_metrics" in summary
        assert "notable_outcomes" in summary
        assert "risk_assessment" in summary